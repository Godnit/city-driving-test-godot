from pathlib import Path
import re

path = Path('src/com/godnit/circlefootballlite/MainActivity.java')
s = path.read_text(encoding='utf-8')


def replace_method(text, name, replacement):
    pattern = (r'(?m)^        (?:@Override\s+)?(?:(?:public|protected|private)\s+)?'
               r'(?:static\s+)?(?:void|float|int|boolean|short\[\]|String|MediaPlayer)\s+'
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

# Human movement remains responsive, but after a kick the controlled disc is
# briefly prevented from immediately driving back into the ball. This removes
# the old "holding/sticking to the ball" feeling without freezing the player.
update_human = r'''        void updateHuman(float dt){
            Disc d=blue[0];
            float speed=300*s;
            float wx=joyNX*speed,wy=joyNY*speed;
            float k=Math.min(1f,dt*15f);
            d.vx+=(wx-d.vx)*k;d.vy+=(wy-d.vy)*k;

            // Release window after KICK: cancel only the velocity component that
            // would drive the player straight back into the just-kicked ball.
            if(d.kickCd>.13f){
                float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);
                if(l<kickReach()+24*s && l>1f){
                    float nx=dx/l,ny=dy/l;
                    float toward=d.vx*nx+d.vy*ny;
                    if(toward>0f){
                        d.vx-=nx*toward*.90f;
                        d.vy-=ny*toward*.90f;
                    }
                }
            }

            if(joyPointer<0){
                float damp=(float)Math.pow(.82,dt*60);
                d.vx*=damp;d.vy*=damp;
            }
        }'''
s = replace_method(s, 'updateHuman', update_human)

# Full 360-degree human kick control. When the joystick is held, its direction
# is the shot direction exactly (not merely a small steering influence). The
# ball is released to the outside edge of the controlled disc before impulse so
# a backward/sideways shot cannot remain trapped inside the player's collider.
do_kick = r'''        void doKick(){
            Disc d=blue[0];
            if(d.kickCd>0)return;

            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);
            if(l>kickReach())return;
            if(l<1f)l=1f;
            float contactX=dx/l,contactY=dy/l;

            float aimX=contactX,aimY=contactY;
            float jl=len(joyNX,joyNY);
            if(jl>.12f){
                // True free aim: the joystick can shoot in any 360-degree direction,
                // even opposite the side where the ball touched the player.
                aimX=joyNX/jl;
                aimY=joyNY/jl;
            }

            // Put the ball just outside the player on the chosen shot side. This is
            // an arcade-style release that prevents the player from continuing to
            // "carry" or pin the ball after pressing KICK.
            float release=discR+ballR+7.0f*s;
            bx=d.x+aimX*release;
            by=d.y+aimY*release;
            bx=clamp(bx,pitch.left+ballR,pitch.right-ballR);
            by=clamp(by,pitch.top+ballR,pitch.bottom-ballR);

            float power=735*s;
            // The chosen direction dominates old ball momentum so a 180-degree shot
            // actually changes direction instead of being dragged by the previous roll.
            bvx=bvx*.10f+aimX*power+d.vx*.08f;
            bvy=bvy*.10f+aimY*power+d.vy*.08f;
            limitBallSpeed(950*s);

            // Small recoil creates visible separation and stops instant re-contact.
            d.vx-=aimX*95*s;
            d.vy-=aimY*95*s;
            d.kickCd=.30f;

            spawnKickBurst(aimX,aimY,power);
            haptic(20);
            playSfx(SFX_KICK);
        }'''
s = replace_method(s, 'doKick', do_kick)

# Keep this test build separate from v1.8.
s = s.replace('circle_football_v18', 'circle_football_v19')
path.write_text(s, encoding='utf-8')

manifest = Path('AndroidManifest.xml')
m = manifest.read_text(encoding='utf-8')
m = m.replace('com.godnit.circlefootballlite.v18', 'com.godnit.circlefootballlite.v19')
m = re.sub(r'android:versionCode="\d+"', 'android:versionCode="10"', m, count=1)
m = re.sub(r'android:versionName="[^"]+"', 'android:versionName="1.9.0"', m, count=1)
manifest.write_text(m, encoding='utf-8')

print('Applied Circle Football v1.9 free 360 kick / clean release patch')
