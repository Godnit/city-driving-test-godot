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

# v2.3: calmer match pace. Human and every CPU player use exactly the same
# running speed and response; difficulty affects decisions only.
update_human = r'''        void updateHuman(float dt){
            Disc d=blue[0];
            float speed=185f*s;
            float wx=joyNX*speed,wy=joyNY*speed;
            float k=Math.min(1f,dt*7.0f);
            d.vx+=(wx-d.vx)*k;
            d.vy+=(wy-d.vy)*k;
            if(joyPointer<0){
                float damp=(float)Math.pow(.78,dt*60f);
                d.vx*=damp;
                d.vy*=damp;
            }
        }'''
s = replace_method(s, 'updateHuman', update_human)

move_ai = r'''        void moveAiToward(Disc d,float tx,float ty,float dt){
            float dx=tx-d.x,dy=ty-d.y,l=len(dx,dy);
            float speed=185f*s;
            float wx=0f,wy=0f;
            if(l>2f*s){
                wx=dx/l*speed;
                wy=dy/l*speed;
            }
            float k=Math.min(1f,dt*7.0f);
            d.vx+=(wx-d.vx)*k;
            d.vy+=(wy-d.vy)*k;
        }'''
s = replace_method(s, 'moveAiToward', move_ai)

# Slightly larger but still close-range kick window. Shorter cooldown makes taps
# feel reliable without turning KICK into a remote shot.
kick_reach = r'''        float kickReach(){return discR+ballR+24f*s;}'''
s = replace_method(s, 'kickReach', kick_reach)

do_kick = r'''        void doKick(){
            Disc d=blue[0];
            if(d.kickCd>0f)return;
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);
            if(l>kickReach())return;
            if(l<1f){dx=1f;dy=0f;l=1f;}
            float nx=dx/l,ny=dy/l;
            float power=520f*s;
            bvx+=nx*power+d.vx*.12f;
            bvy+=ny*power+d.vy*.12f;
            limitBallSpeed(690f*s);
            d.kickCd=.17f;
            spawnKickBurst(nx,ny,power);
            haptic(16);
            playSfx(SFX_KICK);
        }'''
s = replace_method(s, 'doKick', do_kick)

# CPU uses the same ball-speed envelope as the human. Difficulty no longer grants
# stronger shots; only pass/shot intent changes the impulse.
cpu_kick = r'''        void cpuKick(Disc d,float power,float desiredX,float desiredY,boolean pass){
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);
            if(l<1f){dx=d.team==0?1f:-1f;dy=0f;l=1f;}
            if(l>kickReach())return;
            float nx=dx/l,ny=dy/l;
            float align=nx*desiredX+ny*desiredY;
            if(align<.78f)return;
            float ix=nx*.84f+desiredX*.16f,iy=ny*.84f+desiredY*.16f;
            float il=len(ix,iy);if(il<1f)il=1f;ix/=il;iy/=il;
            float eff=(pass?455f:515f)*s;
            bvx+=ix*eff+d.vx*.10f;
            bvy+=iy*eff+d.vy*.10f;
            limitBallSpeed(690f*s);
            d.kickCd=pass?.31f:.24f;
            spawnKickBurst(ix,iy,eff);
            playSfx(pass?SFX_PASS:SFX_KICK);
        }'''
s = replace_method(s, 'cpuKick', cpu_kick)

# Ball loses speed a little faster and is capped lower, so the entire match is
# calmer rather than only slowing the player discs.
s = s.replace('float fr=(float)Math.pow(.9885,dt*60f);bvx*=fr;bvy*=fr;',
              'float fr=(float)Math.pow(.9850,dt*60f);bvx*=fr;bvy*=fr;')
s = s.replace('limitBallSpeed(920*s);', 'limitBallSpeed(690*s);')
s = s.replace('limitBallSpeed(930*s);', 'limitBallSpeed(690*s);')
s = s.replace('limitBallSpeed(900*s);', 'limitBallSpeed(690*s);')

# Proper goal posts: the four post corners are real circular colliders. This
# prevents the old case where the ball entered the mouth, touched a post, then
# slipped through the side wall and came back out.
if 'void resolveGoalPost(float px,float py)' not in s:
    marker = '        void handleBallWalls(){'
    helper = r'''        void resolveGoalPost(float px,float py){
            float dx=bx-px,dy=by-py;
            float pr=5.0f*s,min=ballR+pr;
            float l=len(dx,dy);
            if(l>=min)return;
            if(l<.001f){dx=(bvx>=0?1f:-1f);dy=0f;l=1f;}
            float nx=dx/l,ny=dy/l;
            float overlap=min-l+.45f*s;
            bx+=nx*overlap;by+=ny*overlap;
            float rel=bvx*nx+bvy*ny;
            if(rel<0f){
                float impulse=-1.72f*rel;
                bvx+=nx*impulse;bvy+=ny*impulse;
            }
            bvx*=.94f;bvy*=.94f;
            if(wallSoundCooldown<=0f && len(bvx,bvy)>75f*s){
                playSfx(SFX_WALL);wallSoundCooldown=.11f;
            }
        }

'''
    if marker not in s: raise RuntimeError('handleBallWalls marker missing')
    s = s.replace(marker, helper + marker, 1)

handle_walls = r'''        void handleBallWalls(){
            float left=pitch.left,right=pitch.right,top=pitch.top,bottom=pitch.bottom;
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf;
            boolean bounced=false;

            if(by-ballR<top){by=top+ballR;bvy=Math.abs(bvy)*.76f;bounced=true;}
            if(by+ballR>bottom){by=bottom-ballR;bvy=-Math.abs(bvy)*.76f;bounced=true;}

            // Physical posts first, before deciding whether the ball is inside the mouth.
            resolveGoalPost(left,y1);resolveGoalPost(left,y2);
            resolveGoalPost(right,y1);resolveGoalPost(right,y2);

            boolean mouth=by>y1+ballR*.30f && by<y2-ballR*.30f;

            // Count a goal once most of the ball has crossed the line. Doing it here
            // avoids letting a scored ball travel behind the wall and escape again.
            if(mouth && bx>right+ballR*.58f){scoreGoal(true);return;}
            if(mouth && bx<left-ballR*.58f){scoreGoal(false);return;}

            if(!mouth){
                if(bx-ballR<left){bx=left+ballR;bvx=Math.abs(bvx)*.78f;bounced=true;}
                if(bx+ballR>right){bx=right-ballR;bvx=-Math.abs(bvx)*.78f;bounced=true;}
            }else if(bx<left || bx>right){
                // While the ball is partly across the goal line, the top/bottom of
                // the goal mouth act as short rails so it cannot cut through a post.
                float railTop=y1+ballR*.34f,railBottom=y2-ballR*.34f;
                if(by<railTop){by=railTop;bvy=Math.abs(bvy)*.72f;bounced=true;}
                if(by>railBottom){by=railBottom;bvy=-Math.abs(bvy)*.72f;bounced=true;}
            }

            if(bounced && wallSoundCooldown<=0f && len(bvx,bvy)>85f*s){
                playSfx(SFX_WALL);wallSoundCooldown=.10f;
            }
        }'''
s = replace_method(s, 'handleBallWalls', handle_walls)

# Crowd becomes excited mainly when the ball is actually approaching a goal,
# rather than simply because it happens to be near an end line.
update_game = r'''        void updateGame(float dt){
            if(!goldenGoal){
                matchTime-=dt;
                if(matchTime<=0){
                    matchTime=0;
                    if(blueScore==redScore) goldenGoal=true; else finishMatch();
                }
            }
            if(mode!=GAME)return;
            for(int i=0;i<teamSize;i++){
                blue[i].kickCd=Math.max(0,blue[i].kickCd-dt);
                red[i].kickCd=Math.max(0,red[i].kickCd-dt);
                blue[i].wallPlayTime=Math.max(0,blue[i].wallPlayTime-dt);
                red[i].wallPlayTime=Math.max(0,red[i].wallPlayTime-dt);
            }
            wallSoundCooldown=Math.max(0,wallSoundCooldown-dt);
            touchSoundCooldown=Math.max(0,touchSoundCooldown-dt);

            updateHuman(dt);
            chooseChasers();
            updateTeamAI(blue,red,0,blueChaser,dt);
            updateTeamAI(red,blue,1,redChaser,dt);

            int steps=Math.max(3,Math.min(14,(int)Math.ceil(dt/0.0034f)));
            float sub=dt/steps;
            for(int st=0;st<steps;st++) physicsStep(sub);
            updateParticles(dt);

            float dl=Math.abs(bx-pitch.left),dr=Math.abs(pitch.right-bx);
            float near=Math.min(dl,dr)/Math.max(1f,pitch.width());
            float threat=clamp((.31f-near)/.31f,0f,1f);
            float toward=(dl<dr)?Math.max(0f,-bvx):Math.max(0f,bvx);
            float approach=clamp(toward/(520f*s),0f,1f);
            float speedBoost=clamp(len(bvx,bvy)/(690f*s),0f,1f)*.16f;
            crowdExcitement=clamp(threat*(.42f+.58f*approach)+speedBoost,0f,1f);
            syncRealAudio();
        }'''
s = replace_method(s, 'updateGame', update_game)

# Cleaner volume balance and event timing. Real clips are also trimmed at build
# time, so kick/bounce sounds start at the exact physical event instead of late.
play_sfx = r'''        void playSfx(final int type){
            if(!sounds||!hostActive)return;
            initRealAudio();
            if(realSoundPool==null)return;
            int id=0;float vol=.65f,rate=1f;
            if(type==SFX_KICK){id=rng.nextBoolean()?sndKickA:sndKickB;vol=.68f;rate=.98f+rng.nextFloat()*.04f;}
            else if(type==SFX_PASS){id=sndKickB;vol=.46f;rate=1.04f;}
            else if(type==SFX_WALL){id=sndBallBounce;vol=.36f;rate=.97f+rng.nextFloat()*.05f;}
            else if(type==SFX_GOAL){id=sndGoalCheer;vol=.96f;rate=1f;}
            else if(type==SFX_WIN){id=sndGoalCheer;vol=.88f;rate=1.01f;}
            else if(type==SFX_LOSE){id=sndCrowdBurst;vol=.42f;rate=.98f;}
            else {id=sndUiClick;vol=.34f;}
            if(id!=0)realSoundPool.play(id,vol,vol,1,0,rate);
        }'''
s = replace_method(s, 'playSfx', play_sfx)

sync_audio = r'''        void syncRealAudio(){
            if(!sounds||!hostActive){stopAmbient();return;}
            initRealAudio();
            boolean match=(mode==GAME||mode==PAUSE||mode==RESULT);
            if(match){
                pausePlayer(menuMusicPlayer);
                if(crowdLoopPlayer!=null){
                    float v=(mode==GAME?.050f:.035f)+crowdExcitement*.075f;
                    try{crowdLoopPlayer.setVolume(v,v);}catch(Exception ignored){}
                }
                safeStart(crowdLoopPlayer);
            }else{
                pausePlayer(crowdLoopPlayer);
                if(menuMusicPlayer!=null)try{menuMusicPlayer.setVolume(.16f,.16f);}catch(Exception ignored){}
                safeStart(menuMusicPlayer);
            }
        }'''
s = replace_method(s, 'syncRealAudio', sync_audio)

# Separate app id for testing alongside v2.2.
s = s.replace('circle_football_v22', 'circle_football_v23')
path.write_text(s, encoding='utf-8')

manifest = Path('AndroidManifest.xml')
m = manifest.read_text(encoding='utf-8')
m = m.replace('com.godnit.circlefootballlite.v22', 'com.godnit.circlefootballlite.v23')
m = re.sub(r'android:versionCode="\d+"', 'android:versionCode="14"', m, count=1)
m = re.sub(r'android:versionName="[^"]+"', 'android:versionName="2.3.0"', m, count=1)
manifest.write_text(m, encoding='utf-8')

print('Applied Circle Football v2.3 slower ball, reliable kick, goal-post and audio timing patch')
