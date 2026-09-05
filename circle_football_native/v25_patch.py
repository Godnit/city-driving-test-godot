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

# v2.5 keeps the slower equal-speed gameplay, but reduces the visual/physical
# size of every player and the ball. It also leaves a clear runoff area around
# the touchlines/corners like the reference game.
configure = r'''        void configureField(){
            float mxRatio,myRatio;
            if(fieldTheme==3){mxRatio=.040f;myRatio=.075f;}
            else if(fieldTheme==2){mxRatio=.064f;myRatio=.104f;}
            else{mxRatio=teamSize>=3?.058f:.073f;myRatio=teamSize>=3?.098f:.116f;}
            float mx=w*mxRatio,my=h*myRatio;
            pitch.set(mx,my,w-mx,h-my);
            goalHalf=pitch.height()*.19f;

            float teamScale=teamSize>=4?.78f:(teamSize==3?.87f:1f);
            float themeScale=fieldTheme==3?.88f:(fieldTheme==2?.95f:1f);
            discR=24.5f*s*teamScale*themeScale;

            float ballTeam=teamSize>=4?.84f:(teamSize==3?.91f:1f);
            float ballTheme=fieldTheme==3?.86f:(fieldTheme==2?.94f:1f);
            ballR=11.8f*s*ballTeam*ballTheme;
        }'''
s = replace_method(s, 'configureField', configure)

# Draw a more Hax-like / classic small-sided football field: visible runoff,
# large goal-area semicircles, and compact curved goals behind the line.
draw_game = r'''        void drawGame(Canvas c){
            int outside,p1,p2,line;
            if(fieldTheme==1){outside=Color.rgb(39,118,43);p1=Color.rgb(54,156,56);p2=Color.rgb(48,145,51);line=Color.rgb(244,247,242);}
            else if(fieldTheme==2){outside=Color.rgb(18,36,55);p1=Color.rgb(31,57,84);p2=Color.rgb(27,50,76);line=Color.rgb(215,232,246);}
            else if(fieldTheme==3){outside=Color.rgb(42,122,47);p1=Color.rgb(60,153,64);p2=Color.rgb(51,139,57);line=Color.rgb(244,247,242);}
            else{outside=Color.rgb(52,56,60);p1=Color.rgb(68,73,78);p2=Color.rgb(61,66,71);line=Color.WHITE;}

            c.drawColor(outside);
            p.setStyle(Paint.Style.FILL);p.setColor(p1);c.drawRect(pitch,p);
            int bands=fieldTheme==3?12:10;
            for(int i=0;i<bands;i++){
                p.setColor(i%2==0?p1:p2);
                float xx=pitch.left+pitch.width()*i/bands;
                c.drawRect(xx,pitch.top,xx+pitch.width()/bands,pitch.bottom,p);
            }
            if(fieldTheme==1||fieldTheme==3){
                p.setColor(Color.argb(15,255,255,255));
                for(int i=0;i<7;i++)c.drawRect(pitch.left,pitch.top+i*pitch.height()/7f,pitch.right,pitch.top+(i+.11f)*pitch.height()/7f,p);
            }

            stroke.setColor(line);stroke.setStrokeWidth(3*s);
            c.drawRect(pitch,stroke);
            c.drawLine(pitch.centerX(),pitch.top,pitch.centerX(),pitch.bottom,stroke);
            c.drawCircle(pitch.centerX(),pitch.centerY(),74*s,stroke);
            c.drawCircle(pitch.centerX(),pitch.centerY(),3.5f*s,stroke);

            float areaR=Math.min(pitch.height()*.34f,pitch.width()*.19f);
            RectF la=new RectF(pitch.left-areaR,pitch.centerY()-areaR,pitch.left+areaR,pitch.centerY()+areaR);
            RectF ra=new RectF(pitch.right-areaR,pitch.centerY()-areaR,pitch.right+areaR,pitch.centerY()+areaR);
            c.drawArc(la,-90f,180f,false,stroke);
            c.drawArc(ra,90f,180f,false,stroke);

            drawGoals(c);
            drawPredictionGuideV24(c);
            drawParticles(c);
            for(int i=0;i<teamSize;i++)drawDisc(c,blue[i]);
            for(int i=0;i<teamSize;i++)drawDisc(c,red[i]);
            drawFootball(c,bx,by,ballR,ballAngle);
            drawScoreHud(c);
            drawJoystick(c,false);drawKick(c,false);
        }'''
s = replace_method(s, 'drawGame', draw_game)

draw_goals = r'''        void drawGoals(Canvas c){
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf;
            float depth=62f*s,curve=15f*s;
            int frame=fieldTheme==2?Color.rgb(195,222,239):Color.rgb(246,247,245);
            int net=fieldTheme==2?Color.argb(112,148,184,207):Color.argb(105,190,198,202);

            stroke.setStyle(Paint.Style.STROKE);
            stroke.setStrokeWidth(3f*s);stroke.setColor(frame);

            path.reset();
            path.moveTo(pitch.left,y1);
            path.lineTo(pitch.left-depth*.62f,y1);
            path.quadTo(pitch.left-depth,y1,pitch.left-depth,y1+curve);
            path.lineTo(pitch.left-depth,y2-curve);
            path.quadTo(pitch.left-depth,y2,pitch.left-depth*.62f,y2);
            path.lineTo(pitch.left,y2);
            c.drawPath(path,stroke);

            path.reset();
            path.moveTo(pitch.right,y1);
            path.lineTo(pitch.right+depth*.62f,y1);
            path.quadTo(pitch.right+depth,y1,pitch.right+depth,y1+curve);
            path.lineTo(pitch.right+depth,y2-curve);
            path.quadTo(pitch.right+depth,y2,pitch.right+depth*.62f,y2);
            path.lineTo(pitch.right,y2);
            c.drawPath(path,stroke);

            stroke.setStrokeWidth(1f*s);stroke.setColor(net);
            for(int i=1;i<4;i++){
                float yy=y1+(y2-y1)*i/4f;
                c.drawLine(pitch.left-depth*.94f,yy,pitch.left,yy,stroke);
                c.drawLine(pitch.right,yy,pitch.right+depth*.94f,yy,stroke);
            }
            for(int i=1;i<3;i++){
                float t=i/3f;
                float lx=pitch.left-depth*(1f-t),rx=pitch.right+depth*(1f-t);
                c.drawLine(lx,y1+curve*.25f,lx,y2-curve*.25f,stroke);
                c.drawLine(rx,y1+curve*.25f,rx,y2-curve*.25f,stroke);
            }

            // Prominent circular posts like the reference game.
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(20,22,24));
            c.drawCircle(pitch.left,y1,6.2f*s,p);c.drawCircle(pitch.left,y2,6.2f*s,p);
            c.drawCircle(pitch.right,y1,6.2f*s,p);c.drawCircle(pitch.right,y2,6.2f*s,p);
            p.setColor(frame);
            c.drawCircle(pitch.left,y1,4.5f*s,p);c.drawCircle(pitch.left,y2,4.5f*s,p);
            c.drawCircle(pitch.right,y1,4.5f*s,p);c.drawCircle(pitch.right,y2,4.5f*s,p);
        }'''
s = replace_method(s, 'drawGoals', draw_goals)

# Remove the noisy half-rings around every player. Only the controlled player
# gets a tiny selection rim; the trajectory guide below is also human-only.
draw_disc = r'''        void drawDisc(Canvas c,Disc d){
            int col=d.team==0?Color.rgb(35,103,235):Color.rgb(239,57,61);
            if(d==blue[0]){
                stroke.setStyle(Paint.Style.STROKE);stroke.setColor(Color.argb(46,255,255,255));stroke.setStrokeWidth(1.5f*s);
                c.drawCircle(d.x,d.y,discR+5f*s,stroke);
            }
            p.setStyle(Paint.Style.FILL);p.setColor(Color.BLACK);c.drawCircle(d.x,d.y,discR+2.5f*s,p);
            p.setColor(col);c.drawCircle(d.x,d.y,discR,p);
            p.setColor(Color.argb(75,255,255,255));c.drawCircle(d.x-discR*.28f,d.y-discR*.30f,discR*.20f,p);
            p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(10.5f*s);p.setColor(Color.WHITE);
            c.drawText(d.name,d.x,d.y+discR+14f*s,p);
        }'''
s = replace_method(s, 'drawDisc', draw_disc)

# Only YOU gets a short, very faint predicted path. Its maximum length stays
# smaller than the goal opening and still shows a wall reflection when relevant.
prediction = r'''        void drawPredictionGuideV24(Canvas c){
            Disc d=blue[0];
            float db=dist(d.x,d.y,bx,by);
            if(db>kickReach()+26f*s)return;
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);
            if(l<1f){dx=1f;dy=0f;l=1f;}
            float vx=dx/l,vy=dy/l;
            float bs=len(bvx,bvy);
            if(bs>25f*s){
                vx=vx*.91f+(bvx/bs)*.09f;vy=vy*.91f+(bvy/bs)*.09f;
                float vl=len(vx,vy);if(vl>0f){vx/=vl;vy/=vl;}
            }
            float maxLen=Math.min(goalHalf*1.45f,150f*s);
            float step=13.5f*s,travel=0f,px=bx,py=by;
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf;
            p.setStyle(Paint.Style.FILL);
            int dot=0;
            while(travel<maxLen){
                px+=vx*step;py+=vy*step;travel+=step;
                if(py-ballR<pitch.top){py=pitch.top+ballR;vy=Math.abs(vy);}
                if(py+ballR>pitch.bottom){py=pitch.bottom-ballR;vy=-Math.abs(vy);}
                boolean mouth=py>y1+ballR*.16f&&py<y2-ballR*.16f;
                if(!mouth){
                    if(px-ballR<pitch.left){px=pitch.left+ballR;vx=Math.abs(vx);}
                    if(px+ballR>pitch.right){px=pitch.right-ballR;vx=-Math.abs(vx);}
                }
                int alpha=Math.max(10,42-dot*3);
                p.setColor(Color.argb(alpha,255,255,255));
                c.drawCircle(px,py,1.7f*s,p);
                dot++;
            }
        }'''
s = replace_method(s, 'drawPredictionGuideV24', prediction)

# Players may use the runoff strip and may enter the goal, but once inside a
# goal they are contained by its side/back frame and cannot escape behind it.
clamp_disc = r'''        void clampDisc(Disc d){
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf;
            float sideRun=42f*s,endRun=24f*s,goalDepth=60f*s;

            d.y=clamp(d.y,pitch.top-sideRun,pitch.bottom+sideRun);

            if(d.x<pitch.left){
                boolean entered=d.y>y1-discR*.25f&&d.y<y2+discR*.25f;
                if(entered){
                    d.x=clamp(d.x,pitch.left-goalDepth+discR*.45f,pitch.left);
                    d.y=clamp(d.y,y1+discR*.62f,y2-discR*.62f);
                }else d.x=clamp(d.x,pitch.left-endRun,pitch.right+endRun);
            }else if(d.x>pitch.right){
                boolean entered=d.y>y1-discR*.25f&&d.y<y2+discR*.25f;
                if(entered){
                    d.x=clamp(d.x,pitch.right,pitch.right+goalDepth-discR*.45f);
                    d.y=clamp(d.y,y1+discR*.62f,y2-discR*.62f);
                }else d.x=clamp(d.x,pitch.left-endRun,pitch.right+endRun);
            }else{
                d.x=clamp(d.x,pitch.left-endRun,pitch.right+endRun);
            }
        }'''
s = replace_method(s, 'clampDisc', clamp_disc)

# Better attacking decisions. Difficulty changes anticipation/accuracy/decision
# quality only; everybody keeps the same running speed from v2.3.
if 'float bestGoalLaneV25(' not in s:
    marker='        float[] chooseKickTarget('
    helper=r'''        float bestGoalLaneV25(Disc[] opp,int teamId){
            float gx=teamId==0?pitch.right+20f*s:pitch.left-20f*s;
            float y1=pitch.centerY()-goalHalf+ballR*1.5f,y2=pitch.centerY()+goalHalf-ballR*1.5f;
            int samples=difficulty==0?1:(difficulty==1?3:5);
            float bestY=pitch.centerY(),bestScore=-999999f;
            for(int k=0;k<samples;k++){
                float gy=samples==1?pitch.centerY():y1+(y2-y1)*(k+.5f)/samples;
                float clearance=999999f;
                for(int i=0;i<teamSize;i++){
                    float t=segmentT(opp[i].x,opp[i].y,bx,by,gx,gy);
                    if(t>.04f&&t<1.02f)clearance=Math.min(clearance,distToSegment(opp[i].x,opp[i].y,bx,by,gx,gy));
                }
                float score=clearance-Math.abs(gy-pitch.centerY())*.04f;
                if(difficulty==2){
                    Disc near=nearestOpponentToLine(opp,bx,by,gx,gy);
                    if(near!=null)score+=Math.abs(gy-near.y)*.10f;
                }
                if(score>bestScore){bestScore=score;bestY=gy;}
            }
            return bestY;
        }

        boolean forwardPassV25(Disc from,Disc to,int teamId){
            float f=teamId==0?to.x-from.x:from.x-to.x;
            return f>22f*s;
        }

'''
    if marker not in s:raise RuntimeError('chooseKickTarget marker missing')
    s=s.replace(marker,helper+marker,1)

best_pass = r'''        int bestPassTarget(Disc d,Disc[] team,Disc[] opp,int teamId){
            int best=-1;float bestScore=-999999f;
            for(int i=0;i<teamSize;i++){
                Disc m=team[i];if(m==d)continue;
                float pd=dist(d.x,d.y,m.x,m.y);
                if(pd<72f*s||pd>pitch.width()*.58f)continue;
                boolean keeper=d.index==teamSize-1&&teamSize>=2;
                boolean defender=d.index>0&&!keeper;
                if(!keeper&&!defender&&!forwardPassV25(d,m,teamId))continue;
                float laneRadius=discR*(difficulty==2?1.12f:(difficulty==1?1.30f:1.48f));
                if(isLaneBlocked(opp,bx,by,m.x,m.y,laneRadius))continue;
                float open=nearestOpponentDistance(opp,m.x,m.y);
                float forward=teamId==0?(m.x-d.x):(d.x-m.x);
                float score=open*.72f+forward*.36f-pd*.08f;
                if(i==0)score+=70f*s;
                if(i==teamSize-1&&teamSize>=2)score-=90f*s;
                if(score>bestScore){bestScore=score;best=i;}
            }
            return best;
        }'''
s = replace_method(s, 'bestPassTarget', best_pass)

choose_target = r'''        float[] chooseKickTarget(Disc d,Disc[] team,Disc[] opp,int teamId){
            float sign=teamId==0?1f:-1f;
            float gx=teamId==0?pitch.right+24f*s:pitch.left-24f*s;
            float gy=bestGoalLaneV25(opp,teamId);
            float goalDist=Math.abs(gx-bx);
            boolean keeper=d.index==teamSize-1&&teamSize>=2;
            boolean defender=d.index>0&&!keeper;
            int passTo=bestPassTarget(d,team,opp,teamId);
            int pressure=countOpponentsNear(opp,d.x,d.y,(difficulty==2?108f:(difficulty==1?98f:88f))*s);
            float shotRadius=discR*(difficulty==2?1.18f:(difficulty==1?1.34f:1.52f));
            boolean blocked=isLaneBlocked(opp,bx,by,gx,gy,shotRadius);
            float finalFrac=difficulty==0?.30f:(difficulty==1?.39f:.46f);
            boolean finalZone=goalDist<pitch.width()*finalFrac;

            if(keeper||defender){
                if(passTo>=0){
                    Disc m=team[passTo];
                    return new float[]{m.x+m.vx*.14f,m.y+m.vy*.14f,1f,0f,0f,0f};
                }
                float clearY=pitch.centerY()+(d.y<pitch.centerY()?goalHalf*.38f:-goalHalf*.38f);
                return new float[]{bx+sign*190f*s,clearY,0f,0f,0f,0f};
            }

            // In the attacking zone, shoot first. Passing is a fallback only when
            // the lane is genuinely crowded; wall-banks are no longer preferred.
            if(finalZone){
                if(!blocked||passTo<0||pressure==0)return new float[]{gx,gy,0f,0f,0f,0f};
                if(passTo>=0&&pressure>0){
                    Disc m=team[passTo];
                    return new float[]{m.x+m.vx*.12f,m.y+m.vy*.12f,1f,0f,0f,0f};
                }
                return new float[]{gx,gy,0f,0f,0f,0f};
            }

            if(passTo>=0&&pressure>0){
                Disc m=team[passTo];
                return new float[]{m.x+m.vx*.12f,m.y+m.vy*.12f,1f,0f,0f,0f};
            }

            // With space, carry the ball forward instead of exchanging pointless
            // passes or shooting at the wall from midfield.
            float carryX=bx+sign*Math.min(190f*s,goalDist*.42f);
            float carryY=by*.72f+pitch.centerY()*.28f;
            return new float[]{carryX,carryY,2f,0f,0f,0f};
        }'''
s = replace_method(s, 'chooseKickTarget', choose_target)

update_team = r'''        void updateTeamAI(Disc[] team,Disc[] opp,int teamId,int chaser,float dt){
            for(int i=0;i<teamSize;i++){
                Disc d=team[i];if(!d.ai)continue;
                float tx,ty;
                if(i==chaser){
                    float[] target=chooseKickTarget(d,team,opp,teamId);
                    boolean pass=target[2]>.5f&&target[2]<1.5f;
                    boolean carry=target[2]>1.5f;
                    float lead=difficulty==0?.025f:(difficulty==1?.065f:.115f);
                    float pbx=bx+bvx*lead,pby=by+bvy*lead;
                    float dx=target[0]-pbx,dy=target[1]-pby,ll=len(dx,dy);if(ll<1f)ll=1f;
                    float dirX=dx/ll,dirY=dy/ll;
                    float behind=discR+ballR+(carry?3.5f*s:7.5f*s);
                    float rawX=pbx-dirX*behind,rawY=pby-dirY*behind;
                    tx=clamp(rawX,pitch.left-10f*s,pitch.right+10f*s);
                    ty=clamp(rawY,pitch.top-18f*s,pitch.bottom+18f*s);

                    // Near a wall, approach from the open side rather than pinning
                    // the ball into it.
                    if(ballNearWall()){
                        float wallGap=Math.min(Math.min(by-pitch.top,pitch.bottom-by),Math.min(bx-pitch.left,pitch.right-bx));
                        if(wallGap<ballR+12f*s){
                            float sx=-dirY,sy=dirX;
                            float towardCenter=(pitch.centerX()-bx)*sx+(pitch.centerY()-by)*sy;
                            if(towardCenter<0f){sx=-sx;sy=-sy;}
                            tx=bx+sx*(discR+ballR+9f*s);
                            ty=by+sy*(discR+ballR+9f*s);
                        }
                    }

                    float bd=dist(d.x,d.y,bx,by);
                    float cdx=bx-d.x,cdy=by-d.y,cl=len(cdx,cdy);if(cl<1f)cl=1f;
                    float align=(cdx/cl)*dirX+(cdy/cl)*dirY;
                    float need=difficulty==0?.84f:(difficulty==1?.76f:.68f);
                    if(!carry&&bd<=kickReach()&&align>need&&d.kickCd<=0f){
                        cpuKick(d,pass?445f*s:515f*s,dirX,dirY,pass);
                    }
                }else{
                    float[] pos=formationTarget(teamId,i,chaser);tx=pos[0];ty=pos[1];
                    float minSpace=discR*(i==teamSize-1?4.0f:3.45f);
                    float db=dist(d.x,d.y,bx,by);
                    if(db<minSpace){
                        float ax=d.x-bx,ay=d.y-by,al=len(ax,ay);if(al<1f)al=1f;
                        tx+=ax/al*(minSpace-db+24f*s);ty+=ay/al*(minSpace-db+24f*s);
                    }
                }
                moveAiToward(d,tx,ty,dt);
            }
        }'''
s = replace_method(s, 'updateTeamAI', update_team)

cpu_kick = r'''        void cpuKick(Disc d,float power,float desiredX,float desiredY,boolean pass){
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);
            if(l<1f){dx=d.team==0?1f:-1f;dy=0f;l=1f;}
            if(l>kickReach())return;
            float nx=dx/l,ny=dy/l;
            float need=difficulty==0?.84f:(difficulty==1?.76f:.68f);
            float align=nx*desiredX+ny*desiredY;if(align<need)return;
            float blend=difficulty==0?.08f:(difficulty==1?.14f:.20f);
            float ix=nx*(1f-blend)+desiredX*blend,iy=ny*(1f-blend)+desiredY*blend;
            float il=len(ix,iy);if(il<1f)il=1f;ix/=il;iy/=il;
            float eff=(pass?445f:515f)*s;
            bvx+=ix*eff+d.vx*.08f;bvy+=iy*eff+d.vy*.08f;
            limitBallSpeed(690f*s);
            d.kickCd=pass?.29f:.22f;
            spawnKickBurst(ix,iy,eff);
            playSfx(pass?SFX_PASS:SFX_KICK);
        }'''
s = replace_method(s, 'cpuKick', cpu_kick)

# Role-based spacing: one striker, defenders behind the ball, goalkeeper close
# to the goal line. This keeps teammates from clustering around the ball.
formation = r'''        float[] formationTarget(int teamId,int idx,int chaser){
            float own=teamId==0?pitch.left:pitch.right;
            float sign=teamId==0?1f:-1f;
            float x,y;
            if(idx==0){
                x=clamp(bx+sign*pitch.width()*.16f,pitch.left+pitch.width()*.18f,pitch.right-pitch.width()*.18f);
                y=clamp(by,pitch.top+pitch.height()*.20f,pitch.bottom-pitch.height()*.20f);
            }else if(idx==teamSize-1&&teamSize>=2){
                x=own+sign*10f*s;
                y=clamp(by,pitch.centerY()-goalHalf*.62f,pitch.centerY()+goalHalf*.62f);
            }else{
                int defenders=Math.max(1,teamSize-2),slot=idx-1;
                float f=(slot+1f)/(defenders+1f);
                float ballSide=teamId==0?Math.min(bx,pitch.centerX()):Math.max(bx,pitch.centerX());
                x=own+sign*pitch.width()*.24f;
                x=x*.72f+ballSide*.28f;
                float zone=pitch.top+pitch.height()*f;
                y=zone*.68f+clamp(by,pitch.top+discR,pitch.bottom-discR)*.32f;
            }
            return new float[]{clamp(x,pitch.left-8f*s,pitch.right+8f*s),clamp(y,pitch.top-16f*s,pitch.bottom+16f*s)};
        }'''
s = replace_method(s, 'formationTarget', formation)

# One aggregate ball-contact solve per substep. When two or more players squeeze
# the ball from opposite sides, separate the players and damp the ball instead of
# stacking multiple impulses and launching it unnaturally.
if 'void solveBallContactsV25()' not in s:
    marker='        void physicsStep(float dt){'
    helper=r'''        void solveBallContactsV25(){
            Disc[] cs=new Disc[8];float[] nx=new float[8],ny=new float[8],pen=new float[8];int n=0;
            float min=discR+ballR;
            for(int team=0;team<2;team++){
                Disc[] arr=team==0?blue:red;
                for(int i=0;i<teamSize&&n<8;i++){
                    float dx=bx-arr[i].x,dy=by-arr[i].y,l=len(dx,dy);
                    if(l<min){
                        if(l<.001f){dx=arr[i].team==0?1f:-1f;dy=0f;l=1f;}
                        cs[n]=arr[i];nx[n]=dx/l;ny[n]=dy/l;pen[n]=min-l+.22f*s;n++;
                    }
                }
            }
            if(n==0)return;
            boolean squeeze=false;
            for(int i=0;i<n&&!squeeze;i++)for(int j=i+1;j<n;j++)if(nx[i]*nx[j]+ny[i]*ny[j]<-.42f){squeeze=true;break;}
            if(squeeze){
                float sx=0f,sy=0f,maxPen=0f;
                for(int i=0;i<n;i++){
                    Disc d=cs[i];float move=pen[i]*.48f;
                    d.x-=nx[i]*move;d.y-=ny[i]*move;clampDisc(d);
                    sx+=nx[i]*pen[i];sy+=ny[i]*pen[i];maxPen=Math.max(maxPen,pen[i]);
                }
                float sl=len(sx,sy);
                if(sl>.05f){bx+=sx/sl*Math.min(maxPen*.46f,5f*s);by+=sy/sl*Math.min(maxPen*.46f,5f*s);}
                bvx*=.72f;bvy*=.72f;limitBallSpeed(410f*s);
                return;
            }
            float dvx=0f,dvy=0f;
            for(int i=0;i<n;i++){
                Disc d=cs[i];float move=pen[i];
                bx+=nx[i]*move*.68f;by+=ny[i]*move*.68f;
                d.x-=nx[i]*move*.32f;d.y-=ny[i]*move*.32f;clampDisc(d);
                float rel=(bvx-d.vx)*nx[i]+(bvy-d.vy)*ny[i];
                if(rel<0f){float imp=Math.min(-rel*.86f,38f*s);dvx+=nx[i]*imp;dvy+=ny[i]*imp;}
            }
            float dl=len(dvx,dvy),cap=54f*s;if(dl>cap&&dl>0f){dvx=dvx/dl*cap;dvy=dvy/dl*cap;}
            bvx+=dvx;bvy+=dvy;
        }

'''
    if marker not in s:raise RuntimeError('physicsStep marker missing')
    s=s.replace(marker,helper+marker,1)

physics = r'''        void physicsStep(float dt){
            for(int i=0;i<teamSize;i++){
                Disc a=blue[i],b=red[i];
                a.x+=a.vx*dt;a.y+=a.vy*dt;b.x+=b.vx*dt;b.y+=b.vy*dt;
                clampDisc(a);clampDisc(b);
            }
            for(int pass=0;pass<3;pass++)resolveAllDiscCollisions();

            lastBallX=bx;lastBallY=by;
            bx+=bvx*dt;by+=bvy*dt;
            float fr=(float)Math.pow(.9850,dt*60f);bvx*=fr;bvy*=fr;

            int bs=blueScore,rs=redScore;
            for(int pass=0;pass<3;pass++){
                solveBallContactsV25();
                handleBallWalls();
                if(blueScore!=bs||redScore!=rs)return;
            }
            limitBallSpeed(690f*s);

            float moved=dist(lastBallX,lastBallY,bx,by);
            if(moved>.001f){
                float sign=(Math.abs(bvx)>Math.abs(bvy))?(bvx>=0?1f:-1f):(bvy>=0?-1f:1f);
                ballAngle+=sign*(moved/Math.max(1f,ballR))*57.2958f;
            }
            emitMotionTrail(dt);
        }'''
s = replace_method(s, 'physicsStep', physics)

# Keep the v2.4 goal rule: score as soon as the whole ball is behind the front
# goal line between the posts. Update app identity for side-by-side testing.
s = s.replace('circle_football_v24','circle_football_v25')
path.write_text(s,encoding='utf-8')

manifest=Path('AndroidManifest.xml')
m=manifest.read_text(encoding='utf-8')
m=m.replace('com.godnit.circlefootballlite.v24','com.godnit.circlefootballlite.v25')
m=re.sub(r'android:versionCode="\d+"','android:versionCode="16"',m,count=1)
m=re.sub(r'android:versionName="[^"]+"','android:versionName="2.5.0"',m,count=1)
manifest.write_text(m,encoding='utf-8')

print('Applied Circle Football v2.5 smaller scale, classic goals, human guide, smarter AI and stable squeeze contacts')
