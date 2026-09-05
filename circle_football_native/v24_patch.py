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

# Stadium selection state.
s = s.replace('int difficulty=1, teamSize=2, targetGoals=5;',
              'int difficulty=1, teamSize=2, targetGoals=5, fieldTheme=0;')
s = s.replace('targetGoals=prefs.getInt("target_goals",5);',
              'targetGoals=prefs.getInt("target_goals",5);\n            fieldTheme=clampInt(prefs.getInt("field_theme",0),0,3);')

# Four stadium styles. WIDE uses a larger playable area and smaller discs/ball,
# matching the alternate versions the user referenced.
configure = r'''        void configureField(){
            float mxRatio,myRatio;
            if(fieldTheme==3){mxRatio=.025f;myRatio=.058f;}
            else if(fieldTheme==2){mxRatio=.050f;myRatio=.078f;}
            else{mxRatio=teamSize>=3?.045f:.065f;myRatio=teamSize>=3?.082f:.105f;}
            float mx=w*mxRatio,my=h*myRatio;
            pitch.set(mx,my,w-mx,h-my);
            goalHalf=pitch.height()*.19f;
            float scale=teamSize>=4?.80f:(teamSize==3?.88f:1f);
            if(fieldTheme==3)scale*=.82f;
            else if(fieldTheme==2)scale*=.94f;
            discR=29f*s*scale;
            float bscale=teamSize>=4?.86f:(teamSize==3?.92f:1f);
            if(fieldTheme==3)bscale*=.78f;
            else if(fieldTheme==2)bscale*=.92f;
            ballR=15f*s*bscale;
        }'''
s = replace_method(s, 'configureField', configure)

# Compact PLAY screen: all previous choices remain, but are shown in a much
# shorter screen, plus a stadium selector.
draw_setup = r'''        void drawSetup(Canvas c){
            background(c);
            title(c,"PLAY",52*s,32);

            subtitle(c,"DIFFICULTY",82*s,13,Color.LTGRAY);
            String[] ds={"EASY","NORMAL","HARD"};
            float bw=190*s,gap=14*s,start=(w-(bw*3+gap*2))/2f;
            for(int i=0;i<3;i++)menuButton(c,ds[i],"diff"+i,start+i*(bw+gap),94*s,bw,48*s,
                    i==difficulty?Color.rgb(29,121,255):Color.rgb(48,56,70));

            subtitle(c,"PLAYERS",164*s,13,Color.LTGRAY);
            float pW=132*s,pGap=12*s,pTotal=pW*4+pGap*3,pStart=(w-pTotal)/2f;
            for(int i=1;i<=4;i++)menuButton(c,i+"v"+i,"team"+i,pStart+(i-1)*(pW+pGap),176*s,pW,46*s,
                    i==teamSize?Color.rgb(34,174,91):Color.rgb(48,56,70));

            subtitle(c,"GOALS",246*s,13,Color.LTGRAY);
            int[] gs={3,5,7};
            for(int i=0;i<3;i++)menuButton(c,""+gs[i],"goal"+gs[i],start+i*(bw+gap),258*s,bw,46*s,
                    gs[i]==targetGoals?Color.rgb(245,165,35):Color.rgb(48,56,70));

            subtitle(c,"STADIUM",328*s,13,Color.LTGRAY);
            String[] fs={"CLASSIC","GRASS","NIGHT","WIDE"};
            float fW=176*s,fGap=12*s,fTotal=fW*4+fGap*3,fStart=(w-fTotal)/2f;
            for(int i=0;i<4;i++)menuButton(c,fs[i],"field"+i,fStart+i*(fW+fGap),340*s,fW,48*s,
                    i==fieldTheme?Color.rgb(104,88,210):Color.rgb(48,56,70));

            menuButton(c,"START MATCH","start",(w-420*s)/2f,424*s,420*s,62*s,Color.rgb(29,121,255));
            menuButton(c,"BACK","home",(w-220*s)/2f,502*s,220*s,48*s,Color.rgb(48,56,70));
        }'''
s = replace_method(s, 'drawSetup', draw_setup)

# Theme-aware pitch rendering + aiming helpers.
draw_game = r'''        void drawGame(Canvas c){
            int outside,p1,p2,line;
            if(fieldTheme==1){outside=Color.rgb(24,72,31);p1=Color.rgb(53,155,55);p2=Color.rgb(47,143,50);line=Color.rgb(242,246,240);}
            else if(fieldTheme==2){outside=Color.rgb(10,20,36);p1=Color.rgb(31,57,84);p2=Color.rgb(27,50,76);line=Color.rgb(206,228,246);}
            else if(fieldTheme==3){outside=Color.rgb(22,62,31);p1=Color.rgb(59,151,63);p2=Color.rgb(50,137,56);line=Color.rgb(242,246,240);}
            else{outside=Color.rgb(17,22,27);p1=Color.rgb(65,71,77);p2=Color.rgb(58,64,70);line=Color.WHITE;}
            c.drawColor(outside);
            p.setStyle(Paint.Style.FILL);p.setColor(p1);c.drawRect(pitch,p);
            int bands=fieldTheme==3?12:10;
            for(int i=0;i<bands;i++){
                p.setColor(i%2==0?p1:p2);
                float xx=pitch.left+pitch.width()*i/bands;
                c.drawRect(xx,pitch.top,xx+pitch.width()/bands,pitch.bottom,p);
            }
            if(fieldTheme==1||fieldTheme==3){
                p.setColor(Color.argb(18,255,255,255));
                for(int i=0;i<7;i++)c.drawRect(pitch.left,pitch.top+i*pitch.height()/7f,pitch.right,pitch.top+(i+.12f)*pitch.height()/7f,p);
            }
            stroke.setColor(line);stroke.setStrokeWidth(3*s);
            c.drawRect(pitch,stroke);c.drawLine(pitch.centerX(),pitch.top,pitch.centerX(),pitch.bottom,stroke);
            c.drawCircle(pitch.centerX(),pitch.centerY(),78*s,stroke);c.drawCircle(pitch.centerX(),pitch.centerY(),4*s,stroke);
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

# Goals are deeper visually because players are now allowed to enter them.
draw_goals = r'''        void drawGoals(Canvas c){
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf,depth=58*s;
            int net=fieldTheme==2?Color.rgb(135,177,205):Color.rgb(225,230,235);
            p.setStyle(Paint.Style.FILL);p.setColor(Color.argb(18,210,225,235));
            c.drawRect(new RectF(pitch.left-depth,y1,pitch.left,y2),p);
            c.drawRect(new RectF(pitch.right,y1,pitch.right+depth,y2),p);
            stroke.setColor(net);stroke.setStrokeWidth(3*s);
            c.drawRect(new RectF(pitch.left-depth,y1,pitch.left,y2),stroke);
            c.drawRect(new RectF(pitch.right,y1,pitch.right+depth,y2),stroke);
            stroke.setStrokeWidth(1*s);stroke.setColor(Color.argb(150,145,160,172));
            for(int i=1;i<5;i++){
                float yy=y1+(y2-y1)*i/5f;
                c.drawLine(pitch.left-depth,yy,pitch.left,yy,stroke);
                c.drawLine(pitch.right,yy,pitch.right+depth,yy,stroke);
            }
            for(int i=1;i<4;i++){
                float lx=pitch.left-depth+depth*i/4f,rx=pitch.right+depth*i/4f;
                c.drawLine(lx,y1,lx,y2,stroke);c.drawLine(rx,y1,rx,y2,stroke);
            }
        }'''
s = replace_method(s, 'drawGoals', draw_goals)

# Light half-ring around players, oriented toward the ball. It is intentionally
# subtle so 3v3/4v4 does not become visually noisy.
draw_disc = r'''        void drawDisc(Canvas c,Disc d){
            int col=d.team==0?Color.rgb(35,103,235):Color.rgb(239,57,61);
            float db=dist(d.x,d.y,bx,by);
            if(db<discR+ballR+105*s){
                float ang=(float)Math.toDegrees(Math.atan2(by-d.y,bx-d.x));
                float rr=discR+11*s;
                stroke.setColor(Color.argb(db<kickReach()+12*s?105:46,255,255,255));
                stroke.setStrokeWidth((db<kickReach()+12*s?2.1f:1.4f)*s);
                c.drawArc(new RectF(d.x-rr,d.y-rr,d.x+rr,d.y+rr),ang-90f,180f,false,stroke);
            }
            p.setStyle(Paint.Style.FILL);p.setColor(Color.BLACK);c.drawCircle(d.x,d.y,discR+3*s,p);
            p.setColor(col);c.drawCircle(d.x,d.y,discR,p);
            p.setColor(Color.argb(82,255,255,255));c.drawCircle(d.x-discR*.28f,d.y-discR*.30f,discR*.22f,p);
            if((d.team==0?blueChaser:redChaser)==d.index&&d.ai){
                stroke.setColor(Color.argb(105,255,255,255));stroke.setStrokeWidth(2*s);
                c.drawCircle(d.x,d.y,discR+7*s,stroke);
            }
            p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(12*s);p.setColor(Color.WHITE);
            c.drawText(d.name,d.x,d.y+discR+17*s,p);
        }'''
s = replace_method(s, 'drawDisc', draw_disc)

# Insert a dotted predicted kick path. It uses the real contact normal between
# the nearest player and the ball, and reflects off the same pitch walls.
if 'void drawPredictionGuideV24(Canvas c)' not in s:
    marker='        void drawGame(Canvas c){'
    helper=r'''        Disc nearestGuideDiscV24(){
            Disc best=null;float bd=Float.MAX_VALUE;
            for(int i=0;i<teamSize;i++){
                float q=dist(blue[i].x,blue[i].y,bx,by);if(q<bd){bd=q;best=blue[i];}
                q=dist(red[i].x,red[i].y,bx,by);if(q<bd){bd=q;best=red[i];}
            }
            return bd<=kickReach()+32*s?best:null;
        }

        void drawPredictionGuideV24(Canvas c){
            Disc d=nearestGuideDiscV24();if(d==null)return;
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);
            if(l<1f){dx=d.team==0?1f:-1f;dy=0f;l=1f;}
            float vx=dx/l,vy=dy/l;
            // Blend a little current momentum so the dots better match a moving ball.
            float bs=len(bvx,bvy);
            if(bs>20*s){vx=vx*.88f+(bvx/bs)*.12f;vy=vy*.88f+(bvy/bs)*.12f;float vl=len(vx,vy);if(vl>0){vx/=vl;vy/=vl;}}
            float px=bx,py=by,step=18*s;
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf;
            p.setStyle(Paint.Style.FILL);
            for(int i=0;i<30;i++){
                px+=vx*step;py+=vy*step;
                if(py-ballR<pitch.top){py=pitch.top+ballR;vy=Math.abs(vy);}
                if(py+ballR>pitch.bottom){py=pitch.bottom-ballR;vy=-Math.abs(vy);}
                boolean mouth=py>y1+ballR*.18f&&py<y2-ballR*.18f;
                if(!mouth){
                    if(px-ballR<pitch.left){px=pitch.left+ballR;vx=Math.abs(vx);}
                    if(px+ballR>pitch.right){px=pitch.right-ballR;vx=-Math.abs(vx);}
                }else if(px+ballR<pitch.left||px-ballR>pitch.right){
                    break;
                }
                if(i%2==0){
                    int a=Math.max(18,82-i*2);
                    p.setColor(Color.argb(a,255,255,255));c.drawCircle(px,py,2.5f*s,p);
                }
            }
        }

'''
    if marker not in s:raise RuntimeError('drawGame marker missing')
    s=s.replace(marker,helper+marker,1)

# Allow every player to move slightly beyond the touchlines and to enter the
# goal mouth, like the original game. The ball still uses its own wall rules.
clamp_disc = r'''        void clampDisc(Disc d){
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf;
            float out=22f*s,goalDepth=50f*s;
            d.y=clamp(d.y,pitch.top-out,pitch.bottom+out);
            boolean inGoalLane=d.y>y1-discR*.30f&&d.y<y2+discR*.30f;
            float lx=inGoalLane?pitch.left-goalDepth:pitch.left-out;
            float rx=inGoalLane?pitch.right+goalDepth:pitch.right+out;
            d.x=clamp(d.x,lx,rx);
        }'''
s = replace_method(s, 'clampDisc', clamp_disc)

# Stable player-ball collision. Previous versions could add several full impulses
# in one frame when the ball was squeezed between two discs, causing a strange launch.
resolve_ball = r'''        void resolveBallDisc(Disc d){
            float dx=bx-d.x,dy=by-d.y,min=discR+ballR,dst=len(dx,dy);
            if(dst>=min)return;
            float nx,ny;
            if(dst<.001f){
                float rvx=bvx-d.vx,rvy=bvy-d.vy,rl=len(rvx,rvy);
                if(rl>.01f){nx=rvx/rl;ny=rvy/rl;}else{nx=d.team==0?1f:-1f;ny=0f;}
                dst=.001f;
            }else{nx=dx/dst;ny=dy/dst;}
            float overlap=min-dst+.35f*s;
            // Share positional correction with the player. This is much more stable
            // than teleporting the whole overlap into the ball when it is sandwiched.
            bx+=nx*overlap*.70f;by+=ny*overlap*.70f;
            d.x-=nx*overlap*.30f;d.y-=ny*overlap*.30f;clampDisc(d);
            float rel=(bvx-d.vx)*nx+(bvy-d.vy)*ny;
            if(rel<0f){
                float impulse=Math.min(-rel*1.05f,92f*s);
                bvx+=nx*impulse;bvy+=ny*impulse;
            }
        }'''
s = replace_method(s, 'resolveBallDisc', resolve_ball)

# Add a squeeze detector for opposing contacts. It damps only the impossible
# acceleration spike; normal dribbles and kicks keep their current behavior.
if 'void stabilizeBallSqueezeV24()' not in s:
    marker='        void physicsStep(float dt){'
    helper=r'''        void stabilizeBallSqueezeV24(){
            float[] nx=new float[8],ny=new float[8];int n=0;
            float min=discR+ballR+2.2f*s;
            for(int team=0;team<2;team++){
                Disc[] arr=team==0?blue:red;
                for(int i=0;i<teamSize&&n<8;i++){
                    float dx=bx-arr[i].x,dy=by-arr[i].y,l=len(dx,dy);
                    if(l<min&&l>.001f){nx[n]=dx/l;ny[n]=dy/l;n++;}
                }
            }
            boolean squeezed=false;
            for(int i=0;i<n&&!squeezed;i++)for(int j=i+1;j<n;j++)if(nx[i]*nx[j]+ny[i]*ny[j]<-.28f){squeezed=true;break;}
            if(squeezed){
                bvx*=.76f;bvy*=.76f;
                limitBallSpeed(500f*s);
            }
        }

'''
    if marker not in s:raise RuntimeError('physicsStep marker missing')
    s=s.replace(marker,helper+marker,1)

physics = r'''        void physicsStep(float dt){
            for(int i=0;i<teamSize;i++){
                Disc a=blue[i],b=red[i];
                a.x+=a.vx*dt;a.y+=a.vy*dt;
                b.x+=b.vx*dt;b.y+=b.vy*dt;
                clampDisc(a);clampDisc(b);
            }
            for(int pass=0;pass<3;pass++)resolveAllDiscCollisions();

            lastBallX=bx;lastBallY=by;
            bx+=bvx*dt;by+=bvy*dt;
            float fr=(float)Math.pow(.9850,dt*60f);bvx*=fr;bvy*=fr;

            int bs=blueScore,rs=redScore;
            for(int pass=0;pass<3;pass++){
                for(int i=0;i<teamSize;i++){resolveBallDisc(blue[i]);resolveBallDisc(red[i]);}
                handleBallWalls();
                if(blueScore!=bs||redScore!=rs)return;
            }
            stabilizeBallSqueezeV24();
            limitBallSpeed(690f*s);

            float moved=dist(lastBallX,lastBallY,bx,by);
            if(moved>0.001f){
                float sign=(Math.abs(bvx)>Math.abs(bvy))?(bvx>=0?1f:-1f):(bvy>=0?-1f:1f);
                ballAngle+=sign*(moved/Math.max(1f,ballR))*57.2958f;
            }
            emitMotionTrail(dt);
        }'''
s = replace_method(s, 'physicsStep', physics)

# Goal = entire ball has crossed the front goal line between the posts. Post
# collision remains physical, and balls outside the mouth still bounce as before.
handle_walls = r'''        void handleBallWalls(){
            float left=pitch.left,right=pitch.right,top=pitch.top,bottom=pitch.bottom;
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf;
            boolean bounced=false;

            if(by-ballR<top){by=top+ballR;bvy=Math.abs(bvy)*.76f;bounced=true;}
            if(by+ballR>bottom){by=bottom-ballR;bvy=-Math.abs(bvy)*.76f;bounced=true;}

            resolveGoalPost(left,y1);resolveGoalPost(left,y2);
            resolveGoalPost(right,y1);resolveGoalPost(right,y2);

            boolean wholeBetweenPosts=by-ballR>=y1&&by+ballR<=y2;
            if(wholeBetweenPosts&&bx-ballR>=right){scoreGoal(true);return;}
            if(wholeBetweenPosts&&bx+ballR<=left){scoreGoal(false);return;}

            boolean mouth=by>y1+ballR*.18f&&by<y2-ballR*.18f;
            if(!mouth){
                if(bx-ballR<left){bx=left+ballR;bvx=Math.abs(bvx)*.78f;bounced=true;}
                if(bx+ballR>right){bx=right-ballR;bvx=-Math.abs(bvx)*.78f;bounced=true;}
            }else if(bx<left||bx>right){
                float railTop=y1+ballR*.20f,railBottom=y2-ballR*.20f;
                if(by<railTop){by=railTop;bvy=Math.abs(bvy)*.72f;bounced=true;}
                if(by>railBottom){by=railBottom;bvy=-Math.abs(bvy)*.72f;bounced=true;}
            }
            if(bounced&&wallSoundCooldown<=0f&&len(bvx,bvy)>85f*s){playSfx(SFX_WALL);wallSoundCooldown=.10f;}
        }'''
s = replace_method(s, 'handleBallWalls', handle_walls)

# Compact menu handlers and persist stadium choice. Reconfigure the field as soon
# as player count/theme changes so WIDE visibly changes before the match starts.
click = r'''        void click(String id){
            if(id.equals("play")){playSfx(SFX_MENU);mode=SETUP;return;}
            if(id.equals("players")){playSfx(SFX_MENU);mode=PLAYERS;return;}
            if(id.equals("settings")){playSfx(SFX_MENU);mode=SETTINGS;return;}
            if(id.equals("home")){playSfx(SFX_MENU);mode=HOME;releaseJoy();return;}
            if(id.equals("start")){startMatch();return;}
            if(id.equals("resume")){playSfx(SFX_MENU);mode=GAME;lastFrame=System.nanoTime();return;}
            if(id.equals("restart")||id.equals("rematch")){startMatch();return;}
            if(id.startsWith("diff")){difficulty=Integer.parseInt(id.substring(4));prefs.edit().putInt("difficulty",difficulty).apply();playSfx(SFX_MENU);return;}
            if(id.startsWith("team")){teamSize=clampInt(Integer.parseInt(id.substring(4)),1,4);prefs.edit().putInt("team_size",teamSize).apply();configureField();resetPositions();playSfx(SFX_MENU);return;}
            if(id.startsWith("goal")){targetGoals=Integer.parseInt(id.substring(4));prefs.edit().putInt("target_goals",targetGoals).apply();playSfx(SFX_MENU);return;}
            if(id.startsWith("field")){fieldTheme=clampInt(Integer.parseInt(id.substring(5)),0,3);prefs.edit().putInt("field_theme",fieldTheme).apply();configureField();resetPositions();playSfx(SFX_MENU);return;}
            if(id.equals("sounds")){sounds=!sounds;prefs.edit().putBoolean("sounds",sounds).apply();if(sounds)playSfx(SFX_MENU);else stopAmbient();return;}
            if(id.equals("vibration")){vibration=!vibration;prefs.edit().putBoolean("vibration",vibration).apply();haptic(20);return;}
            if(id.equals("controls")){mode=CONTROLS;playSfx(SFX_MENU);return;}
            if(id.equals("joyminus")){joyScale=clamp(joyScale-.1f,.65f,1.45f);updateControlRects();saveControls();return;}
            if(id.equals("joyplus")){joyScale=clamp(joyScale+.1f,.65f,1.45f);updateControlRects();saveControls();return;}
            if(id.equals("kickminus")){kickScale=clamp(kickScale-.1f,.65f,1.45f);updateControlRects();saveControls();return;}
            if(id.equals("kickplus")){kickScale=clamp(kickScale+.1f,.65f,1.45f);updateControlRects();saveControls();return;}
            if(id.equals("controlreset")){joyNormX=.115f;joyNormY=.82f;kickNormX=.91f;kickNormY=.82f;joyScale=kickScale=1f;updateControlRects();saveControls();return;}
            if(id.equals("controlsave")){saveControls();mode=SETTINGS;playSfx(SFX_MENU);}
        }'''
s = replace_method(s, 'click', click)

s = s.replace('putInt("target_goals",targetGoals).apply();',
              'putInt("target_goals",targetGoals).putInt("field_theme",fieldTheme).apply();')

# Separate app id for side-by-side testing.
s = s.replace('circle_football_v23', 'circle_football_v24')
path.write_text(s, encoding='utf-8')

manifest = Path('AndroidManifest.xml')
m = manifest.read_text(encoding='utf-8')
m = m.replace('com.godnit.circlefootballlite.v23', 'com.godnit.circlefootballlite.v24')
m = re.sub(r'android:versionCode="\d+"', 'android:versionCode="15"', m, count=1)
m = re.sub(r'android:versionName="[^"]+"', 'android:versionName="2.4.0"', m, count=1)
manifest.write_text(m, encoding='utf-8')

print('Applied Circle Football v2.4 stadium themes, trajectory guide, goal-line and stable squeeze physics')
