from pathlib import Path
import re

path = Path('src/com/godnit/circlefootballlite/MainActivity.java')
s = path.read_text(encoding='utf-8')


def replace_method(text, name, replacement):
    pattern = (r'(?m)^        (?:@Override\s+)?(?:(?:public|protected|private)\s+)?'
               r'(?:static\s+)?(?:void|float(?:\[\])?|int|boolean|short\[\]|String|MediaPlayer)\s+'
               + re.escape(name) + r'\s*\(')
    m = re.search(pattern, text)
    if not m:
        raise RuntimeError('method declaration not found: ' + name)
    line_start = m.start()
    brace = text.find('{', m.end())
    depth = 0
    end = None
    for i in range(brace, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        raise RuntimeError('unterminated method: ' + name)
    return text[:line_start] + replacement.rstrip() + text[end:]

# v2.1 deliberately returns to HaxBall-style control:
# - nobody possesses/attaches the ball
# - player movement pushes it through normal disc collisions
# - KICK adds an impulse only along the real player->ball contact normal
# - CPU uses the exact same kick rule; desired target only affects positioning.

# More HaxBall-like inertial movement. Default HaxBall uses player damping 0.96,
# and the ball uses damping about 0.99; we preserve that relationship here.
update_human = r'''        void updateHuman(float dt){
            Disc d=blue[0];
            float damp=(float)Math.pow(.96,dt*60f);
            d.vx*=damp;d.vy*=damp;

            float il=len(joyNX,joyNY);
            if(il>.025f){
                float ax=joyNX,ay=joyNY;
                if(il>1f){ax/=il;ay/=il;}
                float accel=520f*s;
                d.vx+=ax*accel*dt;
                d.vy+=ay*accel*dt;
            }
            limitDiscSpeed(d,215f*s);
        }'''
s = replace_method(s, 'updateHuman', update_human)

# CPUs obey the same acceleration/damping and nearly the same maximum speed.
# Difficulty changes reaction quality far more than raw speed.
move_ai = r'''        void moveAiToward(Disc d,float tx,float ty,float dt){
            float damp=(float)Math.pow(.96,dt*60f);
            d.vx*=damp;d.vy*=damp;

            float dx=tx-d.x,dy=ty-d.y,l=len(dx,dy);
            if(l>3f*s){
                float accel=(difficulty==0?475f:difficulty==1?505f:520f)*s;
                d.vx+=(dx/l)*accel*dt;
                d.vy+=(dy/l)*accel*dt;
            }
            limitDiscSpeed(d,215f*s);
        }'''
s = replace_method(s, 'moveAiToward', move_ai)

if 'void limitDiscSpeed(Disc d,float max)' not in s:
    marker = '        void moveAiToward(Disc d,float tx,float ty,float dt){'
    helper = r'''        void limitDiscSpeed(Disc d,float max){
            float l=len(d.vx,d.vy);
            if(l>max&&l>0f){d.vx=d.vx/l*max;d.vy=d.vy/l*max;}
        }

'''
    if marker not in s:
        raise RuntimeError('moveAiToward insertion marker missing')
    s = s.replace(marker, helper + marker, 1)

# Human kick: no aiming joystick, no teleport, no sticky possession. The ball's
# launch direction is determined by where the player's circle is touching it.
do_kick = r'''        void doKick(){
            Disc d=blue[0];
            if(d.kickCd>0f)return;
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);
            if(l>kickReach())return;
            if(l<1f){dx=1f;dy=0f;l=1f;}
            float nx=dx/l,ny=dy/l;
            float power=650f*s;
            bvx+=nx*power+d.vx*.12f;
            bvy+=ny*power+d.vy*.12f;
            limitBallSpeed(900f*s);
            d.kickCd=.28f;
            spawnKickBurst(nx,ny,power);
            haptic(18);
            playSfx(SFX_KICK);
        }'''
s = replace_method(s, 'doKick', do_kick)

# CPU kick follows the identical physical rule. desiredX/desiredY are used only
# to verify that the CPU has actually moved to the correct side of the ball.
cpu_kick = r'''        void cpuKick(Disc d,float power,float desiredX,float desiredY,boolean pass){
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);
            if(l<1f){dx=d.team==0?1f:-1f;dy=0f;l=1f;}
            if(l>kickReach())return;
            float nx=dx/l,ny=dy/l;
            float align=nx*desiredX+ny*desiredY;
            if(align<.80f)return;

            // Same rule as the human: actual contact normal determines the impulse.
            bvx+=nx*power+d.vx*.12f;
            bvy+=ny*power+d.vy*.12f;
            limitBallSpeed(900f*s);
            d.kickCd=pass?.43f:.34f;
            spawnKickBurst(nx,ny,power);
            playSfx(pass?SFX_PASS:SFX_KICK);
        }'''
s = replace_method(s, 'cpuKick', cpu_kick)

# Keep kicking close-range, like HaxBall: you must physically get around the
# ball to change its shot angle instead of remotely redirecting it.
kick_reach = r'''        float kickReach(){return discR+ballR+12f*s;}'''
s = replace_method(s, 'kickReach', kick_reach)

# Slightly soften CPU kick power. Hard is smarter/cleaner rather than just much stronger.
s = s.replace('cpuKick(d,isPass?580*s:(bank?610*s:(difficulty==0?570*s:difficulty==1?635*s:690*s)),dirX,dirY,isPass||bank);',
              'cpuKick(d,isPass?555*s:(bank?585*s:(difficulty==0?575*s:difficulty==1?605*s:625*s)),dirX,dirY,isPass||bank);')

# Make player/ball collision response closer to a clean elastic dribble instead
# of a hidden carry. Keep the ball fully independent for every player.
resolve_ball = r'''        void resolveBallDisc(Disc d){
            float dx=bx-d.x,dy=by-d.y,min=discR+ballR,dst=len(dx,dy);
            if(dst>=min)return;
            float nx,ny;
            if(dst<.001f){
                float rvx=bvx-d.vx,rvy=bvy-d.vy,rl=len(rvx,rvy);
                if(rl>.01f){nx=rvx/rl;ny=rvy/rl;}
                else{nx=d.team==0?1f:-1f;ny=0f;}
                dst=.001f;
            }else{nx=dx/dst;ny=dy/dst;}

            float overlap=min-dst+.55f*s;
            bx+=nx*overlap;
            by+=ny*overlap;

            float rel=(bvx-d.vx)*nx+(bvy-d.vy)*ny;
            if(rel<0f){
                // bCoef around 0.5: enough bounce to stay free, but controllable.
                float impulse=-1.50f*rel;
                bvx+=nx*impulse;
                bvy+=ny*impulse;
            }
            // Tiny velocity transfer makes natural dribbling possible without attachment.
            bvx+=d.vx*.010f;
            bvy+=d.vy*.010f;
        }'''
s = replace_method(s, 'resolveBallDisc', resolve_ball)

# Version identity/preferences.
s = s.replace('circle_football_v18', 'circle_football_v21')
path.write_text(s, encoding='utf-8')

manifest = Path('AndroidManifest.xml')
m = manifest.read_text(encoding='utf-8')
m = m.replace('com.godnit.circlefootballlite.v18', 'com.godnit.circlefootballlite.v21')
m = re.sub(r'android:versionCode="\d+"', 'android:versionCode="12"', m, count=1)
m = re.sub(r'android:versionName="[^"]+"', 'android:versionName="2.1.0"', m, count=1)
manifest.write_text(m, encoding='utf-8')

print('Applied Circle Football v2.1 HaxBall-style universal physics patch')
