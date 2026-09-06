from pathlib import Path
import re

path=Path('src/com/godnit/circlefootballlite/MainActivity.java')
s=path.read_text(encoding='utf-8')

def rep(text,name,repl):
    pat=(r'(?m)^        (?:@Override\s+)?(?:(?:public|protected|private)\s+)?'
         r'(?:static\s+)?(?:void|float(?:\[\])?|int|boolean|short\[\]|String|MediaPlayer|Disc)\s+'
         +re.escape(name)+r'\s*\(')
    m=re.search(pat,text)
    if not m: raise RuntimeError('method not found: '+name)
    st=m.start(); br=text.find('{',m.end()); dep=0
    for i in range(br,len(text)):
        if text[i]=='{': dep+=1
        elif text[i]=='}':
            dep-=1
            if dep==0: return text[:st]+repl.rstrip()+text[i+1:]
    raise RuntimeError('unterminated: '+name)

# Extra state for a loose, springy possession tether. The ball is never pinned to
# one exact point: it keeps inertia and swings around the player when direction changes.
if 'holderAngularVelV31' not in s:
    s=s.replace('        float holderAngleV29=0f,holderReleaseV29=0f;\n',
                '        float holderAngleV29=0f,holderReleaseV29=0f;\n        float holderAngularVelV31=0f;\n',1)

# Restore movement exactly to the v2.2 model: everyone has the same 220*s top speed
# and the same 8.5 steering response. Difficulty does not alter raw running speed.
s=rep(s,'updateHuman',r'''        void updateHuman(float dt){
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
        }''')

s=rep(s,'moveAiToward',r'''        void moveAiToward(Disc d,float tx,float ty,float dt){
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
        }''')

# Loose tether possession for ALL players.
# Think of the ball as attached by a short elastic cord rather than glued to the disc:
# it follows the carrier, but keeps momentum, lags on turns, and swings around the rim.
s=rep(s,'possessionV29',r'''        void possessionV29(float dt){
            holderReleaseV29=Math.max(0,holderReleaseV29-dt);
            if(goalLatchedV29){ballHolderV29=null;holderAngularVelV31=0;return;}
            float touch=discR+ballR;

            if(ballHolderV29!=null){
                Disc d=ballHolderV29;
                float hd=dist(d.x,d.y,bx,by);
                Disc o=nearestOpponentV29(d);
                float od=o==null?99999f:dist(o.x,o.y,bx,by);
                float rel=o==null?0f:len(o.vx-d.vx,o.vy-d.vy);

                // A clean tackle transfers possession instead of making the ball magnetic.
                if(o!=null && od<=touch+2.5f*s && (od+0.9f*s<hd || rel>72*s)){
                    ballHolderV29=o;
                    holderAngleV29=(float)Math.atan2(by-o.y,bx-o.x);
                    holderAngularVelV31=0f;
                    return;
                }
                if(hd>touch+22*s){releasePossessionV29(.065f);holderAngularVelV31=0f;return;}

                float sp=len(d.vx,d.vy);
                float targetAngle=holderAngleV29;
                if(sp>10*s)targetAngle=(float)Math.atan2(d.vy,d.vx);

                // Angular spring: slow enough to visibly swing when the carrier turns,
                // quick enough that normal dribbling still feels controlled.
                float diff=wrapAngleV29(targetAngle-holderAngleV29);
                float angularAccel=diff*(8.2f+clamp(sp/(220*s),0f,1f)*3.0f)-holderAngularVelV31*4.0f;
                holderAngularVelV31+=angularAccel*dt;
                holderAngularVelV31=clamp(holderAngularVelV31,-5.2f,5.2f);
                holderAngleV29=wrapAngleV29(holderAngleV29+holderAngularVelV31*dt);

                float slack=4.5f*s+clamp(sp/(220*s),0f,1f)*5.5f*s;
                float desiredR=touch+slack;
                float tx=d.x+(float)Math.cos(holderAngleV29)*desiredR;
                float ty=d.y+(float)Math.sin(holderAngleV29)*desiredR;

                // Keep the target inside ball-valid space, but do not teleport the ball there.
                float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf;
                ty=clamp(ty,pitch.top+ballR,pitch.bottom-ballR);
                if(!(ty>y1+ballR*.20f&&ty<y2-ballR*.20f))tx=clamp(tx,pitch.left+ballR,pitch.right-ballR);

                float ex=tx-bx,ey=ty-by;
                float spring=5.8f;
                float targetVx=d.vx+ex*spring;
                float targetVy=d.vy+ey*spring;
                float vk=clamp(dt*6.7f,0f,.115f);
                bvx+=(targetVx-bvx)*vk;
                bvy+=(targetVy-bvy)*vk;

                // The cord only tightens strongly near its maximum length. This preserves
                // the bottle/pendulum feel rather than fixing the ball at a constant radius.
                float maxR=touch+15.5f*s;
                if(hd>maxR){
                    float nx=(bx-d.x)/Math.max(1f,hd),ny=(by-d.y)/Math.max(1f,hd);
                    float stretch=hd-maxR;
                    bvx-=nx*stretch*16f*dt;
                    bvy-=ny*stretch*16f*dt;
                }

                limitBallSpeed(610*s);
                return;
            }

            if(holderReleaseV29>0 || len(bvx,bvy)>315*s)return;
            Disc best=null;float bd=99999f,second=99999f;
            for(int t=0;t<2;t++){
                Disc[] a=t==0?blue:red;
                for(int i=0;i<teamSize;i++){
                    Disc d=a[i];float q=dist(d.x,d.y,bx,by);
                    if(q<bd){second=bd;bd=q;best=d;}else if(q<second)second=q;
                }
            }
            if(best!=null && bd<=touch+3.0f*s && second-bd>1.2f*s && best.kickCd<=0){
                float rv=len(bvx-best.vx,bvy-best.vy);
                if(rv<225*s){
                    ballHolderV29=best;
                    holderAngleV29=(float)Math.atan2(by-best.y,bx-best.x);
                    float rx=bx-best.x,ry=by-best.y,rl=Math.max(1f,len(rx,ry));
                    holderAngularVelV31=((bvy-best.vy)*(rx/rl)-(bvx-best.vx)*(ry/rl))/Math.max(1f,touch);
                    holderAngularVelV31=clamp(holderAngularVelV31,-3.0f,3.0f);
                }
            }
        }''')

# Reset the swing state whenever possession is explicitly released.
s=rep(s,'releasePossessionV29',r'''        void releasePossessionV29(float lock){
            ballHolderV29=null;
            holderAngularVelV31=0f;
            holderReleaseV29=Math.max(holderReleaseV29,lock);
        }''')

s=s.replace('circle_football_v30','circle_football_v31')
path.write_text(s,encoding='utf-8')

m=Path('AndroidManifest.xml')
x=m.read_text(encoding='utf-8')
x=x.replace('com.godnit.circlefootballlite.v30','com.godnit.circlefootballlite.v31')
x=re.sub(r'android:versionCode="\d+"','android:versionCode="22"',x,count=1)
x=re.sub(r'android:versionName="[^"]+"','android:versionName="3.1.0"',x,count=1)
m.write_text(x,encoding='utf-8')
print('Applied v3.1 exact v2.2 movement and loose spring-tether possession')
