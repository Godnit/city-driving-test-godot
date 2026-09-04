from pathlib import Path
import re

path = Path('src/com/godnit/circlefootballlite/MainActivity.java')
s = path.read_text(encoding='utf-8')

# HaxBall-like size ratio: default HaxBall uses a noticeably larger ball relative to the player.
s = s.replace('ballR = 14f * s;', 'ballR = 18f * s;')

new_update = r'''        private void updateGame(float dt) {
            kickCooldown = Math.max(0f, kickCooldown-dt);
            cpuKickCooldown = Math.max(0f, cpuKickCooldown-dt);
            touchSoundCooldownV13 = Math.max(0f, touchSoundCooldownV13-dt);
            wallSoundCooldown = Math.max(0f, wallSoundCooldown-dt);
            if (!training && !goldenGoal) {
                matchTime -= dt;
                if (matchTime <= 0f) {
                    matchTime = 0f;
                    if (blueScore == redScore) goldenGoal = true;
                    else finishMatch();
                }
            }

            // Small fixed-ish substeps keep disc/ball contacts stable and make dribbling feel like HaxBall.
            int steps = Math.max(1, Math.min(5, (int)Math.ceil(dt / (1f/120f))));
            float sub = dt / steps;
            for (int i=0; i<steps && (mode==GAME || mode==TRAINING); i++) physicsStepV13(sub);
        }
'''

s, n = re.subn(r'        private void updateGame\(float dt\) \{.*?\n        \}\n\n        private void collideDiscs\(\)',
                new_update + '\n        private void collideDiscs()', s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('Could not replace updateGame')

new_kick = r'''        private void doKick() {
            if (kickCooldown > 0f) return;
            float dx = bx-px, dy = by-py;
            float d = len(dx,dy);
            float reach = discR + ballR + 11*s;
            if (d < reach && d > 0.001f) {
                float nx = dx/d, ny = dy/d;
                // HaxBall-style kick: force is applied away from the player's centre,
                // while the ball remains a completely independent physical disc.
                float impulse = 405*s;
                bvx += nx*impulse + pvx*0.10f;
                bvy += ny*impulse + pvy*0.10f;
                pvx -= nx*24*s;
                pvy -= ny*24*s;
                ballOwner = 0;
                possessionLock = 0f;
                kickCooldown = 0.14f;
                haptic(18);
                playSfx(SFX_KICK);
            }
        }
'''

s, n = re.subn(r'        private void doKick\(\) \{.*?\n        \}\n\n        private void haptic',
                new_kick + '\n        private void haptic', s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('Could not replace doKick')

# Add two light state variables using fields that do not affect saved data.
anchor = '        private float wallSoundCooldown = 0f;\n'
if anchor not in s:
    raise SystemExit('Field anchor missing')
s = s.replace(anchor, anchor + '        private float touchSoundCooldownV13 = 0f;\n        private float cpuDecisionTimerV13 = 0f;\n', 1)

helpers = r'''
        private void physicsStepV13(float dt) {
            applyPlayerMotionV13(dt);
            if (!training) applyCpuMotionV13(dt);

            px += pvx*dt;
            py += pvy*dt;
            clampDisc(true);
            if (!training) {
                cx += cvx*dt;
                cy += cvy*dt;
                clampDisc(false);
                collidePlayersV13();
            }

            bx += bvx*dt;
            by += bvy*dt;
            float ballDamp = (float)Math.pow(0.99, dt*60f);
            bvx *= ballDamp;
            bvy *= ballDamp;

            collideBallV13(true);
            if (!training) collideBallV13(false);
            if (!training) maybeCpuKickV13();
            handleBallWalls();
        }

        private void applyPlayerMotionV13(float dt) {
            float damp = (float)Math.pow(0.96, dt*60f);
            pvx *= damp;
            pvy *= damp;
            float accel = 720*s;
            pvx += joyNX*accel*dt;
            pvy += joyNY*accel*dt;
            float cap = 315*s;
            float sp = len(pvx,pvy);
            if (sp > cap) { pvx = pvx/sp*cap; pvy = pvy/sp*cap; }
        }

        private void applyCpuMotionV13(float dt) {
            cpuDecisionTimerV13 -= dt;
            cpuLaneTimer -= dt;
            float prediction = difficulty==0 ? 0.05f : (difficulty==1 ? 0.13f : 0.22f);
            float pbx = bx + bvx*prediction;
            float pby = clamp(by + bvy*prediction, pitch.top+ballR, pitch.bottom-ballR);

            if (cpuLaneTimer <= 0f) {
                cpuLaneTimer = difficulty==2 ? 0.38f : (difficulty==1 ? 0.55f : 0.82f);
                float topAim = pitch.centerY()-goalHalf*0.62f;
                float bottomAim = pitch.centerY()+goalHalf*0.62f;
                boolean topBlocked = isPlayerBlockingLane(bx,by,pitch.left,topAim);
                boolean bottomBlocked = isPlayerBlockingLane(bx,by,pitch.left,bottomAim);
                if (topBlocked && !bottomBlocked) cpuLaneY = bottomAim;
                else if (bottomBlocked && !topBlocked) cpuLaneY = topAim;
                else cpuLaneY = (py < pitch.centerY() ? bottomAim : topAim) + (rng.nextFloat()*2f-1f)*goalHalf*0.10f;
            }

            float tx, ty;
            boolean danger = pbx > pitch.centerX()+pitch.width()*0.06f || bvx > 110*s;
            if (danger) {
                // Intercept instead of blindly chasing: stay on the ball-goal line.
                float gx = pitch.right-52*s;
                float gy = pitch.centerY();
                float dx = pbx-gx, dy = pby-gy;
                float l = len(dx,dy); if (l<1f) l=1f;
                tx = gx + dx/l*Math.min(155*s,l*0.58f);
                ty = gy + dy/l*Math.min(155*s,l*0.58f);
            } else {
                // Approach from BEHIND the ball, aligned to an open part of the goal.
                float goalX = pitch.left-24*s;
                float goalY = cpuLaneY;
                float dx = goalX-pbx, dy = goalY-pby;
                float l = len(dx,dy); if (l<1f) l=1f;
                dx /= l; dy /= l;
                float behind = discR+ballR+5*s;
                tx = pbx-dx*behind;
                ty = pby-dy*behind;

                float bd = len(bx-cx,by-cy);
                float align = cpuAlignmentV13(goalX,goalY);
                // Once correctly behind it, keep moving through the ball: repeated physical
                // contacts make a natural dribble instead of attaching the ball to the CPU.
                if (bd < behind+14*s && align > 0.89f) {
                    tx = pbx+dx*92*s;
                    ty = pby+dy*92*s;
                }
                if (isPlayerBlockingLane(bx,by,goalX,goalY) && bd < behind+28*s) {
                    ty += py < pitch.centerY() ? 72*s : -72*s;
                }
            }

            float dx = tx-cx, dy = ty-cy;
            float l = len(dx,dy);
            float ix=0f, iy=0f;
            if (l > 2*s) { ix=dx/l; iy=dy/l; }

            float damp = (float)Math.pow(0.96, dt*60f);
            cvx *= damp;
            cvy *= damp;
            float skill = difficulty==0 ? 0.90f : (difficulty==1 ? 0.98f : 1.03f);
            float accel = 720*s*skill;
            cvx += ix*accel*dt;
            cvy += iy*accel*dt;
            float cap = (difficulty==0 ? 288f : (difficulty==1 ? 302f : 314f))*s;
            float sp = len(cvx,cvy);
            if (sp > cap) { cvx=cvx/sp*cap; cvy=cvy/sp*cap; }
        }

        private void collidePlayersV13() {
            float dx=cx-px, dy=cy-py;
            float d=len(dx,dy), min=discR*2f;
            if (d<=0.001f || d>=min) return;
            float nx=dx/d, ny=dy/d, pen=min-d;
            px-=nx*pen*0.5f; py-=ny*pen*0.5f;
            cx+=nx*pen*0.5f; cy+=ny*pen*0.5f;
            float rvx=cvx-pvx, rvy=cvy-pvy;
            float vel=rvx*nx+rvy*ny;
            if (vel<0f) {
                float invP=0.5f;
                float j=-(1f+0.35f)*vel/(invP+invP);
                pvx-=j*nx*invP; pvy-=j*ny*invP;
                cvx+=j*nx*invP; cvy+=j*ny*invP;
            }
            clampDisc(true); clampDisc(false);
        }

        private void collideBallV13(boolean player) {
            float x=player?px:cx, y=player?py:cy;
            float vx=player?pvx:cvx, vy=player?pvy:cvy;
            float dx=bx-x, dy=by-y;
            float d=len(dx,dy), min=discR+ballR;
            if (d<=0.001f || d>=min) return;
            float nx=dx/d, ny=dy/d, pen=min-d;
            float invPlayer=0.5f, invBall=1f, invSum=invPlayer+invBall;
            float movePlayer=pen*(invPlayer/invSum);
            float moveBall=pen*(invBall/invSum);
            if (player) { px-=nx*movePlayer; py-=ny*movePlayer; }
            else { cx-=nx*movePlayer; cy-=ny*movePlayer; }
            bx+=nx*moveBall; by+=ny*moveBall;

            float rvx=bvx-vx, rvy=bvy-vy;
            float vel=rvx*nx+rvy*ny;
            if (vel<0f) {
                float j=-(1f+0.50f)*vel/invSum;
                float pd=j*invPlayer, bd=j*invBall;
                if (player) { pvx-=nx*pd; pvy-=ny*pd; }
                else { cvx-=nx*pd; cvy-=ny*pd; }
                bvx+=nx*bd; bvy+=ny*bd;
                if (touchSoundCooldownV13<=0f && Math.abs(vel)>32*s) {
                    playSfx(SFX_TOUCH);
                    touchSoundCooldownV13=0.055f;
                }
            }
            if (player) clampDisc(true); else clampDisc(false);
        }

        private float cpuAlignmentV13(float goalX,float goalY) {
            float ax=bx-cx, ay=by-cy;
            float gx=goalX-bx, gy=goalY-by;
            float al=len(ax,ay), gl=len(gx,gy);
            if (al<1f || gl<1f) return -1f;
            return (ax/al)*(gx/gl)+(ay/al)*(gy/gl);
        }

        private void maybeCpuKickV13() {
            if (cpuKickCooldown>0f) return;
            float dx=bx-cx, dy=by-cy;
            float d=len(dx,dy), reach=discR+ballR+10*s;
            if (d>reach || d<0.001f) return;

            float goalX=pitch.left-24*s, goalY=cpuLaneY;
            float align=cpuAlignmentV13(goalX,goalY);
            boolean laneOpen=!isPlayerBlockingLane(bx,by,goalX,goalY);
            boolean attackZone=bx < pitch.left+pitch.width()*(difficulty==2?0.43f:0.36f);
            boolean emergency=bx > pitch.centerX()+pitch.width()*0.13f;
            if (!((attackZone && laneOpen && align>0.93f) || (emergency && align>0.84f))) return;

            float nx=dx/d, ny=dy/d;
            float impulse=(difficulty==0?345f:(difficulty==1?380f:405f))*s;
            bvx += nx*impulse + cvx*0.08f;
            bvy += ny*impulse + cvy*0.08f;
            cvx -= nx*18*s;
            cvy -= ny*18*s;
            cpuKickCooldown = difficulty==2 ? 0.40f : 0.54f;
            cpuLaneTimer = 0f;
            playSfx(SFX_KICK);
        }
'''

marker = '        private void handleBallWalls() {'
if marker not in s:
    raise SystemExit('handleBallWalls marker missing')
s = s.replace(marker, helpers + '\n' + marker, 1)

# Text reflects the real handling model now.
s = s.replace('subtitle(c, "OFFLINE • CPU EDITION", 222*s, 18, Color.rgb(150, 175, 205));',
              'subtitle(c, "HAX-LIKE PHYSICS • OFFLINE CPU", 222*s, 17, Color.rgb(150, 175, 205));')
s = s.replace('subtitle(c, "Move and resize joystick + kick button", 410*s, 17, Color.rgb(145,160,181));',
              'subtitle(c, "Fixed joystick • free-ball collision dribbling", 410*s, 17, Color.rgb(145,160,181));')

path.write_text(s, encoding='utf-8')
print('v1.3 physics patch applied')
