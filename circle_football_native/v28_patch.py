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

# Camera state and longer visible loading screen.
s=s.replace('        float goalPauseTimer=0f,bluePassLock=0f,redPassLock=0f,countdownTimer=0f,blueChaserHold=0f,redChaserHold=0f;\n',
            '        float goalPauseTimer=0f,bluePassLock=0f,redPassLock=0f,countdownTimer=0f,blueChaserHold=0f,redChaserHold=0f;\n        float camX=0f,camY=0f,camZoom=1f;\n',1)
s=s.replace('        long splashUntil=SystemClock.uptimeMillis()+2600L;\n','        long splashUntil=SystemClock.uptimeMillis()+4000L;\n',1)

# Match the reference clip more closely: slightly smaller discs/ball, while the camera itself is closer.
s=rep(s,'configureField',r'''        void configureField(){
            float mxRatio,myRatio;
            if(fieldTheme==3){mxRatio=.052f;myRatio=.078f;}
            else if(fieldTheme==2){mxRatio=.064f;myRatio=.104f;}
            else{mxRatio=teamSize>=3?.058f:.073f;myRatio=teamSize>=3?.098f:.116f;}
            float mx=Math.max(w*mxRatio,56f*s),my=h*myRatio;
            pitch.set(mx,my,w-mx,h-my);
            goalHalf=pitch.height()*.215f;
            float ts=teamSize>=4?.83f:(teamSize==3?.90f:1f),fs=fieldTheme==3?.92f:(fieldTheme==2?.96f:1f);
            discR=20.2f*s*ts*fs;
            float bt=teamSize>=4?.86f:(teamSize==3?.92f:1f),bf=fieldTheme==3?.90f:(fieldTheme==2?.95f:1f);
            ballR=8.8f*s*bt*bf;
        }''')

# A compact setup screen: all options remain, but the empty space is removed.
s=rep(s,'drawSetup',r'''        void drawSetup(Canvas c){
            background(c);title(c,"PLAY MATCH",42*s,27f);
            float left=w*.12f,right=w*.88f,top=68*s,bottom=h-76*s;
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(30,35,44));c.drawRoundRect(new RectF(left,top,right,bottom),18*s,18*s,p);
            float labelX=left+72*s,choicesX=left+150*s,row=86*s;
            p.setTextAlign(Paint.Align.LEFT);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(11*s);p.setColor(Color.rgb(145,160,181));
            c.drawText("DIFFICULTY",labelX,row+25*s,p);String[] ds={"EASY","NORMAL","HARD"};float bw=112*s,g=7*s;for(int i=0;i<3;i++)menuButton(c,ds[i],"diff"+i,choicesX+i*(bw+g),row,bw,39*s,i==difficulty?Color.rgb(29,121,255):Color.rgb(52,59,72));
            row+=58*s;c.drawText("PLAYERS",labelX,row+25*s,p);float pw=82*s,pg=7*s;for(int i=1;i<=4;i++)menuButton(c,i+"v"+i,"team"+i,choicesX+(i-1)*(pw+pg),row,pw,39*s,i==teamSize?Color.rgb(34,174,91):Color.rgb(52,59,72));
            row+=58*s;c.drawText("GOALS",labelX,row+25*s,p);int[] gs={3,5,7};for(int i=0;i<3;i++)menuButton(c,""+gs[i],"goal"+gs[i],choicesX+i*(bw+g),row,bw,39*s,gs[i]==targetGoals?Color.rgb(238,157,32):Color.rgb(52,59,72));
            row+=58*s;c.drawText("STADIUM",labelX,row+25*s,p);String[] ns={"CLASSIC","GRASS","NIGHT","WIDE"};float fw=90*s,fg=6*s;for(int i=0;i<4;i++)menuButton(c,ns[i],"field"+i,choicesX+i*(fw+fg),row,fw,39*s,i==fieldTheme?Color.rgb(102,82,205):Color.rgb(52,59,72));
            float py=row+54*s;drawStadiumPreviewV26(c,new RectF(left+44*s,py,right-44*s,Math.min(bottom-18*s,py+150*s)));
            menuButton(c,"START MATCH","start",w/2f-190*s,h-65*s,380*s,46*s,Color.rgb(29,121,255));
            menuButton(c,"BACK","home",w/2f-74*s,h-17*s,148*s,28*s,Color.rgb(48,56,70));
        }''')

# First-version style pursuit helper: choose a single decisive presser, but keep all other roles moving.
if 'int nearestAiV28(' not in s:
    s=s.replace('        void chooseChasers(){',r'''        int nearestAiV28(Disc[] t,int from,int to,float x,float y){
            int best=-1;float bd=Float.MAX_VALUE;for(int i=from;i<to;i++){if(!t[i].ai)continue;float q=sq(t[i].x-x)+sq(t[i].y-y);if(q<bd){bd=q;best=i;}}return best;
        }

        void chooseChasers(){''',1)

s=rep(s,'chooseChasers',r'''        void chooseChasers(){
            float pred=difficulty==0?.08f:(difficulty==1?.18f:.30f),px=bx+bvx*pred,py=by+bvy*pred,cw=pitch.width(),cx=pitch.centerX();
            blueChaserHold=Math.max(0,blueChaserHold-.016f);redChaserHold=Math.max(0,redChaserHold-.016f);

            int wantBlue=-1;
            if(teamSize>=2){
                float humanD=dist(blue[0].x,blue[0].y,px,py);
                if(px<pitch.left+cw*.14f)wantBlue=teamSize-1;
                else if(px<cx+cw*.08f || humanD>cw*.28f)wantBlue=nearestAiV28(blue,1,teamSize,px,py);
            }
            int wantRed=0;
            if(teamSize>=2){
                if(px>pitch.right-cw*.14f)wantRed=teamSize-1;
                else if(px>cx+cw*.08f)wantRed=nearestAiV28(red,1,teamSize,px,py);
                else wantRed=0;
            }
            if(wantBlue!=blueChaser&&(blueChaserHold<=0||px<pitch.left+cw*.10f)){blueChaser=wantBlue;blueChaserHold=.72f;}
            if(wantRed!=redChaser&&(redChaserHold<=0||px>pitch.right-cw*.10f)){redChaser=wantRed;redChaserHold=.72f;}
        }''')

# Active formation: defenders slide with the ball and mark passing lanes instead of standing still.
s=rep(s,'formationTarget',r'''        float[] formationTarget(int teamId,int idx,int chaser){
            float sg=teamId==0?1f:-1f,own=teamId==0?pitch.left:pitch.right,cw=pitch.width(),ch=pitch.height();
            float pred=difficulty==2?.20f:.12f,px=bx+bvx*pred,py=by+bvy*pred;
            if(idx==0){
                float ax=teamId==0?clamp(px+cw*.18f,pitch.centerX()-cw*.04f,pitch.right-cw*.10f):clamp(px-cw*.18f,pitch.left+cw*.10f,pitch.centerX()+cw*.04f);
                float ay=clamp(py+(py<pitch.centerY()?ch*.12f:-ch*.12f),pitch.top+discR*1.5f,pitch.bottom-discR*1.5f);
                return new float[]{ax,ay};
            }
            if(idx==teamSize-1&&teamSize>=2){
                float danger=teamId==0?clamp((pitch.centerX()-px)/(cw*.48f),0,1):clamp((px-pitch.centerX())/(cw*.48f),0,1);
                float kx=own+sg*cw*(.055f+.055f*danger),ky=clamp(py,pitch.centerY()-goalHalf*.74f,pitch.centerY()+goalHalf*.74f);
                return new float[]{kx,ky};
            }
            int slot=idx-1;Disc m=markV26(teamId==0?red:blue,teamId,slot);
            float baseX=own+sg*cw*(.20f+.055f*slot),interceptX=px-sg*(74f+18f*slot)*s;
            float threat=teamId==0?clamp((cxBallV28()-px)/(cw*.52f),0,1):clamp((px-cxBallV28())/(cw*.52f),0,1);
            float lo=teamId==0?pitch.left+cw*.12f:pitch.centerX()-cw*.08f,hi=teamId==0?pitch.centerX()+cw*.08f:pitch.right-cw*.12f;
            float x=clamp(baseX*(1-threat)+interceptX*threat,lo,hi);
            float zoneY=pitch.top+ch*(slot+1f)/(Math.max(1,teamSize-2)+1f),markY=m==null?zoneY:m.y;
            float y=clamp(zoneY*.28f+markY*.50f+py*.22f,pitch.top+discR*1.5f,pitch.bottom-discR*1.5f);
            return new float[]{x,y};
        }''')
if 'float cxBallV28()' not in s:
    s=s.replace('        int nearestAiV28(', '        float cxBallV28(){return pitch.centerX();}\n\n        int nearestAiV28(',1)

# Escape pass when surrounded. Otherwise the carrier behaves like the first version: get behind the ball and go forward.
s=rep(s,'chooseKickTarget',r'''        float[] chooseKickTarget(Disc d,Disc[] team,Disc[] opp,int teamId){
            float sg=teamId==0?1f:-1f,gx=teamId==0?pitch.right+20*s:pitch.left-20*s,gy=bestGoalLaneV25(opp,teamId),gd=Math.abs(gx-bx);
            int pressure=countOpponentsNear(opp,bx,by,(difficulty==2?106f:(difficulty==1?98f:90f))*s);
            int pass=escapePassV27(d,team,opp,teamId);
            float clear=shotClearV26(opp,teamId,gy);
            boolean finalZ=gd<pitch.width()*(difficulty==0?.31f:(difficulty==1?.39f:.46f));
            boolean clearShot=clear>discR*(difficulty==2?1.00f:(difficulty==1?1.18f:1.38f));
            boolean keeper=d.index==teamSize-1&&teamSize>=2,def=d.index>0&&!keeper;
            if(finalZ&&clearShot)return new float[]{gx,gy,0,0,0,0};
            if(pressure>=2&&pass>=0){Disc m=team[pass];return new float[]{m.x+m.vx*.15f,m.y+m.vy*.15f,1,0,0,0};}
            if((keeper||def)&&pressure>=1&&pass>=0){Disc m=team[pass];return new float[]{m.x+m.vx*.15f,m.y+m.vy*.15f,1,0,0,0};}
            if(finalZ)return new float[]{gx,gy,0,0,0,0};
            return new float[]{gx,gy,2,0,0,0};
        }''')

# Continuous movement with the exact same top speed as the human. Small steering corrections stop the AI from freezing.
s=rep(s,'moveAiToward',r'''        void moveAiToward(Disc d,float tx,float ty,float dt){
            float odx=tx-d.x,ody=ty-d.y,ol=len(odx,ody);
            if(d.escapeTimer>0){d.escapeTimer=Math.max(0,d.escapeTimer-dt);tx=d.escapeX;ty=d.escapeY;}
            else{
                float moved=dist(d.x,d.y,d.lastAiX,d.lastAiY),act=len(d.vx,d.vy);
                if(ol>18*s&&act<42*s&&moved<1.0f*s)d.stuckTimer+=dt;else d.stuckTimer=Math.max(0,d.stuckTimer-dt*2.8f);
                if(d.stuckTimer>.18f){float l=Math.max(1,ol),nx=odx/l,ny=ody/l,sx=-ny,sy=nx;if((pitch.centerX()-d.x)*sx+(pitch.centerY()-d.y)*sy<0){sx=-sx;sy=-sy;}d.escapeX=clamp(d.x+sx*54*s+nx*30*s,pitch.left-20*s,pitch.right+20*s);d.escapeY=clamp(d.y+sy*54*s+ny*30*s,pitch.top-28*s,pitch.bottom+28*s);d.escapeTimer=.34f;d.stuckTimer=0;tx=d.escapeX;ty=d.escapeY;}
            }
            float dx=tx-d.x,dy=ty-d.y,l=len(dx,dy),speed=185*s,wx=0,wy=0;
            if(l>1.2f*s){wx=dx/l*speed;wy=dy/l*speed;}
            float k=Math.min(1,dt*7.0f);d.vx+=(wx-d.vx)*k;d.vy+=(wy-d.vy)*k;d.lastAiX=d.x;d.lastAiY=d.y;
        }''')

# Chaser logic: approach from behind, then actually drive THROUGH the ball for dribbling instead of stopping beside it.
s=rep(s,'updateTeamAI',r'''        void updateTeamAI(Disc[] team,Disc[] opp,int teamId,int chaser,float dt){
            for(int i=0;i<teamSize;i++){
                Disc d=team[i];if(!d.ai)continue;float tx,ty;
                if(i==chaser){
                    float[] tar=chooseKickTarget(d,team,opp,teamId);boolean pass=tar[2]>.5f&&tar[2]<1.5f,carry=tar[2]>1.5f;
                    float lead=difficulty==0?.08f:(difficulty==1?.18f:.30f),pbx=bx+bvx*lead,pby=by+bvy*lead;
                    float dx=tar[0]-pbx,dy=tar[1]-pby,ll=len(dx,dy);if(ll<1)ll=1;float dirX=dx/ll,dirY=dy/ll;
                    float cdx=bx-d.x,cdy=by-d.y,cl=len(cdx,cdy);if(cl<1)cl=1;float align=(cdx/cl)*dirX+(cdy/cl)*dirY,bd=dist(d.x,d.y,bx,by);
                    if(carry&&bd<discR+ballR+18*s&&align>.56f){tx=pbx+dirX*(discR+ballR+28*s);ty=pby+dirY*(discR+ballR+28*s);}else{float behind=discR+ballR+(carry?4*s:7*s);tx=pbx-dirX*behind;ty=pby-dirY*behind;}
                    if(by<pitch.top+ballR+10*s||by>pitch.bottom-ballR-10*s){float open=by<pitch.centerY()?1:-1;ty+=open*(discR+ballR+12*s);}
                    float need=difficulty==0?.83f:(difficulty==1?.74f:.65f);
                    if(!carry&&bd<=kickReach()&&align>need&&d.kickCd<=0)cpuKick(d,pass?440*s:515*s,dirX,dirY,pass);
                }else{
                    float[] pos=formationTarget(teamId,i,chaser);tx=pos[0];ty=pos[1];
                    float db=dist(d.x,d.y,bx,by),min=(i==teamSize-1?discR*3.3f:discR*2.9f);if(db<min){float ax=d.x-bx,ay=d.y-by,al=len(ax,ay);if(al<1)al=1;tx+=ax/al*(min-db+12*s);ty+=ay/al*(min-db+12*s);}
                }
                moveAiToward(d,tx,ty,dt);
            }
        }''')

# Soft physical dribble for EVERY player. It never snaps/teleports the ball; it only damps relative velocity while one player has clean contact.
if 'void softDribbleV28(float dt)' not in s:
    s=s.replace('        void updateGame(float dt){',r'''        void softDribbleV28(float dt){
            Disc best=null;float bd=999999f,second=999999f;
            for(int t=0;t<2;t++){Disc[] a=t==0?blue:red;for(int i=0;i<teamSize;i++){Disc d=a[i];float q=dist(d.x,d.y,bx,by);if(q<bd){second=bd;bd=q;best=d;}else if(q<second)second=q;}}
            if(best==null||bd>discR+ballR+5.5f*s||second-bd<2.3f*s||best.kickCd>0)return;
            float sp=len(best.vx,best.vy);if(sp<32*s||len(bvx,bvy)>390*s)return;
            float rx=(bx-best.x)/Math.max(1,bd),ry=(by-best.y)/Math.max(1,bd),dot=(rx*best.vx+ry*best.vy)/Math.max(1,sp);if(dot<.05f)return;
            float wantX=best.vx*1.06f,wantY=best.vy*1.06f,k=Math.min(1f,dt*5.4f);
            bvx+=(wantX-bvx)*k;bvy+=(wantY-bvy)*k;
        }

        void updateGame(float dt){''',1)

# Keep the first-version-like AI, add the soft dribble each physics substep, and preserve live control after goals.
s=rep(s,'updateGame',r'''        void updateGame(float dt){
            bluePassLock=Math.max(0,bluePassLock-dt);redPassLock=Math.max(0,redPassLock-dt);
            if(countdownTimer>0){countdownTimer=Math.max(0,countdownTimer-dt);crowdExcitement=.18f;syncRealAudio();for(int i=0;i<teamSize;i++){blue[i].vx*=.80f;blue[i].vy*=.80f;red[i].vx*=.80f;red[i].vy*=.80f;}bvx*=.80f;bvy*=.80f;return;}
            if(goalPauseTimer>0){
                goalPauseTimer=Math.max(0,goalPauseTimer-dt);updateConfettiV26(dt);for(int i=0;i<teamSize;i++){blue[i].kickCd=Math.max(0,blue[i].kickCd-dt);red[i].kickCd=Math.max(0,red[i].kickCd-dt);}updateHuman(dt);
                int steps=Math.max(3,Math.min(12,(int)Math.ceil(dt/.0036f)));float sub=dt/steps;for(int st=0;st<steps;st++){physicsStep(sub);softDribbleV28(sub);}updateParticles(dt);crowdExcitement=1;syncRealAudio();
                if(goalPauseTimer<=0){confetti.clear();if(pendingFinishAfterGoal){pendingFinishAfterGoal=false;finishMatch();return;}resetPositions();countdownTimer=4.0f;joyPointer=-1;joyNX=joyNY=0;joyX=joyBaseX;joyY=joyBaseY;}return;
            }
            if(!goldenGoal){matchTime-=dt;if(matchTime<=0){matchTime=0;if(blueScore==redScore)goldenGoal=true;else{finishMatch();return;}}}if(mode!=GAME)return;
            for(int i=0;i<teamSize;i++){blue[i].kickCd=Math.max(0,blue[i].kickCd-dt);red[i].kickCd=Math.max(0,red[i].kickCd-dt);blue[i].wallPlayTime=Math.max(0,blue[i].wallPlayTime-dt);red[i].wallPlayTime=Math.max(0,red[i].wallPlayTime-dt);}wallSoundCooldown=Math.max(0,wallSoundCooldown-dt);touchSoundCooldown=Math.max(0,touchSoundCooldown-dt);
            updateHuman(dt);chooseChasers();updateTeamAI(blue,red,0,blueChaser,dt);updateTeamAI(red,blue,1,redChaser,dt);
            int steps=Math.max(3,Math.min(14,(int)Math.ceil(dt/.0034f)));float sub=dt/steps;for(int st=0;st<steps;st++){physicsStep(sub);softDribbleV28(sub);if(goalPauseTimer>0)break;}updateParticles(dt);
            float dl=Math.abs(bx-pitch.left),dr=Math.abs(pitch.right-bx),near=Math.min(dl,dr)/Math.max(1,pitch.width()),th=clamp((.31f-near)/.31f,0,1),tow=(dl<dr)?Math.max(0,-bvx):Math.max(0,bvx),app=clamp(tow/(520*s),0,1),sb=clamp(len(bvx,bvy)/(690*s),0,1)*.16f;crowdExcitement=clamp(th*(.42f+.58f*app)+sb,0,1);syncRealAudio();
        }''')

# Longer celebration and a full 3-2-1-GO kick-off.
s=rep(s,'scoreGoal',r'''        void scoreGoal(boolean blueGoal){
            if(mode!=GAME||goalPauseTimer>0)return;if(blueGoal)blueScore++;else redScore++;lastGoalBlue=blueGoal;playSfx(SFX_GOAL);haptic(70);pendingFinishAfterGoal=blueScore>=targetGoals||redScore>=targetGoals||goldenGoal;goalPauseTimer=pendingFinishAfterGoal?4.4f:3.5f;spawnGoalConfettiV26();
        }''')
s=rep(s,'startMatch',r'''        void startMatch(){
            blueScore=redScore=0;matchTime=180f;goldenGoal=false;savedResult=false;goalPauseTimer=0;pendingFinishAfterGoal=false;confetti.clear();bluePassLock=redPassLock=0;blueChaserHold=redChaserHold=0;countdownTimer=4.0f;mode=GAME;lastFrame=System.nanoTime();joyPointer=-1;joyNX=joyNY=0;joyX=joyBaseX;joyY=joyBaseY;prefs.edit().putInt("difficulty",difficulty).putInt("team_size",teamSize).putInt("target_goals",targetGoals).putInt("field_theme",fieldTheme).apply();resetPositions();camX=bx;camY=by;camZoom=1f;playSfx(SFX_MENU);
        }''')

# Camera like the supplied clip: it follows the ball/action throughout the match instead of showing the whole pitch permanently.
if 'void updateCameraV28()' not in s:
    s=s.replace('        void drawGame(Canvas c){',r'''        void updateCameraV28(){
            float base=teamSize<=2?1.30f:(teamSize==3?1.20f:1.12f);if(fieldTheme==3)base-=.04f;if(goalPauseTimer>0)base=1.58f;
            float tx=goalPauseTimer>0?bx:(bx*.76f+blue[0].x*.24f),ty=goalPauseTimer>0?by:(by*.78f+blue[0].y*.22f);
            float halfW=w/(2f*base),halfH=h/(2f*base),minX=pitch.left-halfW*.20f,maxX=pitch.right+halfW*.20f,minY=pitch.top-halfH*.15f,maxY=pitch.bottom+halfH*.15f;
            tx=clamp(tx,minX,maxX);ty=clamp(ty,minY,maxY);if(camX==0&&camY==0){camX=tx;camY=ty;camZoom=base;}camX+=(tx-camX)*.085f;camY+=(ty-camY)*.085f;camZoom+=(base-camZoom)*.075f;
        }

        void drawGame(Canvas c){''',1)

s=rep(s,'drawGame',r'''        void drawGame(Canvas c){
            int out,p1,p2,line;if(fieldTheme==1){out=Color.rgb(39,118,43);p1=Color.rgb(54,156,56);p2=Color.rgb(48,145,51);line=Color.rgb(244,247,242);}else if(fieldTheme==2){out=Color.rgb(18,36,55);p1=Color.rgb(31,57,84);p2=Color.rgb(27,50,76);line=Color.rgb(215,232,246);}else if(fieldTheme==3){out=Color.rgb(42,122,47);p1=Color.rgb(60,153,64);p2=Color.rgb(51,139,57);line=Color.rgb(244,247,242);}else{out=Color.rgb(52,56,60);p1=Color.rgb(68,73,78);p2=Color.rgb(61,66,71);line=Color.WHITE;}
            c.drawColor(out);updateCameraV28();c.save();c.translate(w*.5f,h*.50f);c.scale(camZoom,camZoom);c.translate(-camX,-camY);
            p.setStyle(Paint.Style.FILL);p.setColor(p1);c.drawRect(pitch,p);int bands=fieldTheme==3?12:10;for(int i=0;i<bands;i++){p.setColor(i%2==0?p1:p2);float xx=pitch.left+pitch.width()*i/bands;c.drawRect(xx,pitch.top,xx+pitch.width()/bands,pitch.bottom,p);}stroke.setStyle(Paint.Style.STROKE);stroke.setColor(line);stroke.setStrokeWidth(2.4f*s/camZoom);c.drawRect(pitch,stroke);c.drawLine(pitch.centerX(),pitch.top,pitch.centerX(),pitch.bottom,stroke);c.drawCircle(pitch.centerX(),pitch.centerY(),72*s,stroke);c.drawCircle(pitch.centerX(),pitch.centerY(),3.5f*s,stroke);float ar=Math.min(pitch.height()*.32f,pitch.width()*.18f);c.drawArc(new RectF(pitch.left-ar,pitch.centerY()-ar,pitch.left+ar,pitch.centerY()+ar),-90,180,false,stroke);c.drawArc(new RectF(pitch.right-ar,pitch.centerY()-ar,pitch.right+ar,pitch.centerY()+ar),90,180,false,stroke);drawGoals(c);drawPredictionGuideV24(c);drawParticles(c);for(int i=0;i<teamSize;i++)drawDisc(c,blue[i]);for(int i=0;i<teamSize;i++)drawDisc(c,red[i]);drawFootball(c,bx,by,ballR,ballAngle);c.restore();
            drawScoreHud(c);drawJoystick(c,false);drawKick(c,false);if(goalPauseTimer>0)drawGoalCelebrationV26(c);if(countdownTimer>0)drawCountdownV27(c);
        }''')

# Make loading progress visibly slower instead of flashing by.
s=s.replace('float t=clamp(1f-(splashUntil-SystemClock.uptimeMillis())/1150f,0f,1f);','float t=clamp(1f-(splashUntil-SystemClock.uptimeMillis())/4000f,0f,1f);')
s=s.replace('circle_football_v27','circle_football_v28')
path.write_text(s,encoding='utf-8')

m=Path('AndroidManifest.xml');x=m.read_text(encoding='utf-8');x=x.replace('com.godnit.circlefootballlite.v27','com.godnit.circlefootballlite.v28');x=re.sub(r'android:versionCode="\d+"','android:versionCode="19"',x,count=1);x=re.sub(r'android:versionName="[^"]+"','android:versionName="2.8.0"',x,count=1);m.write_text(x,encoding='utf-8')
print('Applied v2.8 video-style camera, first-version pursuit AI and soft physical dribble')
