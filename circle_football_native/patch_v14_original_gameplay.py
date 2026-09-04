from pathlib import Path
import re

path = Path('src/com/godnit/circlefootballlite/MainActivity.java')
s = path.read_text(encoding='utf-8')

def replace_method(text, name, replacement):
    start = text.index('        private void ' + name + '(')
    i = text.index('{', start)
    depth = 0
    end = None
    for j in range(i, len(text)):
        ch = text[j]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    if end is None:
        raise RuntimeError('method end not found: ' + name)
    return text[:start] + replacement.rstrip() + text[end:]

update_game = r'''        private void updateGame(float dt) {
            kickCooldown = Math.max(0f, kickCooldown-dt);
            cpuKickCooldown = Math.max(0f, cpuKickCooldown-dt);
            wallSoundCooldown = Math.max(0f, wallSoundCooldown-dt);
            ballOwner = 0;
            if (!training && !goldenGoal) {
                matchTime -= dt;
                if (matchTime <= 0f) {
                    matchTime = 0f;
                    if (blueScore == redScore) goldenGoal = true;
                    else finishMatch();
                }
            }

            float playerSpeed = 290*s;
            float desiredVx = joyNX*playerSpeed;
            float desiredVy = joyNY*playerSpeed;
            float lerp = Math.min(1f, dt*14f);
            pvx += (desiredVx-pvx)*lerp;
            pvy += (desiredVy-pvy)*lerp;
            if (joyPointer < 0) {
                pvx *= Math.pow(0.82,dt*60);
                pvy *= Math.pow(0.82,dt*60);
            }
            px += pvx*dt;
            py += pvy*dt;
            clampDisc(true);

            if (!training) updateCpu(dt);

            bx += bvx*dt;
            by += bvy*dt;
            float friction = (float)Math.pow(0.987,dt*60f);
            bvx *= friction;
            bvy *= friction;
            collideFreeBallWithDisc(px,py,pvx,pvy,1);
            if (!training) collideFreeBallWithDisc(cx,cy,cvx,cvy,2);
            handleBallWalls();
        }'''

update_cpu = r'''        private void updateCpu(float dt) {
            float ownGoalX = pitch.right;
            float targetGoalX = pitch.left;
            float pred = difficulty==0 ? 0.08f : (difficulty==1 ? 0.20f : 0.34f);
            float pbx = bx + bvx*pred;
            float pby = by + bvy*pred;
            pby = clamp(pby,pitch.top+discR,pitch.bottom-discR);

            float tx,ty;
            boolean danger = bx > pitch.centerX()+pitch.width()*0.08f || bvx > 120*s;
            if (danger) {
                float gx = ownGoalX - 28*s;
                float gy = pitch.centerY();
                float dx = pbx-gx, dy=pby-gy;
                float ll = len(dx,dy);
                if (ll<1) ll=1;
                tx = gx + dx/ll*Math.min(120*s,ll*0.45f);
                ty = gy + dy/ll*Math.min(120*s,ll*0.45f);
            } else {
                float dx = pbx-targetGoalX, dy=pby-pitch.centerY();
                float ll=len(dx,dy);
                if(ll<1)ll=1;
                tx = pbx + dx/ll*(discR+ballR+8*s);
                ty = pby + dy/ll*(discR+ballR+8*s);
            }
            if (difficulty==0) {
                tx = tx*0.86f + (pitch.right-135*s)*0.14f;
                ty = ty*0.90f + pitch.centerY()*0.10f;
            }
            float dx=tx-cx, dy=ty-cy, l=len(dx,dy);
            float speed = (difficulty==0 ? 215 : difficulty==1 ? 270 : 315)*s;
            float wantX=0,wantY=0;
            if(l>3*s){wantX=dx/l*speed;wantY=dy/l*speed;}
            float response = difficulty==0 ? 4.2f : difficulty==1 ? 7.0f : 10.5f;
            float k=Math.min(1f,dt*response);
            cvx += (wantX-cvx)*k;
            cvy += (wantY-cvy)*k;
            cx += cvx*dt;
            cy += cvy*dt;
            clampDisc(false);

            float bd=len(bx-cx,by-cy);
            if (bd < discR+ballR+15*s && cpuKickCooldown<=0f) {
                float aimY = pitch.centerY();
                if (difficulty>=1) aimY += (py-pitch.centerY())*0.15f;
                if (difficulty==2) aimY += (by-pitch.centerY())*0.10f;
                float kx=targetGoalX-bx, ky=aimY-by, kl=len(kx,ky);
                if(kl<1)kl=1;
                float force=(difficulty==0?560:difficulty==1?650:720)*s;
                bvx=kx/kl*force + cvx*0.15f;
                bvy=ky/kl*force + cvy*0.15f;
                cpuKickCooldown = difficulty==2 ? 0.32f : 0.45f;
                playSfx(SFX_KICK);
            }
        }'''

collide = r'''        private void collideFreeBallWithDisc(float x, float y, float vx, float vy, int who) {
            float dx=bx-x, dy=by-y;
            float min=discR+ballR;
            float d=len(dx,dy);
            if(d<min && d>0.001f){
                float nx=dx/d, ny=dy/d;
                float overlap=min-d;
                bx += nx*overlap;
                by += ny*overlap;
                float rel=(vx-bvx)*nx+(vy-bvy)*ny;
                float impulse=Math.max(90*s, rel*0.9f + 135*s);
                bvx += nx*impulse;
                bvy += ny*impulse;
            }
        }'''

do_kick = r'''        private void doKick() {
            if(kickCooldown>0)return;
            ballOwner=0;
            float dx=bx-px,dy=by-py,d=len(dx,dy);
            if(d<discR+ballR+42*s){
                if(d<1)d=1;
                float force=720*s;
                bvx=dx/d*force+pvx*0.20f;
                bvy=dy/d*force+pvy*0.20f;
                kickCooldown=0.25f;
                haptic(22);
                playSfx(SFX_KICK);
            }
        }'''

s = replace_method(s, 'updateGame', update_game)
s = replace_method(s, 'updateCpu', update_cpu)
s = replace_method(s, 'collideFreeBallWithDisc', collide)
s = replace_method(s, 'doKick', do_kick)

# Make the UI wording explicit that gameplay is restored to the original feel.
s = s.replace('OFFLINE • CPU EDITION', 'OFFLINE • ORIGINAL GAMEPLAY')

path.write_text(s, encoding='utf-8')
print('Patched v1.4 original gameplay')
