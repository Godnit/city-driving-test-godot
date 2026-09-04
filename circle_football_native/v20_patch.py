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

# Second joystick state for aiming/shooting, plus controlled possession state.
if 'int kickAimPointer=-1;' not in s:
    s = s.replace('        int joyPointer=-1;\n',
                  '        int joyPointer=-1;\n'
                  '        int kickAimPointer=-1;\n'
                  '        float kickAimX,kickAimY,kickAimNX,kickAimNY;\n', 1)
if 'boolean humanHasBall=false;' not in s:
    s = s.replace('        float touchSoundCooldown=0f, wallSoundCooldown=0f;\n',
                  '        float touchSoundCooldown=0f, wallSoundCooldown=0f;\n'
                  '        boolean humanHasBall=false;\n'
                  '        float possessionDirX=1f,possessionDirY=0f,possessionGrace=0f;\n', 1)

update_rects = r'''        void updateControlRects(){
            float jr=joyRadius();
            joyBaseX=clamp(joyNormX*w,jr+8*s,w-jr-8*s);
            joyBaseY=clamp(joyNormY*h,jr+8*s,h-jr-8*s);
            joyNormX=joyBaseX/w;joyNormY=joyBaseY/h;
            float kr=kickRadius();
            float kx=clamp(kickNormX*w,kr+8*s,w-kr-8*s);
            float ky=clamp(kickNormY*h,kr+8*s,h-kr-8*s);
            kickNormX=kx/w;kickNormY=ky/h;
            kickButton.set(kx-kr,ky-kr,kx+kr,ky+kr);
            if(joyPointer<0){joyX=joyBaseX;joyY=joyBaseY;}
            if(kickAimPointer<0){kickAimX=kx;kickAimY=ky;kickAimNX=kickAimNY=0f;}
        }'''
s = replace_method(s, 'updateControlRects', update_rects)

# The old KICK button becomes an actual aim joystick. The ball visibly moves
# around the player's edge while aiming, so releasing feels like a real kick
# rather than a sudden teleport.
draw_kick = r'''        void drawKick(Canvas c,boolean editor){
            float cx=kickButton.centerX(),cy=kickButton.centerY(),r=kickRadius();
            boolean active=editor||humanHasBall;

            if(mode==GAME && humanHasBall && kickAimPointer>=0){
                float al=len(kickAimNX,kickAimNY);
                if(al>.10f){
                    float ax=kickAimNX/al,ay=kickAimNY/al;
                    stroke.setColor(Color.argb(175,105,181,255));stroke.setStrokeWidth(4*s);
                    c.drawLine(bx,by,bx+ax*120*s,by+ay*120*s,stroke);
                    path.reset();
                    float ex=bx+ax*120*s,ey=by+ay*120*s;
                    path.moveTo(ex,ey);
                    path.lineTo(ex-ax*19*s-ay*10*s,ey-ay*19*s+ax*10*s);
                    path.lineTo(ex-ax*19*s+ay*10*s,ey-ay*19*s-ax*10*s);
                    path.close();
                    p.setStyle(Paint.Style.FILL);p.setColor(Color.argb(190,105,181,255));c.drawPath(path,p);
                }
            }

            p.setStyle(Paint.Style.FILL);
            p.setColor(active?Color.argb(editor?185:150,28,116,255):Color.argb(75,95,108,128));
            c.drawCircle(cx,cy,r,p);
            stroke.setColor(active?Color.argb(190,116,176,255):Color.argb(90,160,170,185));
            stroke.setStrokeWidth(2*s);c.drawCircle(cx,cy,r,stroke);

            float kx=kickAimPointer>=0?kickAimX:cx,ky=kickAimPointer>=0?kickAimY:cy;
            p.setColor(active?Color.argb(editor?225:205,220,236,255):Color.argb(115,220,225,232));
            c.drawCircle(kx,ky,27*s*kickScale,p);

            p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);
            p.setTextSize(14*s*kickScale);p.setColor(Color.WHITE);
            c.drawText(humanHasBall?"SHOT":"AIM",cx,cy+5*s*kickScale,p);
        }'''
s = replace_method(s, 'drawKick', draw_kick)

# Slower, calmer movement. Easy is now noticeably easier and all players have
# more time to react instead of flying around the pitch.
update_human = r'''        void updateHuman(float dt){
            Disc d=blue[0];
            float speed=245*s;
            float wx=joyNX*speed,wy=joyNY*speed;
            float k=Math.min(1f,dt*11.5f);
            d.vx+=(wx-d.vx)*k;d.vy+=(wy-d.vy)*k;
            if(joyPointer<0){
                float damp=(float)Math.pow(.78,dt*60);
                d.vx*=damp;d.vy*=damp;
            }
        }'''
s = replace_method(s, 'updateHuman', update_human)

move_ai = r'''        void moveAiToward(Disc d,float tx,float ty,float dt){
            float dx=tx-d.x,dy=ty-d.y,l=len(dx,dy);
            float speed=(difficulty==0?155:difficulty==1?195:225)*s;
            float wx=0,wy=0;if(l>2*s){wx=dx/l*speed;wy=dy/l*speed;}
            float response=difficulty==0?4.0f:difficulty==1?5.7f:7.1f;
            float k=Math.min(1f,dt*response);
            d.vx+=(wx-d.vx)*k;d.vy+=(wy-d.vy)*k;
        }'''
s = replace_method(s, 'moveAiToward', move_ai)

update_game = r'''        void updateGame(float dt){
            if(!goldenGoal){
                matchTime-=dt;
                if(matchTime<=0){
                    matchTime=0;
                    if(blueScore==redScore) goldenGoal=true; else finishMatch();
                }
            }
            if(mode!=GAME)return;
            possessionGrace=Math.max(0f,possessionGrace-dt);
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

            int steps=Math.max(2,Math.min(12,(int)Math.ceil(dt/0.0038f)));
            float sub=dt/steps;
            for(int st=0;st<steps;st++) physicsStep(sub);
            updateParticles(dt);

            float near=Math.min(Math.abs(bx-pitch.left),Math.abs(pitch.right-bx))/Math.max(1f,pitch.width());
            float threat=clamp((.34f-near)/.34f,0f,1f);
            float speedBoost=clamp(len(bvx,bvy)/(820*s),0f,1f)*.24f;
            crowdExcitement=clamp(threat+speedBoost,0f,1f);
            syncRealAudio();
        }'''
s = replace_method(s, 'updateGame', update_game)

# Possession is deliberate: touching a manageable ball lets the human receive it.
# While held, it sits just outside the disc and follows movement/shot aim smoothly.
# A real opponent-ball contact can knock it loose again.
possession_methods = r'''
        boolean tryAcquireHumanPossession(){
            if(humanHasBall||possessionGrace>0f)return false;
            Disc d=blue[0];
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);
            float rel=len(bvx-d.vx,bvy-d.vy);
            if(l>discR+ballR+7*s || rel>690*s)return false;
            if(l>1f){possessionDirX=dx/l;possessionDirY=dy/l;}
            else if(len(joyNX,joyNY)>.10f){
                float jl=len(joyNX,joyNY);possessionDirX=joyNX/jl;possessionDirY=joyNY/jl;
            }
            humanHasBall=true;
            bvx=d.vx;bvy=d.vy;
            updateHeldBall(.016f);
            return true;
        }

        void updateHeldBall(float dt){
            if(!humanHasBall)return;
            Disc d=blue[0];
            float tx=possessionDirX,ty=possessionDirY;
            float aimLen=len(kickAimNX,kickAimNY);
            float moveLen=len(joyNX,joyNY);
            if(kickAimPointer>=0 && aimLen>.08f){tx=kickAimNX/aimLen;ty=kickAimNY/aimLen;}
            else if(moveLen>.08f){tx=joyNX/moveLen;ty=joyNY/moveLen;}

            float turn=Math.min(1f,dt*(kickAimPointer>=0?16f:8.5f));
            possessionDirX+=(tx-possessionDirX)*turn;
            possessionDirY+=(ty-possessionDirY)*turn;
            float pl=len(possessionDirX,possessionDirY);
            if(pl<.01f){possessionDirX=1f;possessionDirY=0f;}else{possessionDirX/=pl;possessionDirY/=pl;}

            float hold=discR+ballR+3.0f*s;
            float targetX=d.x+possessionDirX*hold;
            float targetY=d.y+possessionDirY*hold;
            bx=clamp(targetX,pitch.left+ballR,pitch.right-ballR);
            by=clamp(targetY,pitch.top+ballR,pitch.bottom-ballR);
            bvx=d.vx;bvy=d.vy;
        }

        boolean tackleHumanPossession(){
            if(!humanHasBall)return false;
            for(int i=0;i<teamSize;i++){
                Disc o=red[i];
                float dx=bx-o.x,dy=by-o.y,l=len(dx,dy);
                if(l<discR+ballR-1.0f*s){
                    if(l<1f){dx=1f;dy=0f;l=1f;}
                    humanHasBall=false;
                    possessionGrace=.22f;
                    float nx=dx/l,ny=dy/l;
                    bvx=o.vx*.30f+nx*210*s;
                    bvy=o.vy*.30f+ny*210*s;
                    return true;
                }
            }
            return false;
        }

        void updateKickAim(float x,float y){
            float cx=kickButton.centerX(),cy=kickButton.centerY();
            float dx=x-cx,dy=y-cy,max=kickRadius(),l=len(dx,dy);
            if(l>max){dx=dx/l*max;dy=dy/l*max;}
            kickAimX=cx+dx;kickAimY=cy+dy;
            kickAimNX=dx/max;kickAimNY=dy/max;
        }

        void releaseKickAim(boolean shoot){
            float mag=len(kickAimNX,kickAimNY);
            if(shoot&&humanHasBall&&mag>.14f){
                doKickAim(kickAimNX/mag,kickAimNY/mag,mag);
            }
            kickAimPointer=-1;kickAimNX=kickAimNY=0f;
            kickAimX=kickButton.centerX();kickAimY=kickButton.centerY();
        }

        void doKickAim(float aimX,float aimY,float strength){
            if(!humanHasBall)return;
            Disc d=blue[0];
            float al=len(aimX,aimY);if(al<.01f)return;aimX/=al;aimY/=al;
            humanHasBall=false;
            possessionGrace=.26f;
            float power=(625f+55f*clamp(strength,0f,1f))*s;
            bvx=aimX*power+d.vx*.22f;
            bvy=aimY*power+d.vy*.22f;
            limitBallSpeed(850*s);
            d.kickCd=.23f;
            spawnKickBurst(aimX,aimY,power);
            haptic(20);playSfx(SFX_KICK);
        }
'''
marker = '        void doKick(){'
if 'void doKickAim(' not in s:
    if marker not in s: raise RuntimeError('doKick marker missing')
    s = s.replace(marker, possession_methods + '\n' + marker, 1)

# Kept for any legacy call sites; actual shooting now happens on shot-stick release.
do_kick = r'''        void doKick(){
            if(!humanHasBall)return;
            float mag=len(kickAimNX,kickAimNY);
            if(mag>.14f)doKickAim(kickAimNX/mag,kickAimNY/mag,mag);
        }'''
s = replace_method(s, 'doKick', do_kick)

physics = r'''        void physicsStep(float dt){
            for(int i=0;i<teamSize;i++){
                Disc a=blue[i],b=red[i];
                a.x+=a.vx*dt;a.y+=a.vy*dt;
                b.x+=b.vx*dt;b.y+=b.vy*dt;
                clampDisc(a);clampDisc(b);
            }
            for(int pass=0;pass<3;pass++) resolveAllDiscCollisions();

            lastBallX=bx;lastBallY=by;

            if(humanHasBall){
                updateHeldBall(dt);
                tackleHumanPossession();
                if(humanHasBall){
                    float moved=dist(lastBallX,lastBallY,bx,by);
                    if(moved>.001f){
                        float speed=len(blue[0].vx,blue[0].vy);
                        float sign=(blue[0].vx+blue[0].vy)>=0?1f:-1f;
                        ballAngle+=sign*(moved/Math.max(1f,ballR))*57.2958f;
                    }
                    return;
                }
            }

            bx+=bvx*dt;by+=bvy*dt;
            float fr=(float)Math.pow(.9885,dt*60f);bvx*=fr;bvy*=fr;

            for(int pass=0;pass<5;pass++){
                for(int i=0;i<teamSize;i++){
                    if(!(i==0&&possessionGrace>0f))resolveBallDisc(blue[i]);
                    resolveBallDisc(red[i]);
                }
                handleBallWalls();
                resolveWallPin();
            }
            limitBallSpeed(900*s);
            tryAcquireHumanPossession();

            float moved=dist(lastBallX,lastBallY,bx,by);
            if(moved>0.001f){
                float cross=bvx*(by-lastBallY)-bvy*(bx-lastBallX);
                float sign=cross>=0?1f:-1f;
                if(Math.abs(cross)<.01f)sign=(bvx+bvy)>=0?1f:-1f;
                ballAngle += sign*(moved/Math.max(1f,ballR))*57.2958f;
            }
            if(!humanHasBall)emitMotionTrail(dt);
        }'''
s = replace_method(s, 'physicsStep', physics)

# Touch handling: left joystick moves. Right joystick aims. Releasing the right
# joystick is the kick action; pressing it never fires immediately.
on_touch = r'''        @Override public boolean onTouchEvent(MotionEvent e){
            int action=e.getActionMasked(),idx=e.getActionIndex();
            if(mode==CONTROLS)return handleControlTouch(e,action,idx);
            if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_POINTER_DOWN){
                float x=e.getX(idx),y=e.getY(idx);
                if(mode==GAME){
                    if(pauseButton.contains(x,y)){
                        previousMode=GAME;mode=PAUSE;releaseJoy();releaseKickAim(false);return true;
                    }
                    if(kickAimPointer<0&&kickButton.contains(x,y)){
                        kickAimPointer=e.getPointerId(idx);updateKickAim(x,y);return true;
                    }
                    if(joyPointer<0&&dist(x,y,joyBaseX,joyBaseY)<=joyRadius()*1.35f){
                        joyPointer=e.getPointerId(idx);updateJoy(x,y);return true;
                    }
                }
            }
            if(action==MotionEvent.ACTION_MOVE){
                if(joyPointer>=0){int pi=e.findPointerIndex(joyPointer);if(pi>=0)updateJoy(e.getX(pi),e.getY(pi));}
                if(kickAimPointer>=0){int pi=e.findPointerIndex(kickAimPointer);if(pi>=0)updateKickAim(e.getX(pi),e.getY(pi));}
                return true;
            }
            if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_POINTER_UP){
                int id=e.getPointerId(idx);float x=e.getX(idx),y=e.getY(idx);
                if(id==joyPointer)releaseJoy();
                if(id==kickAimPointer)releaseKickAim(true);
                if(action==MotionEvent.ACTION_UP&&mode!=GAME)processHit(x,y);
                return true;
            }
            if(action==MotionEvent.ACTION_CANCEL){releaseJoy();releaseKickAim(false);return true;}
            return true;
        }'''
s = replace_method(s, 'onTouchEvent', on_touch)

reset_positions = r'''        void resetPositions(){
            if(w<=0||h<=0)return;
            humanHasBall=false;possessionGrace=.20f;possessionDirX=1f;possessionDirY=0f;
            releaseKickAim(false);
            float cy=pitch.centerY();
            for(int i=0;i<4;i++){
                float lane=((i%3)-1)*pitch.height()*.22f;
                blue[i].x=pitch.left+pitch.width()*(i==0?.28f:(i==teamSize-1?.075f:.23f));
                red[i].x=pitch.right-pitch.width()*(i==0?.28f:(i==teamSize-1?.075f:.23f));
                blue[i].y=clamp(cy+(i==0?pitch.height()*.10f:lane),pitch.top+discR,pitch.bottom-discR);
                red[i].y=clamp(cy+(i==0?-pitch.height()*.10f:lane),pitch.top+discR,pitch.bottom-discR);
                blue[i].vx=blue[i].vy=red[i].vx=red[i].vy=0;
                blue[i].kickCd=red[i].kickCd=.20f;
                blue[i].wallPlayTime=red[i].wallPlayTime=0f;
            }
            bx=pitch.centerX();by=cy;bvx=bvy=0;ballAngle=0;particles.clear();trailCarry=0;crowdExcitement=.05f;
            for(int i=0;i<teamSize;i++){separateFromBall(blue[i]);separateFromBall(red[i]);}
        }'''
s = replace_method(s, 'resetPositions', reset_positions)

finish_match = r'''        void finishMatch(){
            if(mode==RESULT)return;
            humanHasBall=false;releaseKickAim(false);
            mode=RESULT;
            if(!savedResult){playSfx(blueScore>redScore?SFX_WIN:SFX_LOSE);savedResult=true;}
            joyPointer=-1;joyNX=joyNY=0;joyX=joyBaseX;joyY=joyBaseY;
        }'''
s = replace_method(s, 'finishMatch', finish_match)

handle_back = r'''        boolean handleBack(){
            if(mode==GAME){previousMode=GAME;mode=PAUSE;releaseJoy();releaseKickAim(false);return true;}
            if(mode==PAUSE){mode=GAME;lastFrame=System.nanoTime();return true;}
            if(mode==CONTROLS){saveControls();mode=SETTINGS;return true;}
            if(mode!=HOME){mode=HOME;releaseKickAim(false);return true;}
            return false;
        }'''
s = replace_method(s, 'handleBack', handle_back)

# Update wording in the controls editor to match the new control.
s = s.replace('Move and resize the joystick and KICK button.', 'Move and resize movement and shot joysticks.')
s = s.replace('"KICK -"', '"SHOT -"').replace('"KICK +"', '"SHOT +"')

# Version-specific preferences/package.
s = s.replace('circle_football_v19', 'circle_football_v20')
path.write_text(s, encoding='utf-8')

manifest = Path('AndroidManifest.xml')
m = manifest.read_text(encoding='utf-8')
m = m.replace('com.godnit.circlefootballlite.v19', 'com.godnit.circlefootballlite.v20')
m = re.sub(r'android:versionCode="\d+"', 'android:versionCode="11"', m, count=1)
m = re.sub(r'android:versionName="[^"]+"', 'android:versionName="2.0.0"', m, count=1)
manifest.write_text(m, encoding='utf-8')

print('Applied Circle Football v2.0 possession + release-to-shoot joystick patch')
