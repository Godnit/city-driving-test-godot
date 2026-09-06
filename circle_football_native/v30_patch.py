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

# Role-based pressure selection. The striker is always allowed to roam, defenders
# may step out when they are truly the closest useful player, and the keeper only
# leaves goal for an immediate box threat. Exactly one AI presses per team.
if 'int roleChaserV30(' not in s:
    s=s.replace('        void chooseChasers(){',r'''        int roleChaserV30(Disc[] team,int teamId){
            float own=teamId==0?pitch.left:pitch.right,sg=teamId==0?1f:-1f,cw=pitch.width();
            float box=own+sg*cw*.16f,defLine=own+sg*cw*.43f;
            boolean inBox=teamId==0?bx<box:bx>box;
            if(teamSize>=2&&inBox)return teamSize-1;
            int best=-1;float bestCost=Float.MAX_VALUE;
            for(int i=0;i<teamSize;i++){
                Disc d=team[i];if(!d.ai)continue;
                if(i==teamSize-1&&teamSize>=2)continue;
                float cost=dist(d.x,d.y,bx,by);
                if(i==0)cost*=.78f; // striker gets a strong roaming bias
                else{
                    boolean ballBeyondDef=teamId==0?bx>defLine:bx<defLine;
                    if(ballBeyondDef)cost+=cw*.12f; // defenders do not abandon shape far upfield
                }
                if(cost<bestCost){bestCost=cost;best=i;}
            }
            return best;
        }

        void chooseChasers(){''',1)

s=rep(s,'chooseChasers',r'''        void chooseChasers(){
            blueChaser=roleChaserV30(blue,0);
            redChaser=roleChaserV30(red,1);
        }''')

# Moving role targets: no fixed parking points. Striker stays available anywhere,
# defenders slide between ball and goal while marking lanes, keeper tracks ball
# across the mouth. This removes the stop/back-up/stop feel from previous builds.
s=rep(s,'formationTarget',r'''        float[] formationTarget(int teamId,int idx,int chaser){
            float own=teamId==0?pitch.left:pitch.right,sg=teamId==0?1f:-1f,cw=pitch.width(),ch=pitch.height();
            float pred=difficulty==2?.18f:(difficulty==1?.12f:.08f),pbx=bx+bvx*pred,pby=by+bvy*pred;
            if(idx==0){
                float fx=teamId==0?clamp(pbx+cw*.18f,pitch.centerX()-cw*.06f,pitch.right-cw*.08f):clamp(pbx-cw*.18f,pitch.left+cw*.08f,pitch.centerX()+cw*.06f);
                float fy=clamp(pby+(pby<pitch.centerY()?ch*.11f:-ch*.11f),pitch.top+discR*1.6f,pitch.bottom-discR*1.6f);
                return new float[]{fx,fy};
            }
            if(idx==teamSize-1&&teamSize>=2){
                float danger=teamId==0?clamp((pitch.centerX()-pbx)/(cw*.52f),0,1):clamp((pbx-pitch.centerX())/(cw*.52f),0,1);
                float kx=own+sg*cw*(.055f+.045f*danger);
                float ky=clamp(pby,pitch.centerY()-goalHalf*.72f,pitch.centerY()+goalHalf*.72f);
                return new float[]{kx,ky};
            }
            int defenders=Math.max(1,teamSize-2),slot=idx-1;
            float band=(slot+1f)/(defenders+1f),zoneY=pitch.top+ch*band;
            float baseX=own+sg*cw*(.22f+.045f*slot);
            float interceptX=pbx-sg*(72f+20f*slot)*s;
            float threat=teamId==0?clamp((pitch.centerX()+cw*.10f-pbx)/(cw*.62f),0,1):clamp((pbx-(pitch.centerX()-cw*.10f))/(cw*.62f),0,1);
            float x=baseX*(1-threat)+interceptX*threat;
            float y=zoneY*.44f+pby*.56f;
            return new float[]{clamp(x,pitch.left+discR,pitch.right-discR),clamp(y,pitch.top+discR,pitch.bottom-discR)};
        }''')

# Stable continuous steering. AI does not intentionally reverse when the target is
# nearly reached; it arcs around instead. A short sidestep escape handles collisions.
s=rep(s,'moveAiToward',r'''        void moveAiToward(Disc d,float tx,float ty,float dt){
            float dx=tx-d.x,dy=ty-d.y,l=len(dx,dy);
            float moved=dist(d.x,d.y,d.lastAiX,d.lastAiY),speedNow=len(d.vx,d.vy);
            if(d.escapeTimer>0){d.escapeTimer=Math.max(0,d.escapeTimer-dt);tx=d.escapeX;ty=d.escapeY;dx=tx-d.x;dy=ty-d.y;l=len(dx,dy);}
            else if(l>18*s&&speedNow<34*s&&moved<.85f*s){
                d.stuckTimer+=dt;
                if(d.stuckTimer>.16f){
                    float ll=Math.max(1,l),nx=dx/ll,ny=dy/ll,sx=-ny,sy=nx;
                    if((pitch.centerX()-d.x)*sx+(pitch.centerY()-d.y)*sy<0){sx=-sx;sy=-sy;}
                    d.escapeX=clamp(d.x+sx*52*s+nx*24*s,pitch.left-20*s,pitch.right+20*s);
                    d.escapeY=clamp(d.y+sy*52*s+ny*24*s,pitch.top-26*s,pitch.bottom+26*s);
                    d.escapeTimer=.30f;d.stuckTimer=0;tx=d.escapeX;ty=d.escapeY;dx=tx-d.x;dy=ty-d.y;l=len(dx,dy);
                }
            }else d.stuckTimer=Math.max(0,d.stuckTimer-dt*3f);
            float max=185*s,wx=0,wy=0;
            if(l>1.5f*s){wx=dx/Math.max(1,l)*max;wy=dy/Math.max(1,l)*max;}
            else if(speedNow>42*s){wx=d.vx*.82f;wy=d.vy*.82f;}
            float k=Math.min(1,dt*7.2f);d.vx+=(wx-d.vx)*k;d.vy+=(wy-d.vy)*k;
            d.lastAiX=d.x;d.lastAiY=d.y;
        }''')

# Passing and attacking decisions: defenders/GK look forward, striker attacks the
# goal unless genuinely trapped. No pointless back-and-forth passing.
s=rep(s,'chooseKickTarget',r'''        float[] chooseKickTarget(Disc d,Disc[] team,Disc[] opp,int teamId){
            float goalX=teamId==0?pitch.right+24*s:pitch.left-24*s,goalY=bestGoalLaneV25(opp,teamId);
            float goalDist=Math.abs(goalX-bx);
            int pressure=countOpponentsNear(opp,d.x,d.y,100*s);
            int passTo=bestPassTarget(d,team,opp,teamId);
            boolean keeper=d.index==teamSize-1&&teamSize>=2,defender=d.index>0&&!keeper;
            boolean laneBlocked=isLaneBlocked(opp,bx,by,goalX,goalY,discR*1.35f);
            boolean shootZone=goalDist<pitch.width()*(difficulty==0?.30f:(difficulty==1?.38f:.46f));
            if((keeper||defender)&&passTo>=0){Disc m=team[passTo];return new float[]{m.x+m.vx*.16f,m.y+m.vy*.16f,1f};}
            if(shootZone&&!laneBlocked)return new float[]{goalX,goalY,0f};
            if(pressure>=2&&passTo>=0){Disc m=team[passTo];return new float[]{m.x+m.vx*.16f,m.y+m.vy*.16f,1f};}
            if(shootZone)return new float[]{goalX,goalY,0f};
            return new float[]{goalX,goalY,2f};
        }''')

# Chaser always completes the approach and drives through the ball; support players
# keep their roles and never all collapse onto the ball.
s=rep(s,'updateTeamAI',r'''        void updateTeamAI(Disc[] team,Disc[] opp,int teamId,int chaser,float dt){
            for(int i=0;i<teamSize;i++){
                Disc d=team[i];if(!d.ai)continue;float tx,ty;
                if(i==chaser){
                    float[] tar=chooseKickTarget(d,team,opp,teamId);boolean pass=tar[2]>.5f&&tar[2]<1.5f,carry=tar[2]>1.5f;
                    float lead=difficulty==0?.07f:(difficulty==1?.13f:.20f),pbx=bx+bvx*lead,pby=by+bvy*lead;
                    float dx=tar[0]-pbx,dy=tar[1]-pby,ll=len(dx,dy);if(ll<1)ll=1;float dirX=dx/ll,dirY=dy/ll;
                    float bd=dist(d.x,d.y,bx,by),cdx=bx-d.x,cdy=by-d.y,cl=len(cdx,cdy);if(cl<1)cl=1;
                    float align=(cdx/cl)*dirX+(cdy/cl)*dirY;
                    if(carry&&bd<discR+ballR+20*s&&align>.42f){
                        tx=pbx+dirX*(discR+ballR+25*s);ty=pby+dirY*(discR+ballR+25*s);
                    }else{
                        float behind=discR+ballR+(carry?3*s:6*s);tx=pbx-dirX*behind;ty=pby-dirY*behind;
                    }
                    if(bd<=kickReach()&&!carry&&align>(difficulty==2?.58f:.66f)&&d.kickCd<=0)cpuKick(d,pass?445*s:515*s,dirX,dirY,pass);
                }else{
                    float[] pos=formationTarget(teamId,i,chaser);tx=pos[0];ty=pos[1];
                    float db=dist(d.x,d.y,bx,by),bubble=(i==teamSize-1?discR*3.6f:discR*3.15f);
                    if(db<bubble){float ax=d.x-bx,ay=d.y-by,al=len(ax,ay);if(al<1)al=1;tx+=ax/al*(bubble-db+12*s);ty+=ay/al*(bubble-db+12*s);}
                }
                moveAiToward(d,tx,ty,dt);
            }
        }''')

# v3.0 package/version for side-by-side testing.
s=s.replace('circle_football_v29','circle_football_v30')
path.write_text(s,encoding='utf-8')

m=Path('AndroidManifest.xml');x=m.read_text(encoding='utf-8');x=x.replace('com.godnit.circlefootballlite.v29','com.godnit.circlefootballlite.v30');x=re.sub(r'android:versionCode="\d+"','android:versionCode="21"',x,count=1);x=re.sub(r'android:versionName="[^"]+"','android:versionName="3.0.0"',x,count=1);m.write_text(x,encoding='utf-8')
print('Applied v3.0 stable role-based AI with roaming striker and nearest eligible presser')
