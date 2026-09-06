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

# New match flow state: visible startup splash, kick-off countdown and chaser hysteresis.
s=s.replace('        float goalPauseTimer=0f,bluePassLock=0f,redPassLock=0f;\n',
            '        float goalPauseTimer=0f,bluePassLock=0f,redPassLock=0f,countdownTimer=0f,blueChaserHold=0f,redChaserHold=0f;\n',1)
s=s.replace('        long splashUntil=SystemClock.uptimeMillis()+1150L;\n',
            '        long splashUntil=SystemClock.uptimeMillis()+2600L;\n',1)

# Compact two-column setup: gameplay options left, stadium selector + live preview right.
s=rep(s,'drawSetup',r'''        void drawSetup(Canvas c){
            background(c);title(c,"PLAY MATCH",48*s,28f);
            float cardTop=76*s,cardBottom=h-104*s,left=w*.10f,right=w*.90f,mid=w*.50f;
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(30,35,44));
            c.drawRoundRect(new RectF(left,cardTop,mid-10*s,cardBottom),18*s,18*s,p);
            c.drawRoundRect(new RectF(mid+10*s,cardTop,right,cardBottom),18*s,18*s,p);

            String[] ds={"EASY","NORMAL","HARD"};
            subtitle(c,"DIFFICULTY",108*s,11,Color.rgb(143,159,180));
            float bw=116*s,g=8*s,tot=bw*3+g*2,st=(left+mid-tot)/2f;
            for(int i=0;i<3;i++)menuButton(c,ds[i],"diff"+i,st+i*(bw+g),120*s,bw,38*s,i==difficulty?Color.rgb(29,121,255):Color.rgb(52,59,72));

            subtitle(c,"PLAYERS",186*s,11,Color.rgb(143,159,180));
            float pw=82*s,pg=7*s,pt=pw*4+pg*3,ps=(left+mid-pt)/2f;
            for(int i=1;i<=4;i++)menuButton(c,i+"v"+i,"team"+i,ps+(i-1)*(pw+pg),198*s,pw,38*s,i==teamSize?Color.rgb(34,174,91):Color.rgb(52,59,72));

            subtitle(c,"GOALS",266*s,11,Color.rgb(143,159,180));
            int[] gs={3,5,7};
            for(int i=0;i<3;i++)menuButton(c,""+gs[i],"goal"+gs[i],st+i*(bw+g),278*s,bw,38*s,gs[i]==targetGoals?Color.rgb(238,157,32):Color.rgb(52,59,72));

            subtitle(c,"STADIUM",108*s,11,Color.rgb(143,159,180));
            String[] names={"CLASSIC","GRASS","NIGHT","WIDE"};
            float fw=92*s,fg=7*s,ft=fw*4+fg*3,fstart=(mid+right-ft)/2f;
            for(int i=0;i<4;i++)menuButton(c,names[i],"field"+i,fstart+i*(fw+fg),120*s,fw,38*s,i==fieldTheme?Color.rgb(102,82,205):Color.rgb(52,59,72));
            drawStadiumPreviewV26(c,new RectF(mid+34*s,184*s,right-34*s,cardBottom-30*s));

            menuButton(c,"START MATCH","start",w/2f-205*s,h-88*s,410*s,50*s,Color.rgb(29,121,255));
            menuButton(c,"BACK","home",w/2f-92*s,h-34*s,184*s,30*s,Color.rgb(48,56,70));
        }''')

# A clearer countdown overlay used for the first kick-off and after every goal.
if 'void drawCountdownV27(Canvas c)' not in s:
    s=s.replace('        void drawGoalCelebrationV26(Canvas c){',r'''        void drawCountdownV27(Canvas c){
            if(countdownTimer<=0)return;
            float n=countdownTimer;
            String txt=n>3f?"3":n>2f?"2":n>1f?"1":"GO!";
            float pulse=.88f+.12f*(float)Math.sin((3.4f-n)*8f);
            p.setStyle(Paint.Style.FILL);p.setColor(Color.argb(78,0,0,0));c.drawCircle(w*.5f,h*.46f,62*s,p);
            p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize((txt.equals("GO!")?42f:58f)*s*pulse);p.setColor(Color.WHITE);c.drawText(txt,w*.5f,h*.46f+19*s,p);
        }

        void drawGoalCelebrationV26(Canvas c){''',1)

# Longer celebration, but do not freeze the controlled player or the ball.
s=rep(s,'scoreGoal',r'''        void scoreGoal(boolean blueGoal){
            if(mode!=GAME||goalPauseTimer>0)return;
            if(blueGoal)blueScore++;else redScore++;
            lastGoalBlue=blueGoal;playSfx(SFX_GOAL);haptic(70);
            pendingFinishAfterGoal=blueScore>=targetGoals||redScore>=targetGoals||goldenGoal;
            goalPauseTimer=pendingFinishAfterGoal?3.4f:2.8f;
            spawnGoalConfettiV26();
        }''')

s=rep(s,'startMatch',r'''        void startMatch(){
            blueScore=redScore=0;matchTime=180f;goldenGoal=false;savedResult=false;goalPauseTimer=0;pendingFinishAfterGoal=false;confetti.clear();bluePassLock=redPassLock=0;blueChaserHold=redChaserHold=0;countdownTimer=3.4f;
            mode=GAME;lastFrame=System.nanoTime();joyPointer=-1;joyNX=joyNY=0;joyX=joyBaseX;joyY=joyBaseY;
            prefs.edit().putInt("difficulty",difficulty).putInt("team_size",teamSize).putInt("target_goals",targetGoals).putInt("field_theme",fieldTheme).apply();
            resetPositions();playSfx(SFX_MENU);
        }''')

# One stable chaser per team with hysteresis: striker presses high, one defender presses in midfield,
# keeper only commits inside the danger area. This avoids the attack/stop/attack oscillation.
s=rep(s,'chooseChasers',r'''        void chooseChasers(){
            float px=bx+bvx*(difficulty==2?.16f:.10f),py=by+bvy*(difficulty==2?.16f:.10f),cw=pitch.width(),cx=pitch.centerX();
            blueChaserHold=Math.max(0,blueChaserHold-.016f);redChaserHold=Math.max(0,redChaserHold-.016f);

            int wantBlue=-1;
            if(teamSize>=2){
                if(px<pitch.left+cw*.15f)wantBlue=teamSize-1;
                else if(px<cx+cw*.04f){
                    if(teamSize>=3)wantBlue=closestDefenderV26(blue,1,teamSize-1,px,py);
                    else wantBlue=teamSize-1;
                }
            }
            int wantRed=0;
            if(teamSize>=2){
                if(px>pitch.right-cw*.15f)wantRed=teamSize-1;
                else if(px>cx-cw*.04f){
                    if(teamSize>=3)wantRed=closestDefenderV26(red,1,teamSize-1,px,py);
                    else wantRed=teamSize-1;
                }else wantRed=0;
            }

            if(wantBlue!=blueChaser){
                boolean urgent=px<pitch.left+cw*.12f;
                if(urgent||blueChaserHold<=0){blueChaser=wantBlue;blueChaserHold=.46f;}
            }else blueChaserHold=Math.max(blueChaserHold,.16f);
            if(wantRed!=redChaser){
                boolean urgent=px>pitch.right-cw*.12f;
                if(urgent||redChaserHold<=0){redChaser=wantRed;redChaserHold=.46f;}
            }else redChaserHold=Math.max(redChaserHold,.16f);
        }''')

# More useful support positions. Non-chasers move continuously into passing/marking lanes rather
# than parking at fixed coordinates, while only one player actively attacks the ball.
s=rep(s,'formationTarget',r'''        float[] formationTarget(int teamId,int idx,int chaser){
            float sg=teamId==0?1f:-1f,own=teamId==0?pitch.left:pitch.right;
            float px=bx+bvx*(difficulty==2?.18f:.11f),py=by+bvy*(difficulty==2?.18f:.11f);
            float cw=pitch.width(),ch=pitch.height();
            if(idx==0){
                float ahead=teamId==0?clamp(px+cw*.16f,pitch.centerX()-cw*.02f,pitch.right-cw*.10f):clamp(px-cw*.16f,pitch.left+cw*.10f,pitch.centerX()+cw*.02f);
                float lane=clamp(py+(py<pitch.centerY()?ch*.10f:-ch*.10f),pitch.top+discR*1.5f,pitch.bottom-discR*1.5f);
                return new float[]{ahead,lane};
            }
            if(idx==teamSize-1&&teamSize>=2){
                float kx=own+sg*cw*.055f,ky=clamp(py,pitch.centerY()-goalHalf*.72f,pitch.centerY()+goalHalf*.72f);
                return new float[]{kx,ky};
            }
            int slot=idx-1;
            Disc m=markV26(teamId==0?red:blue,teamId,slot);
            float lineX=own+sg*cw*(.21f+.045f*slot);
            float interceptX=px-sg*(88f+18f*slot)*s;
            float danger=teamId==0?clamp((pitch.centerX()+cw*.12f-px)/(cw*.55f),0,1):clamp((px-(pitch.centerX()-cw*.12f))/(cw*.55f),0,1);
            float lo=teamId==0?pitch.left+cw*.13f:pitch.centerX()-cw*.05f,hi=teamId==0?pitch.centerX()+cw*.05f:pitch.right-cw*.13f;
            float x=clamp(lineX*(1-danger)+interceptX*danger,lo,hi);
            float zoneY=pitch.top+ch*(slot+1f)/(Math.max(1,teamSize-2)+1f);
            float markY=m==null?zoneY:m.y;
            float y=clamp(zoneY*.32f+markY*.46f+py*.22f,pitch.top+discR*1.5f,pitch.bottom-discR*1.5f);
            return new float[]{x,y};
        }''')

# Escape-pass target: when surrounded, passing can be sideways/backwards if that teammate is clearly open.
if 'int escapePassV27(' not in s:
    s=s.replace('        int bestPassTarget(',r'''        int escapePassV27(Disc d,Disc[] team,Disc[] opp,int teamId){
            int best=-1;float bs=-999999f;
            for(int i=0;i<teamSize;i++){
                Disc m=team[i];if(m==d)continue;
                float pd=dist(d.x,d.y,m.x,m.y);if(pd<58*s||pd>pitch.width()*.62f)continue;
                if(isLaneBlocked(opp,bx,by,m.x,m.y,discR*1.12f))continue;
                float open=nearestOpponentDistance(opp,m.x,m.y);
                float forward=teamId==0?m.x-d.x:d.x-m.x;
                float score=open*.82f+Math.max(-40*s,forward)*.20f-pd*.06f;
                if(i==teamSize-1&&teamSize>=2)score-=42*s;
                if(score>bs){bs=score;best=i;}
            }
            return best;
        }

        int bestPassTarget(''',1)

s=rep(s,'chooseKickTarget',r'''        float[] chooseKickTarget(Disc d,Disc[] team,Disc[] opp,int teamId){
            float sg=teamId==0?1f:-1f,gx=teamId==0?pitch.right+18*s:pitch.left-18*s,gy=bestGoalLaneV25(opp,teamId),gd=Math.abs(gx-bx);
            float clear=shotClearV26(opp,teamId); /* placeholder replaced below */
            return new float[]{gx,gy,0,0,0,0};
        }''')
# Repair overload call and replace the temporary body with the full decision tree.
s=s.replace('            float clear=shotClearV26(opp,teamId); /* placeholder replaced below */\n            return new float[]{gx,gy,0,0,0,0};',r'''            float clear=shotClearV26(opp,teamId,gy);
            boolean finalZ=gd<pitch.width()*(difficulty==0?.30f:(difficulty==1?.40f:.48f));
            boolean clearShot=clear>discR*(difficulty==2?1.02f:(difficulty==1?1.20f:1.42f));
            int pressure=countOpponentsNear(opp,d.x,d.y,(difficulty==2?118f:(difficulty==1?108f:98f))*s);
            int passTo=bestPassTarget(d,team,opp,teamId);
            int escape=escapePassV27(d,team,opp,teamId);
            boolean keeper=d.index==teamSize-1&&teamSize>=2,def=d.index>0&&!keeper;

            if(finalZ&&clearShot)return new float[]{gx,gy,0,0,0,0};
            if(pressure>=2&&escape>=0){Disc m=team[escape];return new float[]{m.x+m.vx*.15f,m.y+m.vy*.15f,1,0,0,0};}
            if((keeper||def)&&pressure>=1&&escape>=0){Disc m=team[escape];return new float[]{m.x+m.vx*.15f,m.y+m.vy*.15f,1,0,0,0};}
            if(finalZ){
                if(!clearShot&&passTo>=0&&pressure>0){Disc m=team[passTo];return new float[]{m.x+m.vx*.14f,m.y+m.vy*.14f,1,0,0,0};}
                return new float[]{gx,gy,0,0,0,0};
            }
            if(passTo>=0&&pressure>0){Disc m=team[passTo];return new float[]{m.x+m.vx*.13f,m.y+m.vy*.13f,1,0,0,0};}
            return new float[]{bx+sg*(185f+28f*difficulty)*s,gy*.32f+by*.68f,2,0,0,0};''',1)

# Continuous steering + stronger anti-stuck escape. No complete stop unless actually at a valid role target.
s=rep(s,'moveAiToward',r'''        void moveAiToward(Disc d,float tx,float ty,float dt){
            float odx=tx-d.x,ody=ty-d.y,ol=len(odx,ody);
            if(d.escapeTimer>0){d.escapeTimer=Math.max(0,d.escapeTimer-dt);tx=d.escapeX;ty=d.escapeY;}
            else{
                float moved=dist(d.x,d.y,d.lastAiX,d.lastAiY),act=len(d.vx,d.vy);
                if(ol>20*s&&act<48*s&&moved<1.25f*s)d.stuckTimer+=dt;else d.stuckTimer=Math.max(0,d.stuckTimer-dt*2.5f);
                if(d.stuckTimer>.22f){
                    float l=Math.max(1,ol),nx=odx/l,ny=ody/l,sx=-ny,sy=nx;
                    float c1=(pitch.centerX()-d.x)*sx+(pitch.centerY()-d.y)*sy;if(c1<0){sx=-sx;sy=-sy;}
                    d.escapeX=clamp(d.x+sx*68*s+nx*34*s,pitch.left-18*s,pitch.right+18*s);
                    d.escapeY=clamp(d.y+sy*68*s+ny*34*s,pitch.top-28*s,pitch.bottom+28*s);
                    d.escapeTimer=.48f;d.stuckTimer=0;tx=d.escapeX;ty=d.escapeY;
                }
            }
            float dx=tx-d.x,dy=ty-d.y,l=len(dx,dy),speed=185*s,wx=0,wy=0;
            if(l>5*s){wx=dx/l*speed;wy=dy/l*speed;}
            else if(l>1.5f*s){wx=dx/l*speed*.42f;wy=dy/l*speed*.42f;}
            float k=Math.min(1,dt*(difficulty==0?6.4f:difficulty==1?7.8f:9.2f));
            d.vx+=(wx-d.vx)*k;d.vy+=(wy-d.vy)*k;d.lastAiX=d.x;d.lastAiY=d.y;
        }''')

# Team AI: one ball chaser only. Others maintain active support/defensive lanes and do not crowd the ball.
s=rep(s,'updateTeamAI',r'''        void updateTeamAI(Disc[] team,Disc[] opp,int teamId,int chaser,float dt){
            for(int i=0;i<teamSize;i++){
                Disc d=team[i];if(!d.ai)continue;float tx,ty;
                if(i==chaser){
                    float[] tar=chooseKickTarget(d,team,opp,teamId);boolean pass=tar[2]>.5f&&tar[2]<1.5f,carry=tar[2]>1.5f;
                    float lead=difficulty==0?.05f:difficulty==1?.10f:.16f,pbx=bx+bvx*lead,pby=by+bvy*lead;
                    float dx=tar[0]-pbx,dy=tar[1]-pby,ll=len(dx,dy);if(ll<1)ll=1;float dirX=dx/ll,dirY=dy/ll;
                    float behind=discR+ballR+(carry?3*s:6*s);tx=pbx-dirX*behind;ty=pby-dirY*behind;
                    if(by<pitch.top+ballR+12*s||by>pitch.bottom-ballR-12*s){float open=by<pitch.centerY()?1:-1;ty=by+open*(discR+ballR+15*s);}
                    float bd=dist(d.x,d.y,bx,by),cdx=bx-d.x,cdy=by-d.y,cl=len(cdx,cdy);if(cl<1)cl=1;
                    float align=(cdx/cl)*dirX+(cdy/cl)*dirY,need=difficulty==0?.84f:difficulty==1?.74f:.64f;
                    if(!carry&&bd<=kickReach()&&align>need&&d.kickCd<=0)cpuKick(d,pass?445*s:515*s,dirX,dirY,pass);
                }else{
                    float[] pos=formationTarget(teamId,i,chaser);tx=pos[0];ty=pos[1];
                    float db=dist(d.x,d.y,bx,by),min=(i==teamSize-1?discR*3.8f:discR*3.35f);
                    if(db<min){float ax=d.x-bx,ay=d.y-by,al=len(ax,ay);if(al<1)al=1;tx+=ax/al*(min-db+18*s);ty+=ay/al*(min-db+18*s);}
                }
                moveAiToward(d,tx,ty,dt);
            }
        }''')

# Match update: countdown freezes the kick-off; goal celebration keeps human control and ball physics alive,
# then resets and starts another countdown. Final-goal celebration stays longer before result screen.
s=rep(s,'updateGame',r'''        void updateGame(float dt){
            bluePassLock=Math.max(0,bluePassLock-dt);redPassLock=Math.max(0,redPassLock-dt);

            if(countdownTimer>0){
                countdownTimer=Math.max(0,countdownTimer-dt);crowdExcitement=.18f;syncRealAudio();
                for(int i=0;i<teamSize;i++){blue[i].vx*=.78f;blue[i].vy*=.78f;red[i].vx*=.78f;red[i].vy*=.78f;}
                bvx*=.78f;bvy*=.78f;return;
            }

            if(goalPauseTimer>0){
                goalPauseTimer=Math.max(0,goalPauseTimer-dt);updateConfettiV26(dt);
                for(int i=0;i<teamSize;i++){blue[i].kickCd=Math.max(0,blue[i].kickCd-dt);red[i].kickCd=Math.max(0,red[i].kickCd-dt);}
                updateHuman(dt);
                int steps=Math.max(3,Math.min(12,(int)Math.ceil(dt/.0036f)));float sub=dt/steps;
                for(int st=0;st<steps;st++)physicsStep(sub);
                updateParticles(dt);crowdExcitement=1;syncRealAudio();
                if(goalPauseTimer<=0){
                    confetti.clear();
                    if(pendingFinishAfterGoal){pendingFinishAfterGoal=false;finishMatch();return;}
                    resetPositions();countdownTimer=3.4f;joyPointer=-1;joyNX=joyNY=0;joyX=joyBaseX;joyY=joyBaseY;
                }
                return;
            }

            if(!goldenGoal){matchTime-=dt;if(matchTime<=0){matchTime=0;if(blueScore==redScore)goldenGoal=true;else{finishMatch();return;}}}
            if(mode!=GAME)return;
            for(int i=0;i<teamSize;i++){
                blue[i].kickCd=Math.max(0,blue[i].kickCd-dt);red[i].kickCd=Math.max(0,red[i].kickCd-dt);
                blue[i].wallPlayTime=Math.max(0,blue[i].wallPlayTime-dt);red[i].wallPlayTime=Math.max(0,red[i].wallPlayTime-dt);
            }
            wallSoundCooldown=Math.max(0,wallSoundCooldown-dt);touchSoundCooldown=Math.max(0,touchSoundCooldown-dt);
            updateHuman(dt);chooseChasers();updateTeamAI(blue,red,0,blueChaser,dt);updateTeamAI(red,blue,1,redChaser,dt);
            int steps=Math.max(3,Math.min(14,(int)Math.ceil(dt/.0034f)));float sub=dt/steps;
            for(int st=0;st<steps;st++){physicsStep(sub);if(goalPauseTimer>0)break;}
            updateParticles(dt);
            float dl=Math.abs(bx-pitch.left),dr=Math.abs(pitch.right-bx),near=Math.min(dl,dr)/Math.max(1,pitch.width()),th=clamp((.31f-near)/.31f,0,1),tow=(dl<dr)?Math.max(0,-bvx):Math.max(0,bvx),app=clamp(tow/(520*s),0,1),sb=clamp(len(bvx,bvy)/(690*s),0,1)*.16f;
            crowdExcitement=clamp(th*(.42f+.58f*app)+sb,0,1);syncRealAudio();
        }''')

# World rendering with a short camera zoom that follows the ball after a goal. HUD and controls stay fixed.
s=rep(s,'drawGame',r'''        void drawGame(Canvas c){
            int out,p1,p2,line;if(fieldTheme==1){out=Color.rgb(39,118,43);p1=Color.rgb(54,156,56);p2=Color.rgb(48,145,51);line=Color.rgb(244,247,242);}else if(fieldTheme==2){out=Color.rgb(18,36,55);p1=Color.rgb(31,57,84);p2=Color.rgb(27,50,76);line=Color.rgb(215,232,246);}else if(fieldTheme==3){out=Color.rgb(42,122,47);p1=Color.rgb(60,153,64);p2=Color.rgb(51,139,57);line=Color.rgb(244,247,242);}else{out=Color.rgb(52,56,60);p1=Color.rgb(68,73,78);p2=Color.rgb(61,66,71);line=Color.WHITE;}
            c.drawColor(out);
            boolean cam=goalPauseTimer>0;float zoom=1f;
            if(cam){float phase=1f-clamp(goalPauseTimer/(pendingFinishAfterGoal?3.4f:2.8f),0,1);zoom=1f+.16f*(float)Math.sin(Math.min(1f,phase*1.5f)*1.5708f);c.save();c.translate(w*.5f,h*.48f);c.scale(zoom,zoom);c.translate(-bx,-by);}

            p.setStyle(Paint.Style.FILL);p.setColor(p1);c.drawRect(pitch,p);int bands=fieldTheme==3?12:10;for(int i=0;i<bands;i++){p.setColor(i%2==0?p1:p2);float xx=pitch.left+pitch.width()*i/bands;c.drawRect(xx,pitch.top,xx+pitch.width()/bands,pitch.bottom,p);}stroke.setStyle(Paint.Style.STROKE);stroke.setColor(line);stroke.setStrokeWidth(2.7f*s);c.drawRect(pitch,stroke);c.drawLine(pitch.centerX(),pitch.top,pitch.centerX(),pitch.bottom,stroke);c.drawCircle(pitch.centerX(),pitch.centerY(),72*s,stroke);c.drawCircle(pitch.centerX(),pitch.centerY(),3.5f*s,stroke);float ar=Math.min(pitch.height()*.32f,pitch.width()*.18f);c.drawArc(new RectF(pitch.left-ar,pitch.centerY()-ar,pitch.left+ar,pitch.centerY()+ar),-90,180,false,stroke);c.drawArc(new RectF(pitch.right-ar,pitch.centerY()-ar,pitch.right+ar,pitch.centerY()+ar),90,180,false,stroke);drawGoals(c);drawPredictionGuideV24(c);drawParticles(c);for(int i=0;i<teamSize;i++)drawDisc(c,blue[i]);for(int i=0;i<teamSize;i++)drawDisc(c,red[i]);drawFootball(c,bx,by,ballR,ballAngle);
            if(cam)c.restore();
            drawScoreHud(c);drawJoystick(c,false);drawKick(c,false);
            if(goalPauseTimer>0)drawGoalCelebrationV26(c);
            if(countdownTimer>0)drawCountdownV27(c);
        }''')

# Make the celebration panel a little less dominant so the zoomed play remains visible.
s=s.replace('float cw=430*s,ch=132*s,cx=w/2f,cy=h*.43f;', 'float cw=390*s,ch=116*s,cx=w/2f,cy=h*.31f;',1)
s=s.replace('p.setColor(Color.argb(72,0,0,0));', 'p.setColor(Color.argb(48,0,0,0));',1)

# The v2.6 touch blocker froze controls after goals; remove it for v2.7.
s=s.replace('            if(mode==GAME&&goalPauseTimer>0f)return true;\n','',1)

s=s.replace('circle_football_v26','circle_football_v27')
path.write_text(s,encoding='utf-8')

m=Path('AndroidManifest.xml');x=m.read_text(encoding='utf-8');x=x.replace('com.godnit.circlefootballlite.v26','com.godnit.circlefootballlite.v27');x=re.sub(r'android:versionCode="\d+"','android:versionCode="18"',x,count=1);x=re.sub(r'android:versionName="[^"]+"','android:versionName="2.7.0"',x,count=1);m.write_text(x,encoding='utf-8')
print('Applied v2.7 stable team AI, escape passing, countdown, live goal camera and compact setup')
