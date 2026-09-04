package com.godnit.circlefootballlite;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Vibrator;
import android.view.MotionEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class MainActivity extends Activity {
    private GameView gameView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN);
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

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideSystemUI();
    }

    @Override
    public void onBackPressed() {
        if (gameView != null && gameView.handleBack()) return;
        super.onBackPressed();
    }

    static final class GameView extends View {
        private static final int HOME = 0;
        private static final int SETUP = 1;
        private static final int GAME = 2;
        private static final int PAUSE = 3;
        private static final int RESULT = 4;
        private static final int TRAINING = 5;
        private static final int STATS = 6;
        private static final int SETTINGS = 7;

        private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final SharedPreferences prefs;
        private final List<ButtonHit> hits = new ArrayList<>();

        private int mode = HOME;
        private int previousMode = GAME;
        private int difficulty;
        private int targetGoals;
        private boolean vibration;
        private boolean training = false;

        private int w, h;
        private float s = 1f;
        private final RectF pitch = new RectF();
        private float goalHalf;
        private float discR;
        private float ballR;

        private float px, py, pvx, pvy;
        private float cx, cy, cvx, cvy;
        private float bx, by, bvx, bvy;
        private int blueScore = 0;
        private int redScore = 0;
        private float matchTime = 180f;
        private boolean goldenGoal = false;
        private boolean savedResult = false;
        private long lastFrame = 0L;
        private float kickCooldown = 0f;
        private float cpuKickCooldown = 0f;

        private int joyPointer = -1;
        private float joyBaseX, joyBaseY;
        private float joyX, joyY;
        private float joyNX, joyNY;
        private final RectF kickButton = new RectF();
        private final RectF pauseButton = new RectF();

        private int wins, losses, draws, matches, gf, ga;

        GameView(Context c) {
            super(c);
            setFocusable(true);
            setKeepScreenOn(true);
            stroke.setStyle(Paint.Style.STROKE);
            stroke.setStrokeWidth(4f);
            prefs = c.getSharedPreferences("circle_football", Context.MODE_PRIVATE);
            difficulty = prefs.getInt("difficulty", 1);
            targetGoals = prefs.getInt("target_goals", 5);
            vibration = prefs.getBoolean("vibration", true);
            wins = prefs.getInt("wins", 0);
            losses = prefs.getInt("losses", 0);
            draws = prefs.getInt("draws", 0);
            matches = prefs.getInt("matches", 0);
            gf = prefs.getInt("gf", 0);
            ga = prefs.getInt("ga", 0);
        }

        @Override
        protected void onSizeChanged(int ww, int hh, int oldw, int oldh) {
            w = ww;
            h = hh;
            s = Math.max(0.6f, Math.min(w / 1280f, h / 720f));
            float mx = w * 0.065f;
            float my = h * 0.105f;
            pitch.set(mx, my, w - mx, h - my);
            goalHalf = pitch.height() * 0.19f;
            discR = 29f * s;
            ballR = 14f * s;
            kickButton.set(w - 180f*s, h - 180f*s, w - 45f*s, h - 45f*s);
            pauseButton.set(w - 78f*s, 18f*s, w - 18f*s, 78f*s);
            resetPositions();
        }

        @Override
        protected void onDraw(Canvas c) {
            super.onDraw(c);
            long now = System.nanoTime();
            float dt = lastFrame == 0L ? 0f : Math.min(0.035f, (now - lastFrame) / 1_000_000_000f);
            lastFrame = now;
            hits.clear();

            if (mode == GAME || mode == TRAINING) {
                if (dt > 0f) updateGame(dt);
                drawGame(c);
            } else if (mode == PAUSE) {
                drawGame(c);
                drawPause(c);
            } else if (mode == HOME) {
                drawHome(c);
            } else if (mode == SETUP) {
                drawSetup(c);
            } else if (mode == RESULT) {
                drawResult(c);
            } else if (mode == STATS) {
                drawStats(c);
            } else if (mode == SETTINGS) {
                drawSettings(c);
            }
            postInvalidateOnAnimation();
        }

        private void background(Canvas c) {
            c.drawColor(Color.rgb(16, 19, 24));
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.rgb(28, 33, 42));
            c.drawRect(0, 0, w, h, p);
        }

        private void title(Canvas c, String text, float y, float size) {
            p.setTypeface(Typeface.DEFAULT_BOLD);
            p.setTextAlign(Paint.Align.CENTER);
            p.setTextSize(size * s);
            p.setColor(Color.WHITE);
            c.drawText(text, w/2f, y, p);
        }

        private void subtitle(Canvas c, String text, float y, float size, int color) {
            p.setTypeface(Typeface.DEFAULT);
            p.setTextAlign(Paint.Align.CENTER);
            p.setTextSize(size * s);
            p.setColor(color);
            c.drawText(text, w/2f, y, p);
        }

        private void drawHome(Canvas c) {
            background(c);
            p.setColor(Color.rgb(19, 125, 255));
            c.drawCircle(w/2f - 70*s, 112*s, 34*s, p);
            p.setColor(Color.rgb(236, 52, 58));
            c.drawCircle(w/2f + 70*s, 112*s, 34*s, p);
            p.setColor(Color.rgb(250, 209, 46));
            c.drawCircle(w/2f, 112*s, 15*s, p);
            title(c, "CIRCLE FOOTBALL", 185*s, 43);
            subtitle(c, "OFFLINE • CPU EDITION", 222*s, 18, Color.rgb(150, 175, 205));
            float bw = 420*s, bh = 64*s, x = (w-bw)/2f, y = 270*s;
            menuButton(c, "QUICK MATCH", "quick", x, y, bw, bh, Color.rgb(29, 121, 255));
            menuButton(c, "MATCH SETUP", "setup", x, y+78*s, bw, bh, Color.rgb(48, 56, 70));
            menuButton(c, "TRAINING", "training", x, y+156*s, bw, bh, Color.rgb(48, 56, 70));
            menuButton(c, "STATISTICS", "stats", x, y+234*s, bw, bh, Color.rgb(48, 56, 70));
            menuButton(c, "SETTINGS", "settings", x, y+312*s, bw, bh, Color.rgb(48, 56, 70));
            subtitle(c, "No internet required", h - 20*s, 16, Color.rgb(115, 130, 150));
        }

        private void drawSetup(Canvas c) {
            background(c);
            title(c, "MATCH SETUP", 85*s, 38);
            subtitle(c, "CPU difficulty", 145*s, 20, Color.LTGRAY);
            String[] ds = {"EASY", "NORMAL", "HARD"};
            float bw = 220*s, gap = 18*s;
            float start = (w - (bw*3 + gap*2))/2f;
            for (int i=0;i<3;i++) {
                int col = i==difficulty ? Color.rgb(29,121,255) : Color.rgb(48,56,70);
                menuButton(c, ds[i], "diff"+i, start+i*(bw+gap), 170*s, bw, 62*s, col);
            }
            subtitle(c, "Goal limit", 290*s, 20, Color.LTGRAY);
            int[] gs = {3,5,7};
            for (int i=0;i<3;i++) {
                int col = gs[i]==targetGoals ? Color.rgb(29,121,255) : Color.rgb(48,56,70);
                menuButton(c, Integer.toString(gs[i])+" GOALS", "goal"+gs[i], start+i*(bw+gap), 315*s, bw, 62*s, col);
            }
            menuButton(c, "START MATCH", "start", (w-440*s)/2f, 460*s, 440*s, 70*s, Color.rgb(34,174,91));
            menuButton(c, "BACK", "home", (w-260*s)/2f, 550*s, 260*s, 58*s, Color.rgb(48,56,70));
            subtitle(c, "Match time: 3 minutes • Tie = Golden Goal", 655*s, 17, Color.rgb(140,156,177));
        }

        private void drawStats(Canvas c) {
            background(c);
            title(c, "STATISTICS", 90*s, 38);
            float cardW = 250*s, cardH = 112*s, gap=18*s;
            float x0 = (w - (cardW*3+gap*2))/2f;
            statCard(c, "MATCHES", matches, x0, 160*s, cardW, cardH);
            statCard(c, "WINS", wins, x0+cardW+gap, 160*s, cardW, cardH);
            statCard(c, "LOSSES", losses, x0+(cardW+gap)*2, 160*s, cardW, cardH);
            statCard(c, "DRAWS", draws, x0, 295*s, cardW, cardH);
            statCard(c, "GOALS FOR", gf, x0+cardW+gap, 295*s, cardW, cardH);
            statCard(c, "GOALS AGAINST", ga, x0+(cardW+gap)*2, 295*s, cardW, cardH);
            menuButton(c, "CLEAR STATS", "clearstats", (w-300*s)/2f, 465*s, 300*s, 62*s, Color.rgb(149,50,58));
            menuButton(c, "BACK", "home", (w-260*s)/2f, 550*s, 260*s, 58*s, Color.rgb(48,56,70));
        }

        private void statCard(Canvas c, String label, int value, float x, float y, float ww, float hh) {
            p.setColor(Color.rgb(39,45,56));
            c.drawRoundRect(new RectF(x,y,x+ww,y+hh), 16*s,16*s,p);
            p.setTextAlign(Paint.Align.CENTER);
            p.setTypeface(Typeface.DEFAULT_BOLD);
            p.setTextSize(35*s);
            p.setColor(Color.WHITE);
            c.drawText(Integer.toString(value), x+ww/2f, y+50*s, p);
            p.setTypeface(Typeface.DEFAULT);
            p.setTextSize(14*s);
            p.setColor(Color.rgb(151,166,186));
            c.drawText(label, x+ww/2f, y+82*s, p);
        }

        private void drawSettings(Canvas c) {
            background(c);
            title(c, "SETTINGS", 90*s, 38);
            subtitle(c, "Vibration feedback", 190*s, 22, Color.LTGRAY);
            menuButton(c, vibration ? "VIBRATION: ON" : "VIBRATION: OFF", "vibration", (w-420*s)/2f, 220*s, 420*s, 65*s,
                    vibration ? Color.rgb(34,174,91) : Color.rgb(98,105,118));
            subtitle(c, "This version is pure Java: no game engine, no internet, no native libraries.", 340*s, 17, Color.rgb(145,160,181));
            subtitle(c, "Built for Android 5.0+ including Android 8.1.0.", 375*s, 17, Color.rgb(145,160,181));
            menuButton(c, "BACK", "home", (w-260*s)/2f, 490*s, 260*s, 58*s, Color.rgb(48,56,70));
        }

        private void drawResult(Canvas c) {
            background(c);
            String result = blueScore > redScore ? "YOU WIN" : (blueScore < redScore ? "CPU WINS" : "DRAW");
            int rc = blueScore > redScore ? Color.rgb(50,210,112) : (blueScore < redScore ? Color.rgb(244,72,75) : Color.rgb(245,195,46));
            p.setTextAlign(Paint.Align.CENTER);
            p.setTypeface(Typeface.DEFAULT_BOLD);
            p.setTextSize(48*s);
            p.setColor(rc);
            c.drawText(result, w/2f, 155*s, p);
            p.setTextSize(64*s);
            p.setColor(Color.WHITE);
            c.drawText(blueScore + "  -  " + redScore, w/2f, 250*s, p);
            subtitle(c, difficultyName()+" CPU • First to "+targetGoals+" or 3:00", 305*s, 18, Color.rgb(150,165,185));
            menuButton(c, "REMATCH", "rematch", (w-420*s)/2f, 385*s, 420*s, 68*s, Color.rgb(29,121,255));
            menuButton(c, "MATCH SETUP", "setup", (w-420*s)/2f, 470*s, 420*s, 62*s, Color.rgb(48,56,70));
            menuButton(c, "MAIN MENU", "home", (w-420*s)/2f, 548*s, 420*s, 62*s, Color.rgb(48,56,70));
        }

        private void drawPause(Canvas c) {
            p.setColor(Color.argb(190, 10, 12, 16));
            c.drawRect(0,0,w,h,p);
            title(c, previousMode == TRAINING ? "TRAINING PAUSED" : "MATCH PAUSED", 170*s, 42);
            menuButton(c, "RESUME", "resume", (w-400*s)/2f, 240*s, 400*s, 66*s, Color.rgb(29,121,255));
            menuButton(c, "RESTART", "restart", (w-400*s)/2f, 325*s, 400*s, 62*s, Color.rgb(48,56,70));
            menuButton(c, "MAIN MENU", "home", (w-400*s)/2f, 403*s, 400*s, 62*s, Color.rgb(149,50,58));
        }

        private void menuButton(Canvas c, String label, String id, float x, float y, float ww, float hh, int color) {
            RectF r = new RectF(x,y,x+ww,y+hh);
            p.setColor(color);
            p.setStyle(Paint.Style.FILL);
            c.drawRoundRect(r, 15*s,15*s,p);
            p.setColor(Color.argb(45,255,255,255));
            c.drawRoundRect(new RectF(x+2*s,y+2*s,x+ww-2*s,y+hh*0.48f), 13*s,13*s,p);
            p.setColor(Color.WHITE);
            p.setTypeface(Typeface.DEFAULT_BOLD);
            p.setTextAlign(Paint.Align.CENTER);
            p.setTextSize(20*s);
            Paint.FontMetrics fm = p.getFontMetrics();
            float ty = y+hh/2f-(fm.ascent+fm.descent)/2f;
            c.drawText(label, x+ww/2f, ty, p);
            hits.add(new ButtonHit(id,r));
        }

        private void drawGame(Canvas c) {
            c.drawColor(Color.rgb(17, 22, 27));
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.rgb(61, 67, 73));
            c.drawRect(pitch, p);
            for (int i=0;i<9;i++) {
                p.setColor(i%2==0 ? Color.rgb(64,70,76) : Color.rgb(58,64,70));
                float xx = pitch.left + pitch.width()*i/9f;
                c.drawRect(xx,pitch.top,xx+pitch.width()/9f,pitch.bottom,p);
            }
            stroke.setColor(Color.WHITE);
            stroke.setStrokeWidth(3*s);
            c.drawRect(pitch, stroke);
            c.drawLine(pitch.centerX(), pitch.top, pitch.centerX(), pitch.bottom, stroke);
            c.drawCircle(pitch.centerX(), pitch.centerY(), 78*s, stroke);
            c.drawCircle(pitch.centerX(), pitch.centerY(), 4*s, stroke);
            drawGoals(c);

            drawDisc(c, px, py, discR, Color.rgb(22,92,236), "YOU");
            if (!training) drawDisc(c, cx, cy, discR, Color.rgb(234,47,48), "CPU");
            p.setColor(Color.rgb(252,211,47));
            c.drawCircle(bx,by,ballR,p);
            stroke.setColor(Color.rgb(52,44,9));
            stroke.setStrokeWidth(2*s);
            c.drawCircle(bx,by,ballR,stroke);

            drawScoreHud(c);
            drawControls(c);
        }

        private void drawGoals(Canvas c) {
            float gy1 = pitch.centerY()-goalHalf;
            float gy2 = pitch.centerY()+goalHalf;
            stroke.setColor(Color.rgb(225,230,235));
            stroke.setStrokeWidth(3*s);
            RectF gl = new RectF(pitch.left-42*s,gy1,pitch.left,gy2);
            RectF gr = new RectF(pitch.right,gy1,pitch.right+42*s,gy2);
            c.drawRect(gl,stroke);
            c.drawRect(gr,stroke);
            stroke.setStrokeWidth(1*s);
            stroke.setColor(Color.rgb(145,155,165));
            for (int i=1;i<4;i++) {
                float yy=gy1+(gy2-gy1)*i/4f;
                c.drawLine(pitch.left-42*s,yy,pitch.left,yy,stroke);
                c.drawLine(pitch.right,yy,pitch.right+42*s,yy,stroke);
            }
        }

        private void drawDisc(Canvas c, float x, float y, float r, int color, String label) {
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.BLACK);
            c.drawCircle(x,y,r+3*s,p);
            p.setColor(color);
            c.drawCircle(x,y,r,p);
            p.setColor(Color.argb(80,255,255,255));
            c.drawCircle(x-r*0.28f,y-r*0.28f,r*0.24f,p);
            p.setTextAlign(Paint.Align.CENTER);
            p.setTypeface(Typeface.DEFAULT_BOLD);
            p.setTextSize(13*s);
            p.setColor(Color.WHITE);
            c.drawText(label,x,y+r+18*s,p);
        }

        private void drawScoreHud(Canvas c) {
            p.setColor(Color.argb(210, 10,13,17));
            RectF hud = new RectF(w/2f-175*s, 12*s, w/2f+175*s, 68*s);
            c.drawRoundRect(hud, 16*s,16*s,p);
            p.setTextAlign(Paint.Align.CENTER);
            p.setTypeface(Typeface.DEFAULT_BOLD);
            p.setTextSize(26*s);
            p.setColor(Color.rgb(83,147,255));
            c.drawText(Integer.toString(blueScore), w/2f-92*s, 49*s,p);
            p.setColor(Color.WHITE);
            c.drawText("-", w/2f,49*s,p);
            p.setColor(Color.rgb(255,91,92));
            c.drawText(Integer.toString(redScore), w/2f+92*s,49*s,p);
            if (training) {
                p.setTextSize(15*s); p.setColor(Color.LTGRAY); c.drawText("TRAINING",w/2f,29*s,p);
            } else {
                String tm = goldenGoal ? "GOLDEN" : formatTime(matchTime);
                p.setTextSize(15*s); p.setColor(goldenGoal ? Color.rgb(255,205,45) : Color.LTGRAY); c.drawText(tm,w/2f,29*s,p);
            }
            p.setColor(Color.argb(220,45,50,58));
            c.drawRoundRect(pauseButton,12*s,12*s,p);
            p.setColor(Color.WHITE); p.setTextSize(24*s); p.setTypeface(Typeface.DEFAULT_BOLD); p.setTextAlign(Paint.Align.CENTER);
            c.drawText("II",pauseButton.centerX(),pauseButton.centerY()+8*s,p);
        }

        private void drawControls(Canvas c) {
            float baseX = joyPointer >= 0 ? joyBaseX : 145*s;
            float baseY = joyPointer >= 0 ? joyBaseY : h-135*s;
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.argb(85,255,255,255));
            c.drawCircle(baseX,baseY,78*s,p);
            p.setColor(Color.argb(150,255,255,255));
            float knobX = joyPointer >=0 ? joyX : baseX;
            float knobY = joyPointer >=0 ? joyY : baseY;
            c.drawCircle(knobX,knobY,36*s,p);
            p.setColor(Color.argb(150, 28,116,255));
            c.drawOval(kickButton,p);
            p.setTextAlign(Paint.Align.CENTER);
            p.setTypeface(Typeface.DEFAULT_BOLD);
            p.setTextSize(20*s);
            p.setColor(Color.WHITE);
            c.drawText("KICK",kickButton.centerX(),kickButton.centerY()+7*s,p);
            if (training) {
                p.setColor(Color.argb(210,45,50,58));
                RectF rr = new RectF(w/2f-75*s, h-62*s, w/2f+75*s, h-18*s);
                c.drawRoundRect(rr,10*s,10*s,p);
                p.setTextSize(14*s); c.drawText("RESET BALL",w/2f,h-34*s,p);
                hits.add(new ButtonHit("resetball",rr));
            }
        }

        private void updateGame(float dt) {
            kickCooldown = Math.max(0f, kickCooldown-dt);
            cpuKickCooldown = Math.max(0f, cpuKickCooldown-dt);
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
            if (joyPointer < 0) { pvx *= Math.pow(0.82,dt*60); pvy *= Math.pow(0.82,dt*60); }
            px += pvx*dt; py += pvy*dt;
            clampDisc(true);

            if (!training) updateCpu(dt);

            bx += bvx*dt; by += bvy*dt;
            float friction = (float)Math.pow(0.987,dt*60f);
            bvx *= friction; bvy *= friction;
            collidePlayerBall(px,py,pvx,pvy);
            if (!training) collidePlayerBall(cx,cy,cvx,cvy);
            handleBallWalls();
        }

        private void updateCpu(float dt) {
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
                float len = len(dx,dy);
                if (len<1) len=1;
                tx = gx + dx/len*Math.min(120*s,len*0.45f);
                ty = gy + dy/len*Math.min(120*s,len*0.45f);
            } else {
                float dx = pbx-targetGoalX, dy=pby-pitch.centerY();
                float len=len(dx,dy); if(len<1)len=1;
                tx = pbx + dx/len*(discR+ballR+8*s);
                ty = pby + dy/len*(discR+ballR+8*s);
            }
            if (difficulty==0) { tx = tx*0.86f + (pitch.right-135*s)*0.14f; ty = ty*0.90f + pitch.centerY()*0.10f; }
            float dx=tx-cx, dy=ty-cy, l=len(dx,dy);
            float speed = (difficulty==0 ? 215 : difficulty==1 ? 270 : 315)*s;
            float wantX=0,wantY=0;
            if(l>3*s){wantX=dx/l*speed;wantY=dy/l*speed;}
            float response = difficulty==0 ? 4.2f : difficulty==1 ? 7.0f : 10.5f;
            float k=Math.min(1f,dt*response);
            cvx += (wantX-cvx)*k; cvy += (wantY-cvy)*k;
            cx += cvx*dt; cy += cvy*dt;
            clampDisc(false);

            float bd=len(bx-cx,by-cy);
            if (bd < discR+ballR+15*s && cpuKickCooldown<=0f) {
                float aimY = pitch.centerY();
                if (difficulty>=1) aimY += (py-pitch.centerY())*0.15f;
                if (difficulty==2) aimY += (by-pitch.centerY())*0.10f;
                float kx=targetGoalX-bx, ky=aimY-by, kl=len(kx,ky); if(kl<1)kl=1;
                float force=(difficulty==0?560:difficulty==1?650:720)*s;
                bvx=kx/kl*force + cvx*0.15f;
                bvy=ky/kl*force + cvy*0.15f;
                cpuKickCooldown = difficulty==2 ? 0.32f : 0.45f;
            }
        }

        private void collidePlayerBall(float x, float y, float vx, float vy) {
            float dx=bx-x, dy=by-y;
            float min=discR+ballR;
            float d=len(dx,dy);
            if(d<min && d>0.001f){
                float nx=dx/d, ny=dy/d;
                float overlap=min-d;
                bx += nx*overlap; by += ny*overlap;
                float rel=(vx-bvx)*nx+(vy-bvy)*ny;
                float impulse=Math.max(90*s, rel*0.9f + 135*s);
                bvx += nx*impulse;
                bvy += ny*impulse;
            }
        }

        private void handleBallWalls() {
            float gy1=pitch.centerY()-goalHalf, gy2=pitch.centerY()+goalHalf;
            if(by-ballR<pitch.top){by=pitch.top+ballR;bvy=Math.abs(bvy)*0.82f;}
            if(by+ballR>pitch.bottom){by=pitch.bottom-ballR;bvy=-Math.abs(bvy)*0.82f;}
            boolean inGoal = by>gy1+ballR*0.2f && by<gy2-ballR*0.2f;
            if(!inGoal){
                if(bx-ballR<pitch.left){bx=pitch.left+ballR;bvx=Math.abs(bvx)*0.84f;}
                if(bx+ballR>pitch.right){bx=pitch.right-ballR;bvx=-Math.abs(bvx)*0.84f;}
            } else {
                float back=42*s;
                if(bx < pitch.left-back) scoreGoal(false);
                if(bx > pitch.right+back) scoreGoal(true);
            }
        }

        private void scoreGoal(boolean blue) {
            if (training) { resetBallOnly(); haptic(35); return; }
            if (blue) blueScore++; else redScore++;
            haptic(85);
            if (blueScore>=targetGoals || redScore>=targetGoals || goldenGoal) {
                finishMatch();
            } else {
                resetPositions();
            }
        }

        private void finishMatch() {
            if (mode==RESULT) return;
            mode=RESULT;
            if (!savedResult) {
                matches++;
                gf+=blueScore; ga+=redScore;
                if(blueScore>redScore)wins++; else if(blueScore<redScore)losses++; else draws++;
                prefs.edit().putInt("matches",matches).putInt("wins",wins).putInt("losses",losses)
                        .putInt("draws",draws).putInt("gf",gf).putInt("ga",ga).apply();
                savedResult=true;
            }
            joyPointer=-1; joyNX=joyNY=0;
        }

        private void resetPositions() {
            if(w<=0||h<=0)return;
            px=pitch.left+pitch.width()*0.24f; py=pitch.centerY(); pvx=pvy=0;
            cx=pitch.right-pitch.width()*0.24f; cy=pitch.centerY(); cvx=cvy=0;
            resetBallOnly();
        }

        private void resetBallOnly(){bx=pitch.centerX();by=pitch.centerY();bvx=bvy=0;}

        private void clampDisc(boolean player) {
            float x=player?px:cx, y=player?py:cy;
            x=clamp(x,pitch.left+discR,pitch.right-discR);
            y=clamp(y,pitch.top+discR,pitch.bottom-discR);
            if(player){px=x;py=y;}else{cx=x;cy=y;}
        }

        private void startMatch(boolean isTraining) {
            training=isTraining;
            mode=isTraining?TRAINING:GAME;
            blueScore=redScore=0;
            matchTime=180f;
            goldenGoal=false;
            savedResult=false;
            kickCooldown=cpuKickCooldown=0;
            joyPointer=-1; joyNX=joyNY=0;
            resetPositions();
            lastFrame=System.nanoTime();
            prefs.edit().putInt("difficulty",difficulty).putInt("target_goals",targetGoals).apply();
        }

        private void doKick() {
            if(kickCooldown>0)return;
            float dx=bx-px,dy=by-py,d=len(dx,dy);
            if(d<discR+ballR+42*s){
                if(d<1)d=1;
                float force=720*s;
                bvx=dx/d*force+pvx*0.20f;
                bvy=dy/d*force+pvy*0.20f;
                kickCooldown=0.25f;
                haptic(22);
            }
        }

        private void haptic(long ms){
            if(!vibration)return;
            try{
                Vibrator v=(Vibrator)getContext().getSystemService(Context.VIBRATOR_SERVICE);
                if(v!=null&&v.hasVibrator())v.vibrate(ms);
            }catch(Exception ignored){}
        }

        @Override
        public boolean onTouchEvent(MotionEvent e) {
            int action=e.getActionMasked();
            int idx=e.getActionIndex();
            if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_POINTER_DOWN){
                float x=e.getX(idx), y=e.getY(idx);
                if(mode==GAME||mode==TRAINING){
                    if(pauseButton.contains(x,y)) { previousMode=mode; mode=PAUSE; joyPointer=-1;joyNX=joyNY=0; return true; }
                    if(kickButton.contains(x,y)){doKick();return true;}
                    if(x<w*0.58f && y>h*0.40f && joyPointer<0){
                        joyPointer=e.getPointerId(idx);joyBaseX=x;joyBaseY=y;joyX=x;joyY=y;joyNX=joyNY=0;return true;
                    }
                }
            }
            if(action==MotionEvent.ACTION_MOVE && joyPointer>=0){
                int pi=e.findPointerIndex(joyPointer);
                if(pi>=0) updateJoy(e.getX(pi),e.getY(pi));
                return true;
            }
            if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_POINTER_UP){
                int id=e.getPointerId(idx);
                float x=e.getX(idx),y=e.getY(idx);
                if(id==joyPointer){joyPointer=-1;joyNX=joyNY=0;}
                if(action==MotionEvent.ACTION_UP && !(mode==GAME||mode==TRAINING)) processHit(x,y);
                else if(action==MotionEvent.ACTION_UP && mode==TRAINING) processHit(x,y);
                return true;
            }
            if(action==MotionEvent.ACTION_CANCEL){joyPointer=-1;joyNX=joyNY=0;return true;}
            return true;
        }

        private void updateJoy(float x,float y){
            float dx=x-joyBaseX,dy=y-joyBaseY;
            float max=78*s,d=len(dx,dy);
            if(d>max){dx=dx/d*max;dy=dy/d*max;d=max;}
            joyX=joyBaseX+dx;joyY=joyBaseY+dy;
            joyNX=dx/max;joyNY=dy/max;
        }

        private void processHit(float x,float y){
            for(int i=hits.size()-1;i>=0;i--){
                ButtonHit b=hits.get(i);
                if(b.r.contains(x,y)){click(b.id);return;}
            }
        }

        private void click(String id){
            if(id.equals("quick")){startMatch(false);return;}
            if(id.equals("setup")){mode=SETUP;return;}
            if(id.equals("training")){startMatch(true);return;}
            if(id.equals("stats")){mode=STATS;return;}
            if(id.equals("settings")){mode=SETTINGS;return;}
            if(id.equals("home")){mode=HOME;training=false;joyPointer=-1;joyNX=joyNY=0;return;}
            if(id.equals("start")){startMatch(false);return;}
            if(id.startsWith("diff")){difficulty=Integer.parseInt(id.substring(4));prefs.edit().putInt("difficulty",difficulty).apply();return;}
            if(id.startsWith("goal")){targetGoals=Integer.parseInt(id.substring(4));prefs.edit().putInt("target_goals",targetGoals).apply();return;}
            if(id.equals("resume")){mode=previousMode;lastFrame=System.nanoTime();return;}
            if(id.equals("restart")){startMatch(previousMode==TRAINING);return;}
            if(id.equals("rematch")){startMatch(false);return;}
            if(id.equals("vibration")){vibration=!vibration;prefs.edit().putBoolean("vibration",vibration).apply();haptic(25);return;}
            if(id.equals("clearstats")){wins=losses=draws=matches=gf=ga=0;prefs.edit().putInt("wins",0).putInt("losses",0).putInt("draws",0).putInt("matches",0).putInt("gf",0).putInt("ga",0).apply();return;}
            if(id.equals("resetball")){resetBallOnly();return;}
        }

        boolean handleBack(){
            if(mode==GAME||mode==TRAINING){previousMode=mode;mode=PAUSE;joyPointer=-1;joyNX=joyNY=0;return true;}
            if(mode==PAUSE){mode=previousMode;lastFrame=System.nanoTime();return true;}
            if(mode!=HOME){mode=HOME;return true;}
            return false;
        }

        private String difficultyName(){return difficulty==0?"Easy":difficulty==1?"Normal":"Hard";}
        private String formatTime(float t){int sec=Math.max(0,(int)Math.ceil(t));return String.format(Locale.US,"%d:%02d",sec/60,sec%60);}
        private float len(float x,float y){return (float)Math.sqrt(x*x+y*y);}
        private float clamp(float v,float lo,float hi){return Math.max(lo,Math.min(hi,v));}

        static final class ButtonHit{
            final String id; final RectF r;
            ButtonHit(String id,RectF r){this.id=id;this.r=new RectF(r);}
        }
    }
}
