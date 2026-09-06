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

s=s.replace('        float camX=0f,camY=0f,camZoom=1f;\n',
'''        float camX=0f,camY=0f,camZoom=1f;\n        Disc ballHolderV29=null;\n        float holderAngleV29=0f,holderReleaseV29=0f;\n        boolean goalLatchedV29=false;\n''',1)
s=s.replace('fieldTheme=clampInt(prefs.getInt("field_theme",0),0,3);',
            'fieldTheme=clampInt(prefs.getInt("field_theme",0),0,4);')
s=s.replace('fieldTheme=clampInt(Integer.parseInt(id.substring(5)),0,3);',
            'fieldTheme=clampInt(Integer.parseInt(id.substring(5)),0,4);')

s=rep(s,'configureField',r'''        void configureField(){
            float mxRatio,myRatio;
            if(fieldTheme==4){mxRatio=.040f;myRatio=.070f;}
            else if(fieldTheme==3){mxRatio=.052f;myRatio=.078f;}
            else if(fieldTheme==2){mxRatio=.064f;myRatio=.104f;}
            else{mxRatio=teamSize>=3?.058f:.073f;myRatio=teamSize>=3?.098f:.116f;}
            float mx=Math.max(w*mxRatio,48f*s),my=h*myRatio;
            pitch.set(mx,my,w-mx,h-my);
            goalHalf=pitch.height()*(fieldTheme==4?.195f:.215f);
            if(fieldTheme==4){
                float ts=teamSize>=4?.88f:(teamSize==3?.94f:1f);
                discR=18.4f*s*ts;
                ballR=6.6f*s*(teamSize>=4?.91f:(teamSize==3?.95f:1f));
            }else{
                float ts=teamSize>=4?.83f:(teamSize==3?.90f:1f),fs=fieldTheme==3?.92f:(fieldTheme==2?.96f:1f);
                discR=20.2f*s*ts*fs;
                float bt=teamSize>=4?.86f:(teamSize==3?.92f:1f),bf=fieldTheme==3?.90f:(fieldTheme==2?.95f:1f);
                ballR=8.8f*s*bt*bf;
            }
        }''')

if 'void selectorRowV29(' not in s:
    s=s.replace('        void drawSetup(Canvas c){',r'''        String fieldNameV29(){return fieldTheme==0?"CLASSIC":fieldTheme==1?"GRASS":fieldTheme==2?"NIGHT":fieldTheme==3?"WIDE":"VIDEO";}
        String difficultyNameV29(){return difficulty==0?"EASY":difficulty==1?"NORMAL":"HARD";}
        void selectorRowV29(Canvas c,String label,String value,float x,float y,float ww,String leftId,String rightId,int accent){
            float hh=48*s,arrow=52*s;
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(36,42,52));c.drawRoundRect(new RectF(x,y,x+ww,y+hh),13*s,13*s,p);
            p.setTextAlign(Paint.Align.LEFT);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(13*s);p.setColor(Color.rgb(150,166,188));c.drawText(label,x+18*s,y+30*s,p);
            p.setTextAlign(Paint.Align.CENTER);p.setTextSize(17*s);p.setColor(Color.WHITE);c.drawText(value,x+ww*.69f,y+31*s,p);
            p.setTextSize(26*s);p.setColor(Color.rgb(190,202,218));c.drawText("‹",x+ww-arrow*1.55f,y+33*s,p);c.drawText("›",x+ww-arrow*.52f,y+33*s,p);
            hits.add(new ButtonHit(leftId,new RectF(x+ww-arrow*2.05f,y,x+ww-arrow*1.05f,y+hh)));
            hits.add(new ButtonHit(rightId,new RectF(x+ww-arrow*1.02f,y,x+ww,y+hh)));
            p.setColor(accent);c.drawRoundRect(new RectF(x+ww*.52f,y+hh-3*s,x+ww*.86f,y+hh),2*s,2*s,p);
        }
        void drawFieldPreviewV29(Canvas c,RectF r){
            int out,p1,p2,line;
            if(fieldTheme==1){out=Color.rgb(34,96,38);p1=Color.rgb(54,156,56);p2=Color.rgb(47,143,50);line=Color.WHITE;}
            else if(fieldTheme==2){out=Color.rgb(11,23,38);p1=Color.rgb(31,57,84);p2=Color.rgb(26,48,73);line=Color.rgb(213,231,245);}
            else if(fieldTheme==3){out=Color.rgb(36,103,41);p1=Color.rgb(60,153,64);p2=Color.rgb(51,139,57);line=Color.WHITE;}
            else if(fieldTheme==4){out=Color.rgb(42,42,43);p1=Color.rgb(76,76,77);p2=Color.rgb(71,71,72);line=Color.WHITE;}
            else{out=Color.rgb(43,47,52);p1=Color.rgb(68,73,78);p2=Color.rgb(61,66,71);line=Color.WHITE;}
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(30,35,43));c.drawRoundRect(r,17*s,17*s,p);
            float pad=17*s;RectF f=new RectF(r.left+pad,r.top+pad+16*s,r.right-pad,r.bottom-pad);
            p.setColor(out);c.drawRoundRect(f,10*s,10*s,p);RectF q=new RectF(f.left+9*s,f.top+9*s,f.right-9*s,f.bottom-9*s);p.setColor(p1);c.drawRect(q,p);
            int bands=fieldTheme==4?9:8;for(int i=0;i<bands;i++){p.setColor(i%2==0?p1:p2);float xx=q.left+q.width()*i/bands;c.drawRect(xx,q.top,xx+q.width()/bands,q.bottom,p);}
            if(fieldTheme==4){p.setColor(Color.argb(18,255,255,255));for(int j=1;j<6;j++){float yy=q.top+q.height()*j/6f;c.drawRect(q.left,yy,q.right,yy+1*s,p);}}
            stroke.setStyle(Paint.Style.STROKE);stroke.setStrokeWidth(1.3f*s);stroke.setColor(line);c.drawRect(q,stroke);c.drawLine(q.centerX(),q.top,q.centerX(),q.bottom,stroke);c.drawCircle(q.centerX(),q.centerY(),q.height()*.17f,stroke);
            float ar=q.height()*.32f;c.drawArc(new RectF(q.left-ar,q.centerY()-ar,q.left+ar,q.centerY()+ar),-90,180,false,stroke);c.drawArc(new RectF(q.right-ar,q.centerY()-ar,q.right+ar,q.centerY()+ar),90,180,false,stroke);
            float gh=q.height()*.20f,gd=fieldTheme==4?10*s:12*s;c.drawRoundRect(new RectF(q.left-gd,q.centerY()-gh,q.left,q.centerY()+gh),3*s,3*s,stroke);c.drawRoundRect(new RectF(q.right,q.centerY()-gh,q.right+gd,q.centerY()+gh),3*s,3*s,stroke);
            p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(13*s);p.setColor(Color.WHITE);c.drawText(fieldNameV29(),r.centerX(),r.top+18*s,p);
        }

        void drawSetup(Canvas c){''',1)

s=rep(s,'drawSetup',r'''        void drawSetup(Canvas c){
            background(c);title(c,"PLAY MATCH",42*s,27f);
            float cw=Math.min(660*s,w*.72f),x=(w-cw)/2f,top=72*s;
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(27,32,40));c.drawRoundRect(new RectF(x,top,x+cw,h-70*s),20*s,20*s,p);
            int dL=(difficulty+2)%3,dR=(difficulty+1)%3;
            int tL=teamSize==1?4:teamSize-1,tR=teamSize==4?1:teamSize+1;
            int[] gs={3,5,7};int gi=targetGoals==3?0:targetGoals==5?1:2,gL=gs[(gi+2)%3],gR=gs[(gi+1)%3];
            float rw=cw-44*s,rx=x+22*s;
            selectorRowV29(c,"DIFFICULTY",difficultyNameV29(),rx,94*s,rw,"diff"+dL,"diff"+dR,Color.rgb(52,132,255));
            selectorRowV29(c,"PLAYERS",teamSize+"v"+teamSize,rx,151*s,rw,"team"+tL,"team"+tR,Color.rgb(44,188,104));
            selectorRowV29(c,"GOALS",""+targetGoals,rx,208*s,rw,"goal"+gL,"goal"+gR,Color.rgb(242,164,40));
            int fL=(fieldTheme+4)%5,fR=(fieldTheme+1)%5;
            RectF prev=new RectF(x+30*s,280*s,x+88*s,338*s),next=new RectF(x+cw-88*s,280*s,x+cw-30*s,338*s);
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(42,49,61));c.drawRoundRect(prev,14*s,14*s,p);c.drawRoundRect(next,14*s,14*s,p);p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(34*s);p.setColor(Color.WHITE);c.drawText("‹",prev.centerX(),prev.centerY()+11*s,p);c.drawText("›",next.centerX(),next.centerY()+11*s,p);hits.add(new ButtonHit("field"+fL,prev));hits.add(new ButtonHit("field"+fR,next));
            float ps=Math.min(230*s,h-390*s);RectF pr=new RectF(w/2f-ps/2f,268*s,w/2f+ps/2f,268*s+ps);drawFieldPreviewV29(c,pr);
            menuButton(c,"START MATCH","start",w/2f-190*s,h-61*s,380*s,44*s,Color.rgb(29,121,255));
            RectF back=new RectF(18*s,18*s,102*s,54*s);p.setColor(Color.rgb(47,54,66));c.drawRoundRect(back,10*s,10*s,p);p.setTextSize(13*s);p.setColor(Color.WHITE);p.setTextAlign(Paint.Align.CENTER);c.drawText("BACK",back.centerX(),back.centerY()+5*s,p);hits.add(new ButtonHit("home",back));
        }''')

s=rep(s,'chooseChasers',r'''        void chooseChasers(){
            float leftDanger=pitch.left+pitch.width()*.30f,leftBox=pitch.left+pitch.width()*.15f;
            float rightDanger=pitch.right-pitch.width()*.30f,rightBox=pitch.right-pitch.width()*.15f;
            blueChaser=-1;
            if(teamSize>=2&&bx<leftDanger){
                if(bx<leftBox)blueChaser=teamSize-1;
                else if(teamSize>=3)blueChaser=closestRangeToBall(blue,1,teamSize-1);
                else blueChaser=teamSize-1;
            }
            redChaser=0;
            if(teamSize>=2&&bx>rightDanger){
                if(bx>rightBox)redChaser=teamSize-1;
                else if(teamSize>=3)redChaser=closestRangeToBall(red,1,teamSize-1);
            }
        }''')

s=rep(s,'formationTarget',r'''        float[] formationTarget(int teamId,int idx,int chaser){
            float ownX=teamId==0?pitch.left:pitch.right,sign=teamId==0?1f:-1f,x,y;
            if(idx==0){
                x=pitch.centerX()+sign*pitch.width()*.15f;
                y=clamp(by,pitch.top+pitch.height()*.24f,pitch.bottom-pitch.height()*.24f);
            }else if(idx==teamSize-1&&teamSize>=2){
                x=ownX+sign*pitch.width()*.075f;
                y=clamp(by,pitch.centerY()-goalHalf*.65f,pitch.centerY()+goalHalf*.65f);
            }else{
                int defenders=Math.max(1,teamSize-2),slot=idx-1;float frac=(slot+1f)/(defenders+1f);
                x=ownX+sign*pitch.width()*(.23f+slot*.035f);
                float zoneY=pitch.top+pitch.height()*frac,follow=clamp(by,pitch.top+discR,pitch.bottom-discR);
                y=zoneY*.62f+follow*.38f;
            }
            return new float[]{clamp(x,pitch.left+discR,pitch.right-discR),clamp(y,pitch.top+discR,pitch.bottom-discR)};
        }''')

s=rep(s,'bestPassTarget',r'''        int bestPassTarget(Disc d,Disc[] team,Disc[] opp,int teamId){
            int best=-1;float bestScore=-99999;
            for(int i=0;i<teamSize;i++){
                Disc m=team[i];if(m==d)continue;float passDist=dist(d.x,d.y,m.x,m.y);
                if(passDist<58*s||passDist>pitch.width()*.68f)continue;
                if(isLaneBlocked(opp,bx,by,m.x,m.y,discR*1.18f))continue;
                float open=nearestOpponentDistance(opp,m.x,m.y),forward=teamId==0?(m.x-d.x):(d.x-m.x);
                float score=open*.74f+forward*.24f-passDist*.06f;
                if(i==0)score+=105*s;
                if(i==teamSize-1&&teamSize>=2)score-=80*s;
                if(score>bestScore){bestScore=score;best=i;}
            }
            return best;
        }''')

s=rep(s,'chooseKickTarget',r'''        float[] chooseKickTarget(Disc d,Disc[] team,Disc[] opp,int teamId){
            float goalX=teamId==0?pitch.right+25*s:pitch.left-25*s,goalY=bestGoalLaneV25(opp,teamId);
            int passTo=bestPassTarget(d,team,opp,teamId),crowd=countOpponentsNear(opp,d.x,d.y,105*s);
            boolean keeper=d.index==teamSize-1&&teamSize>=2,defender=d.index>0&&!keeper;
            if((keeper||defender)&&passTo>=0){Disc mate=team[passTo];return new float[]{mate.x+mate.vx*.18f,mate.y+mate.vy*.18f,1f};}
            float gd=Math.abs(goalX-bx);boolean finalThird=gd<pitch.width()*(difficulty==0?.30f:(difficulty==1?.37f:.43f));
            boolean laneBlocked=isLaneBlocked(opp,bx,by,goalX,goalY,discR*1.42f);
            if(passTo>=0&&(crowd>=2||(crowd>=1&&laneBlocked))){Disc mate=team[passTo];return new float[]{mate.x+mate.vx*.18f,mate.y+mate.vy*.18f,1f};}
            if(finalThird)return new float[]{goalX,goalY,0f};
            return new float[]{goalX,goalY,2f};
        }''')

s=rep(s,'updateTeamAI',r'''        void updateTeamAI(Disc[] team,Disc[] opp,int teamId,int chaser,float dt){
            for(int i=0;i<teamSize;i++){
                Disc d=team[i];if(!d.ai)continue;float tx,ty;
                if(i==chaser){
                    float[] target=chooseKickTarget(d,team,opp,teamId);boolean pass=target[2]>.5f&&target[2]<1.5f,carry=target[2]>1.5f;
                    float dx=target[0]-bx,dy=target[1]-by,ll=len(dx,dy);if(ll<1)ll=1;float dirX=dx/ll,dirY=dy/ll;
                    float bd=dist(d.x,d.y,bx,by),cdx=bx-d.x,cdy=by-d.y,cl=len(cdx,cdy);if(cl<1)cl=1;float align=(cdx/cl)*dirX+(cdy/cl)*dirY;
                    if(carry&&bd<discR+ballR+15*s&&align>.48f){tx=bx+dirX*(discR+ballR+24*s);ty=by+dirY*(discR+ballR+24*s);}
                    else{
                        float behind=discR+ballR+(ballNearWall()?16*s:7*s);float rawX=bx-dirX*behind,rawY=by-dirY*behind;
                        tx=clamp(rawX,pitch.left-discR*.3f,pitch.right+discR*.3f);ty=clamp(rawY,pitch.top-discR*.3f,pitch.bottom+discR*.3f);
                        if(ballNearWall()&&(Math.abs(tx-rawX)>2*s||Math.abs(ty-rawY)>2*s)){float sx=-dirY,sy=dirX;if((pitch.centerX()-bx)*sx+(pitch.centerY()-by)*sy<0){sx=-sx;sy=-sy;}tx=bx+sx*behind;ty=by+sy*behind;}
                    }
                    float need=difficulty==0?.82f:(difficulty==1?.74f:.66f);
                    if(!carry&&bd<=kickReach()&&align>need&&d.kickCd<=0f)cpuKick(d,pass?455*s:515*s,dirX,dirY,pass);
                }else{
                    float[] pos=formationTarget(teamId,i,chaser);tx=pos[0];ty=pos[1];
                    float minSpace=discR*(i==teamSize-1?3.7f:3.2f),db=dist(d.x,d.y,bx,by);
                    if(db<minSpace){float ax=d.x-bx,ay=d.y-by,al=len(ax,ay);if(al<1)al=1;tx+=ax/al*(minSpace-db+18*s);ty+=ay/al*(minSpace-db+18*s);}
                }
                moveAiToward(d,tx,ty,dt);
            }
        }''')

if 'void possessionV29(float dt)' not in s:
    s=s.replace('        void updateGame(float dt){',r'''        float wrapAngleV29(float a){while(a>3.1415927f)a-=6.2831853f;while(a<-3.1415927f)a+=6.2831853f;return a;}
        Disc nearestOpponentV29(Disc h){Disc best=null;float bd=Float.MAX_VALUE;Disc[] a=h.team==0?red:blue;for(int i=0;i<teamSize;i++){float q=dist(a[i].x,a[i].y,bx,by);if(q<bd){bd=q;best=a[i];}}return best;}
        void releasePossessionV29(float lock){ballHolderV29=null;holderReleaseV29=Math.max(holderReleaseV29,lock);}
        void possessionV29(float dt){
            holderReleaseV29=Math.max(0,holderReleaseV29-dt);
            if(goalLatchedV29){ballHolderV29=null;return;}
            float touch=discR+ballR;
            if(ballHolderV29!=null){
                Disc d=ballHolderV29;float hd=dist(d.x,d.y,bx,by);Disc o=nearestOpponentV29(d);float od=o==null?99999:dist(o.x,o.y,bx,by);
                float rel=o==null?0:len(o.vx-d.vx,o.vy-d.vy);
                if(hd>touch+15*s||(od<touch+2.2f*s&&(od<hd+1.5f*s||rel>42*s))){releasePossessionV29(.075f);return;}
                float sp=len(d.vx,d.vy);float target=holderAngleV29;
                if(sp>14*s)target=(float)Math.atan2(d.vy,d.vx);
                float diff=wrapAngleV29(target-holderAngleV29),turn=(3.8f+clamp(sp/(185*s),0,1)*2.8f)*dt;holderAngleV29+=clamp(diff,-turn,turn);
                float orbit=touch+1.5f*s,tx=d.x+(float)Math.cos(holderAngleV29)*orbit,ty=d.y+(float)Math.sin(holderAngleV29)*orbit;
                ty=clamp(ty,pitch.top+ballR,pitch.bottom-ballR);float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf;
                if(!(ty>y1+ballR*.2f&&ty<y2-ballR*.2f))tx=clamp(tx,pitch.left+ballR,pitch.right-ballR);
                float ex=tx-bx,ey=ty-by,k=clamp(dt*17f,0,.18f),tvx=d.vx+ex*8.5f,tvy=d.vy+ey*8.5f;
                bvx+=(tvx-bvx)*k;bvy+=(tvy-bvy)*k;float pk=clamp(dt*5.5f,0,.055f);bx+=ex*pk;by+=ey*pk;limitBallSpeed(620*s);
                return;
            }
            if(holderReleaseV29>0||len(bvx,bvy)>330*s)return;
            Disc best=null;float bd=99999,second=99999;
            for(int t=0;t<2;t++){Disc[] a=t==0?blue:red;for(int i=0;i<teamSize;i++){Disc d=a[i];float q=dist(d.x,d.y,bx,by);if(q<bd){second=bd;bd=q;best=d;}else if(q<second)second=q;}}
            if(best!=null&&bd<=touch+3.2f*s&&(second-bd)>1.4f*s&&best.kickCd<=0){
                float rv=len(bvx-best.vx,bvy-best.vy);if(rv<245*s){ballHolderV29=best;holderAngleV29=(float)Math.atan2(by-best.y,bx-best.x);}
            }
        }

        void updateGame(float dt){''',1)

s=rep(s,'doKick',r'''        void doKick(){
            Disc d=blue[0];if(d.kickCd>0)return;float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);if(l>kickReach())return;if(l<1){dx=1;dy=0;l=1;}
            if(ballHolderV29==d)releasePossessionV29(.16f);float nx=dx/l,ny=dy/l,power=520*s;bvx+=nx*power+d.vx*.12f;bvy+=ny*power+d.vy*.12f;limitBallSpeed(690*s);d.kickCd=.17f;spawnKickBurst(nx,ny,power);haptic(16);playSfx(SFX_KICK);
        }''')

s=rep(s,'cpuKick',r'''        void cpuKick(Disc d,float power,float desiredX,float desiredY,boolean pass){
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);if(l<1){dx=d.team==0?1:-1;dy=0;l=1;}if(l>kickReach())return;float nx=dx/l,ny=dy/l,align=nx*desiredX+ny*desiredY;if(align<(difficulty==0?.82f:difficulty==1?.74f:.66f))return;
            if(ballHolderV29==d)releasePossessionV29(.15f);float blend=difficulty==0?.12f:difficulty==1?.18f:.24f,ix=nx*(1-blend)+desiredX*blend,iy=ny*(1-blend)+desiredY*blend,il=len(ix,iy);if(il<1)il=1;ix/=il;iy/=il;float eff=(pass?450f:515f)*s;bvx+=ix*eff+d.vx*.10f;bvy+=iy*eff+d.vy*.10f;limitBallSpeed(690*s);d.kickCd=pass?.30f:.22f;if(pass){if(d.team==0)bluePassLock=.46f;else redPassLock=.46f;}spawnKickBurst(ix,iy,eff);playSfx(pass?SFX_PASS:SFX_KICK);
        }''')

s=rep(s,'scoreGoal',r'''        void scoreGoal(boolean blueGoal){
            if(mode!=GAME||goalLatchedV29)return;goalLatchedV29=true;releasePossessionV29(.30f);
            if(blueGoal)blueScore++;else redScore++;lastGoalBlue=blueGoal;playSfx(SFX_GOAL);haptic(70);pendingFinishAfterGoal=blueScore>=targetGoals||redScore>=targetGoals||goldenGoal;goalPauseTimer=pendingFinishAfterGoal?4.2f:3.25f;spawnGoalConfettiV26();
        }''')

s=rep(s,'resetPositions',r'''        void resetPositions(){
            if(w<=0||h<=0)return;float cy=pitch.centerY();
            for(int i=0;i<4;i++){
                float lane=((i%3)-1)*pitch.height()*.22f;blue[i].x=pitch.left+pitch.width()*(i==0?.28f:(i==teamSize-1?.075f:.23f));red[i].x=pitch.right-pitch.width()*(i==0?.28f:(i==teamSize-1?.075f:.23f));
                blue[i].y=clamp(cy+(i==0?pitch.height()*.10f:lane),pitch.top+discR,pitch.bottom-discR);red[i].y=clamp(cy+(i==0?-pitch.height()*.10f:lane),pitch.top+discR,pitch.bottom-discR);
                blue[i].vx=blue[i].vy=red[i].vx=red[i].vy=0;blue[i].kickCd=red[i].kickCd=.20f;
            }
            bx=pitch.centerX();by=cy;bvx=bvy=0;ballAngle=0;particles.clear();trailCarry=0;crowdExcitement=.05f;ballHolderV29=null;holderReleaseV29=.12f;goalLatchedV29=false;
            for(int i=0;i<teamSize;i++){separateFromBall(blue[i]);separateFromBall(red[i]);}
        }''')

s=rep(s,'startMatch',r'''        void startMatch(){
            blueScore=redScore=0;matchTime=180f;goldenGoal=false;savedResult=false;goalPauseTimer=0;pendingFinishAfterGoal=false;confetti.clear();bluePassLock=redPassLock=0;blueChaserHold=redChaserHold=0;countdownTimer=4.0f;goalLatchedV29=false;ballHolderV29=null;holderReleaseV29=.12f;mode=GAME;lastFrame=System.nanoTime();joyPointer=-1;joyNX=joyNY=0;joyX=joyBaseX;joyY=joyBaseY;prefs.edit().putInt("difficulty",difficulty).putInt("team_size",teamSize).putInt("target_goals",targetGoals).putInt("field_theme",fieldTheme).apply();resetPositions();camX=bx;camY=by;camZoom=1f;playSfx(SFX_MENU);
        }''')

s=rep(s,'updateGame',r'''        void updateGame(float dt){
            bluePassLock=Math.max(0,bluePassLock-dt);redPassLock=Math.max(0,redPassLock-dt);holderReleaseV29=Math.max(0,holderReleaseV29-dt);
            if(countdownTimer>0){countdownTimer=Math.max(0,countdownTimer-dt);crowdExcitement=.18f;syncRealAudio();for(int i=0;i<teamSize;i++){blue[i].vx*=.80f;blue[i].vy*=.80f;red[i].vx*=.80f;red[i].vy*=.80f;}bvx*=.80f;bvy*=.80f;return;}
            if(goalPauseTimer>0){
                goalPauseTimer=Math.max(0,goalPauseTimer-dt);updateConfettiV26(dt);for(int i=0;i<teamSize;i++){blue[i].kickCd=Math.max(0,blue[i].kickCd-dt);red[i].kickCd=Math.max(0,red[i].kickCd-dt);}updateHuman(dt);
                int steps=Math.max(3,Math.min(10,(int)Math.ceil(dt/.0040f)));float sub=dt/steps;for(int st=0;st<steps;st++)physicsStep(sub);updateParticles(dt);crowdExcitement=1;syncRealAudio();
                if(goalPauseTimer<=0){confetti.clear();if(pendingFinishAfterGoal){pendingFinishAfterGoal=false;finishMatch();return;}resetPositions();countdownTimer=4.0f;joyPointer=-1;joyNX=joyNY=0;joyX=joyBaseX;joyY=joyBaseY;}return;
            }
            if(!goldenGoal){matchTime-=dt;if(matchTime<=0){matchTime=0;if(blueScore==redScore)goldenGoal=true;else{finishMatch();return;}}}if(mode!=GAME)return;
            for(int i=0;i<teamSize;i++){blue[i].kickCd=Math.max(0,blue[i].kickCd-dt);red[i].kickCd=Math.max(0,red[i].kickCd-dt);blue[i].wallPlayTime=Math.max(0,blue[i].wallPlayTime-dt);red[i].wallPlayTime=Math.max(0,red[i].wallPlayTime-dt);}wallSoundCooldown=Math.max(0,wallSoundCooldown-dt);touchSoundCooldown=Math.max(0,touchSoundCooldown-dt);
            updateHuman(dt);chooseChasers();updateTeamAI(blue,red,0,blueChaser,dt);updateTeamAI(red,blue,1,redChaser,dt);
            int steps=Math.max(3,Math.min(14,(int)Math.ceil(dt/.0034f)));float sub=dt/steps;for(int st=0;st<steps;st++){physicsStep(sub);possessionV29(sub);if(goalLatchedV29)break;}updateParticles(dt);
            float dl=Math.abs(bx-pitch.left),dr=Math.abs(pitch.right-bx),near=Math.min(dl,dr)/Math.max(1,pitch.width()),th=clamp((.31f-near)/.31f,0,1),tow=(dl<dr)?Math.max(0,-bvx):Math.max(0,bvx),app=clamp(tow/(520*s),0,1),sb=clamp(len(bvx,bvy)/(690*s),0,1)*.16f;crowdExcitement=clamp(th*(.42f+.58f*app)+sb,0,1);syncRealAudio();
        }''')

s=rep(s,'updateCameraV28',r'''        void updateCameraV28(){
            float base=teamSize<=2?1.40f:(teamSize==3?1.31f:1.24f);if(fieldTheme==3)base-=.03f;if(fieldTheme==4)base+=.09f;if(goalPauseTimer>0)base=1.48f;
            float tx=goalPauseTimer>0?clamp(bx,pitch.left-36*s,pitch.right+36*s):(bx*.86f+blue[0].x*.14f),ty=goalPauseTimer>0?clamp(by,pitch.top-20*s,pitch.bottom+20*s):(by*.88f+blue[0].y*.12f);
            float halfW=w/(2f*base),halfH=h/(2f*base),minX=pitch.left-halfW*.18f,maxX=pitch.right+halfW*.18f,minY=pitch.top-halfH*.16f,maxY=pitch.bottom+halfH*.16f;tx=clamp(tx,minX,maxX);ty=clamp(ty,minY,maxY);
            if(camX==0&&camY==0){camX=tx;camY=ty;camZoom=base;}camX+=(tx-camX)*.105f;camY+=(ty-camY)*.105f;camZoom+=(base-camZoom)*.085f;
        }''')

s=rep(s,'drawGoals',r'''        void drawGoals(Canvas c){
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf,depth=fieldTheme==4?36*s:goalDepthV26(),curve=fieldTheme==4?9*s:12*s;
            int frame=fieldTheme==2?Color.rgb(205,228,242):Color.rgb(248,249,247),net=fieldTheme==2?Color.argb(95,148,184,207):Color.argb(fieldTheme==4?55:92,190,198,202);
            stroke.setStyle(Paint.Style.STROKE);stroke.setStrokeWidth((fieldTheme==4?2.2f:2.7f)*s);stroke.setColor(frame);
            path.reset();path.moveTo(pitch.left,y1);path.lineTo(pitch.left-depth*.62f,y1);path.quadTo(pitch.left-depth,y1,pitch.left-depth,y1+curve);path.lineTo(pitch.left-depth,y2-curve);path.quadTo(pitch.left-depth,y2,pitch.left-depth*.62f,y2);path.lineTo(pitch.left,y2);c.drawPath(path,stroke);
            path.reset();path.moveTo(pitch.right,y1);path.lineTo(pitch.right+depth*.62f,y1);path.quadTo(pitch.right+depth,y1,pitch.right+depth,y1+curve);path.lineTo(pitch.right+depth,y2-curve);path.quadTo(pitch.right+depth,y2,pitch.right+depth*.62f,y2);path.lineTo(pitch.right,y2);c.drawPath(path,stroke);
            stroke.setStrokeWidth(.75f*s);stroke.setColor(net);for(int i=1;i<4;i++){float yy=y1+(y2-y1)*i/4f;c.drawLine(pitch.left-depth*.90f,yy,pitch.left,yy,stroke);c.drawLine(pitch.right,yy,pitch.right+depth*.90f,yy,stroke);}if(fieldTheme!=4)for(int i=1;i<3;i++){float lx=pitch.left-depth+depth*i/3f,rx=pitch.right+depth-depth*i/3f;c.drawLine(lx,y1+3*s,lx,y2-3*s,stroke);c.drawLine(rx,y1+3*s,rx,y2-3*s,stroke);}
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(18,20,22));float rr=fieldTheme==4?4.6f*s:5.6f*s;c.drawCircle(pitch.left,y1,rr,p);c.drawCircle(pitch.left,y2,rr,p);c.drawCircle(pitch.right,y1,rr,p);c.drawCircle(pitch.right,y2,rr,p);p.setColor(frame);rr=fieldTheme==4?3.3f*s:4*s;c.drawCircle(pitch.left,y1,rr,p);c.drawCircle(pitch.left,y2,rr,p);c.drawCircle(pitch.right,y1,rr,p);c.drawCircle(pitch.right,y2,rr,p);
        }''')

s=rep(s,'drawFootball',r'''        void drawFootball(Canvas c,float x,float y,float r,float angle){
            if(fieldTheme==4){p.setStyle(Paint.Style.FILL);p.setColor(Color.argb(75,0,0,0));c.drawCircle(x+1.4f*s,y+2.1f*s,r*1.08f,p);p.setColor(Color.rgb(246,239,62));c.drawCircle(x,y,r,p);stroke.setStyle(Paint.Style.STROKE);stroke.setStrokeWidth(1.35f*s);stroke.setColor(Color.rgb(35,35,26));c.drawCircle(x,y,r,stroke);p.setColor(Color.argb(125,255,255,255));c.drawCircle(x-r*.28f,y-r*.33f,r*.24f,p);return;}
            c.save();c.rotate(angle,x,y);p.setStyle(Paint.Style.FILL);p.setColor(Color.argb(90,0,0,0));c.drawCircle(x+2.2f*s,y+3.2f*s,r*1.04f,p);p.setColor(Color.rgb(247,248,246));c.drawCircle(x,y,r,p);stroke.setStyle(Paint.Style.STROKE);stroke.setStrokeWidth(Math.max(1f,1.15f*s));stroke.setColor(Color.rgb(42,45,48));c.drawCircle(x,y,r,stroke);polygon(c,x,y,r*.31f,5,-90f,Color.rgb(22,24,27),true);for(int i=0;i<5;i++){double a=Math.toRadians(-90+i*72);float px=x+(float)Math.cos(a)*r*.70f,py=y+(float)Math.sin(a)*r*.70f;polygon(c,px,py,r*.19f,5,-90f+i*72,Color.rgb(30,32,35),true);stroke.setColor(Color.rgb(86,89,92));stroke.setStrokeWidth(Math.max(1f,.72f*s));c.drawLine(x+(float)Math.cos(a)*r*.30f,y+(float)Math.sin(a)*r*.30f,px,py,stroke);double b=Math.toRadians(-90+i*72+36);c.drawLine(px,py,x+(float)Math.cos(b)*r*.96f,y+(float)Math.sin(b)*r*.96f,stroke);}p.setColor(Color.argb(105,255,255,255));c.drawCircle(x-r*.31f,y-r*.36f,r*.25f,p);c.restore();
        }''')

s=rep(s,'drawDisc',r'''        void drawDisc(Canvas c,Disc d){
            int col=d.team==0?Color.rgb(35,103,235):Color.rgb(239,57,61);p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(12,13,15));c.drawCircle(d.x,d.y,discR+(fieldTheme==4?2.4f:3f)*s,p);p.setColor(col);c.drawCircle(d.x,d.y,discR,p);
            if(fieldTheme==4){if(d==blue[0]){stroke.setStyle(Paint.Style.STROKE);stroke.setStrokeWidth(2.2f*s);stroke.setColor(Color.WHITE);c.drawCircle(d.x,d.y,discR+3.2f*s,stroke);}}
            else{p.setColor(Color.argb(82,255,255,255));c.drawCircle(d.x-discR*.28f,d.y-discR*.30f,discR*.22f,p);}
            p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize((fieldTheme==4?10.5f:12f)*s);p.setColor(Color.WHITE);c.drawText(d.name,d.x,d.y+discR+(fieldTheme==4?14f:17f)*s,p);
        }''')

s=rep(s,'drawGame',r'''        void drawGame(Canvas c){
            int out,p1,p2,line;if(fieldTheme==1){out=Color.rgb(39,118,43);p1=Color.rgb(54,156,56);p2=Color.rgb(48,145,51);line=Color.rgb(244,247,242);}else if(fieldTheme==2){out=Color.rgb(18,36,55);p1=Color.rgb(31,57,84);p2=Color.rgb(27,50,76);line=Color.rgb(215,232,246);}else if(fieldTheme==3){out=Color.rgb(42,122,47);p1=Color.rgb(60,153,64);p2=Color.rgb(51,139,57);line=Color.rgb(244,247,242);}else if(fieldTheme==4){out=Color.rgb(45,45,46);p1=Color.rgb(76,76,77);p2=Color.rgb(71,71,72);line=Color.WHITE;}else{out=Color.rgb(52,56,60);p1=Color.rgb(68,73,78);p2=Color.rgb(61,66,71);line=Color.WHITE;}
            c.drawColor(out);updateCameraV28();c.save();c.translate(w*.5f,h*.50f);c.scale(camZoom,camZoom);c.translate(-camX,-camY);
            p.setStyle(Paint.Style.FILL);p.setColor(p1);c.drawRect(pitch,p);int bands=fieldTheme==4?14:(fieldTheme==3?12:10);for(int i=0;i<bands;i++){p.setColor(i%2==0?p1:p2);float xx=pitch.left+pitch.width()*i/bands;c.drawRect(xx,pitch.top,xx+pitch.width()/bands,pitch.bottom,p);}if(fieldTheme==4){p.setColor(Color.argb(15,255,255,255));for(int j=1;j<13;j++){float yy=pitch.top+pitch.height()*j/13f;c.drawRect(pitch.left,yy,pitch.right,yy+.8f*s,p);}}
            stroke.setStyle(Paint.Style.STROKE);stroke.setColor(line);stroke.setStrokeWidth((fieldTheme==4?2.15f:2.4f)*s/camZoom);c.drawRect(pitch,stroke);c.drawLine(pitch.centerX(),pitch.top,pitch.centerX(),pitch.bottom,stroke);c.drawCircle(pitch.centerX(),pitch.centerY(),72*s,stroke);c.drawCircle(pitch.centerX(),pitch.centerY(),3.5f*s,stroke);float ar=Math.min(pitch.height()*.32f,pitch.width()*.18f);c.drawArc(new RectF(pitch.left-ar,pitch.centerY()-ar,pitch.left+ar,pitch.centerY()+ar),-90,180,false,stroke);c.drawArc(new RectF(pitch.right-ar,pitch.centerY()-ar,pitch.right+ar,pitch.centerY()+ar),90,180,false,stroke);drawGoals(c);drawPredictionGuideV24(c);drawParticles(c);for(int i=0;i<teamSize;i++)drawDisc(c,blue[i]);for(int i=0;i<teamSize;i++)drawDisc(c,red[i]);drawFootball(c,bx,by,ballR,ballAngle);c.restore();drawScoreHud(c);drawJoystick(c,false);drawKick(c,false);if(goalPauseTimer>0)drawGoalCelebrationV26(c);if(countdownTimer>0)drawCountdownV27(c);
        }''')

s=rep(s,'nearestGuideDiscV24',r'''        Disc nearestGuideDiscV24(){Disc d=blue[0];return dist(d.x,d.y,bx,by)<=kickReach()+25*s?d:null;}''')

s=s.replace('circle_football_v28','circle_football_v29')
path.write_text(s,encoding='utf-8')

m=Path('AndroidManifest.xml');x=m.read_text(encoding='utf-8');x=x.replace('com.godnit.circlefootballlite.v28','com.godnit.circlefootballlite.v29');x=re.sub(r'android:versionCode="\d+"','android:versionCode="20"',x,count=1);x=re.sub(r'android:versionName="[^"]+"','android:versionName="2.9.0"',x,count=1);m.write_text(x,encoding='utf-8')
print('Applied v2.9 role AI, stealable orbit possession, goal latch, compact selector and video stadium')
