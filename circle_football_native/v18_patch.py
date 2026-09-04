from pathlib import Path
import re

path = Path('src/com/godnit/circlefootballlite/MainActivity.java')
s = path.read_text(encoding='utf-8')


def replace_method(text, name, replacement):
    pattern = (r'(?m)^        (?:@Override\s+)?(?:(?:public|protected|private)\s+)?'
               r'(?:static\s+)?(?:void|float|int|boolean|short\[\]|String|MediaPlayer)\s+'
               + re.escape(name) + r'\s*\(')
    m = re.search(pattern, text)
    if not m:
        raise RuntimeError('method declaration not found: ' + name)
    line_start = m.start()
    brace = text.find('{', m.end())
    depth = 0
    end = None
    for i in range(brace, len(text)):
        if text[i] == '{': depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        raise RuntimeError('unterminated method: ' + name)
    return text[:line_start] + replacement.rstrip() + text[end:]

# Real Android audio classes.
if 'import android.media.MediaPlayer;' not in s:
    s = s.replace('import android.media.AudioManager;\n',
                  'import android.media.AudioManager;\nimport android.media.MediaPlayer;\nimport android.media.SoundPool;\n')

# Host lifecycle: audio must stop immediately when app loses foreground.
activity_marker = '    @Override public void onBackPressed() {'
if 'void onPause()' not in s.split('static final class GameView')[0]:
    lifecycle = r'''    @Override protected void onPause() {
        if (gameView != null) gameView.onHostPause();
        super.onPause();
    }

    @Override protected void onResume() {
        super.onResume();
        hideSystemUI();
        if (gameView != null) gameView.onHostResume();
    }

    @Override protected void onDestroy() {
        if (gameView != null) gameView.onHostDestroy();
        super.onDestroy();
    }

'''
    if activity_marker not in s:
        raise RuntimeError('activity lifecycle marker missing')
    s = s.replace(activity_marker, lifecycle + activity_marker, 1)

# Replace old generated ambience state with real-resource players.
field_marker = '        volatile float crowdExcitement=0f;\n'
real_fields = (
    '        volatile float crowdExcitement=0f;\n'
    '        SoundPool realSoundPool;\n'
    '        MediaPlayer menuMusicPlayer, crowdLoopPlayer;\n'
    '        int sndKickA=0,sndKickB=0,sndBallBounce=0,sndGoalCheer=0,sndCrowdBurst=0,sndUiClick=0;\n'
    '        boolean hostActive=true, realAudioReady=false;\n'
)
if field_marker in s and 'SoundPool realSoundPool;' not in s:
    s = s.replace(field_marker, real_fields, 1)

# Wall-return state for AI discs.
s = s.replace('            float x,y,vx,vy,kickCd;\n',
              '            float x,y,vx,vy,kickCd,wallPlayTime,wallPlayX,wallPlayY;\n', 1)

# Update real crowd level and wall-return timers.
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
                blue[i].wallPlayTime=Math.max(0,blue[i].wallPlayTime-dt);
                red[i].wallPlayTime=Math.max(0,red[i].wallPlayTime-dt);
            }
            wallSoundCooldown=Math.max(0,wallSoundCooldown-dt);
            touchSoundCooldown=Math.max(0,touchSoundCooldown-dt);

            updateHuman(dt);
            chooseChasers();
            updateTeamAI(blue,red,0,blueChaser,dt);
            updateTeamAI(red,blue,1,redChaser,dt);

            int steps=Math.max(2,Math.min(12,(int)Math.ceil(dt/0.0038f)));
            float sub=dt/steps;
            for(int st=0;st<steps;st++) physicsStep(sub);
            updateParticles(dt);

            float near=Math.min(Math.abs(bx-pitch.left),Math.abs(pitch.right-bx))/Math.max(1f,pitch.width());
            float threat=clamp((.34f-near)/.34f,0f,1f);
            float speedBoost=clamp(len(bvx,bvy)/(850*s),0f,1f)*.28f;
            crowdExcitement=clamp(threat+speedBoost,0f,1f);
            syncRealAudio();
        }'''
s = replace_method(s, 'updateGame', update_game)

update_team = r'''        void updateTeamAI(Disc[] team,Disc[] opp,int teamId,int chaser,float dt){
            for(int i=0;i<teamSize;i++){
                Disc d=team[i];
                if(!d.ai)continue;
                float tx,ty;

                // After an intentional wall pass, run to the predicted rebound point instead of chasing the wall.
                if(d.wallPlayTime>0f){
                    tx=d.wallPlayX;ty=d.wallPlayY;
                    if(dist(d.x,d.y,bx,by)<kickReach()*.92f)d.wallPlayTime=0f;
                    moveAiToward(d,tx,ty,dt);
                    continue;
                }

                if(i==chaser){
                    if(d.kickCd>.17f){
                        float[] hold=formationTarget(teamId,i,chaser);
                        tx=hold[0];ty=hold[1];
                    }else{
                        float[] target=chooseKickTarget(d,team,opp,teamId);
                        float dx=target[0]-bx,dy=target[1]-by,ll=len(dx,dy);if(ll<1)ll=1;
                        float dirX=dx/ll,dirY=dy/ll;
                        float behind=discR+ballR+(ballNearWall()?21*s:9*s);
                        float rawX=bx-dirX*behind,rawY=by-dirY*behind;
                        tx=clamp(rawX,pitch.left+discR,pitch.right-discR);
                        ty=clamp(rawY,pitch.top+discR,pitch.bottom-discR);

                        if(Math.abs(tx-rawX)>3*s || Math.abs(ty-rawY)>3*s){
                            float sideX=-dirY,sideY=dirX;
                            float centerSide=(pitch.centerX()-bx)*sideX+(pitch.centerY()-by)*sideY;
                            if(centerSide<0){sideX=-sideX;sideY=-sideY;}
                            tx=clamp(bx+sideX*behind*1.15f,pitch.left+discR,pitch.right-discR);
                            ty=clamp(by+sideY*behind*1.15f,pitch.top+discR,pitch.bottom-discR);
                        }

                        float bd=dist(d.x,d.y,bx,by);
                        float cdx=bx-d.x,cdy=by-d.y,cl=len(cdx,cdy);if(cl<1)cl=1;
                        float align=(cdx/cl)*dirX+(cdy/cl)*dirY;
                        if(bd<=kickReach() && align>.82f && d.kickCd<=0f){
                            boolean isPass=target[2]>.5f;
                            boolean bank=target.length>=6 && target[3]>.5f;
                            cpuKick(d,isPass?580*s:(bank?610*s:(difficulty==0?570*s:difficulty==1?635*s:690*s)),dirX,dirY,isPass||bank);
                            if(bank){
                                d.wallPlayTime=.72f;
                                d.wallPlayX=target[4];d.wallPlayY=target[5];
                            }
                        }
                    }
                }else{
                    float[] pos=formationTarget(teamId,i,chaser);
                    tx=pos[0];ty=pos[1];
                    float minSpace=discR*(i==teamSize-1?4.1f:3.6f);
                    float db=dist(d.x,d.y,bx,by);
                    if(db<minSpace){
                        float awayX=d.x-bx,awayY=d.y-by,al=len(awayX,awayY);if(al<1)al=1;
                        tx+=awayX/al*(minSpace-db+34*s);
                        ty+=awayY/al*(minSpace-db+34*s);
                    }
                }
                moveAiToward(d,tx,ty,dt);
            }
        }'''
s = replace_method(s, 'updateTeamAI', update_team)

choose_target = r'''        float[] chooseKickTarget(Disc d,Disc[] team,Disc[] opp,int teamId){
            float goalX=teamId==0?pitch.right+35*s:pitch.left-35*s;
            float goalY=pitch.centerY();
            int passTo=bestPassTarget(d,team,opp,teamId);
            boolean keeper=d.index==teamSize-1 && teamSize>=2;
            boolean defender=d.index>0 && !keeper;

            float desiredX=goalX,desiredY=goalY;
            boolean pass=false;
            if((keeper||defender) && passTo>=0){
                Disc mate=team[passTo];
                desiredX=mate.x+mate.vx*.20f;desiredY=mate.y+mate.vy*.20f;pass=true;
            }else{
                Disc blocker=nearestOpponentToLine(opp,bx,by,goalX,goalY);
                if(blocker!=null && distToSegment(blocker.x,blocker.y,bx,by,goalX,goalY)<discR*2.0f){
                    goalY=clamp(pitch.centerY()+(blocker.y<pitch.centerY()?goalHalf*.62f:-goalHalf*.62f),
                            pitch.centerY()-goalHalf*.75f,pitch.centerY()+goalHalf*.75f);
                    desiredY=goalY;
                }
                int crowd=countOpponentsNear(opp,d.x,d.y,130*s);
                boolean laneBlocked=isLaneBlocked(opp,bx,by,goalX,goalY,discR*1.8f);
                boolean farFromGoal=teamId==0?bx<pitch.right-pitch.width()*.32f:bx>pitch.left+pitch.width()*.32f;
                if(passTo>=0 && (crowd>=1 || (laneBlocked&&farFromGoal))){
                    Disc mate=team[passTo];desiredX=mate.x+mate.vx*.20f;desiredY=mate.y+mate.vy*.20f;pass=true;
                }
            }

            boolean blocked=isLaneBlocked(opp,bx,by,desiredX,desiredY,discR*1.65f);
            float sideDist=Math.min(by-pitch.top,pitch.bottom-by);
            boolean sideOpportunity=sideDist<pitch.height()*.20f;
            boolean canBank=!keeper && (blocked||sideOpportunity) && Math.abs(desiredX-bx)>pitch.width()*.12f;
            if(canBank){
                float[] bank=chooseWallBank(desiredX,desiredY,teamId,opp);
                if(bank!=null)return new float[]{bank[0],bank[1],1f,1f,bank[2],bank[3]};
            }
            return new float[]{desiredX,desiredY,pass?1f:0f,0f,0f,0f};
        }

        float[] chooseWallBank(float finalX,float finalY,int teamId,Disc[] opp){
            float topY=pitch.top+ballR+1.5f*s,bottomY=pitch.bottom-ballR-1.5f*s;
            float sign=teamId==0?1f:-1f;
            float advance=165*s;
            float pickupX=clamp(bx+sign*advance,pitch.left+discR*2f,pitch.right-discR*2f);
            float bestScore=-999999f;float[] best=null;
            for(int side=0;side<2;side++){
                float wallY=side==0?topY:bottomY;
                float pickupY=side==0?clamp(by+120*s,pitch.top+discR*2f,pitch.bottom-discR*2f)
                                     :clamp(by-120*s,pitch.top+discR*2f,pitch.bottom-discR*2f);
                float mirrorY=2*wallY-pickupY;
                float den=mirrorY-by;if(Math.abs(den)<1f)continue;
                float t=(wallY-by)/den;
                if(t<.08f||t>.92f)continue;
                float hitX=bx+(pickupX-bx)*t;
                if(hitX<pitch.left+ballR*2.2f||hitX>pitch.right-ballR*2.2f)continue;
                float lane=nearestOpponentDistance(opp,hitX,wallY);
                float pickupOpen=nearestOpponentDistance(opp,pickupX,pickupY);
                float wallDistance=Math.abs(wallY-by);
                float score=lane*.42f+pickupOpen*.58f-wallDistance*.12f;
                if((side==0&&by<pitch.centerY())||(side==1&&by>pitch.centerY()))score+=30*s;
                if(score>bestScore){bestScore=score;best=new float[]{hitX,wallY,pickupX,pickupY};}
            }
            return best;
        }'''
s = replace_method(s, 'chooseKickTarget', choose_target)

# Stronger wall unpinning: move the pressing player away and launch the ball back into legal space.
resolve_ball = r'''        void resolveBallDisc(Disc d){
            float dx=bx-d.x,dy=by-d.y,min=discR+ballR,dst=len(dx,dy);
            if(dst>=min)return;
            float nx,ny;
            if(dst<.001f){
                float vx=bx-pitch.centerX(),vy=by-pitch.centerY(),vl=len(vx,vy);
                if(vl<.1f){vx=d.team==0?1f:-1f;vy=0;vl=1;}
                nx=vx/vl;ny=vy/vl;dst=.001f;
            }else{nx=dx/dst;ny=dy/dst;}
            float overlap=min-dst+1.15f*s;
            boolean tight=bx<pitch.left+ballR+3*s||bx>pitch.right-ballR-3*s||by<pitch.top+ballR+3*s||by>pitch.bottom-ballR-3*s;
            float ballShare=tight?.52f:.91f;
            bx+=nx*overlap*ballShare;by+=ny*overlap*ballShare;
            d.x-=nx*overlap*(1f-ballShare);d.y-=ny*overlap*(1f-ballShare);clampDisc(d);
            float rel=(bvx-d.vx)*nx+(bvy-d.vy)*ny;
            if(rel<0){
                float impulse=-1.44f*rel;
                bvx+=nx*impulse+d.vx*.075f;bvy+=ny*impulse+d.vy*.075f;
            }
        }

        void resolveWallPin(){
            float eps=4.0f*s,minSep=discR+ballR+3.5f*s,push=155*s;
            for(int team=0;team<2;team++){
                Disc[] arr=team==0?blue:red;
                float forward=team==0?1f:-1f;
                for(int i=0;i<teamSize;i++){
                    Disc d=arr[i];float dd=dist(d.x,d.y,bx,by);
                    if(dd>minSep+5*s)continue;
                    if(by<=pitch.top+ballR+eps && d.y>by){
                        d.y=Math.max(d.y,by+minSep);if(d.vy<0)d.vy*=.12f;
                        bvy=Math.max(bvy,push);bvx+=forward*push*.34f;by=pitch.top+ballR+1.2f*s;
                    }
                    if(by>=pitch.bottom-ballR-eps && d.y<by){
                        d.y=Math.min(d.y,by-minSep);if(d.vy>0)d.vy*=.12f;
                        bvy=Math.min(bvy,-push);bvx+=forward*push*.34f;by=pitch.bottom-ballR-1.2f*s;
                    }
                    if(bx<=pitch.left+ballR+eps && d.x>bx){
                        d.x=Math.max(d.x,bx+minSep);if(d.vx<0)d.vx*=.12f;
                        bvx=Math.max(bvx,push);bvy+=(by<pitch.centerY()?1f:-1f)*push*.24f;bx=pitch.left+ballR+1.2f*s;
                    }
                    if(bx>=pitch.right-ballR-eps && d.x<bx){
                        d.x=Math.min(d.x,bx-minSep);if(d.vx>0)d.vx*=.12f;
                        bvx=Math.min(bvx,-push);bvy+=(by<pitch.centerY()?1f:-1f)*push*.24f;bx=pitch.right-ballR-1.2f*s;
                    }
                    clampDisc(d);
                }
            }
        }

        void limitBallSpeed(float max){
            float l=len(bvx,bvy);if(l>max&&l>0){bvx=bvx/l*max;bvy=bvy/l*max;}
        }'''
s = replace_method(s, 'resolveBallDisc', resolve_ball)

# Human shot direction: KICK uses joystick aim blended with physical contact angle.
do_kick = r'''        void doKick(){
            Disc d=blue[0];if(d.kickCd>0)return;
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);
            if(l>kickReach())return;
            if(l<1)l=1;
            float nx=dx/l,ny=dy/l;
            float aimX=nx,aimY=ny;
            float jl=len(joyNX,joyNY);
            if(jl>.16f){
                float jx=joyNX/jl,jy=joyNY/jl;
                float dot=nx*jx+ny*jy;
                if(dot>-.20f){
                    float steer=.62f;
                    aimX=nx*(1f-steer)+jx*steer;
                    aimY=ny*(1f-steer)+jy*steer;
                    float al=len(aimX,aimY);if(al<1)al=1;aimX/=al;aimY/=al;
                }
            }
            float power=720*s;
            bvx+=aimX*power+d.vx*.15f;bvy+=aimY*power+d.vy*.15f;
            limitBallSpeed(930*s);
            d.kickCd=.27f;
            spawnKickBurst(aimX,aimY,power);
            haptic(20);playSfx(SFX_KICK);
        }'''
s = replace_method(s, 'doKick', do_kick)

# Reset wall-play state between kickoffs.
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
                blue[i].wallPlayTime=red[i].wallPlayTime=0f;
            }
            bx=pitch.centerX();by=cy;bvx=bvy=0;ballAngle=0;particles.clear();trailCarry=0;crowdExcitement=.05f;
            for(int i=0;i<teamSize;i++){separateFromBall(blue[i]);separateFromBall(red[i]);}
        }'''
s = replace_method(s, 'resetPositions', reset_positions)

# Replace generated AudioTrack SFX with real files loaded into SoundPool.
play_sfx = r'''        void playSfx(final int type){
            if(!sounds||!hostActive)return;
            initRealAudio();
            if(realSoundPool==null)return;
            int id=0;float vol=.72f,rate=1f;
            if(type==SFX_KICK){id=rng.nextBoolean()?sndKickA:sndKickB;vol=.82f;rate=.96f+rng.nextFloat()*.08f;}
            else if(type==SFX_PASS){id=sndKickB;vol=.52f;rate=1.07f;}
            else if(type==SFX_WALL){id=sndBallBounce;vol=.46f;rate=.94f+rng.nextFloat()*.10f;}
            else if(type==SFX_GOAL){id=sndGoalCheer;vol=.92f;}
            else if(type==SFX_WIN){id=sndGoalCheer;vol=.84f;rate=1.02f;}
            else if(type==SFX_LOSE){id=sndCrowdBurst;vol=.46f;rate=.96f;}
            else {id=sndUiClick;vol=.48f;}
            if(id!=0)realSoundPool.play(id,vol,vol,1,0,rate);
        }'''
s = replace_method(s, 'playSfx', play_sfx)

# Replace synthetic ambience with real looping MediaPlayer tracks and lifecycle-safe control.
ensure_ambient = r'''        void ensureAmbient(){
            syncRealAudio();
        }'''
s = replace_method(s, 'ensureAmbient', ensure_ambient)

stop_ambient = r'''        void stopAmbient(){
            pausePlayer(menuMusicPlayer);pausePlayer(crowdLoopPlayer);
        }'''
s = replace_method(s, 'stopAmbient', stop_ambient)

on_detached = r'''        @Override protected void onDetachedFromWindow(){
            releaseRealAudio();
            super.onDetachedFromWindow();
        }'''
s = replace_method(s, 'onDetachedFromWindow', on_detached)

real_audio_methods = r'''
        int rawId(String name){return getResources().getIdentifier(name,"raw",getContext().getPackageName());}

        MediaPlayer makeLoopPlayer(String name,float volume){
            int id=rawId(name);if(id==0)return null;
            try{
                MediaPlayer m=MediaPlayer.create(getContext(),id);
                if(m!=null){m.setLooping(true);m.setVolume(volume,volume);}
                return m;
            }catch(Exception ignored){return null;}
        }

        void initRealAudio(){
            if(realAudioReady)return;
            try{
                AudioAttributes attrs=new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build();
                realSoundPool=new SoundPool.Builder().setMaxStreams(7).setAudioAttributes(attrs).build();
                int id;
                id=rawId("kick_a");if(id!=0)sndKickA=realSoundPool.load(getContext(),id,1);
                id=rawId("kick_b");if(id!=0)sndKickB=realSoundPool.load(getContext(),id,1);
                id=rawId("ball_bounce");if(id!=0)sndBallBounce=realSoundPool.load(getContext(),id,1);
                id=rawId("goal_cheer");if(id!=0)sndGoalCheer=realSoundPool.load(getContext(),id,1);
                id=rawId("crowd_burst");if(id!=0)sndCrowdBurst=realSoundPool.load(getContext(),id,1);
                id=rawId("ui_click");if(id!=0)sndUiClick=realSoundPool.load(getContext(),id,1);
                menuMusicPlayer=makeLoopPlayer("menu_music",.22f);
                crowdLoopPlayer=makeLoopPlayer("crowd_loop",.09f);
                realAudioReady=true;
            }catch(Exception ignored){realAudioReady=true;}
        }

        void safeStart(MediaPlayer m){
            if(m==null)return;try{if(!m.isPlaying())m.start();}catch(Exception ignored){}
        }
        void pausePlayer(MediaPlayer m){
            if(m==null)return;try{if(m.isPlaying())m.pause();}catch(Exception ignored){}
        }

        void syncRealAudio(){
            if(!sounds||!hostActive){stopAmbient();return;}
            initRealAudio();
            boolean match=(mode==GAME||mode==PAUSE||mode==RESULT);
            if(match){
                pausePlayer(menuMusicPlayer);
                if(crowdLoopPlayer!=null){
                    float v=.075f+crowdExcitement*.095f;
                    try{crowdLoopPlayer.setVolume(v,v);}catch(Exception ignored){}
                }
                safeStart(crowdLoopPlayer);
            }else{
                pausePlayer(crowdLoopPlayer);
                safeStart(menuMusicPlayer);
            }
        }

        void onHostPause(){
            hostActive=false;stopAmbient();
            if(realSoundPool!=null)try{realSoundPool.autoPause();}catch(Exception ignored){}
        }
        void onHostResume(){
            hostActive=true;
            if(realSoundPool!=null)try{realSoundPool.autoResume();}catch(Exception ignored){}
            syncRealAudio();
        }
        void onHostDestroy(){releaseRealAudio();}

        void releaseRealAudio(){
            hostActive=false;
            pausePlayer(menuMusicPlayer);pausePlayer(crowdLoopPlayer);
            if(menuMusicPlayer!=null){try{menuMusicPlayer.release();}catch(Exception ignored){}menuMusicPlayer=null;}
            if(crowdLoopPlayer!=null){try{crowdLoopPlayer.release();}catch(Exception ignored){}crowdLoopPlayer=null;}
            if(realSoundPool!=null){try{realSoundPool.release();}catch(Exception ignored){}realSoundPool=null;}
            realAudioReady=false;
        }
'''
insert_marker = '        String difficultyName(){'
if 'void initRealAudio()' not in s:
    if insert_marker not in s: raise RuntimeError('audio method insertion marker missing')
    s = s.replace(insert_marker, real_audio_methods + '\n' + insert_marker, 1)

# Version-specific preferences.
s = s.replace('circle_football_v17', 'circle_football_v18')

path.write_text(s, encoding='utf-8')

# Manifest version/package so it can coexist with v1.7 during testing.
manifest = Path('AndroidManifest.xml')
m = manifest.read_text(encoding='utf-8')
m = m.replace('com.godnit.circlefootballlite.v17','com.godnit.circlefootballlite.v18')
m = re.sub(r'android:versionCode="\d+"', 'android:versionCode="9"', m, count=1)
m = re.sub(r'android:versionName="[^"]+"', 'android:versionName="1.8.0"', m, count=1)
manifest.write_text(m, encoding='utf-8')
print('Applied Circle Football v1.8 real audio / lifecycle / wall-bank / aim patch')
