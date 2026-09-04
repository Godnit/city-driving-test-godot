from pathlib import Path

path = Path('src/com/godnit/circlefootballlite/MainActivity.java')
s = path.read_text(encoding='utf-8')


def replace_method(text, name, replacement):
    needle = name + '('
    pos = text.find(needle)
    if pos < 0:
        raise RuntimeError('method not found: ' + name)
    line_start = text.rfind('\n', 0, pos) + 1
    brace = text.find('{', pos)
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

# Version-specific preferences and background audio state.
s = s.replace('circle_football_v16', 'circle_football_v17')
s = s.replace(
    '        float touchSoundCooldown=0f, wallSoundCooldown=0f;\n',
    '        float touchSoundCooldown=0f, wallSoundCooldown=0f;\n'
    '        volatile boolean ambientRunning=false;\n'
    '        Thread ambientThread;\n'
    '        volatile float crowdExcitement=0f;\n'
)

on_size = r'''        @Override protected void onSizeChanged(int ww,int hh,int oldw,int oldh){
            w=ww;h=hh;
            s=Math.max(0.60f,Math.min(w/1280f,h/720f));
            configureField();
            pauseButton.set(w-78*s,18*s,w-18*s,78*s);
            updateControlRects();
            resetPositions();
        }

        void configureField(){
            float mxRatio=teamSize>=3?.045f:.065f;
            float myRatio=teamSize>=3?.082f:.105f;
            float mx=w*mxRatio,my=h*myRatio;
            pitch.set(mx,my,w-mx,h-my);
            goalHalf=pitch.height()*.19f;
            float scale=teamSize>=4?.80f:(teamSize==3?.88f:1f);
            discR=29f*s*scale;
            ballR=15f*s*(teamSize>=4?.86f:(teamSize==3?.92f:1f));
        }'''
s = replace_method(s, 'onSizeChanged', on_size)

player_card = r'''        void playerCard(Canvas c,float x,float y,float ww,float hh,String name,int team,int idx){
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(39,45,56));
            c.drawRoundRect(new RectF(x,y,x+ww,y+hh),14*s,14*s,p);
            boolean active=idx<teamSize;
            p.setColor(active?(team==0?Color.rgb(36,104,235):Color.rgb(239,57,61)):Color.rgb(76,81,91));
            c.drawCircle(x+37*s,y+hh/2f,22*s,p);
            p.setColor(active?Color.WHITE:Color.rgb(155,160,170));p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextAlign(Paint.Align.LEFT);p.setTextSize(19*s);
            c.drawText(name,x+76*s,y+31*s,p);
            String role;
            if(!active) role="RESERVE";
            else if(idx==0&&team==0) role="YOU • ATTACKER";
            else if(idx==0) role="STRIKER • ATTACK";
            else if(idx==teamSize-1) role="GOALKEEPER • GUARD / CLEAR";
            else role="DEFENDER • ZONE / PASS";
            p.setTypeface(Typeface.DEFAULT);p.setTextSize(14*s);p.setColor(Color.rgb(155,170,190));
            c.drawText(role,x+76*s,y+55*s,p);
        }'''
s = replace_method(s, 'playerCard', player_card)

# Make the home subtitle accurately describe the new role-based model.
s = s.replace('OFFLINE TEAM EDITION', 'OFFLINE ROLE-BASED FOOTBALL')
s = s.replace('Roles adapt during the match. Only the nearest player presses the ball.',
              'Striker attacks. Defenders hold zones. Goalkeeper guards the goal.')

update_game = r'''        void updateGame(float dt){
            if(!goldenGoal){
                matchTime-=dt;
                if(matchTime<=0){
                    matchTime=0;
                    if(blueScore==redScore) goldenGoal=true; else finishMatch();
                }
            }
            if(mode!=GAME)return;
            for(int i=0;i<teamSize;i++){
                blue[i].kickCd=Math.max(0,blue[i].kickCd-dt);
                red[i].kickCd=Math.max(0,red[i].kickCd-dt);
            }
            wallSoundCooldown=Math.max(0,wallSoundCooldown-dt);
            touchSoundCooldown=Math.max(0,touchSoundCooldown-dt);

            updateHuman(dt);
            chooseChasers();
            updateTeamAI(blue,red,0,blueChaser,dt);
            updateTeamAI(red,blue,1,redChaser,dt);

            int steps=Math.max(2,Math.min(10,(int)Math.ceil(dt/0.0042f)));
            float sub=dt/steps;
            for(int st=0;st<steps;st++) physicsStep(sub);
            updateParticles(dt);

            float near=Math.min(Math.abs(bx-pitch.left),Math.abs(pitch.right-bx))/Math.max(1f,pitch.width());
            float threat=clamp((.34f-near)/.34f,0f,1f);
            float speedBoost=clamp(len(bvx,bvy)/(850*s),0f,1f)*.30f;
            crowdExcitement=clamp(threat+speedBoost,0f,1f);
        }'''
s = replace_method(s, 'updateGame', update_game)

choose_chasers = r'''        void chooseChasers(){
            float leftDanger=pitch.left+pitch.width()*.30f;
            float leftBox=pitch.left+pitch.width()*.15f;
            float rightDanger=pitch.right-pitch.width()*.30f;
            float rightBox=pitch.right-pitch.width()*.15f;

            // Blue: the human is the permanent attacker. AI only steps out when defending its own goal.
            blueChaser=-1;
            if(teamSize>=2 && bx<leftDanger){
                if(bx<leftBox) blueChaser=teamSize-1; // goalkeeper attacks only inside the danger box
                else if(teamSize>=3) blueChaser=closestRangeToBall(blue,1,teamSize-1);
                else blueChaser=teamSize-1;
            }

            // Red: index 0 is the permanent striker. Defenders/GK take over only in their defensive third.
            redChaser=0;
            if(teamSize>=2 && bx>rightDanger){
                if(bx>rightBox) redChaser=teamSize-1;
                else if(teamSize>=3) redChaser=closestRangeToBall(red,1,teamSize-1);
            }
        }

        int closestRangeToBall(Disc[] t,int start,int endExclusive){
            if(start>=endExclusive)return start;
            int best=start;float bd=Float.MAX_VALUE;
            for(int i=start;i<endExclusive;i++){
                float d2=sq(t[i].x-bx)+sq(t[i].y-by);
                if(d2<bd){bd=d2;best=i;}
            }
            return best;
        }'''
s = replace_method(s, 'chooseChasers', choose_chasers)

update_team = r'''        void updateTeamAI(Disc[] team,Disc[] opp,int teamId,int chaser,float dt){
            for(int i=0;i<teamSize;i++){
                Disc d=team[i];
                if(!d.ai)continue;
                float tx,ty;
                if(i==chaser){
                    if(d.kickCd>.17f){
                        float[] hold=formationTarget(teamId,i,chaser);
                        tx=hold[0];ty=hold[1];
                    }else{
                        float[] target=chooseKickTarget(d,team,opp,teamId);
                        float dx=target[0]-bx,dy=target[1]-by,ll=len(dx,dy);if(ll<1)ll=1;
                        float dirX=dx/ll,dirY=dy/ll;
                        float behind=discR+ballR+(ballNearWall()?18*s:9*s);
                        float rawX=bx-dirX*behind,rawY=by-dirY*behind;
                        tx=clamp(rawX,pitch.left+discR,pitch.right-discR);
                        ty=clamp(rawY,pitch.top+discR,pitch.bottom-discR);

                        // If the ideal point is outside the pitch, orbit beside the ball instead of pinning it into the wall.
                        if(Math.abs(tx-rawX)>3*s || Math.abs(ty-rawY)>3*s){
                            float sideX=-dirY,sideY=dirX;
                            float centerSide=(pitch.centerX()-bx)*sideX+(pitch.centerY()-by)*sideY;
                            if(centerSide<0){sideX=-sideX;sideY=-sideY;}
                            tx=clamp(bx+sideX*behind*1.05f,pitch.left+discR,pitch.right-discR);
                            ty=clamp(by+sideY*behind*1.05f,pitch.top+discR,pitch.bottom-discR);
                        }

                        float bd=dist(d.x,d.y,bx,by);
                        float cdx=bx-d.x,cdy=by-d.y,cl=len(cdx,cdy);if(cl<1)cl=1;
                        float align=(cdx/cl)*dirX+(cdy/cl)*dirY;
                        if(bd<=kickReach() && align>.84f && d.kickCd<=0f){
                            boolean isPass=target[2]>.5f;
                            cpuKick(d,isPass?575*s:(difficulty==0?570*s:difficulty==1?635*s:690*s),dirX,dirY,isPass);
                        }
                    }
                }else{
                    float[] pos=formationTarget(teamId,i,chaser);
                    tx=pos[0];ty=pos[1];
                    // Non-chasers deliberately keep a bubble around the ball so teammates never surround it.
                    float minSpace=discR*(i==teamSize-1?4.0f:3.5f);
                    float db=dist(d.x,d.y,bx,by);
                    if(db<minSpace){
                        float awayX=d.x-bx,awayY=d.y-by,al=len(awayX,awayY);if(al<1)al=1;
                        tx+=awayX/al*(minSpace-db+30*s);
                        ty+=awayY/al*(minSpace-db+30*s);
                    }
                }
                moveAiToward(d,tx,ty,dt);
            }
        }

        boolean ballNearWall(){
            float m=ballR+9*s;
            return bx<pitch.left+m || bx>pitch.right-m || by<pitch.top+m || by>pitch.bottom-m;
        }'''
s = replace_method(s, 'updateTeamAI', update_team)

choose_target = r'''        float[] chooseKickTarget(Disc d,Disc[] team,Disc[] opp,int teamId){
            float goalX=teamId==0?pitch.right+35*s:pitch.left-35*s;
            float goalY=pitch.centerY();
            int passTo=bestPassTarget(d,team,opp,teamId);
            boolean keeper=d.index==teamSize-1 && teamSize>=2;
            boolean defender=d.index>0 && !keeper;

            // Keeper and defenders prefer a safe outlet to the striker instead of blindly shooting the whole field.
            if((keeper||defender) && passTo>=0){
                Disc mate=team[passTo];
                return new float[]{mate.x+mate.vx*.20f,mate.y+mate.vy*.20f,1f};
            }

            Disc blocker=nearestOpponentToLine(opp,bx,by,goalX,goalY);
            if(blocker!=null && distToSegment(blocker.x,blocker.y,bx,by,goalX,goalY)<discR*2.0f){
                goalY=clamp(pitch.centerY()+(blocker.y<pitch.centerY()?goalHalf*.62f:-goalHalf*.62f),
                        pitch.centerY()-goalHalf*.75f,pitch.centerY()+goalHalf*.75f);
            }

            int crowd=countOpponentsNear(opp,d.x,d.y,130*s);
            boolean laneBlocked=isLaneBlocked(opp,bx,by,goalX,goalY,discR*1.8f);
            boolean farFromGoal=teamId==0?bx<pitch.right-pitch.width()*.32f:bx>pitch.left+pitch.width()*.32f;
            if(passTo>=0 && (crowd>=1 || (laneBlocked&&farFromGoal))){
                Disc mate=team[passTo];
                return new float[]{mate.x+mate.vx*.20f,mate.y+mate.vy*.20f,1f};
            }
            return new float[]{goalX,goalY,0f};
        }'''
s = replace_method(s, 'chooseKickTarget', choose_target)

best_pass = r'''        int bestPassTarget(Disc d,Disc[] team,Disc[] opp,int teamId){
            int best=-1;float bestScore=-99999;
            for(int i=0;i<teamSize;i++){
                Disc m=team[i];if(m==d)continue;
                float passDist=dist(d.x,d.y,m.x,m.y);
                if(passDist<85*s||passDist>pitch.width()*.65f)continue;
                if(isLaneBlocked(opp,bx,by,m.x,m.y,discR*1.28f))continue;
                float open=nearestOpponentDistance(opp,m.x,m.y);
                float forward=teamId==0?(m.x-d.x):(d.x-m.x);
                float score=open*.70f+forward*.27f-passDist*.07f;
                if(i==0)score+=95*s; // striker/human is the preferred outlet
                if(i==teamSize-1 && teamSize>=2)score-=70*s; // avoid needless back-passes to GK
                if(score>bestScore){bestScore=score;best=i;}
            }
            return best;
        }'''
s = replace_method(s, 'bestPassTarget', best_pass)

formation = r'''        float[] formationTarget(int teamId,int idx,int chaser){
            float ownX=teamId==0?pitch.left:pitch.right;
            float sign=teamId==0?1f:-1f;
            float x,y;

            if(idx==0){ // permanent striker / human outlet
                x=pitch.centerX()+sign*pitch.width()*.15f;
                y=clamp(by,pitch.top+pitch.height()*.24f,pitch.bottom-pitch.height()*.24f);
            }else if(idx==teamSize-1 && teamSize>=2){ // goalkeeper
                x=ownX+sign*pitch.width()*.075f;
                y=clamp(by,pitch.centerY()-goalHalf*.65f,pitch.centerY()+goalHalf*.65f);
            }else{ // zonal defenders
                int defenders=Math.max(1,teamSize-2);
                int slot=idx-1;
                float frac=(slot+1f)/(defenders+1f);
                x=ownX+sign*pitch.width()*(.23f+slot*.035f);
                float zoneY=pitch.top+pitch.height()*frac;
                float follow=clamp(by,pitch.top+discR,pitch.bottom-discR);
                y=zoneY*.62f+follow*.38f;
            }
            return new float[]{clamp(x,pitch.left+discR,pitch.right-discR),clamp(y,pitch.top+discR,pitch.bottom-discR)};
        }'''
s = replace_method(s, 'formationTarget', formation)

cpu_kick = r'''        void cpuKick(Disc d,float power,float desiredX,float desiredY,boolean pass){
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);if(l<1)l=1;
            float nx=dx/l,ny=dy/l;
            float align=nx*desiredX+ny*desiredY;
            if(align<.82f || l>kickReach())return;
            // Kick impulse is constrained by actual contact direction; there are no remote or reverse shots.
            float ix=nx*.82f+desiredX*.18f,iy=ny*.82f+desiredY*.18f,il=len(ix,iy);if(il<1)il=1;
            ix/=il;iy/=il;
            bvx += ix*power + d.vx*.12f;
            bvy += iy*power + d.vy*.12f;
            limitBallSpeed(900*s);
            d.kickCd=pass?.46f:.36f;
            spawnKickBurst(ix,iy,power);
            playSfx(pass?SFX_PASS:SFX_KICK);
        }'''
s = replace_method(s, 'cpuKick', cpu_kick)

kick_reach = r'''        float kickReach(){return discR+ballR+19*s;}'''
s = replace_method(s, 'kickReach', kick_reach)

physics = r'''        void physicsStep(float dt){
            for(int i=0;i<teamSize;i++){
                Disc a=blue[i],b=red[i];
                a.x+=a.vx*dt;a.y+=a.vy*dt;
                b.x+=b.vx*dt;b.y+=b.vy*dt;
                clampDisc(a);clampDisc(b);
            }
            for(int pass=0;pass<3;pass++) resolveAllDiscCollisions();

            lastBallX=bx;lastBallY=by;
            bx+=bvx*dt;by+=bvy*dt;
            float fr=(float)Math.pow(.9885,dt*60f);bvx*=fr;bvy*=fr;

            // Alternate player and wall constraints. This prevents the wall from pushing the ball back inside a player.
            for(int pass=0;pass<5;pass++){
                for(int i=0;i<teamSize;i++){resolveBallDisc(blue[i]);resolveBallDisc(red[i]);}
                handleBallWalls();
                resolveWallPin();
            }
            limitBallSpeed(920*s);

            float moved=dist(lastBallX,lastBallY,bx,by);
            if(moved>0.001f){
                float cross=bvx*(by-lastBallY)-bvy*(bx-lastBallX);
                float sign=cross>=0?1f:-1f;
                if(Math.abs(cross)<.01f)sign=(bvx+bvy)>=0?1f:-1f;
                ballAngle += sign*(moved/Math.max(1f,ballR))*57.2958f;
            }
            emitMotionTrail(dt);
        }'''
s = replace_method(s, 'physicsStep', physics)

resolve_ball = r'''        void resolveBallDisc(Disc d){
            float dx=bx-d.x,dy=by-d.y,min=discR+ballR,dst=len(dx,dy);
            if(dst>=min)return;
            float nx,ny;
            if(dst<.001f){
                float vx=bx-pitch.centerX(),vy=by-pitch.centerY(),vl=len(vx,vy);
                if(vl<.1f){vx=d.team==0?1f:-1f;vy=0;vl=1;}
                nx=vx/vl;ny=vy/vl;dst=.001f;
            }else{nx=dx/dst;ny=dy/dst;}
            float overlap=min-dst+1.0f*s;

            // Share correction with the player near walls instead of forcing the ball deeper into an impossible gap.
            boolean tight=bx<pitch.left+ballR+2*s||bx>pitch.right-ballR-2*s||by<pitch.top+ballR+2*s||by>pitch.bottom-ballR-2*s;
            float ballShare=tight?.70f:.92f;
            bx+=nx*overlap*ballShare;by+=ny*overlap*ballShare;
            d.x-=nx*overlap*(1f-ballShare);d.y-=ny*overlap*(1f-ballShare);clampDisc(d);

            float rel=(bvx-d.vx)*nx+(bvy-d.vy)*ny;
            if(rel<0){
                float impulse=-1.48f*rel;
                bvx+=nx*impulse+d.vx*.08f;
                bvy+=ny*impulse+d.vy*.08f;
            }
        }

        void resolveWallPin(){
            float eps=2.5f*s;
            for(int team=0;team<2;team++){
                Disc[] arr=team==0?blue:red;
                for(int i=0;i<teamSize;i++){
                    Disc d=arr[i];
                    if(dist(d.x,d.y,bx,by)>discR+ballR+4*s)continue;
                    float push=95*s;
                    if(by<=pitch.top+ballR+eps && d.y>by){
                        bvy=Math.max(bvy,push);
                        bvx+=(bx<pitch.centerX()?1f:-1f)*push*.58f;
                        by+=.8f*s;
                    }
                    if(by>=pitch.bottom-ballR-eps && d.y<by){
                        bvy=Math.min(bvy,-push);
                        bvx+=(bx<pitch.centerX()?1f:-1f)*push*.58f;
                        by-=.8f*s;
                    }
                    if(bx<=pitch.left+ballR+eps && d.x>bx){
                        bvx=Math.max(bvx,push);
                        bvy+=(by<pitch.centerY()?1f:-1f)*push*.58f;
                        bx+=.8f*s;
                    }
                    if(bx>=pitch.right-ballR-eps && d.x<bx){
                        bvx=Math.min(bvx,-push);
                        bvy+=(by<pitch.centerY()?1f:-1f)*push*.58f;
                        bx-=.8f*s;
                    }
                }
            }
        }

        void limitBallSpeed(float max){
            float l=len(bvx,bvy);if(l>max&&l>0){bvx=bvx/l*max;bvy=bvy/l*max;}
        }'''
s = replace_method(s, 'resolveBallDisc', resolve_ball)

emit_trail = r'''        void emitMotionTrail(float dt){
            float speed=len(bvx,bvy);
            if(speed<220*s){trailCarry=0;return;}
            trailCarry+=speed*dt;
            float spacing=speed>650*s?8*s:(speed>420*s?12*s:17*s);
            while(trailCarry>=spacing){
                trailCarry-=spacing;
                float l=Math.max(1f,speed),nx=bvx/l,ny=bvy/l;
                float jitter=(rng.nextFloat()-.5f)*ballR*.85f;
                float px=bx-nx*(ballR+5*s)-ny*jitter;
                float py=by-ny*(ballR+5*s)+nx*jitter;
                float life=.20f+clamp(speed/(900*s),0,1)*.22f;
                particles.add(new Particle(px,py,-nx*(55+speed*.12f)-ny*jitter*2f,-ny*(55+speed*.12f)+nx*jitter*2f,
                        life,(1.8f+rng.nextFloat()*2.6f)*s));
                if(particles.size()>120)particles.remove(0);
            }
        }'''
s = replace_method(s, 'emitMotionTrail', emit_trail)

draw_particles = r'''        void drawParticles(Canvas c){
            for(int i=0;i<particles.size();i++){
                Particle q=particles.get(i);
                float a=clamp(q.life/q.maxLife,0f,1f);
                float speed=len(q.vx,q.vy);
                float l=Math.max(1f,speed),nx=q.vx/l,ny=q.vy/l;
                float tail=(7f+Math.min(28f,speed*.045f))*s;
                p.setStrokeWidth(Math.max(1f,q.radius*a*1.35f));
                p.setStrokeCap(Paint.Cap.ROUND);
                p.setColor(Color.argb((int)(80*a),120,190,255));
                c.drawLine(q.x,q.y,q.x-nx*tail,q.y-ny*tail,p);
                p.setStrokeWidth(Math.max(1f,q.radius*a*.62f));
                p.setColor(Color.argb((int)(185*a),242,247,255));
                c.drawLine(q.x,q.y,q.x-nx*tail*.72f,q.y-ny*tail*.72f,p);
                p.setColor(Color.argb((int)(90*a),255,255,255));
                c.drawCircle(q.x,q.y,q.radius*.48f*a,p);
            }
            p.setStrokeCap(Paint.Cap.BUTT);
        }'''
s = replace_method(s, 'drawParticles', draw_particles)

draw_ball = r'''        void drawFootball(Canvas c,float x,float y,float r,float angle){
            c.save();c.rotate(angle,x,y);
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.argb(90,0,0,0));c.drawCircle(x+2.2f*s,y+3.2f*s,r*1.04f,p);
            p.setColor(Color.rgb(247,248,246));c.drawCircle(x,y,r,p);
            stroke.setStyle(Paint.Style.STROKE);stroke.setStrokeWidth(Math.max(1f,1.15f*s));stroke.setColor(Color.rgb(42,45,48));
            c.drawCircle(x,y,r,stroke);
            polygon(c,x,y,r*.31f,5,-90f,Color.rgb(22,24,27),true);
            for(int i=0;i<5;i++){
                double a=Math.toRadians(-90+i*72);
                float px=x+(float)Math.cos(a)*r*.70f,py=y+(float)Math.sin(a)*r*.70f;
                polygon(c,px,py,r*.19f,5,-90f+i*72,Color.rgb(30,32,35),true);
                stroke.setColor(Color.rgb(86,89,92));stroke.setStrokeWidth(Math.max(1f,.72f*s));
                c.drawLine(x+(float)Math.cos(a)*r*.30f,y+(float)Math.sin(a)*r*.30f,px,py,stroke);
                double b=Math.toRadians(-90+i*72+36);
                c.drawLine(px,py,x+(float)Math.cos(b)*r*.96f,y+(float)Math.sin(b)*r*.96f,stroke);
            }
            p.setColor(Color.argb(105,255,255,255));c.drawCircle(x-r*.31f,y-r*.36f,r*.25f,p);
            c.restore();
        }'''
s = replace_method(s, 'drawFootball', draw_ball)

do_kick = r'''        void doKick(){
            Disc d=blue[0];if(d.kickCd>0)return;
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);
            if(l>kickReach())return;
            if(l<1)l=1;
            float nx=dx/l,ny=dy/l;
            float power=715*s;
            bvx+=nx*power+d.vx*.16f;bvy+=ny*power+d.vy*.16f;
            limitBallSpeed(920*s);
            d.kickCd=.27f;
            spawnKickBurst(nx,ny,power);
            haptic(20);playSfx(SFX_KICK);
        }'''
s = replace_method(s, 'doKick', do_kick)

reset_positions = r'''        void resetPositions(){
            if(w<=0||h<=0)return;
            float cy=pitch.centerY();
            for(int i=0;i<4;i++){
                float lane=((i%3)-1)*pitch.height()*.22f;
                blue[i].x=pitch.left+pitch.width()*(i==0?.28f:(i==teamSize-1?.075f:.23f));
                red[i].x=pitch.right-pitch.width()*(i==0?.28f:(i==teamSize-1?.075f:.23f));
                blue[i].y=clamp(cy+(i==0?pitch.height()*.10f:lane),pitch.top+discR,pitch.bottom-discR);
                red[i].y=clamp(cy+(i==0?-pitch.height()*.10f:lane),pitch.top+discR,pitch.bottom-discR);
                blue[i].vx=blue[i].vy=red[i].vx=red[i].vy=0;
                blue[i].kickCd=red[i].kickCd=.20f;
            }
            bx=pitch.centerX();by=cy;bvx=bvy=0;ballAngle=0;particles.clear();trailCarry=0;crowdExcitement=.05f;
            for(int i=0;i<teamSize;i++){separateFromBall(blue[i]);separateFromBall(red[i]);}
        }'''
s = replace_method(s, 'resetPositions', reset_positions)

start_match = r'''        void startMatch(){
            configureField();updateControlRects();
            blueScore=redScore=0;matchTime=180f;goldenGoal=false;savedResult=false;
            mode=GAME;lastFrame=System.nanoTime();
            joyPointer=-1;joyNX=joyNY=0;joyX=joyBaseX;joyY=joyBaseY;
            prefs.edit().putInt("difficulty",difficulty).putInt("team_size",teamSize).putInt("target_goals",targetGoals).apply();
            resetPositions();playSfx(SFX_MENU);
        }'''
s = replace_method(s, 'startMatch', start_match)

# Reconfigure field immediately when team size changes in setup.
s = s.replace(
    'if(id.startsWith("team")){teamSize=clampInt(Integer.parseInt(id.substring(4)),1,4);prefs.edit().putInt("team_size",teamSize).apply();playSfx(SFX_MENU);return;}',
    'if(id.startsWith("team")){teamSize=clampInt(Integer.parseInt(id.substring(4)),1,4);prefs.edit().putInt("team_size",teamSize).apply();configureField();updateControlRects();resetPositions();playSfx(SFX_MENU);return;}'
)

make_sfx = r'''        short[] makeSfx(int type){
            int ms=(type==SFX_GOAL?900:(type==SFX_WIN||type==SFX_LOSE?650:(type==SFX_KICK?120:(type==SFX_PASS?85:60))));
            int sr=22050,n=sr*ms/1000;short[] out=new short[n];
            Random rr=new Random(type*911L+System.nanoTime());
            for(int i=0;i<n;i++){
                double t=i/(double)sr,env=Math.max(0,1-i/(double)n),v=0;
                if(type==SFX_KICK){
                    double thump=Math.sin(2*Math.PI*(105-40*i/(double)n)*t)*Math.pow(env,1.55)*.78;
                    double snap=(rr.nextDouble()*2-1)*Math.pow(env,6)*.24;
                    v=thump+snap;
                }else if(type==SFX_PASS){
                    v=Math.sin(2*Math.PI*185*t)*Math.pow(env,2.3)*.36+(rr.nextDouble()*2-1)*Math.pow(env,5)*.08;
                }else if(type==SFX_WALL){
                    v=Math.sin(2*Math.PI*470*t)*Math.pow(env,2.8)*.31+Math.sin(2*Math.PI*760*t)*Math.pow(env,3.2)*.12;
                }else if(type==SFX_GOAL){
                    double roar=(rr.nextDouble()*2-1)*(.23+.42*Math.sin(Math.PI*Math.min(1,t/.55)))*env;
                    double horn=Math.sin(2*Math.PI*(t<.30?392:523)*t)*env*.19;
                    v=roar+horn;
                }else if(type==SFX_WIN){
                    double roar=(rr.nextDouble()*2-1)*.28*env;
                    double f=t<.18?523:(t<.36?659:784);v=roar+Math.sin(2*Math.PI*f*t)*env*.34;
                }else if(type==SFX_LOSE){
                    v=Math.sin(2*Math.PI*(t<.20?294:(t<.40?247:196))*t)*env*.30+(rr.nextDouble()*2-1)*.08*env;
                }else v=Math.sin(2*Math.PI*690*t)*env*.30;
                out[i]=(short)(clamp((float)v,-1,1)*27500);
            }
            return out;
        }'''
s = replace_method(s, 'makeSfx', make_sfx)

ambient_methods = r'''
        void ensureAmbient(){
            if(ambientRunning||!sounds)return;
            ambientRunning=true;
            ambientThread=new Thread(new Runnable(){@Override public void run(){
                AudioTrack tr=null;
                try{
                    final int sr=16000;
                    int min=AudioTrack.getMinBufferSize(sr,AudioFormat.CHANNEL_OUT_MONO,AudioFormat.ENCODING_PCM_16BIT);
                    tr=new AudioTrack(AudioManager.STREAM_MUSIC,sr,AudioFormat.CHANNEL_OUT_MONO,AudioFormat.ENCODING_PCM_16BIT,
                            Math.max(min,4096),AudioTrack.MODE_STREAM);
                    tr.play();
                    short[] buf=new short[512];
                    Random rr=new Random();
                    double phase=0,beat=0;
                    while(ambientRunning&&sounds){
                        boolean match=(mode==GAME||mode==PAUSE||mode==RESULT);
                        float excitement=match?crowdExcitement:0f;
                        for(int i=0;i<buf.length;i++){
                            double t=(phase+i)/sr;
                            double v;
                            if(match){
                                double noise=rr.nextDouble()*2-1;
                                double wave=Math.sin(2*Math.PI*95*t)*.035+Math.sin(2*Math.PI*137*t)*.025;
                                double amp=.035+excitement*.105;
                                v=noise*amp+wave*(.35+excitement);
                            }else{
                                double pulse=.55+.45*Math.sin(2*Math.PI*.55*t);
                                double chord=Math.sin(2*Math.PI*196*t)+.55*Math.sin(2*Math.PI*247*t)+.42*Math.sin(2*Math.PI*294*t);
                                double bass=Math.sin(2*Math.PI*98*t);
                                double kick=Math.sin(2*Math.PI*52*t)*Math.pow(Math.max(0,Math.sin(2*Math.PI*1.10*t)),10);
                                v=chord*.032*pulse+bass*.025+kick*.045;
                            }
                            buf[i]=(short)(clamp((float)v,-1,1)*24000);
                        }
                        phase+=buf.length;beat+=buf.length;
                        tr.write(buf,0,buf.length);
                    }
                }catch(Exception ignored){}finally{
                    if(tr!=null){try{tr.stop();}catch(Exception ignored){}try{tr.release();}catch(Exception ignored){}}
                    ambientRunning=false;
                }
            }},"cf-ambient");
            ambientThread.start();
        }

        void stopAmbient(){
            ambientRunning=false;
            Thread t=ambientThread;ambientThread=null;
            if(t!=null)t.interrupt();
        }

        @Override protected void onDetachedFromWindow(){
            stopAmbient();
            super.onDetachedFromWindow();
        }
'''
marker = '        String difficultyName(){'
if marker not in s:
    raise RuntimeError('ambient insertion marker missing')
s = s.replace(marker, ambient_methods + '\n' + marker)

# Keep ambient thread synchronized with the sound toggle and screen lifecycle.
s = s.replace('            hits.clear();\n', '            hits.clear();\n            if(sounds)ensureAmbient();else stopAmbient();\n', 1)
s = s.replace('if(id.equals("sounds")){sounds=!sounds;prefs.edit().putBoolean("sounds",sounds).apply();if(sounds)playSfx(SFX_MENU);return;}',
              'if(id.equals("sounds")){sounds=!sounds;prefs.edit().putBoolean("sounds",sounds).apply();if(sounds){ensureAmbient();playSfx(SFX_MENU);}else stopAmbient();return;}')

path.write_text(s, encoding='utf-8')
print('Applied Circle Football v1.7 role AI / anti-pin / stadium audio patch')
