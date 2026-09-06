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
            if dep==0:return text[:st]+repl.rstrip()+text[i+1:]
    raise RuntimeError('unterminated: '+name)

# Presentation/match-flow state only. Player decision logic remains v2.2.
if 'final List<Confetti> confettiV34' not in s:
    s=s.replace('        final List<Particle> particles = new ArrayList<>();\n',
                '        final List<Particle> particles = new ArrayList<>();\n        final List<Confetti> confettiV34 = new ArrayList<>();\n',1)
if 'float countdownV34=' not in s:
    s=s.replace('        boolean goldenGoal=false, savedResult=false;\n',
                '        boolean goldenGoal=false, savedResult=false;\n        float countdownV34=0f,goalShowV34=0f,resultFxV34=0f,camXV34=0f,camYV34=0f;\n        boolean goalLatchedV34=false,pendingFinishV34=false,lastGoalBlueV34=false;\n        long splashUntilV34=SystemClock.uptimeMillis()+2200L;\n',1)
if 'static final class Confetti' not in s:
    marker='        static final class Particle{'
    cls='''        static final class Confetti{\n            float x,y,vx,vy,life,maxLife,rot,spin,ww,hh;int color;\n            Confetti(float x,float y,float vx,float vy,float life,float rot,float spin,float ww,float hh,int color){this.x=x;this.y=y;this.vx=vx;this.vy=vy;this.life=this.maxLife=life;this.rot=rot;this.spin=spin;this.ww=ww;this.hh=hh;this.color=color;}\n        }\n'''
    if marker not in s: raise RuntimeError('Particle marker missing')
    s=s.replace(marker,cls+marker,1)

# Keep the exact v2.2 steering model, only reduce the common speed equally.
s=rep(s,'updateHuman',r'''        void updateHuman(float dt){
            Disc d=blue[0];
            float speed=190f*s;
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
            float speed=190f*s;
            float wx=0f,wy=0f;
            if(l>2f*s){wx=dx/l*speed;wy=dy/l*speed;}
            float k=Math.min(1f,dt*8.5f);
            d.vx+=(wx-d.vx)*k;
            d.vy+=(wy-d.vy)*k;
        }''')

# Stable player-ball contact: keep the v2.2 feel but do not stack huge impulses
# when the ball is squeezed between two discs.
s=rep(s,'resolveBallDisc',r'''        void resolveBallDisc(Disc d){
            float dx=bx-d.x,dy=by-d.y,min=discR+ballR,dst=len(dx,dy);
            if(dst>=min)return;
            float nx,ny;
            if(dst<.001f){
                float rvx=bvx-d.vx,rvy=bvy-d.vy,rl=len(rvx,rvy);
                if(rl>.05f){nx=rvx/rl;ny=rvy/rl;}else{nx=d.team==0?1f:-1f;ny=0f;}
                dst=.001f;
            }else{nx=dx/dst;ny=dy/dst;}
            float overlap=min-dst+.30f*s;
            bx+=nx*overlap*.76f;by+=ny*overlap*.76f;
            d.x-=nx*overlap*.24f;d.y-=ny*overlap*.24f;clampDisc(d);
            float rel=(bvx-d.vx)*nx+(bvy-d.vy)*ny;
            if(rel<0f){
                float impulse=Math.min(-rel*1.08f,88f*s);
                bvx+=nx*impulse;bvy+=ny*impulse;
            }else{
                bvx+=d.vx*.006f;bvy+=d.vy*.006f;
            }
        }''')

# Static circular posts and whole-ball goal-line scoring.
helpers=r'''        boolean collidePostV34(float px,float py){
            float pr=4.8f*s,dx=bx-px,dy=by-py,min=ballR+pr,d=len(dx,dy);
            if(d>=min)return false;
            float nx,ny;if(d<.001f){nx=bvx>=0?-1f:1f;ny=0;d=.001f;}else{nx=dx/d;ny=dy/d;}
            bx=px+nx*(min+.12f*s);by=py+ny*(min+.12f*s);
            float vn=bvx*nx+bvy*ny;
            if(vn<0){float e=1.78f;bvx-=e*vn*nx;bvy-=e*vn*ny;}
            return true;
        }

        void stabilizeSqueezeV34(){
            float min=discR+ballR+2.0f*s;float[] nx=new float[8],ny=new float[8];int n=0;
            for(int t=0;t<2;t++){Disc[] a=t==0?blue:red;for(int i=0;i<teamSize&&n<8;i++){float dx=bx-a[i].x,dy=by-a[i].y,l=len(dx,dy);if(l<min&&l>.01f){nx[n]=dx/l;ny[n]=dy/l;n++;}}}
            boolean squeezed=false;for(int i=0;i<n&&!squeezed;i++)for(int j=i+1;j<n;j++)if(nx[i]*nx[j]+ny[i]*ny[j]<-.35f){squeezed=true;break;}
            if(squeezed){bvx*=.78f;bvy*=.78f;float sp=len(bvx,bvy),cap=430f*s;if(sp>cap){bvx=bvx/sp*cap;bvy=bvy/sp*cap;}}
        }

        void spawnConfettiV34(){
            confettiV34.clear();int[] cs={Color.rgb(255,207,54),Color.rgb(55,130,255),Color.rgb(244,67,76),Color.rgb(72,205,112),Color.WHITE,Color.rgb(176,92,230)};
            for(int i=0;i<94;i++){float x=rng.nextFloat()*w,y=-18*s-rng.nextFloat()*h*.18f,vx=(rng.nextFloat()-.5f)*145*s,vy=(85+rng.nextFloat()*150)*s,life=1.5f+rng.nextFloat()*.9f;confettiV34.add(new Confetti(x,y,vx,vy,life,rng.nextFloat()*360,(rng.nextFloat()-.5f)*400,(5+rng.nextFloat()*4)*s,(2.5f+rng.nextFloat()*3)*s,cs[rng.nextInt(cs.length)]));}
        }
        void updateConfettiV34(float dt){for(int i=confettiV34.size()-1;i>=0;i--){Confetti q=confettiV34.get(i);q.life-=dt;if(q.life<=0){confettiV34.remove(i);continue;}q.vy+=225*s*dt;q.x+=q.vx*dt;q.y+=q.vy*dt;q.rot+=q.spin*dt;}}
        void drawConfettiV34(Canvas c){for(Confetti q:confettiV34){float a=clamp(q.life/q.maxLife,0,1);int al=(int)(255*Math.min(1,a*1.8f));p.setColor((q.color&0x00FFFFFF)|(al<<24));c.save();c.rotate(q.rot,q.x,q.y);c.drawRect(q.x-q.ww*.5f,q.y-q.hh*.5f,q.x+q.ww*.5f,q.y+q.hh*.5f,p);c.restore();}}

        void updateCameraV34(float dt){
            if(w<=0||h<=0)return;float tx=blue[0].x*.82f+bx*.18f,ty=blue[0].y*.82f+by*.18f;
            if(camXV34==0&&camYV34==0){camXV34=tx;camYV34=ty;}
            float k=Math.min(1f,dt*5.3f);camXV34+=(tx-camXV34)*k;camYV34+=(ty-camYV34)*k;
            float z=goalShowV34>0?1.15f:1.10f,hw=w/(2f*z),hh=h/(2f*z);
            camXV34=clamp(camXV34,hw,w-hw);camYV34=clamp(camYV34,hh,h-hh);
        }

        void drawCountdownV34(Canvas c){
            if(countdownV34<=0)return;String txt=countdownV34>3f?"3":countdownV34>2f?"2":countdownV34>1f?"1":"GO!";
            p.setStyle(Paint.Style.FILL);p.setColor(Color.argb(92,0,0,0));c.drawCircle(w*.5f,h*.46f,59*s,p);p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize((txt.equals("GO!")?40f:56f)*s);p.setColor(Color.WHITE);c.drawText(txt,w*.5f,h*.46f+18*s,p);
        }

        void drawGoalV34(Canvas c){
            if(goalShowV34<=0)return;p.setStyle(Paint.Style.FILL);p.setColor(Color.argb(58,0,0,0));c.drawRect(0,0,w,h,p);drawConfettiV34(c);
            float cw=410*s,ch=118*s,cx=w*.5f,cy=h*.40f;p.setColor(Color.argb(214,8,11,16));c.drawRoundRect(new RectF(cx-cw/2,cy-ch/2,cx+cw/2,cy+ch/2),19*s,19*s,p);
            p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(16*s);p.setColor(Color.rgb(247,205,60));c.drawText("GOAL!",cx,cy-27*s,p);
            p.setTextSize(33*s);p.setColor(Color.WHITE);c.drawText(blueScore+"   -   "+redScore,cx,cy+14*s,p);p.setTextSize(11*s);p.setColor(Color.rgb(160,174,194));c.drawText(lastGoalBlueV34?"BLUE SCORED":"RED SCORED",cx,cy+42*s,p);
        }

        void drawSplashV34(Canvas c){
            c.drawColor(Color.rgb(10,14,19));float total=2200f,t=clamp(1f-(splashUntilV34-SystemClock.uptimeMillis())/total,0,1);drawLogo(c,w*.5f,h*.40f);title(c,"CIRCLE FOOTBALL",h*.54f,35);float bw=250*s,bh=5*s,x=(w-bw)/2f,y=h*.64f;p.setColor(Color.rgb(35,41,51));c.drawRoundRect(new RectF(x,y,x+bw,y+bh),bh,bh,p);p.setColor(Color.rgb(47,122,245));c.drawRoundRect(new RectF(x,y,x+bw*t,y+bh),bh,bh,p);subtitle(c,"LOADING",h*.70f,11,Color.rgb(115,132,154));
        }
'''
if 'boolean collidePostV34' not in s:
    marker='        void physicsStep(float dt){'
    if marker not in s: raise RuntimeError('physics marker missing')
    s=s.replace(marker,helpers+'\n'+marker,1)

# Whole-ball crossing counts immediately. Posts are physical; a post hit cannot
# become a phantom goal that then exits again.
s=rep(s,'handleBallWalls',r'''        void handleBallWalls(){
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf;boolean bounced=false;
            if(by-ballR<pitch.top){by=pitch.top+ballR;bvy=Math.abs(bvy)*.84f;bounced=true;}
            if(by+ballR>pitch.bottom){by=pitch.bottom-ballR;bvy=-Math.abs(bvy)*.84f;bounced=true;}

            boolean postHit=false;
            postHit|=collidePostV34(pitch.left,y1);postHit|=collidePostV34(pitch.left,y2);
            postHit|=collidePostV34(pitch.right,y1);postHit|=collidePostV34(pitch.right,y2);
            if(postHit)bounced=true;

            boolean wholeInside=(by-ballR>y1+1.0f*s&&by+ballR<y2-1.0f*s);
            if(!goalLatchedV34&&wholeInside){
                if(bx+ballR<pitch.left){scoreGoal(false);return;}
                if(bx-ballR>pitch.right){scoreGoal(true);return;}
            }
            boolean mouth=by>y1+ballR&&by<y2-ballR;
            if(!mouth){
                if(bx-ballR<pitch.left){bx=pitch.left+ballR;bvx=Math.abs(bvx)*.86f;bounced=true;}
                if(bx+ballR>pitch.right){bx=pitch.right-ballR;bvx=-Math.abs(bvx)*.86f;bounced=true;}
            }
            if(bounced&&wallSoundCooldown<=0&&len(bvx,bvy)>90*s){playSfx(SFX_WALL);wallSoundCooldown=.07f;}
        }''')

# Preserve v2.2 physics order and add only squeeze stabilization.
s=rep(s,'physicsStep',r'''        void physicsStep(float dt){
            for(int i=0;i<teamSize;i++){
                Disc a=blue[i],b=red[i];a.x+=a.vx*dt;a.y+=a.vy*dt;b.x+=b.vx*dt;b.y+=b.vy*dt;clampDisc(a);clampDisc(b);
            }
            for(int pass=0;pass<2;pass++)resolveAllDiscCollisions();
            lastBallX=bx;lastBallY=by;bx+=bvx*dt;by+=bvy*dt;float fr=(float)Math.pow(.9885,dt*60f);bvx*=fr;bvy*=fr;
            for(int pass=0;pass<3;pass++){for(int i=0;i<teamSize;i++){resolveBallDisc(blue[i]);resolveBallDisc(red[i]);}}
            stabilizeSqueezeV34();handleBallWalls();
            float moved=dist(lastBallX,lastBallY,bx,by);if(moved>.001f){float sign=(Math.abs(bvx)>Math.abs(bvy))?(bvx>=0?1f:-1f):(bvy>=0?-1f:1f);ballAngle+=sign*(moved/Math.max(1f,ballR))*57.2958f;}emitMotionTrail(dt);
        }''')

# Goal flow + countdown without changing chasers, formations, passing or kick decisions.
s=rep(s,'updateGame',r'''        void updateGame(float dt){
            if(countdownV34>0f){countdownV34=Math.max(0,countdownV34-dt);updateCameraV34(dt);syncRealAudio();return;}
            if(goalShowV34<=0f&&!goldenGoal){matchTime-=dt;if(matchTime<=0){matchTime=0;if(blueScore==redScore)goldenGoal=true;else{finishMatch();return;}}}
            if(mode!=GAME)return;
            for(int i=0;i<teamSize;i++){blue[i].kickCd=Math.max(0,blue[i].kickCd-dt);red[i].kickCd=Math.max(0,red[i].kickCd-dt);blue[i].wallPlayTime=Math.max(0,blue[i].wallPlayTime-dt);red[i].wallPlayTime=Math.max(0,red[i].wallPlayTime-dt);}
            wallSoundCooldown=Math.max(0,wallSoundCooldown-dt);touchSoundCooldown=Math.max(0,touchSoundCooldown-dt);
            updateHuman(dt);chooseChasers();updateTeamAI(blue,red,0,blueChaser,dt);updateTeamAI(red,blue,1,redChaser,dt);
            int steps=Math.max(2,Math.min(12,(int)Math.ceil(dt/.0038f)));float sub=dt/steps;for(int st=0;st<steps;st++)physicsStep(sub);updateParticles(dt);updateCameraV34(dt);
            if(goalShowV34>0f){goalShowV34=Math.max(0,goalShowV34-dt);updateConfettiV34(dt);if(goalShowV34<=0){confettiV34.clear();if(pendingFinishV34){pendingFinishV34=false;finishMatch();return;}resetPositions();goalLatchedV34=false;countdownV34=3.35f;camXV34=blue[0].x;camYV34=blue[0].y;}}
            float near=Math.min(Math.abs(bx-pitch.left),Math.abs(pitch.right-bx))/Math.max(1f,pitch.width());float threat=clamp((.34f-near)/.34f,0f,1f);float speedBoost=clamp(len(bvx,bvy)/(850*s),0f,1f)*.28f;crowdExcitement=goalShowV34>0?1f:clamp(threat+speedBoost,0f,1f);syncRealAudio();
        }''')

s=rep(s,'scoreGoal',r'''        void scoreGoal(boolean blueGoal){
            if(mode!=GAME||goalLatchedV34)return;goalLatchedV34=true;if(blueGoal)blueScore++;else redScore++;lastGoalBlueV34=blueGoal;playSfx(SFX_GOAL);haptic(70);pendingFinishV34=blueScore>=targetGoals||redScore>=targetGoals||goldenGoal;goalShowV34=pendingFinishV34?4.2f:2.65f;spawnConfettiV34();
        }''')

s=rep(s,'startMatch',r'''        void startMatch(){
            blueScore=redScore=0;matchTime=180f;goldenGoal=false;savedResult=false;goalLatchedV34=false;pendingFinishV34=false;goalShowV34=0;countdownV34=3.35f;confettiV34.clear();
            mode=GAME;lastFrame=System.nanoTime();joyPointer=-1;joyNX=joyNY=0;joyX=joyBaseX;joyY=joyBaseY;
            prefs.edit().putInt("difficulty",difficulty).putInt("team_size",teamSize).putInt("target_goals",targetGoals).putInt("field_theme",fieldTheme).apply();configureField();resetPositions();camXV34=blue[0].x;camYV34=blue[0].y;playSfx(SFX_MENU);
        }''')

s=rep(s,'finishMatch',r'''        void finishMatch(){
            if(mode==RESULT)return;mode=RESULT;resultFxV34=6.0f;if(confettiV34.isEmpty())spawnConfettiV34();if(!savedResult){playSfx(blueScore>redScore?SFX_WIN:SFX_LOSE);savedResult=true;}joyPointer=-1;joyNX=joyNY=0;joyX=joyBaseX;joyY=joyBaseY;
        }''')

# Camera applies only to world rendering; HUD and controls stay fixed on screen.
s=rep(s,'drawGame',r'''        void drawGame(Canvas c){
            int outside,a,b,line;if(fieldTheme==1){outside=Color.rgb(38,119,43);a=Color.rgb(54,156,56);b=Color.rgb(48,145,51);line=Color.rgb(244,247,242);}else if(fieldTheme==2){outside=Color.rgb(16,32,50);a=Color.rgb(31,57,84);b=Color.rgb(27,50,76);line=Color.rgb(215,232,246);}else if(fieldTheme==3){outside=Color.rgb(42,122,47);a=Color.rgb(60,153,64);b=Color.rgb(51,139,57);line=Color.rgb(244,247,242);}else if(fieldTheme==4){outside=Color.rgb(45,45,47);a=Color.rgb(76,76,78);b=Color.rgb(69,69,71);line=Color.WHITE;}else{outside=Color.rgb(52,56,60);a=Color.rgb(68,73,78);b=Color.rgb(61,66,71);line=Color.WHITE;}
            c.drawColor(outside);c.save();float z=goalShowV34>0?1.15f:1.10f;c.translate(w*.5f,h*.5f);c.scale(z,z);c.translate(-camXV34,-camYV34);
            p.setStyle(Paint.Style.FILL);p.setColor(a);c.drawRect(pitch,p);int bands=fieldTheme==4?9:(fieldTheme==3?12:10);for(int i=0;i<bands;i++){p.setColor(i%2==0?a:b);float xx=pitch.left+pitch.width()*i/bands;c.drawRect(xx,pitch.top,xx+pitch.width()/bands,pitch.bottom,p);}if(fieldTheme==1||fieldTheme==3){p.setColor(Color.argb(15,255,255,255));for(int i=0;i<7;i++)c.drawRect(pitch.left,pitch.top+i*pitch.height()/7f,pitch.right,pitch.top+(i+.11f)*pitch.height()/7f,p);}
            stroke.setStyle(Paint.Style.STROKE);stroke.setColor(line);stroke.setStrokeWidth(3*s/z);c.drawRect(pitch,stroke);c.drawLine(pitch.centerX(),pitch.top,pitch.centerX(),pitch.bottom,stroke);c.drawCircle(pitch.centerX(),pitch.centerY(),Math.min(74*s,pitch.height()*.14f),stroke);c.drawCircle(pitch.centerX(),pitch.centerY(),3.5f*s,stroke);float areaR=Math.min(pitch.height()*.34f,pitch.width()*.19f);c.drawArc(new RectF(pitch.left-areaR,pitch.centerY()-areaR,pitch.left+areaR,pitch.centerY()+areaR),-90,180,false,stroke);c.drawArc(new RectF(pitch.right-areaR,pitch.centerY()-areaR,pitch.right+areaR,pitch.centerY()+areaR),90,180,false,stroke);
            drawGoals(c);drawHumanGuideV33(c);drawParticles(c);for(int i=0;i<teamSize;i++)drawDisc(c,blue[i]);for(int i=0;i<teamSize;i++)drawDisc(c,red[i]);drawFootball(c,bx,by,ballR,ballAngle);c.restore();
            drawScoreHud(c);drawJoystick(c,false);drawKick(c,false);if(goalShowV34>0)drawGoalV34(c);if(countdownV34>0)drawCountdownV34(c);
        }''')

# Visible startup loading and result confetti; otherwise retain all existing screens.
s=rep(s,'onDraw',r'''        @Override protected void onDraw(Canvas c){
            super.onDraw(c);if(SystemClock.uptimeMillis()<splashUntilV34){hits.clear();drawSplashV34(c);postInvalidateOnAnimation();return;}
            long now=System.nanoTime();float dt=lastFrame==0?0f:Math.min(.035f,(now-lastFrame)/1_000_000_000f);lastFrame=now;hits.clear();
            if(mode==GAME){if(dt>0)updateGame(dt);drawGame(c);}else if(mode==PAUSE){drawGame(c);drawPause(c);}else if(mode==HOME)drawHome(c);else if(mode==SETUP)drawSetup(c);else if(mode==PLAYERS)drawPlayers(c);else if(mode==SETTINGS)drawSettings(c);else if(mode==CONTROLS)drawControlsEditor(c);else if(mode==RESULT){if(dt>0&&resultFxV34>0){resultFxV34=Math.max(0,resultFxV34-dt);updateConfettiV34(dt);}drawResult(c);drawConfettiV34(c);}postInvalidateOnAnimation();
        }''')

# Ignore match input during kickoff countdown only; after a goal controls keep working.
s=s.replace('            if(mode==CONTROLS)return handleControlTouch(e,action,idx);',
            '            if(mode==CONTROLS)return handleControlTouch(e,action,idx);\n            if(mode==GAME&&countdownV34>0f)return true;',1)

# v3.4 identity.
s=s.replace('circle_football_v33','circle_football_v34')
path.write_text(s,encoding='utf-8')

m=Path('AndroidManifest.xml');x=m.read_text(encoding='utf-8');x=x.replace('com.godnit.circlefootballlite.v33','com.godnit.circlefootballlite.v34');x=re.sub(r'android:versionCode="\d+"','android:versionCode="24"',x,count=1);x=re.sub(r'android:versionName="[^"]+"','android:versionName="3.4.0"',x,count=1);m.write_text(x,encoding='utf-8')
print('Applied v3.4: v2.2 player system + slower equal speed + flow + stable posts/squeeze + follow camera')
