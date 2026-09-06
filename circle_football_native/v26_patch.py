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

# state
s=s.replace('        final List<Particle> particles = new ArrayList<>();\n','        final List<Particle> particles = new ArrayList<>();\n        final List<Confetti> confetti = new ArrayList<>();\n',1)
s=s.replace('        boolean goldenGoal=false, savedResult=false;\n        long lastFrame=0L;\n','        boolean goldenGoal=false, savedResult=false;\n        float goalPauseTimer=0f,bluePassLock=0f,redPassLock=0f;\n        boolean pendingFinishAfterGoal=false,lastGoalBlue=false;\n        long splashUntil=SystemClock.uptimeMillis()+1150L;\n        long lastFrame=0L;\n',1)
s=s.replace('            float x,y,vx,vy,kickCd,wallPlayTime,wallPlayX,wallPlayY;\n','            float x,y,vx,vy,kickCd,wallPlayTime,wallPlayX,wallPlayY;\n            float stuckTimer,escapeTimer,escapeX,escapeY,lastAiX,lastAiY;\n',1)
if 'static final class Confetti' not in s:
    mk='        static final class Particle{'
    cf='''        static final class Confetti{\n            float x,y,vx,vy,life,maxLife,rot,spin,ww,hh;int color;\n            Confetti(float x,float y,float vx,float vy,float life,float rot,float spin,float ww,float hh,int color){\n                this.x=x;this.y=y;this.vx=vx;this.vy=vy;this.life=this.maxLife=life;this.rot=rot;this.spin=spin;this.ww=ww;this.hh=hh;this.color=color;\n            }\n        }\n'''
    s=s.replace(mk,cf+mk,1)

# smaller scale, slightly larger goal opening, guaranteed visible side margin
s=rep(s,'configureField',r'''        void configureField(){
            float mxRatio,myRatio;
            if(fieldTheme==3){mxRatio=.052f;myRatio=.078f;}
            else if(fieldTheme==2){mxRatio=.064f;myRatio=.104f;}
            else{mxRatio=teamSize>=3?.058f:.073f;myRatio=teamSize>=3?.098f:.116f;}
            float mx=Math.max(w*mxRatio,56f*s),my=h*myRatio;
            pitch.set(mx,my,w-mx,h-my);
            goalHalf=pitch.height()*.215f;
            float ts=teamSize>=4?.78f:(teamSize==3?.87f:1f),fs=fieldTheme==3?.88f:(fieldTheme==2?.95f:1f);
            discR=23.5f*s*ts*fs;
            float bt=teamSize>=4?.84f:(teamSize==3?.91f:1f),bf=fieldTheme==3?.86f:(fieldTheme==2?.94f:1f);
            ballR=10.8f*s*bt*bf;
        }''')

if 'float goalDepthV26()' not in s:
    s=s.replace('        void drawGoals(Canvas c){', '        float goalDepthV26(){return clamp(Math.min(pitch.left-8f*s,w-pitch.right-8f*s),28f*s,46f*s);}\n\n        void drawGoals(Canvas c){',1)

s=rep(s,'drawGoals',r'''        void drawGoals(Canvas c){
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf,depth=goalDepthV26(),curve=12f*s;
            int frame=fieldTheme==2?Color.rgb(205,228,242):Color.rgb(248,249,247);
            int net=fieldTheme==2?Color.argb(95,148,184,207):Color.argb(92,190,198,202);
            stroke.setStyle(Paint.Style.STROKE);stroke.setStrokeWidth(2.7f*s);stroke.setColor(frame);
            path.reset();path.moveTo(pitch.left,y1);path.lineTo(pitch.left-depth*.62f,y1);path.quadTo(pitch.left-depth,y1,pitch.left-depth,y1+curve);path.lineTo(pitch.left-depth,y2-curve);path.quadTo(pitch.left-depth,y2,pitch.left-depth*.62f,y2);path.lineTo(pitch.left,y2);c.drawPath(path,stroke);
            path.reset();path.moveTo(pitch.right,y1);path.lineTo(pitch.right+depth*.62f,y1);path.quadTo(pitch.right+depth,y1,pitch.right+depth,y1+curve);path.lineTo(pitch.right+depth,y2-curve);path.quadTo(pitch.right+depth,y2,pitch.right+depth*.62f,y2);path.lineTo(pitch.right,y2);c.drawPath(path,stroke);
            stroke.setStrokeWidth(.8f*s);stroke.setColor(net);
            for(int i=1;i<4;i++){float yy=y1+(y2-y1)*i/4f;c.drawLine(pitch.left-depth*.92f,yy,pitch.left,yy,stroke);c.drawLine(pitch.right,yy,pitch.right+depth*.92f,yy,stroke);}
            for(int i=1;i<3;i++){float lx=pitch.left-depth+depth*i/3f,rx=pitch.right+depth-depth*i/3f;c.drawLine(lx,y1+3*s,lx,y2-3*s,stroke);c.drawLine(rx,y1+3*s,rx,y2-3*s,stroke);}
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(22,24,26));
            c.drawCircle(pitch.left,y1,5.6f*s,p);c.drawCircle(pitch.left,y2,5.6f*s,p);c.drawCircle(pitch.right,y1,5.6f*s,p);c.drawCircle(pitch.right,y2,5.6f*s,p);
            p.setColor(frame);c.drawCircle(pitch.left,y1,4*s,p);c.drawCircle(pitch.left,y2,4*s,p);c.drawCircle(pitch.right,y1,4*s,p);c.drawCircle(pitch.right,y2,4*s,p);
        }''')

s=rep(s,'clampDisc',r'''        void clampDisc(Disc d){
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf,sideRun=36f*s,endRun=22f*s,gd=goalDepthV26();
            d.y=clamp(d.y,pitch.top-sideRun,pitch.bottom+sideRun);
            if(d.x<pitch.left){
                boolean in=d.y>y1+discR*.18f&&d.y<y2-discR*.18f;
                if(in){d.x=clamp(d.x,pitch.left-gd+discR*.55f,pitch.left);d.y=clamp(d.y,y1+discR*.72f,y2-discR*.72f);}else d.x=clamp(d.x,pitch.left-endRun,pitch.right+endRun);
            }else if(d.x>pitch.right){
                boolean in=d.y>y1+discR*.18f&&d.y<y2-discR*.18f;
                if(in){d.x=clamp(d.x,pitch.right,pitch.right+gd-discR*.55f);d.y=clamp(d.y,y1+discR*.72f,y2-discR*.72f);}else d.x=clamp(d.x,pitch.left-endRun,pitch.right+endRun);
            }else d.x=clamp(d.x,pitch.left-endRun,pitch.right+endRun);
        }''')

# loading splash
if 'void drawSplashV26(Canvas c)' not in s:
    s=s.replace('        @Override protected void onDraw(Canvas c){',r'''        void drawSplashV26(Canvas c){
            c.drawColor(Color.rgb(10,14,19));float t=clamp(1f-(splashUntil-SystemClock.uptimeMillis())/1150f,0f,1f);
            p.setStyle(Paint.Style.FILL);p.setColor(Color.argb(28,80,145,255));c.drawCircle(w*.5f,h*.42f,128f*s,p);
            drawLogo(c,w*.5f,h*.39f);title(c,"CIRCLE FOOTBALL",h*.53f,35f);subtitle(c,"TACTICAL ARCADE FOOTBALL",h*.575f,13f,Color.rgb(145,165,190));
            float bw=260f*s,bh=5f*s,x=(w-bw)/2f,y=h*.66f;p.setColor(Color.rgb(35,41,51));c.drawRoundRect(new RectF(x,y,x+bw,y+bh),bh,bh,p);p.setColor(Color.rgb(47,122,245));c.drawRoundRect(new RectF(x,y,x+bw*t,y+bh),bh,bh,p);
            subtitle(c,"LOADING MATCH ENGINE",h*.715f,11f,Color.rgb(102,118,140));
        }

        @Override protected void onDraw(Canvas c){''',1)

s=rep(s,'onDraw',r'''        @Override protected void onDraw(Canvas c){
            super.onDraw(c);
            if(SystemClock.uptimeMillis()<splashUntil){hits.clear();drawSplashV26(c);postInvalidateOnAnimation();return;}
            long now=System.nanoTime();float dt=lastFrame==0?0f:Math.min(.035f,(now-lastFrame)/1_000_000_000f);lastFrame=now;hits.clear();
            if(mode==GAME){if(dt>0)updateGame(dt);drawGame(c);}else if(mode==PAUSE){drawGame(c);drawPause(c);}else if(mode==HOME)drawHome(c);else if(mode==SETUP)drawSetup(c);else if(mode==PLAYERS)drawPlayers(c);else if(mode==SETTINGS)drawSettings(c);else if(mode==CONTROLS)drawControlsEditor(c);else if(mode==RESULT)drawResult(c);
            postInvalidateOnAnimation();
        }''')

# better menu
s=rep(s,'drawHome',r'''        void drawHome(Canvas c){
            background(c);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(2f*s);p.setColor(Color.argb(22,120,150,190));c.drawCircle(w*.5f,h*.43f,170f*s,p);c.drawLine(w*.5f-220f*s,h*.43f,w*.5f+220f*s,h*.43f,p);
            drawLogo(c,w/2f,102f*s);title(c,"CIRCLE FOOTBALL",174f*s,41f);subtitle(c,"SMART TEAM FOOTBALL • OFFLINE",211f*s,15f,Color.rgb(145,169,201));
            float mw=430f*s,x=(w-mw)/2f;menuButton(c,"PLAY MATCH","play",x,265f*s,mw,66f*s,Color.rgb(29,121,255));
            float sw=208f*s,g=14f*s;menuButton(c,"PLAYERS","players",w/2f-sw-g/2f,349f*s,sw,58f*s,Color.rgb(48,56,70));menuButton(c,"SETTINGS","settings",w/2f+g/2f,349f*s,sw,58f*s,Color.rgb(48,56,70));
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(25,30,38));c.drawRoundRect(new RectF(w/2f-250f*s,440f*s,w/2f+250f*s,510f*s),16f*s,16f*s,p);
            subtitle(c,"1v1 • 2v2 • 3v3 • 4v4",468f*s,14f,Color.rgb(185,196,212));subtitle(c,"4 STADIUMS • SMART ROLES • REAL AUDIO",493f*s,11f,Color.rgb(105,124,151));
        }''')

if 'void drawStadiumPreviewV26(Canvas c,RectF r)' not in s:
    s=s.replace('        void drawSetup(Canvas c){',r'''        String fieldNameV26(){return fieldTheme==0?"CLASSIC":fieldTheme==1?"GRASS":fieldTheme==2?"NIGHT":"WIDE";}
        void drawStadiumPreviewV26(Canvas c,RectF r){
            int out,p1,p2,line;if(fieldTheme==1){out=Color.rgb(34,96,38);p1=Color.rgb(54,156,56);p2=Color.rgb(47,143,50);line=Color.WHITE;}else if(fieldTheme==2){out=Color.rgb(11,23,38);p1=Color.rgb(31,57,84);p2=Color.rgb(26,48,73);line=Color.rgb(213,231,245);}else if(fieldTheme==3){out=Color.rgb(36,103,41);p1=Color.rgb(60,153,64);p2=Color.rgb(51,139,57);line=Color.WHITE;}else{out=Color.rgb(43,47,52);p1=Color.rgb(68,73,78);p2=Color.rgb(61,66,71);line=Color.WHITE;}
            p.setStyle(Paint.Style.FILL);p.setColor(out);c.drawRoundRect(r,15f*s,15f*s,p);RectF f=new RectF(r.left+16*s,r.top+16*s,r.right-16*s,r.bottom-16*s);p.setColor(p1);c.drawRect(f,p);for(int i=0;i<8;i++){p.setColor(i%2==0?p1:p2);float xx=f.left+f.width()*i/8f;c.drawRect(xx,f.top,xx+f.width()/8f,f.bottom,p);}stroke.setStyle(Paint.Style.STROKE);stroke.setStrokeWidth(1.4f*s);stroke.setColor(line);c.drawRect(f,stroke);c.drawLine(f.centerX(),f.top,f.centerX(),f.bottom,stroke);c.drawCircle(f.centerX(),f.centerY(),f.height()*.15f,stroke);float gh=f.height()*.23f,gd=11f*s;c.drawRect(new RectF(f.left-gd,f.centerY()-gh,f.left,f.centerY()+gh),stroke);c.drawRect(new RectF(f.right,f.centerY()-gh,f.right+gd,f.centerY()+gh),stroke);
            p.setStyle(Paint.Style.FILL);p.setColor(Color.argb(190,8,11,15));RectF tag=new RectF(r.left+10*s,r.top+9*s,r.left+115*s,r.top+34*s);c.drawRoundRect(tag,10*s,10*s,p);p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(11.5f*s);p.setColor(Color.WHITE);c.drawText(fieldNameV26(),tag.centerX(),tag.centerY()+4*s,p);
        }

        void drawSetup(Canvas c){''',1)

s=rep(s,'drawSetup',r'''        void drawSetup(Canvas c){
            background(c);title(c,"PLAY MATCH",42f*s,27f);String[] ds={"EASY","NORMAL","HARD"};float rw=170*s,g=10*s,total=rw*3+g*2,st=(w-total)/2f;subtitle(c,"DIFFICULTY",69*s,11,Color.rgb(145,160,180));for(int i=0;i<3;i++)menuButton(c,ds[i],"diff"+i,st+i*(rw+g),80*s,rw,40*s,i==difficulty?Color.rgb(29,121,255):Color.rgb(48,56,70));
            subtitle(c,"PLAYERS",139*s,11,Color.rgb(145,160,180));float pw=118*s,pg=9*s,pt=pw*4+pg*3,ps=(w-pt)/2f;for(int i=1;i<=4;i++)menuButton(c,i+"v"+i,"team"+i,ps+(i-1)*(pw+pg),150*s,pw,39*s,i==teamSize?Color.rgb(34,174,91):Color.rgb(48,56,70));
            subtitle(c,"GOAL LIMIT",207*s,11,Color.rgb(145,160,180));int[] gs={3,5,7};for(int i=0;i<3;i++)menuButton(c,""+gs[i],"goal"+gs[i],st+i*(rw+g),218*s,rw,39*s,gs[i]==targetGoals?Color.rgb(238,157,32):Color.rgb(48,56,70));
            subtitle(c,"STADIUM",275*s,11,Color.rgb(145,160,180));String[] fs={"CLASSIC","GRASS","NIGHT","WIDE"};float fw=132*s,fg=9*s,ft=fw*4+fg*3,fs=(w-ft)/2f;for(int i=0;i<4;i++)menuButton(c,fs[i],"field"+i,fs+i*(fw+fg),286*s,fw,39*s,i==fieldTheme?Color.rgb(102,82,205):Color.rgb(48,56,70));
            drawStadiumPreviewV26(c,new RectF(w/2f-250*s,342*s,w/2f+250*s,Math.min(h-145*s,515*s)));menuButton(c,"START MATCH","start",w/2f-215*s,h-118*s,430*s,52*s,Color.rgb(29,121,255));menuButton(c,"BACK","home",w/2f-105*s,h-57*s,210*s,42*s,Color.rgb(48,56,70));
        }''')

# tactical helpers
if 'int closestDefenderV26(' not in s:
    s=s.replace('        void chooseChasers(){',r'''        int closestDefenderV26(Disc[] t,int a,int b,float x,float y){if(a>=b)return Math.min(teamSize-1,a);int best=a;float bd=Float.MAX_VALUE;for(int i=a;i<b;i++){float d=sq(t[i].x-x)+sq(t[i].y-y);if(d<bd){bd=d;best=i;}}return best;}
        Disc markV26(Disc[] opp,int teamId,int slot){float zy=pitch.top+pitch.height()*(slot+1f)/(Math.max(1,teamSize-1)+1f);Disc best=null;float bs=-999999;for(int i=0;i<teamSize;i++){Disc o=opp[i];float prog=teamId==0?(pitch.right-o.x):(o.x-pitch.left);float sc=(pitch.width()-prog)*.85f-Math.abs(o.y-zy)*.42f-dist(o.x,o.y,bx,by)*.08f;if(sc>bs){bs=sc;best=o;}}return best;}
        float shotClearV26(Disc[] opp,int teamId,float gy){float gx=teamId==0?pitch.right+18*s:pitch.left-18*s,best=999999;for(int i=0;i<teamSize;i++){float t=segmentT(opp[i].x,opp[i].y,bx,by,gx,gy);if(t>.03f&&t<1.03f)best=Math.min(best,distToSegment(opp[i].x,opp[i].y,bx,by,gx,gy));}return best;}

        void chooseChasers(){''',1)

s=rep(s,'chooseChasers',r'''        void chooseChasers(){
            float lead=difficulty==0?.07f:(difficulty==1?.13f:.20f),px=bx+bvx*lead,py=by+bvy*lead,cw=pitch.width(),cx=pitch.centerX();
            blueChaser=-1;if(teamSize>=2&&px<cx+cw*.10f){if(px<pitch.left+cw*.13f)blueChaser=teamSize-1;else if(teamSize>=3)blueChaser=closestDefenderV26(blue,1,teamSize-1,px,py);else blueChaser=teamSize-1;}
            redChaser=0;if(teamSize>=2&&px>cx-cw*.10f){if(px>pitch.right-cw*.13f)redChaser=teamSize-1;else if(teamSize>=3)redChaser=closestDefenderV26(red,1,teamSize-1,px,py);else redChaser=teamSize-1;}
        }''')

s=rep(s,'formationTarget',r'''        float[] formationTarget(int teamId,int idx,int chaser){
            float own=teamId==0?pitch.left:pitch.right,sg=teamId==0?1f:-1f,px=bx+bvx*(difficulty==2?.18f:.10f),py=by+bvy*(difficulty==2?.18f:.10f);
            if(idx==0){float x=teamId==0?clamp(px-95*s,pitch.left+pitch.width()*.22f,pitch.right-pitch.width()*.14f):clamp(px+95*s,pitch.left+pitch.width()*.14f,pitch.right-pitch.width()*.22f);return new float[]{x,clamp(py*.58f+pitch.centerY()*.42f,pitch.top+discR*1.5f,pitch.bottom-discR*1.5f)};}
            if(idx==teamSize-1&&teamSize>=2)return new float[]{own+sg*pitch.width()*.055f,clamp(py,pitch.centerY()-goalHalf*.70f,pitch.centerY()+goalHalf*.70f)};
            int slot=idx-1;Disc m=markV26(teamId==0?red:blue,teamId,slot);float threat=teamId==0?clamp((pitch.centerX()+pitch.width()*.14f-px)/(pitch.width()*.60f),0,1):clamp((px-(pitch.centerX()-pitch.width()*.14f))/(pitch.width()*.60f),0,1);float base=own+sg*pitch.width()*(.20f+slot*.045f),ix=px-sg*(72f+slot*18f)*s;float lo=teamId==0?pitch.left+pitch.width()*.13f:pitch.centerX()-pitch.width()*.08f,hi=teamId==0?pitch.centerX()+pitch.width()*.08f:pitch.right-pitch.width()*.13f;ix=clamp(ix,lo,hi);float x=base*(1-threat)+ix*threat,zy=pitch.top+pitch.height()*(slot+1f)/(Math.max(1,teamSize-2)+1f),my=m==null?zy:m.y,y=zy*.22f+my*.48f+py*.30f;return new float[]{x,clamp(y,pitch.top+discR*1.5f,pitch.bottom-discR*1.5f)};
        }''')

s=rep(s,'bestPassTarget',r'''        int bestPassTarget(Disc d,Disc[] team,Disc[] opp,int teamId){
            if((teamId==0?bluePassLock:redPassLock)>0)return -1;int best=-1;float bs=-999999;for(int i=0;i<teamSize;i++){Disc m=team[i];if(m==d)continue;float pd=dist(d.x,d.y,m.x,m.y);if(pd<78*s||pd>pitch.width()*.56f)continue;float f=teamId==0?m.x-d.x:d.x-m.x;if(f<20*s&&d.index==0)continue;float lane=discR*(difficulty==2?1.05f:(difficulty==1?1.22f:1.42f));if(isLaneBlocked(opp,bx,by,m.x,m.y,lane))continue;float score=nearestOpponentDistance(opp,m.x,m.y)*.66f+f*.48f-pd*.08f-Math.abs(m.y-pitch.centerY())*.06f;if(i==0)score+=46*s;if(i==teamSize-1&&teamSize>=2)score-=88*s;if(score>bs){bs=score;best=i;}}return best;
        }''')

s=rep(s,'chooseKickTarget',r'''        float[] chooseKickTarget(Disc d,Disc[] team,Disc[] opp,int teamId){
            float sg=teamId==0?1f:-1f,gx=teamId==0?pitch.right+18*s:pitch.left-18*s,gy=bestGoalLaneV25(opp,teamId),gd=Math.abs(gx-bx),clear=shotClearV26(opp,teamId,gy);boolean finalZ=gd<pitch.width()*(difficulty==0?.30f:(difficulty==1?.39f:.47f)),good=clear>discR*(difficulty==2?1.05f:(difficulty==1?1.25f:1.48f));int pressure=countOpponentsNear(opp,d.x,d.y,(difficulty==2?112f:(difficulty==1?102f:92f))*s),passTo=bestPassTarget(d,team,opp,teamId);boolean keeper=d.index==teamSize-1&&teamSize>=2,def=d.index>0&&!keeper;
            if(finalZ&&good)return new float[]{gx,gy,0,0,0,0};
            if(keeper||def){if(pressure>0&&passTo>=0){Disc m=team[passTo];return new float[]{m.x+m.vx*.16f,m.y+m.vy*.16f,1,0,0,0};}return new float[]{bx+sg*(180f+25f*difficulty)*s,by*.62f+pitch.centerY()*.38f,2,0,0,0};}
            if(finalZ){if(passTo>=0&&pressure>=2){Disc m=team[passTo];return new float[]{m.x+m.vx*.14f,m.y+m.vy*.14f,1,0,0,0};}return new float[]{gx,gy,0,0,0,0};}
            if(passTo>=0&&pressure>0){Disc m=team[passTo];float prog=teamId==0?m.x-d.x:d.x-m.x;if(prog>45*s)return new float[]{m.x+m.vx*.13f,m.y+m.vy*.13f,1,0,0,0};}
            return new float[]{bx+sg*(185f+30f*difficulty)*s,gy*.35f+by*.65f,2,0,0,0};
        }''')

s=rep(s,'moveAiToward',r'''        void moveAiToward(Disc d,float tx,float ty,float dt){
            float odx=tx-d.x,ody=ty-d.y,ol=len(odx,ody);if(d.escapeTimer>0){d.escapeTimer=Math.max(0,d.escapeTimer-dt);tx=d.escapeX;ty=d.escapeY;}else{float moved=dist(d.x,d.y,d.lastAiX,d.lastAiY),act=len(d.vx,d.vy);if(ol>25*s&&act<38*s&&moved<1.1f*s)d.stuckTimer+=dt;else d.stuckTimer=Math.max(0,d.stuckTimer-dt*2.2f);if(d.stuckTimer>.30f){float l=Math.max(1,ol),nx=odx/l,ny=ody/l,sx=-ny,sy=nx,cent=(pitch.centerX()-d.x)*sx+(pitch.centerY()-d.y)*sy;if(cent<0){sx=-sx;sy=-sy;}d.escapeX=clamp(d.x+sx*58*s+nx*24*s,pitch.left-15*s,pitch.right+15*s);d.escapeY=clamp(d.y+sy*58*s+ny*24*s,pitch.top-24*s,pitch.bottom+24*s);d.escapeTimer=.42f;d.stuckTimer=0;tx=d.escapeX;ty=d.escapeY;}}
            float dx=tx-d.x,dy=ty-d.y,l=len(dx,dy),speed=185*s,wx=0,wy=0;if(l>2*s){wx=dx/l*speed;wy=dy/l*speed;}float k=Math.min(1,dt*(difficulty==0?6f:difficulty==1?7.4f:8.8f));d.vx+=(wx-d.vx)*k;d.vy+=(wy-d.vy)*k;d.lastAiX=d.x;d.lastAiY=d.y;
        }''')

s=rep(s,'updateTeamAI',r'''        void updateTeamAI(Disc[] team,Disc[] opp,int teamId,int chaser,float dt){
            for(int i=0;i<teamSize;i++){Disc d=team[i];if(!d.ai)continue;float tx,ty;if(i==chaser){float[] tar=chooseKickTarget(d,team,opp,teamId);boolean pass=tar[2]>.5f&&tar[2]<1.5f,carry=tar[2]>1.5f;float lead=difficulty==0?.045f:difficulty==1?.095f:.155f,pbx=bx+bvx*lead,pby=by+bvy*lead,dx=tar[0]-pbx,dy=tar[1]-pby,ll=len(dx,dy);if(ll<1)ll=1;float dirX=dx/ll,dirY=dy/ll,behind=discR+ballR+(carry?3*s:6*s);tx=pbx-dirX*behind;ty=pby-dirY*behind;if(by<pitch.top+ballR+10*s||by>pitch.bottom-ballR-10*s){float openY=by<pitch.centerY()?1:-1;ty=by+openY*(discR+ballR+13*s);}float bd=dist(d.x,d.y,bx,by),cdx=bx-d.x,cdy=by-d.y,cl=len(cdx,cdy);if(cl<1)cl=1;float align=(cdx/cl)*dirX+(cdy/cl)*dirY,need=difficulty==0?.84f:difficulty==1?.75f:.66f;if(!carry&&bd<=kickReach()&&align>need&&d.kickCd<=0)cpuKick(d,pass?445*s:515*s,dirX,dirY,pass);}else{float[] pos=formationTarget(teamId,i,chaser);tx=pos[0];ty=pos[1];if(i>0&&i<teamSize-1){float ownThreat=teamId==0?pitch.centerX()-bx:bx-pitch.centerX();if(ownThreat>-.08f*pitch.width()){float sg=teamId==0?1:-1,ix=bx-sg*(92f+18f*i)*s;tx=tx*.58f+ix*.42f;ty=ty*.62f+(by+bvy*.10f)*.38f;}}float db=dist(d.x,d.y,bx,by),min=discR*3.15f;if(db<min){float ax=d.x-bx,ay=d.y-by,al=len(ax,ay);if(al<1)al=1;tx+=ax/al*(min-db+14*s);ty+=ay/al*(min-db+14*s);}}moveAiToward(d,tx,ty,dt);}
        }''')

s=rep(s,'cpuKick',r'''        void cpuKick(Disc d,float power,float desiredX,float desiredY,boolean pass){
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);if(l<1){dx=d.team==0?1:-1;dy=0;l=1;}if(l>kickReach())return;float nx=dx/l,ny=dy/l,need=difficulty==0?.84f:difficulty==1?.75f:.66f,align=nx*desiredX+ny*desiredY;if(align<need)return;float blend=difficulty==0?.10f:difficulty==1?.19f:.28f,ix=nx*(1-blend)+desiredX*blend,iy=ny*(1-blend)+desiredY*blend,il=len(ix,iy);if(il<1)il=1;ix/=il;iy/=il;float eff=(pass?440f:515f)*s;bvx+=ix*eff+d.vx*.08f;bvy+=iy*eff+d.vy*.08f;limitBallSpeed(690*s);d.kickCd=pass?.30f:.22f;if(pass){if(d.team==0)bluePassLock=.52f;else redPassLock=.52f;}spawnKickBurst(ix,iy,eff);playSfx(pass?SFX_PASS:SFX_KICK);
        }''')

s=rep(s,'resolveDiscDisc',r'''        void resolveDiscDisc(Disc a,Disc b){
            float dx=b.x-a.x,dy=b.y-a.y,min=discR*2,d=len(dx,dy);if(d>=min)return;float nx,ny;if(d<.001f){nx=a.index<=b.index?1:-1;ny=0;d=.001f;}else{nx=dx/d;ny=dy/d;}float ov=min-d+.28f*s;a.x-=nx*ov*.5f;a.y-=ny*ov*.5f;b.x+=nx*ov*.5f;b.y+=ny*ov*.5f;float rel=(b.vx-a.vx)*nx+(b.vy-a.vy)*ny;if(rel<0){float imp=-rel*.34f;a.vx-=nx*imp;a.vy-=ny*imp;b.vx+=nx*imp;b.vy+=ny*imp;}if(ov>1.8f*s&&len(a.vx,a.vy)<45*s&&len(b.vx,b.vy)<45*s){float tx=-ny,ty=nx,sg=((a.team*5+a.index)-(b.team*5+b.index))<=0?1:-1,n=13*s;a.vx+=tx*n*sg;a.vy+=ty*n*sg;b.vx-=tx*n*sg;b.vy-=ty*n*sg;}clampDisc(a);clampDisc(b);
        }''')

# celebration
if 'void spawnGoalConfettiV26()' not in s:
    s=s.replace('        void updateGame(float dt){',r'''        void spawnGoalConfettiV26(){confetti.clear();int[] cs={Color.rgb(255,207,54),Color.rgb(55,130,255),Color.rgb(244,67,76),Color.rgb(72,205,112),Color.WHITE,Color.rgb(176,92,230)};for(int i=0;i<96;i++){float x=rng.nextFloat()*w,y=-20*s-rng.nextFloat()*h*.2f,vx=(rng.nextFloat()-.5f)*150*s,vy=(90+rng.nextFloat()*155)*s,life=1.35f+rng.nextFloat()*.65f;confetti.add(new Confetti(x,y,vx,vy,life,rng.nextFloat()*360,(rng.nextFloat()-.5f)*420,(5+rng.nextFloat()*4)*s,(2.5f+rng.nextFloat()*3)*s,cs[rng.nextInt(cs.length)]));}}
        void updateConfettiV26(float dt){for(int i=confetti.size()-1;i>=0;i--){Confetti q=confetti.get(i);q.life-=dt;if(q.life<=0){confetti.remove(i);continue;}q.vy+=235*s*dt;q.x+=q.vx*dt;q.y+=q.vy*dt;q.rot+=q.spin*dt;}}
        void drawGoalCelebrationV26(Canvas c){p.setStyle(Paint.Style.FILL);p.setColor(Color.argb(72,0,0,0));c.drawRect(0,0,w,h,p);for(Confetti q:confetti){float a=clamp(q.life/q.maxLife,0,1);int al=(int)(255*Math.min(1,a*1.8f));p.setColor((q.color&0x00FFFFFF)|(al<<24));c.save();c.rotate(q.rot,q.x,q.y);c.drawRect(q.x-q.ww*.5f,q.y-q.hh*.5f,q.x+q.ww*.5f,q.y+q.hh*.5f,p);c.restore();}float cw=430*s,ch=132*s,cx=w/2f,cy=h*.43f;p.setColor(Color.argb(220,8,11,16));c.drawRoundRect(new RectF(cx-cw/2,cy-ch/2,cx+cw/2,cy+ch/2),20*s,20*s,p);p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(18*s);p.setColor(Color.rgb(245,205,64));c.drawText("GOAL!",cx,cy-31*s,p);p.setTextSize(14*s);p.setColor(Color.rgb(91,151,255));c.drawText("BLUE",cx-118*s,cy+2*s,p);p.setColor(Color.rgb(255,99,102));c.drawText("RED",cx+118*s,cy+2*s,p);p.setTextSize(34*s);p.setColor(Color.WHITE);c.drawText(blueScore+"   -   "+redScore,cx,cy+19*s,p);p.setTextSize(11*s);p.setColor(Color.rgb(150,165,185));c.drawText(lastGoalBlue?"BLUE TEAM SCORED":"RED TEAM SCORED",cx,cy+47*s,p);}

        void updateGame(float dt){''',1)

s=rep(s,'updateGame',r'''        void updateGame(float dt){
            bluePassLock=Math.max(0,bluePassLock-dt);redPassLock=Math.max(0,redPassLock-dt);if(goalPauseTimer>0){goalPauseTimer=Math.max(0,goalPauseTimer-dt);updateConfettiV26(dt);crowdExcitement=1;syncRealAudio();if(goalPauseTimer<=0){confetti.clear();if(pendingFinishAfterGoal){pendingFinishAfterGoal=false;finishMatch();return;}resetPositions();}return;}
            if(!goldenGoal){matchTime-=dt;if(matchTime<=0){matchTime=0;if(blueScore==redScore)goldenGoal=true;else{finishMatch();return;}}}if(mode!=GAME)return;for(int i=0;i<teamSize;i++){blue[i].kickCd=Math.max(0,blue[i].kickCd-dt);red[i].kickCd=Math.max(0,red[i].kickCd-dt);blue[i].wallPlayTime=Math.max(0,blue[i].wallPlayTime-dt);red[i].wallPlayTime=Math.max(0,red[i].wallPlayTime-dt);}wallSoundCooldown=Math.max(0,wallSoundCooldown-dt);touchSoundCooldown=Math.max(0,touchSoundCooldown-dt);updateHuman(dt);chooseChasers();updateTeamAI(blue,red,0,blueChaser,dt);updateTeamAI(red,blue,1,redChaser,dt);int steps=Math.max(3,Math.min(14,(int)Math.ceil(dt/.0034f)));float sub=dt/steps;for(int st=0;st<steps;st++){physicsStep(sub);if(goalPauseTimer>0)break;}updateParticles(dt);float dl=Math.abs(bx-pitch.left),dr=Math.abs(pitch.right-bx),near=Math.min(dl,dr)/Math.max(1,pitch.width()),th=clamp((.31f-near)/.31f,0,1),tow=(dl<dr)?Math.max(0,-bvx):Math.max(0,bvx),app=clamp(tow/(520*s),0,1),sb=clamp(len(bvx,bvy)/(690*s),0,1)*.16f;crowdExcitement=clamp(th*(.42f+.58f*app)+sb,0,1);syncRealAudio();
        }''')

s=rep(s,'scoreGoal',r'''        void scoreGoal(boolean blueGoal){if(mode!=GAME||goalPauseTimer>0)return;if(blueGoal)blueScore++;else redScore++;lastGoalBlue=blueGoal;playSfx(SFX_GOAL);haptic(70);pendingFinishAfterGoal=blueScore>=targetGoals||redScore>=targetGoals||goldenGoal;goalPauseTimer=1.70f;spawnGoalConfettiV26();bvx=bvy=0;for(int i=0;i<teamSize;i++){blue[i].vx=blue[i].vy=0;red[i].vx=red[i].vy=0;}}
''')

s=rep(s,'startMatch',r'''        void startMatch(){blueScore=redScore=0;matchTime=180f;goldenGoal=false;savedResult=false;goalPauseTimer=0;pendingFinishAfterGoal=false;confetti.clear();bluePassLock=redPassLock=0;mode=GAME;lastFrame=System.nanoTime();joyPointer=-1;joyNX=joyNY=0;joyX=joyBaseX;joyY=joyBaseY;prefs.edit().putInt("difficulty",difficulty).putInt("team_size",teamSize).putInt("target_goals",targetGoals).putInt("field_theme",fieldTheme).apply();resetPositions();playSfx(SFX_MENU);}
''')

s=rep(s,'drawGame',r'''        void drawGame(Canvas c){
            int out,p1,p2,line;if(fieldTheme==1){out=Color.rgb(39,118,43);p1=Color.rgb(54,156,56);p2=Color.rgb(48,145,51);line=Color.rgb(244,247,242);}else if(fieldTheme==2){out=Color.rgb(18,36,55);p1=Color.rgb(31,57,84);p2=Color.rgb(27,50,76);line=Color.rgb(215,232,246);}else if(fieldTheme==3){out=Color.rgb(42,122,47);p1=Color.rgb(60,153,64);p2=Color.rgb(51,139,57);line=Color.rgb(244,247,242);}else{out=Color.rgb(52,56,60);p1=Color.rgb(68,73,78);p2=Color.rgb(61,66,71);line=Color.WHITE;}c.drawColor(out);p.setStyle(Paint.Style.FILL);p.setColor(p1);c.drawRect(pitch,p);int bands=fieldTheme==3?12:10;for(int i=0;i<bands;i++){p.setColor(i%2==0?p1:p2);float xx=pitch.left+pitch.width()*i/bands;c.drawRect(xx,pitch.top,xx+pitch.width()/bands,pitch.bottom,p);}stroke.setStyle(Paint.Style.STROKE);stroke.setColor(line);stroke.setStrokeWidth(2.7f*s);c.drawRect(pitch,stroke);c.drawLine(pitch.centerX(),pitch.top,pitch.centerX(),pitch.bottom,stroke);c.drawCircle(pitch.centerX(),pitch.centerY(),72*s,stroke);c.drawCircle(pitch.centerX(),pitch.centerY(),3.5f*s,stroke);float ar=Math.min(pitch.height()*.32f,pitch.width()*.18f);c.drawArc(new RectF(pitch.left-ar,pitch.centerY()-ar,pitch.left+ar,pitch.centerY()+ar),-90,180,false,stroke);c.drawArc(new RectF(pitch.right-ar,pitch.centerY()-ar,pitch.right+ar,pitch.centerY()+ar),90,180,false,stroke);drawGoals(c);drawPredictionGuideV24(c);drawParticles(c);for(int i=0;i<teamSize;i++)drawDisc(c,blue[i]);for(int i=0;i<teamSize;i++)drawDisc(c,red[i]);drawFootball(c,bx,by,ballR,ballAngle);drawScoreHud(c);if(goalPauseTimer>0)drawGoalCelebrationV26(c);else{drawJoystick(c,false);drawKick(c,false);}
        }''')

s=s.replace('        @Override public boolean onTouchEvent(MotionEvent e){\n','        @Override public boolean onTouchEvent(MotionEvent e){\n            if(SystemClock.uptimeMillis()<splashUntil)return true;\n            if(mode==GAME&&goalPauseTimer>0f)return true;\n',1)
s=s.replace('circle_football_v25','circle_football_v26')
path.write_text(s,encoding='utf-8')

m=Path('AndroidManifest.xml');x=m.read_text(encoding='utf-8');x=x.replace('com.godnit.circlefootballlite.v25','com.godnit.circlefootballlite.v26');x=re.sub(r'android:versionCode="\d+"','android:versionCode="17"',x,count=1);x=re.sub(r'android:versionName="[^"]+"','android:versionName="2.6.0"',x,count=1);m.write_text(x,encoding='utf-8')
print('Applied v2.6 tactical AI, goal celebration, preview UI, splash and goal-frame fixes')
