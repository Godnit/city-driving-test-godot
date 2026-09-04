package com.godnit.circlefootballlite;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;
import android.os.Bundle;
import android.os.SystemClock;
import android.os.Vibrator;
import android.view.MotionEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Random;

public class MainActivity extends Activity {
    private GameView gameView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        hideSystemUI();
        gameView = new GameView(this);
        setContentView(gameView);
    }

    private void hideSystemUI() {
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
                View.SYSTEM_UI_FLAG_FULLSCREEN |
                View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }

    @Override public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideSystemUI();
    }

    @Override public void onBackPressed() {
        if (gameView != null && gameView.handleBack()) return;
        super.onBackPressed();
    }

    static final class GameView extends View {
        static final int HOME=0, SETUP=1, GAME=2, PAUSE=3, PLAYERS=4, SETTINGS=5, CONTROLS=6, RESULT=7;
        static final int SFX_MENU=0, SFX_KICK=1, SFX_WALL=2, SFX_GOAL=3, SFX_WIN=4, SFX_LOSE=5, SFX_PASS=6;

        final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        final Paint stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
        final Path path = new Path();
        final SharedPreferences prefs;
        final Random rng = new Random();
        final List<ButtonHit> hits = new ArrayList<>();
        final List<Particle> particles = new ArrayList<>();

        int mode=HOME, previousMode=GAME;
        int difficulty=1, teamSize=2, targetGoals=5;
        boolean sounds=true, vibration=true;
        int w,h;
        float s=1f;
        final RectF pitch = new RectF();
        float goalHalf, discR, ballR;
        float bx,by,bvx,bvy;
        float ballAngle=0f, lastBallX, lastBallY, trailCarry=0f;
        float matchTime=180f;
        int blueScore=0, redScore=0;
        boolean goldenGoal=false, savedResult=false;
        long lastFrame=0L;

        final Disc[] blue = new Disc[4];
        final Disc[] red = new Disc[4];
        int blueChaser=-1, redChaser=0;

        int joyPointer=-1;
        float joyBaseX,joyBaseY,joyX,joyY,joyNX,joyNY;
        float joyNormX,joyNormY,kickNormX,kickNormY,joyScale,kickScale;
        final RectF kickButton = new RectF();
        final RectF pauseButton = new RectF();

        int editPointer=-1, editTarget=0;
        float touchSoundCooldown=0f, wallSoundCooldown=0f;

        static final String[] BLUE_NAMES={"YOU","NOVA","LEO","MIRA"};
        static final String[] RED_NAMES={"REX","AXIS","VEX","KIRO"};

        GameView(Context c) {
            super(c);
            setFocusable(true);
            setKeepScreenOn(true);
            stroke.setStyle(Paint.Style.STROKE);
            prefs=c.getSharedPreferences("circle_football_v16", Context.MODE_PRIVATE);
            difficulty=prefs.getInt("difficulty",1);
            teamSize=clampInt(prefs.getInt("team_size",2),1,4);
            targetGoals=prefs.getInt("target_goals",5);
            sounds=prefs.getBoolean("sounds",true);
            vibration=prefs.getBoolean("vibration",true);
            joyNormX=prefs.getFloat("joy_x",0.115f);
            joyNormY=prefs.getFloat("joy_y",0.82f);
            kickNormX=prefs.getFloat("kick_x",0.91f);
            kickNormY=prefs.getFloat("kick_y",0.82f);
            joyScale=prefs.getFloat("joy_scale",1f);
            kickScale=prefs.getFloat("kick_scale",1f);
            for(int i=0;i<4;i++){
                blue[i]=new Disc(0,i,BLUE_NAMES[i],i>0);
                red[i]=new Disc(1,i,RED_NAMES[i],true);
            }
        }

        @Override protected void onSizeChanged(int ww,int hh,int oldw,int oldh){
            w=ww;h=hh;
            s=Math.max(0.60f,Math.min(w/1280f,h/720f));
            float mx=w*0.065f,my=h*0.105f;
            pitch.set(mx,my,w-mx,h-my);
            goalHalf=pitch.height()*0.19f;
            discR=29f*s;
            ballR=15f*s;
            pauseButton.set(w-78*s,18*s,w-18*s,78*s);
            updateControlRects();
            resetPositions();
        }

        float joyRadius(){return 78f*s*joyScale;}
        float joyKnobRadius(){return 36f*s*joyScale;}
        float kickRadius(){return 67f*s*kickScale;}

        void updateControlRects(){
            float jr=joyRadius();
            joyBaseX=clamp(joyNormX*w,jr+8*s,w-jr-8*s);
            joyBaseY=clamp(joyNormY*h,jr+8*s,h-jr-8*s);
            joyNormX=joyBaseX/w;joyNormY=joyBaseY/h;
            float kr=kickRadius();
            float kx=clamp(kickNormX*w,kr+8*s,w-kr-8*s);
            float ky=clamp(kickNormY*h,kr+8*s,h-kr-8*s);
            kickNormX=kx/w;kickNormY=ky/h;
            kickButton.set(kx-kr,ky-kr,kx+kr,ky+kr);
            if(joyPointer<0){joyX=joyBaseX;joyY=joyBaseY;}
        }

        @Override protected void onDraw(Canvas c){
            super.onDraw(c);
            long now=System.nanoTime();
            float dt=lastFrame==0?0f:Math.min(0.035f,(now-lastFrame)/1_000_000_000f);
            lastFrame=now;
            hits.clear();
            if(mode==GAME){
                if(dt>0) updateGame(dt);
                drawGame(c);
            } else if(mode==PAUSE){
                drawGame(c); drawPause(c);
            } else if(mode==HOME) drawHome(c);
            else if(mode==SETUP) drawSetup(c);
            else if(mode==PLAYERS) drawPlayers(c);
            else if(mode==SETTINGS) drawSettings(c);
            else if(mode==CONTROLS) drawControlsEditor(c);
            else if(mode==RESULT) drawResult(c);
            postInvalidateOnAnimation();
        }

        void background(Canvas c){
            c.drawColor(Color.rgb(15,19,24));
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.rgb(28,33,42));
            c.drawRect(0,0,w,h,p);
        }

        void title(Canvas c,String text,float y,float size){
            p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextAlign(Paint.Align.CENTER);
            p.setTextSize(size*s);p.setColor(Color.WHITE);c.drawText(text,w/2f,y,p);
        }

        void subtitle(Canvas c,String text,float y,float size,int color){
            p.setTypeface(Typeface.DEFAULT);p.setTextAlign(Paint.Align.CENTER);
            p.setTextSize(size*s);p.setColor(color);c.drawText(text,w/2f,y,p);
        }

        void drawHome(Canvas c){
            background(c);
            drawLogo(c,w/2f,112*s);
            title(c,"CIRCLE FOOTBALL",185*s,43);
            subtitle(c,"OFFLINE TEAM EDITION",222*s,17,Color.rgb(150,175,205));
            float bw=430*s,bh=72*s,x=(w-bw)/2f,y=290*s;
            menuButton(c,"PLAY","play",x,y,bw,bh,Color.rgb(29,121,255));
            menuButton(c,"PLAYERS","players",x,y+92*s,bw,bh,Color.rgb(48,56,70));
            menuButton(c,"SETTINGS","settings",x,y+184*s,bw,bh,Color.rgb(48,56,70));
            subtitle(c,"1v1 • 2v2 • 3v3 • 4v4",h-34*s,16,Color.rgb(120,138,160));
        }

        void drawLogo(Canvas c,float x,float y){
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.rgb(32,104,238));c.drawCircle(x-72*s,y,34*s,p);
            p.setColor(Color.rgb(239,57,61));c.drawCircle(x+72*s,y,34*s,p);
            drawFootball(c,x,y,17*s,0f);
        }

        void drawSetup(Canvas c){
            background(c);
            title(c,"PLAY",72*s,38);
            subtitle(c,"Difficulty",118*s,18,Color.LTGRAY);
            String[] ds={"EASY","NORMAL","HARD"};
            float bw=210*s,gap=18*s,start=(w-(bw*3+gap*2))/2f;
            for(int i=0;i<3;i++) menuButton(c,ds[i],"diff"+i,start+i*(bw+gap),140*s,bw,58*s,
                    i==difficulty?Color.rgb(29,121,255):Color.rgb(48,56,70));

            subtitle(c,"Players",245*s,18,Color.LTGRAY);
            float bw2=155*s,gap2=14*s,total=bw2*4+gap2*3,start2=(w-total)/2f;
            for(int i=1;i<=4;i++) menuButton(c,i+"v"+i,"team"+i,start2+(i-1)*(bw2+gap2),268*s,bw2,58*s,
                    i==teamSize?Color.rgb(34,174,91):Color.rgb(48,56,70));

            subtitle(c,"Goal limit",375*s,18,Color.LTGRAY);
            int[] gs={3,5,7};
            for(int i=0;i<3;i++) menuButton(c,gs[i]+" GOALS","goal"+gs[i],start+i*(bw+gap),398*s,bw,58*s,
                    gs[i]==targetGoals?Color.rgb(245,165,35):Color.rgb(48,56,70));

            menuButton(c,"START MATCH","start",(w-440*s)/2f,515*s,440*s,70*s,Color.rgb(29,121,255));
            menuButton(c,"BACK","home",(w-240*s)/2f,604*s,240*s,54*s,Color.rgb(48,56,70));
        }

        void drawPlayers(Canvas c){
            background(c);
            title(c,"PLAYERS",74*s,38);
            subtitle(c,"Roles adapt during the match. Only the nearest player presses the ball.",110*s,16,Color.rgb(150,165,185));
            float cardW=460*s,cardH=76*s,gap=14*s;
            float left=w/2f-cardW-18*s,right=w/2f+18*s;
            p.setTextAlign(Paint.Align.LEFT);
            for(int i=0;i<4;i++){
                playerCard(c,left,150*s+i*(cardH+gap),cardW,cardH,BLUE_NAMES[i],0,i);
                playerCard(c,right,150*s+i*(cardH+gap),cardW,cardH,RED_NAMES[i],1,i);
            }
            menuButton(c,"BACK","home",(w-240*s)/2f,h-70*s,240*s,52*s,Color.rgb(48,56,70));
        }

        void playerCard(Canvas c,float x,float y,float ww,float hh,String name,int team,int idx){
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(39,45,56));
            c.drawRoundRect(new RectF(x,y,x+ww,y+hh),14*s,14*s,p);
            p.setColor(team==0?Color.rgb(36,104,235):Color.rgb(239,57,61));
            c.drawCircle(x+37*s,y+hh/2f,22*s,p);
            p.setColor(Color.WHITE);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextAlign(Paint.Align.LEFT);p.setTextSize(19*s);
            c.drawText(name,x+76*s,y+31*s,p);
            String role;
            if(idx==0&&team==0) role="YOU • CONTROLLED";
            else if(idx==3) role="DEFENDER / COVER";
            else if(idx==1) role="PRESS / ATTACK";
            else role="SUPPORT / PASS";
            p.setTypeface(Typeface.DEFAULT);p.setTextSize(14*s);p.setColor(Color.rgb(155,170,190));
            c.drawText(role,x+76*s,y+55*s,p);
        }

        void drawSettings(Canvas c){
            background(c);
            title(c,"SETTINGS",80*s,38);
            float bw=430*s,x=(w-bw)/2f;
            menuButton(c,sounds?"GAME SFX: ON":"GAME SFX: OFF","sounds",x,165*s,bw,64*s,
                    sounds?Color.rgb(34,174,91):Color.rgb(88,94,105));
            menuButton(c,vibration?"VIBRATION: ON":"VIBRATION: OFF","vibration",x,245*s,bw,64*s,
                    vibration?Color.rgb(34,174,91):Color.rgb(88,94,105));
            menuButton(c,"EDIT CONTROLS","controls",x,325*s,bw,68*s,Color.rgb(29,121,255));
            subtitle(c,"Move and resize the joystick and KICK button.",430*s,16,Color.rgb(150,165,185));
            menuButton(c,"BACK","home",(w-240*s)/2f,510*s,240*s,56*s,Color.rgb(48,56,70));
        }

        void drawControlsEditor(Canvas c){
            background(c);
            title(c,"CONTROL LAYOUT",62*s,32);
            subtitle(c,"Drag either control. Use +/- to resize.",94*s,15,Color.rgb(155,170,190));
            float bw=145*s,gap=12*s,total=bw*4+gap*3,x=(w-total)/2f,y=118*s;
            menuButton(c,"JOY -","joyminus",x,y,bw,50*s,Color.rgb(48,56,70));
            menuButton(c,"JOY +","joyplus",x+bw+gap,y,bw,50*s,Color.rgb(48,56,70));
            menuButton(c,"KICK -","kickminus",x+(bw+gap)*2,y,bw,50*s,Color.rgb(48,56,70));
            menuButton(c,"KICK +","kickplus",x+(bw+gap)*3,y,bw,50*s,Color.rgb(48,56,70));
            stroke.setColor(Color.rgb(74,82,94));stroke.setStrokeWidth(2*s);
            c.drawRoundRect(new RectF(28*s,195*s,w-28*s,h-82*s),18*s,18*s,stroke);
            drawJoystick(c,true);drawKick(c,true);
            menuButton(c,"RESET","controlreset",45*s,h-66*s,175*s,48*s,Color.rgb(126,60,68));
            menuButton(c,"SAVE & BACK","controlsave",w-270*s,h-66*s,225*s,48*s,Color.rgb(34,174,91));
        }

        void menuButton(Canvas c,String label,String id,float x,float y,float ww,float hh,int color){
            RectF r=new RectF(x,y,x+ww,y+hh);
            p.setStyle(Paint.Style.FILL);p.setColor(color);c.drawRoundRect(r,15*s,15*s,p);
            p.setColor(Color.argb(40,255,255,255));c.drawRoundRect(new RectF(x+2*s,y+2*s,x+ww-2*s,y+hh*.46f),13*s,13*s,p);
            p.setColor(Color.WHITE);p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(19*s);
            Paint.FontMetrics fm=p.getFontMetrics();
            float ty=y+hh/2f-(fm.ascent+fm.descent)/2f;
            c.drawText(label,x+ww/2f,ty,p);
            hits.add(new ButtonHit(id,r));
        }

        void drawGame(Canvas c){
            c.drawColor(Color.rgb(17,22,27));
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(61,67,73));c.drawRect(pitch,p);
            for(int i=0;i<10;i++){
                p.setColor(i%2==0?Color.rgb(65,71,77):Color.rgb(58,64,70));
                float xx=pitch.left+pitch.width()*i/10f;
                c.drawRect(xx,pitch.top,xx+pitch.width()/10f,pitch.bottom,p);
            }
            stroke.setColor(Color.WHITE);stroke.setStrokeWidth(3*s);
            c.drawRect(pitch,stroke);c.drawLine(pitch.centerX(),pitch.top,pitch.centerX(),pitch.bottom,stroke);
            c.drawCircle(pitch.centerX(),pitch.centerY(),78*s,stroke);c.drawCircle(pitch.centerX(),pitch.centerY(),4*s,stroke);
            drawGoals(c);
            drawParticles(c);
            for(int i=0;i<teamSize;i++) drawDisc(c,blue[i]);
            for(int i=0;i<teamSize;i++) drawDisc(c,red[i]);
            drawFootball(c,bx,by,ballR,ballAngle);
            drawScoreHud(c);
            drawJoystick(c,false);drawKick(c,false);
        }

        void drawGoals(Canvas c){
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf;
            stroke.setColor(Color.rgb(225,230,235));stroke.setStrokeWidth(3*s);
            c.drawRect(new RectF(pitch.left-42*s,y1,pitch.left,y2),stroke);
            c.drawRect(new RectF(pitch.right,y1,pitch.right+42*s,y2),stroke);
            stroke.setStrokeWidth(1*s);stroke.setColor(Color.rgb(145,155,165));
            for(int i=1;i<4;i++){
                float yy=y1+(y2-y1)*i/4f;
                c.drawLine(pitch.left-42*s,yy,pitch.left,yy,stroke);
                c.drawLine(pitch.right,yy,pitch.right+42*s,yy,stroke);
            }
        }

        void drawDisc(Canvas c,Disc d){
            int col=d.team==0?Color.rgb(35,103,235):Color.rgb(239,57,61);
            p.setStyle(Paint.Style.FILL);p.setColor(Color.BLACK);c.drawCircle(d.x,d.y,discR+3*s,p);
            p.setColor(col);c.drawCircle(d.x,d.y,discR,p);
            p.setColor(Color.argb(82,255,255,255));c.drawCircle(d.x-discR*.28f,d.y-discR*.30f,discR*.22f,p);
            if((d.team==0?blueChaser:redChaser)==d.index && d.ai){
                stroke.setColor(Color.argb(120,255,255,255));stroke.setStrokeWidth(2*s);
                c.drawCircle(d.x,d.y,discR+7*s,stroke);
            }
            p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(12*s);p.setColor(Color.WHITE);
            c.drawText(d.name,d.x,d.y+discR+17*s,p);
        }

        void drawFootball(Canvas c,float x,float y,float r,float angle){
            c.save();c.rotate(angle,x,y);
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.argb(75,0,0,0));c.drawCircle(x+2*s,y+3*s,r*1.04f,p);
            p.setColor(Color.rgb(245,246,244));c.drawCircle(x,y,r,p);
            stroke.setStyle(Paint.Style.STROKE);stroke.setStrokeWidth(Math.max(1f,1.2f*s));stroke.setColor(Color.rgb(55,58,61));
            c.drawCircle(x,y,r,stroke);
            polygon(c,x,y,r*.32f,5,-90f,Color.rgb(28,30,32),true);
            for(int i=0;i<5;i++){
                double a=Math.toRadians(-90+i*72);
                float px=x+(float)Math.cos(a)*r*.68f, py=y+(float)Math.sin(a)*r*.68f;
                polygon(c,px,py,r*.20f,5,-90f+i*72,Color.rgb(38,40,42),true);
                stroke.setColor(Color.rgb(75,78,80));stroke.setStrokeWidth(Math.max(1f,.8f*s));
                c.drawLine(x+(float)Math.cos(a)*r*.31f,y+(float)Math.sin(a)*r*.31f,px,py,stroke);
            }
            p.setColor(Color.argb(92,255,255,255));c.drawCircle(x-r*.30f,y-r*.34f,r*.24f,p);
            c.restore();
        }

        void polygon(Canvas c,float cx,float cy,float rad,int sides,float deg,int color,boolean fill){
            path.reset();
            for(int i=0;i<sides;i++){
                double a=Math.toRadians(deg+i*360f/sides);
                float x=cx+(float)Math.cos(a)*rad,y=cy+(float)Math.sin(a)*rad;
                if(i==0) path.moveTo(x,y); else path.lineTo(x,y);
            }
            path.close();p.setStyle(fill?Paint.Style.FILL:Paint.Style.STROKE);p.setColor(color);c.drawPath(path,p);
        }

        void drawParticles(Canvas c){
            for(int i=0;i<particles.size();i++){
                Particle q=particles.get(i);
                float a=clamp(q.life/q.maxLife,0f,1f);
                int alpha=(int)(150*a);
                p.setColor(Color.argb(alpha,235,240,245));
                p.setStrokeWidth(Math.max(1f,q.radius*a));
                c.drawLine(q.x,q.y,q.x-q.vx*.032f,q.y-q.vy*.032f,p);
                p.setColor(Color.argb((int)(70*a),255,255,255));
                c.drawCircle(q.x,q.y,q.radius*.55f*a,p);
            }
        }

        void drawScoreHud(Canvas c){
            p.setStyle(Paint.Style.FILL);p.setColor(Color.argb(215,9,12,16));
            RectF hud=new RectF(w/2f-182*s,12*s,w/2f+182*s,68*s);c.drawRoundRect(hud,16*s,16*s,p);
            p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(25*s);
            p.setColor(Color.rgb(83,147,255));c.drawText(""+blueScore,w/2f-95*s,49*s,p);
            p.setColor(Color.WHITE);c.drawText("-",w/2f,49*s,p);
            p.setColor(Color.rgb(255,91,92));c.drawText(""+redScore,w/2f+95*s,49*s,p);
            p.setTextSize(13*s);p.setColor(Color.LTGRAY);
            String t=goldenGoal?"GOLDEN":formatTime(matchTime);
            c.drawText(t+"  •  "+teamSize+"v"+teamSize,w/2f,28*s,p);
            p.setColor(Color.argb(225,45,50,58));c.drawRoundRect(pauseButton,12*s,12*s,p);
            p.setColor(Color.WHITE);p.setTextSize(24*s);c.drawText("II",pauseButton.centerX(),pauseButton.centerY()+8*s,p);
        }

        void drawJoystick(Canvas c,boolean editor){
            float r=joyRadius();
            p.setStyle(Paint.Style.FILL);p.setColor(Color.argb(editor?95:82,255,255,255));c.drawCircle(joyBaseX,joyBaseY,r,p);
            float kx=joyPointer>=0?joyX:joyBaseX,ky=joyPointer>=0?joyY:joyBaseY;
            p.setColor(Color.argb(editor?185:150,255,255,255));c.drawCircle(kx,ky,joyKnobRadius(),p);
            if(editor){stroke.setColor(Color.rgb(95,150,235));stroke.setStrokeWidth(2*s);c.drawCircle(joyBaseX,joyBaseY,r+5*s,stroke);}
        }

        void drawKick(Canvas c,boolean editor){
            p.setStyle(Paint.Style.FILL);p.setColor(Color.argb(editor?195:170,28,116,255));c.drawOval(kickButton,p);
            p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(20*s*kickScale);p.setColor(Color.WHITE);
            c.drawText("KICK",kickButton.centerX(),kickButton.centerY()+7*s*kickScale,p);
            if(editor){stroke.setColor(Color.rgb(105,160,240));stroke.setStrokeWidth(2*s);c.drawOval(kickButton,stroke);}
        }

        void drawPause(Canvas c){
            p.setColor(Color.argb(195,10,12,16));c.drawRect(0,0,w,h,p);
            title(c,"MATCH PAUSED",180*s,40);
            menuButton(c,"RESUME","resume",(w-400*s)/2f,250*s,400*s,64*s,Color.rgb(29,121,255));
            menuButton(c,"RESTART","restart",(w-400*s)/2f,332*s,400*s,60*s,Color.rgb(48,56,70));
            menuButton(c,"MAIN MENU","home",(w-400*s)/2f,410*s,400*s,60*s,Color.rgb(144,54,62));
        }

        void drawResult(Canvas c){
            background(c);
            String text=blueScore>redScore?"YOU WIN":(blueScore<redScore?"RED WINS":"DRAW");
            int col=blueScore>redScore?Color.rgb(50,210,112):(blueScore<redScore?Color.rgb(244,72,75):Color.rgb(245,195,46));
            p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(48*s);p.setColor(col);
            c.drawText(text,w/2f,160*s,p);
            p.setTextSize(64*s);p.setColor(Color.WHITE);c.drawText(blueScore+"  -  "+redScore,w/2f,255*s,p);
            subtitle(c,difficultyName()+" • "+teamSize+"v"+teamSize,310*s,17,Color.rgb(150,165,185));
            menuButton(c,"REMATCH","rematch",(w-420*s)/2f,390*s,420*s,66*s,Color.rgb(29,121,255));
            menuButton(c,"PLAY SETUP","play",(w-420*s)/2f,475*s,420*s,60*s,Color.rgb(48,56,70));
            menuButton(c,"MAIN MENU","home",(w-420*s)/2f,553*s,420*s,60*s,Color.rgb(48,56,70));
        }

        void updateGame(float dt){
            if(!goldenGoal){
                matchTime-=dt;
                if(matchTime<=0){
                    matchTime=0;
                    if(blueScore==redScore) goldenGoal=true; else finishMatch();
                }
            }
            if(mode!=GAME)return;
            for(int i=0;i<teamSize;i++){blue[i].kickCd=Math.max(0,blue[i].kickCd-dt);red[i].kickCd=Math.max(0,red[i].kickCd-dt);}
            wallSoundCooldown=Math.max(0,wallSoundCooldown-dt);
            touchSoundCooldown=Math.max(0,touchSoundCooldown-dt);

            updateHuman(dt);
            chooseChasers();
            updateTeamAI(blue,red,0,blueChaser,dt);
            updateTeamAI(red,blue,1,redChaser,dt);

            int steps=Math.max(1,Math.min(6,(int)Math.ceil(dt/0.0065f)));
            float sub=dt/steps;
            for(int st=0;st<steps;st++) physicsStep(sub);
            updateParticles(dt);
        }

        void updateHuman(float dt){
            Disc d=blue[0];
            float speed=300*s;
            float wx=joyNX*speed,wy=joyNY*speed;
            float k=Math.min(1f,dt*15f);
            d.vx+=(wx-d.vx)*k;d.vy+=(wy-d.vy)*k;
            if(joyPointer<0){float damp=(float)Math.pow(.82,dt*60);d.vx*=damp;d.vy*=damp;}
        }

        void chooseChasers(){
            redChaser=closestToBall(red,0,teamSize);
            int closestBlue=closestToBall(blue,0,teamSize);
            if(closestBlue==0) blueChaser=-1;
            else {
                float humanDist=dist(blue[0].x,blue[0].y,bx,by);
                float aiDist=dist(blue[closestBlue].x,blue[closestBlue].y,bx,by);
                blueChaser=(aiDist+28*s<humanDist)?closestBlue:-1;
            }
        }

        int closestToBall(Disc[] t,int from,int count){
            int best=from;float bd=Float.MAX_VALUE;
            for(int i=from;i<count;i++){
                float d2=sq(t[i].x-bx)+sq(t[i].y-by);
                if(d2<bd){bd=d2;best=i;}
            }
            return best;
        }

        void updateTeamAI(Disc[] team,Disc[] opp,int teamId,int chaser,float dt){
            for(int i=0;i<teamSize;i++){
                Disc d=team[i];
                if(!d.ai)continue;
                float tx,ty;
                if(i==chaser){
                    float[] target=chooseKickTarget(d,team,opp,teamId);
                    float dx=target[0]-bx,dy=target[1]-by,ll=len(dx,dy);if(ll<1)ll=1;
                    float dirX=dx/ll,dirY=dy/ll;
                    float behind=discR+ballR+7*s;
                    tx=bx-dirX*behind;ty=by-dirY*behind;
                    float bd=dist(d.x,d.y,bx,by);
                    float cdx=bx-d.x,cdy=by-d.y,cl=len(cdx,cdy);if(cl<1)cl=1;
                    float align=(cdx/cl)*dirX+(cdy/cl)*dirY;
                    if(bd<=kickReach() && align>.80f && d.kickCd<=0f){
                        boolean isPass=target[2]>.5f;
                        cpuKick(d,isPass?590*s:(difficulty==0?580*s:difficulty==1?655*s:710*s),dirX,dirY,isPass);
                    }
                }else{
                    float[] pos=formationTarget(teamId,i,chaser);
                    tx=pos[0];ty=pos[1];
                    if(dist(d.x,d.y,bx,by)<discR*3.1f){
                        float awayX=d.x-bx,awayY=d.y-by,al=len(awayX,awayY);if(al<1)al=1;
                        tx+=awayX/al*55*s;ty+=awayY/al*55*s;
                    }
                }
                moveAiToward(d,tx,ty,dt);
            }
        }

        float[] chooseKickTarget(Disc d,Disc[] team,Disc[] opp,int teamId){
            float goalX=teamId==0?pitch.right+35*s:pitch.left-35*s;
            float goalY=pitch.centerY();
            Disc blocker=nearestOpponentToLine(opp,bx,by,goalX,goalY);
            if(blocker!=null && distToSegment(blocker.x,blocker.y,bx,by,goalX,goalY)<discR*2.0f)
                goalY=clamp(pitch.centerY()+(blocker.y<pitch.centerY()?goalHalf*.58f:-goalHalf*.58f),
                        pitch.centerY()-goalHalf*.72f,pitch.centerY()+goalHalf*.72f);

            int crowd=countOpponentsNear(opp,d.x,d.y,120*s);
            boolean laneBlocked=isLaneBlocked(opp,bx,by,goalX,goalY,discR*1.8f);
            int passTo=bestPassTarget(d,team,opp,teamId);
            boolean farFromGoal=teamId==0?bx<pitch.right-pitch.width()*.28f:bx>pitch.left+pitch.width()*.28f;
            if(passTo>=0 && (crowd>=2 || (laneBlocked&&farFromGoal))){
                Disc mate=team[passTo];
                return new float[]{mate.x+mate.vx*.18f,mate.y+mate.vy*.18f,1f};
            }
            return new float[]{goalX,goalY,0f};
        }

        int bestPassTarget(Disc d,Disc[] team,Disc[] opp,int teamId){
            int best=-1;float bestScore=-99999;
            for(int i=0;i<teamSize;i++){
                Disc m=team[i];if(m==d)continue;
                float passDist=dist(d.x,d.y,m.x,m.y);
                if(passDist<100*s||passDist>pitch.width()*.58f)continue;
                if(isLaneBlocked(opp,bx,by,m.x,m.y,discR*1.35f))continue;
                float open=nearestOpponentDistance(opp,m.x,m.y);
                float forward=teamId==0?(m.x-d.x):(d.x-m.x);
                float score=open*.75f+forward*.25f-passDist*.08f;
                if(i==0&&teamId==0)score+=25*s;
                if(score>bestScore){bestScore=score;best=i;}
            }
            return best;
        }

        float[] formationTarget(int teamId,int idx,int chaser){
            float ownX=teamId==0?pitch.left:pitch.right;
            float attackSign=teamId==0?1f:-1f;
            float x,y;
            if(idx==teamSize-1 && teamSize>=2){
                x=ownX+attackSign*pitch.width()*.18f;
                y=clamp(by,pitch.centerY()-goalHalf*.85f,pitch.centerY()+goalHalf*.85f);
            }else{
                float slot=(idx%3)-1f;
                x=pitch.centerX()-attackSign*pitch.width()*.10f;
                if(teamId==0)x=clamp(bx-100*s,pitch.left+pitch.width()*.28f,pitch.right-pitch.width()*.20f);
                else x=clamp(bx+100*s,pitch.left+pitch.width()*.20f,pitch.right-pitch.width()*.28f);
                if(idx==chaser)x-=attackSign*65*s;
                y=pitch.centerY()+slot*pitch.height()*.24f;
                if(teamSize==2)y=pitch.centerY()+(by<pitch.centerY()?pitch.height()*.20f:-pitch.height()*.20f);
            }
            return new float[]{clamp(x,pitch.left+discR,pitch.right-discR),clamp(y,pitch.top+discR,pitch.bottom-discR)};
        }

        void moveAiToward(Disc d,float tx,float ty,float dt){
            float dx=tx-d.x,dy=ty-d.y,l=len(dx,dy);
            float speed=(difficulty==0?220:difficulty==1?270:300)*s;
            float wx=0,wy=0;if(l>2*s){wx=dx/l*speed;wy=dy/l*speed;}
            float response=difficulty==0?5.2f:difficulty==1?7.8f:9.5f;
            float k=Math.min(1f,dt*response);
            d.vx+=(wx-d.vx)*k;d.vy+=(wy-d.vy)*k;
        }

        void cpuKick(Disc d,float power,float desiredX,float desiredY,boolean pass){
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);if(l<1)l=1;
            float nx=dx/l,ny=dy/l;
            float align=nx*desiredX+ny*desiredY;
            if(align<.76f || l>kickReach())return;
            bvx += nx*power + d.vx*.15f;
            bvy += ny*power + d.vy*.15f;
            d.kickCd=pass?.42f:.34f;
            spawnKickBurst(nx,ny,power);
            playSfx(pass?SFX_PASS:SFX_KICK);
        }

        float kickReach(){return discR+ballR+11*s;}

        void physicsStep(float dt){
            for(int i=0;i<teamSize;i++){
                Disc a=blue[i],b=red[i];
                a.x+=a.vx*dt;a.y+=a.vy*dt;
                b.x+=b.vx*dt;b.y+=b.vy*dt;
                clampDisc(a);clampDisc(b);
            }
            for(int pass=0;pass<2;pass++) resolveAllDiscCollisions();

            lastBallX=bx;lastBallY=by;
            bx+=bvx*dt;by+=bvy*dt;
            float fr=(float)Math.pow(.9885,dt*60f);bvx*=fr;bvy*=fr;

            for(int pass=0;pass<3;pass++){
                for(int i=0;i<teamSize;i++){resolveBallDisc(blue[i]);resolveBallDisc(red[i]);}
            }
            handleBallWalls();

            float moved=dist(lastBallX,lastBallY,bx,by);
            if(moved>0.001f){
                float sign=(Math.abs(bvx)>Math.abs(bvy))?(bvx>=0?1f:-1f):(bvy>=0?-1f:1f);
                ballAngle += sign*(moved/Math.max(1f,ballR))*57.2958f;
            }
            emitMotionTrail(dt);
        }

        void resolveAllDiscCollisions(){
            for(int i=0;i<teamSize;i++){
                for(int j=i+1;j<teamSize;j++){resolveDiscDisc(blue[i],blue[j]);resolveDiscDisc(red[i],red[j]);}
                for(int j=0;j<teamSize;j++)resolveDiscDisc(blue[i],red[j]);
            }
        }

        void resolveDiscDisc(Disc a,Disc b){
            float dx=b.x-a.x,dy=b.y-a.y,min=discR*2f,d=len(dx,dy);
            if(d>=min)return;
            float nx,ny;
            if(d<.001f){nx=(a.index<=b.index)?1f:-1f;ny=0f;d=.001f;}else{nx=dx/d;ny=dy/d;}
            float overlap=min-d+0.35f*s;
            a.x-=nx*overlap*.5f;a.y-=ny*overlap*.5f;b.x+=nx*overlap*.5f;b.y+=ny*overlap*.5f;
            float rel=(b.vx-a.vx)*nx+(b.vy-a.vy)*ny;
            if(rel<0){
                float imp=-rel*.42f;
                a.vx-=nx*imp;a.vy-=ny*imp;b.vx+=nx*imp;b.vy+=ny*imp;
            }
            clampDisc(a);clampDisc(b);
        }

        void resolveBallDisc(Disc d){
            float dx=bx-d.x,dy=by-d.y,min=discR+ballR,dst=len(dx,dy);
            if(dst>=min)return;
            float nx,ny;
            if(dst<.001f){
                float vl=len(bvx-d.vx,bvy-d.vy);
                if(vl>.1f){nx=(bvx-d.vx)/vl;ny=(bvy-d.vy)/vl;}else{nx=d.team==0?1f:-1f;ny=0f;}
                dst=.001f;
            }else{nx=dx/dst;ny=dy/dst;}
            float overlap=min-dst+0.75f*s;
            bx+=nx*overlap;by+=ny*overlap;
            float rel=(bvx-d.vx)*nx+(bvy-d.vy)*ny;
            if(rel<0){
                float impulse=-(1.56f)*rel;
                bvx+=nx*impulse+d.vx*.10f;
                bvy+=ny*impulse+d.vy*.10f;
            }else{
                bvx+=d.vx*.014f;bvy+=d.vy*.014f;
            }
        }

        void handleBallWalls(){
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf;
            boolean bounced=false;
            if(by-ballR<pitch.top){by=pitch.top+ballR;bvy=Math.abs(bvy)*.84f;bounced=true;}
            if(by+ballR>pitch.bottom){by=pitch.bottom-ballR;bvy=-Math.abs(bvy)*.84f;bounced=true;}
            boolean mouth=by>y1+ballR*.2f&&by<y2-ballR*.2f;
            if(!mouth){
                if(bx-ballR<pitch.left){bx=pitch.left+ballR;bvx=Math.abs(bvx)*.86f;bounced=true;}
                if(bx+ballR>pitch.right){bx=pitch.right-ballR;bvx=-Math.abs(bvx)*.86f;bounced=true;}
            }else{
                float back=42*s;
                if(bx<pitch.left-back){scoreGoal(false);return;}
                if(bx>pitch.right+back){scoreGoal(true);return;}
            }
            if(bounced&&wallSoundCooldown<=0&&len(bvx,bvy)>100*s){playSfx(SFX_WALL);wallSoundCooldown=.06f;}
        }

        void emitMotionTrail(float dt){
            float speed=len(bvx,bvy);
            if(speed<300*s){trailCarry=0;return;}
            trailCarry+=speed*dt;
            float spacing=speed>650*s?13*s:20*s;
            while(trailCarry>=spacing){
                trailCarry-=spacing;
                float l=Math.max(1f,speed);
                float nx=bvx/l,ny=bvy/l;
                float jitter=(rng.nextFloat()-.5f)*ballR*.7f;
                float px=bx-nx*(ballR+6*s)-ny*jitter;
                float py=by-ny*(ballR+6*s)+nx*jitter;
                float life=speed>650*s?.34f:.24f;
                particles.add(new Particle(px,py,-nx*(70+speed*.10f),-ny*(70+speed*.10f),life,(2.2f+rng.nextFloat()*2.2f)*s));
                if(particles.size()>90)particles.remove(0);
            }
        }

        void spawnKickBurst(float nx,float ny,float power){
            for(int i=0;i<8;i++){
                float spread=(rng.nextFloat()-.5f)*1.2f;
                float px=bx-nx*ballR*.7f,py=by-ny*ballR*.7f;
                float vx=-nx*(120+rng.nextFloat()*150)*s - ny*spread*90*s;
                float vy=-ny*(120+rng.nextFloat()*150)*s + nx*spread*90*s;
                particles.add(new Particle(px,py,vx,vy,.28f,(2.2f+rng.nextFloat()*2f)*s));
            }
        }

        void updateParticles(float dt){
            for(int i=particles.size()-1;i>=0;i--){
                Particle q=particles.get(i);q.life-=dt;
                if(q.life<=0){particles.remove(i);continue;}
                q.x+=q.vx*dt;q.y+=q.vy*dt;
                q.vx*=Math.pow(.88,dt*60);q.vy*=Math.pow(.88,dt*60);
            }
        }

        void doKick(){
            Disc d=blue[0];if(d.kickCd>0)return;
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);
            if(l>kickReach())return;
            if(l<1)l=1;
            float nx=dx/l,ny=dy/l;
            float power=720*s;
            bvx+=nx*power+d.vx*.18f;bvy+=ny*power+d.vy*.18f;
            d.kickCd=.26f;
            spawnKickBurst(nx,ny,power);
            haptic(20);playSfx(SFX_KICK);
        }

        void scoreGoal(boolean blueGoal){
            if(mode!=GAME)return;
            if(blueGoal)blueScore++;else redScore++;
            playSfx(SFX_GOAL);haptic(70);
            if(blueScore>=targetGoals||redScore>=targetGoals||goldenGoal)finishMatch();
            else resetPositions();
        }

        void finishMatch(){
            if(mode==RESULT)return;
            mode=RESULT;
            if(!savedResult){playSfx(blueScore>redScore?SFX_WIN:SFX_LOSE);savedResult=true;}
            joyPointer=-1;joyNX=joyNY=0;joyX=joyBaseX;joyY=joyBaseY;
        }

        void resetPositions(){
            if(w<=0||h<=0)return;
            float cy=pitch.centerY();
            for(int i=0;i<4;i++){
                float lane=((i%3)-1)*pitch.height()*.22f;
                blue[i].x=pitch.left+pitch.width()*(i==0?.25f:(i==3?.18f:.32f));
                red[i].x=pitch.right-pitch.width()*(i==3?.18f:.32f);
                blue[i].y=clamp(cy+(i==0?pitch.height()*.10f:lane),pitch.top+discR,pitch.bottom-discR);
                red[i].y=clamp(cy+lane,pitch.top+discR,pitch.bottom-discR);
                blue[i].vx=blue[i].vy=red[i].vx=red[i].vy=0;
                blue[i].kickCd=red[i].kickCd=.20f;
            }
            bx=pitch.centerX();by=cy;bvx=bvy=0;ballAngle=0;particles.clear();trailCarry=0;
            for(int i=0;i<teamSize;i++){
                separateFromBall(blue[i]);separateFromBall(red[i]);
            }
        }

        void separateFromBall(Disc d){
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy),min=discR+ballR+8*s;
            if(l<min){
                if(l<1){dx=d.team==0?1:-1;dy=0;l=1;}
                d.x=bx-dx/l*min;d.y=by-dy/l*min;clampDisc(d);
            }
        }

        void startMatch(){
            blueScore=redScore=0;matchTime=180f;goldenGoal=false;savedResult=false;
            mode=GAME;lastFrame=System.nanoTime();
            joyPointer=-1;joyNX=joyNY=0;joyX=joyBaseX;joyY=joyBaseY;
            prefs.edit().putInt("difficulty",difficulty).putInt("team_size",teamSize).putInt("target_goals",targetGoals).apply();
            resetPositions();playSfx(SFX_MENU);
        }

        void clampDisc(Disc d){
            d.x=clamp(d.x,pitch.left+discR,pitch.right-discR);
            d.y=clamp(d.y,pitch.top+discR,pitch.bottom-discR);
        }

        int countOpponentsNear(Disc[] opp,float x,float y,float r){
            int n=0;float rr=r*r;
            for(int i=0;i<teamSize;i++)if(sq(opp[i].x-x)+sq(opp[i].y-y)<rr)n++;
            return n;
        }

        float nearestOpponentDistance(Disc[] opp,float x,float y){
            float best=999999;
            for(int i=0;i<teamSize;i++)best=Math.min(best,dist(opp[i].x,opp[i].y,x,y));
            return best;
        }

        Disc nearestOpponentToLine(Disc[] opp,float x1,float y1,float x2,float y2){
            Disc best=null;float bd=Float.MAX_VALUE;
            for(int i=0;i<teamSize;i++){
                float d=distToSegment(opp[i].x,opp[i].y,x1,y1,x2,y2);
                if(d<bd){bd=d;best=opp[i];}
            }
            return best;
        }

        boolean isLaneBlocked(Disc[] opp,float x1,float y1,float x2,float y2,float radius){
            for(int i=0;i<teamSize;i++){
                float t=segmentT(opp[i].x,opp[i].y,x1,y1,x2,y2);
                if(t>.08f&&t<.94f&&distToSegment(opp[i].x,opp[i].y,x1,y1,x2,y2)<radius)return true;
            }
            return false;
        }

        float segmentT(float px,float py,float x1,float y1,float x2,float y2){
            float vx=x2-x1,vy=y2-y1,vv=vx*vx+vy*vy;if(vv<1)return 0;
            return ((px-x1)*vx+(py-y1)*vy)/vv;
        }

        float distToSegment(float px,float py,float x1,float y1,float x2,float y2){
            float t=clamp(segmentT(px,py,x1,y1,x2,y2),0f,1f);
            float qx=x1+(x2-x1)*t,qy=y1+(y2-y1)*t;
            return dist(px,py,qx,qy);
        }

        @Override public boolean onTouchEvent(MotionEvent e){
            int action=e.getActionMasked(),idx=e.getActionIndex();
            if(mode==CONTROLS)return handleControlTouch(e,action,idx);
            if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_POINTER_DOWN){
                float x=e.getX(idx),y=e.getY(idx);
                if(mode==GAME){
                    if(pauseButton.contains(x,y)){previousMode=GAME;mode=PAUSE;releaseJoy();return true;}
                    if(kickButton.contains(x,y)){doKick();return true;}
                    if(joyPointer<0&&dist(x,y,joyBaseX,joyBaseY)<=joyRadius()*1.35f){
                        joyPointer=e.getPointerId(idx);updateJoy(x,y);return true;
                    }
                }
            }
            if(action==MotionEvent.ACTION_MOVE&&joyPointer>=0){
                int pi=e.findPointerIndex(joyPointer);if(pi>=0)updateJoy(e.getX(pi),e.getY(pi));return true;
            }
            if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_POINTER_UP){
                int id=e.getPointerId(idx);float x=e.getX(idx),y=e.getY(idx);
                if(id==joyPointer)releaseJoy();
                if(action==MotionEvent.ACTION_UP&&mode!=GAME)processHit(x,y);
                return true;
            }
            if(action==MotionEvent.ACTION_CANCEL){releaseJoy();return true;}
            return true;
        }

        boolean handleControlTouch(MotionEvent e,int action,int idx){
            if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_POINTER_DOWN){
                float x=e.getX(idx),y=e.getY(idx);
                if(editPointer<0){
                    if(dist(x,y,joyBaseX,joyBaseY)<=joyRadius()*1.2f){editPointer=e.getPointerId(idx);editTarget=1;return true;}
                    if(kickButton.contains(x,y)){editPointer=e.getPointerId(idx);editTarget=2;return true;}
                }
            }
            if(action==MotionEvent.ACTION_MOVE&&editPointer>=0){
                int pi=e.findPointerIndex(editPointer);
                if(pi>=0){
                    float x=e.getX(pi),y=e.getY(pi);
                    if(editTarget==1){
                        float r=joyRadius();joyBaseX=clamp(x,r+8*s,w-r-8*s);joyBaseY=clamp(y,195*s+r,h-82*s-r);
                        joyNormX=joyBaseX/w;joyNormY=joyBaseY/h;joyX=joyBaseX;joyY=joyBaseY;
                    }else{
                        float r=kickRadius(),kx=clamp(x,r+8*s,w-r-8*s),ky=clamp(y,195*s+r,h-82*s-r);
                        kickNormX=kx/w;kickNormY=ky/h;kickButton.set(kx-r,ky-r,kx+r,ky+r);
                    }
                }
                return true;
            }
            if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_POINTER_UP){
                int id=e.getPointerId(idx);float x=e.getX(idx),y=e.getY(idx);
                if(id==editPointer){editPointer=-1;saveControls();return true;}
                if(action==MotionEvent.ACTION_UP)processHit(x,y);
            }
            return true;
        }

        void updateJoy(float x,float y){
            float dx=x-joyBaseX,dy=y-joyBaseY,max=joyRadius(),l=len(dx,dy);
            if(l>max){dx=dx/l*max;dy=dy/l*max;}
            joyX=joyBaseX+dx;joyY=joyBaseY+dy;joyNX=dx/max;joyNY=dy/max;
        }
        void releaseJoy(){joyPointer=-1;joyNX=joyNY=0;joyX=joyBaseX;joyY=joyBaseY;}

        void processHit(float x,float y){
            for(int i=hits.size()-1;i>=0;i--){ButtonHit b=hits.get(i);if(b.r.contains(x,y)){click(b.id);return;}}
        }

        void click(String id){
            if(id.equals("play")){playSfx(SFX_MENU);mode=SETUP;return;}
            if(id.equals("players")){playSfx(SFX_MENU);mode=PLAYERS;return;}
            if(id.equals("settings")){playSfx(SFX_MENU);mode=SETTINGS;return;}
            if(id.equals("home")){playSfx(SFX_MENU);mode=HOME;releaseJoy();return;}
            if(id.equals("start")){startMatch();return;}
            if(id.equals("resume")){playSfx(SFX_MENU);mode=GAME;lastFrame=System.nanoTime();return;}
            if(id.equals("restart")||id.equals("rematch")){startMatch();return;}
            if(id.startsWith("diff")){difficulty=Integer.parseInt(id.substring(4));prefs.edit().putInt("difficulty",difficulty).apply();playSfx(SFX_MENU);return;}
            if(id.startsWith("team")){teamSize=clampInt(Integer.parseInt(id.substring(4)),1,4);prefs.edit().putInt("team_size",teamSize).apply();playSfx(SFX_MENU);return;}
            if(id.startsWith("goal")){targetGoals=Integer.parseInt(id.substring(4));prefs.edit().putInt("target_goals",targetGoals).apply();playSfx(SFX_MENU);return;}
            if(id.equals("sounds")){sounds=!sounds;prefs.edit().putBoolean("sounds",sounds).apply();if(sounds)playSfx(SFX_MENU);return;}
            if(id.equals("vibration")){vibration=!vibration;prefs.edit().putBoolean("vibration",vibration).apply();haptic(20);return;}
            if(id.equals("controls")){mode=CONTROLS;playSfx(SFX_MENU);return;}
            if(id.equals("joyminus")){joyScale=clamp(joyScale-.1f,.65f,1.45f);updateControlRects();saveControls();return;}
            if(id.equals("joyplus")){joyScale=clamp(joyScale+.1f,.65f,1.45f);updateControlRects();saveControls();return;}
            if(id.equals("kickminus")){kickScale=clamp(kickScale-.1f,.65f,1.45f);updateControlRects();saveControls();return;}
            if(id.equals("kickplus")){kickScale=clamp(kickScale+.1f,.65f,1.45f);updateControlRects();saveControls();return;}
            if(id.equals("controlreset")){joyNormX=.115f;joyNormY=.82f;kickNormX=.91f;kickNormY=.82f;joyScale=kickScale=1f;updateControlRects();saveControls();return;}
            if(id.equals("controlsave")){saveControls();mode=SETTINGS;playSfx(SFX_MENU);}
        }

        void saveControls(){
            prefs.edit().putFloat("joy_x",joyNormX).putFloat("joy_y",joyNormY).putFloat("kick_x",kickNormX).putFloat("kick_y",kickNormY)
                    .putFloat("joy_scale",joyScale).putFloat("kick_scale",kickScale).apply();
        }

        boolean handleBack(){
            if(mode==GAME){previousMode=GAME;mode=PAUSE;releaseJoy();return true;}
            if(mode==PAUSE){mode=GAME;lastFrame=System.nanoTime();return true;}
            if(mode==CONTROLS){saveControls();mode=SETTINGS;return true;}
            if(mode!=HOME){mode=HOME;return true;}
            return false;
        }

        void haptic(long ms){
            if(!vibration)return;
            try{Vibrator v=(Vibrator)getContext().getSystemService(Context.VIBRATOR_SERVICE);if(v!=null&&v.hasVibrator())v.vibrate(ms);}catch(Exception ignored){}
        }

        void playSfx(final int type){
            if(!sounds)return;
            final short[] pcm=makeSfx(type);
            new Thread(new Runnable(){@Override public void run(){
                AudioTrack tr=null;
                try{
                    AudioAttributes attrs=new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build();
                    AudioFormat fmt=new AudioFormat.Builder().setEncoding(AudioFormat.ENCODING_PCM_16BIT).setSampleRate(22050).setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build();
                    tr=new AudioTrack(attrs,fmt,pcm.length*2,AudioTrack.MODE_STATIC,AudioManager.AUDIO_SESSION_ID_GENERATE);
                    tr.write(pcm,0,pcm.length);tr.play();SystemClock.sleep((long)(pcm.length*1000f/22050f)+25);
                }catch(Exception ignored){}finally{if(tr!=null){try{tr.stop();}catch(Exception ignored){}try{tr.release();}catch(Exception ignored){}}}
            }},"cf-sfx").start();
        }

        short[] makeSfx(int type){
            int ms=(type==SFX_GOAL||type==SFX_WIN||type==SFX_LOSE)?320:(type==SFX_KICK?95:55);
            int sr=22050,n=sr*ms/1000;short[] out=new short[n];
            for(int i=0;i<n;i++){
                double t=i/(double)sr,env=Math.max(0,1-i/(double)n),v;
                if(type==SFX_KICK)v=Math.sin(2*Math.PI*(110-45*i/(double)n)*t)*Math.pow(env,1.7)*.80+(rng.nextDouble()*2-1)*Math.pow(env,5)*.16;
                else if(type==SFX_PASS)v=Math.sin(2*Math.PI*260*t)*Math.pow(env,2)*.42;
                else if(type==SFX_WALL)v=Math.sin(2*Math.PI*540*t)*Math.pow(env,2.5)*.35;
                else if(type==SFX_GOAL)v=Math.sin(2*Math.PI*(t<.12?392:t<.23?523:659)*t)*env*.48;
                else if(type==SFX_WIN)v=Math.sin(2*Math.PI*(t<.11?523:t<.22?659:784)*t)*env*.48;
                else if(type==SFX_LOSE)v=Math.sin(2*Math.PI*(t<.11?330:t<.22?277:220)*t)*env*.40;
                else v=Math.sin(2*Math.PI*760*t)*env*.35;
                out[i]=(short)(clamp((float)v,-1,1)*26000);
            }
            return out;
        }

        String difficultyName(){return difficulty==0?"Easy":difficulty==1?"Normal":"Hard";}
        String formatTime(float t){int sec=Math.max(0,(int)Math.ceil(t));return String.format(Locale.US,"%d:%02d",sec/60,sec%60);}
        float len(float x,float y){return (float)Math.sqrt(x*x+y*y);}
        float dist(float x1,float y1,float x2,float y2){return len(x2-x1,y2-y1);}
        float sq(float v){return v*v;}
        float clamp(float v,float lo,float hi){return Math.max(lo,Math.min(hi,v));}
        int clampInt(int v,int lo,int hi){return Math.max(lo,Math.min(hi,v));}

        static final class Disc{
            final int team,index;final String name;final boolean ai;
            float x,y,vx,vy,kickCd;
            Disc(int team,int index,String name,boolean ai){this.team=team;this.index=index;this.name=name;this.ai=ai;}
        }
        static final class Particle{
            float x,y,vx,vy,life,maxLife,radius;
            Particle(float x,float y,float vx,float vy,float life,float radius){
                this.x=x;this.y=y;this.vx=vx;this.vy=vy;this.life=this.maxLife=life;this.radius=radius;
            }
        }
        static final class ButtonHit{
            final String id;final RectF r;
            ButtonHit(String id,RectF r){this.id=id;this.r=new RectF(r);}
        }
    }
}
