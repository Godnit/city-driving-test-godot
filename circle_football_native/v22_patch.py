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

# Return to our arcade control from v1.8: one movement joystick + one normal KICK button.
# Everyone uses the same deliberately slower movement speed and the same response.
update_human = r'''        void updateHuman(float dt){
            Disc d=blue[0];
            float speed=220f*s;
            float wx=joyNX*speed,wy=joyNY*speed;
            float k=Math.min(1f,dt*8.5f);
            d.vx+=(wx-d.vx)*k;
            d.vy+=(wy-d.vy)*k;
            if(joyPointer<0){
                float damp=(float)Math.pow(.80,dt*60f);
                d.vx*=damp;
                d.vy*=damp;
            }
        }'''
s = replace_method(s, 'updateHuman', update_human)

move_ai = r'''        void moveAiToward(Disc d,float tx,float ty,float dt){
            float dx=tx-d.x,dy=ty-d.y,l=len(dx,dy);
            float speed=220f*s;
            float wx=0f,wy=0f;
            if(l>2f*s){
                wx=dx/l*speed;
                wy=dy/l*speed;
            }
            float k=Math.min(1f,dt*8.5f);
            d.vx+=(wx-d.vx)*k;
            d.vy+=(wy-d.vy)*k;
        }'''
s = replace_method(s, 'moveAiToward', move_ai)

# Keep difficulty about decisions/positioning only, not raw running speed.
# Preserve the v1.8 kick button and arcade ball physics unchanged.

s = s.replace('circle_football_v18', 'circle_football_v22')
path.write_text(s, encoding='utf-8')

manifest = Path('AndroidManifest.xml')
m = manifest.read_text(encoding='utf-8')
m = m.replace('com.godnit.circlefootballlite.v18', 'com.godnit.circlefootballlite.v22')
m = re.sub(r'android:versionCode="\d+"', 'android:versionCode="13"', m, count=1)
m = re.sub(r'android:versionName="[^"]+"', 'android:versionName="2.2.0"', m, count=1)
manifest.write_text(m, encoding='utf-8')

print('Applied Circle Football v2.2 arcade / slower equal-speed patch')
