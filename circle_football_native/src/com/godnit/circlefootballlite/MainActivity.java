package com.godnit.circlefootballlite;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
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
        private static final int CONTROLS = 8;

        private static final int SFX_MENU = 0;
        private static final int SFX_KICK = 1;
        private static final int SFX_TOUCH = 2;
        private static final int SFX_WALL = 3;
        private static final int SFX_GOAL = 4;
        private static final int SFX_WIN = 5;
        private static final int SFX_LOSE = 6;

        private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final SharedPreferences prefs;
        private final List<ButtonHit> hits = new ArrayList<>();
        private final Random rng = new Random();

        private int mode = HOME;
        private int previousMode = GAME;
        private int difficulty;
        private int targetGoals;
        private boolean vibration;
        private boolean sounds;
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
        private int ballOwner = 0;
        private float possessionLock = 0f;
        private float playerFacingX = 1f, playerFacingY = 0f;
        private float cpuFacingX = -1f, cpuFacingY = 0f;
        private float cpuPossessionTime = 0f;
        private float cpuLaneTimer = 0f;
        private float cpuLaneY = 0f;

        private int blueScore = 0;
        private int redScore = 0;
        private float matchTime = 180f;
        private boolean goldenGoal = false;
        private boolean savedResult = false;
        private long lastFrame = 0L;
        private float kickCooldown = 0f;
        private float cpuKickCooldown = 0f;
        private float wallSoundCooldown = 0f;

        private int joyPointer = -1;
        private float joyBaseX, joyBaseY;
        private float joyX, joyY;
        private float joyNX, joyNY;
        private float joyNormX, joyNormY, kickNormX, kickNormY;
        private float joyScale, kickScale;
        private final RectF kickButton = new RectF();
        private final RectF pauseButton = new RectF();

        private int editTarget = 0;
        private int editPointer = -1;
        private boolean editMoved = false;

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
            sounds = prefs.getBoolean("sounds", true);
            wins = prefs.getInt("wins", 0);
            losses = prefs.getInt("losses", 0);
            draws = prefs.getInt("draws", 0);
            matches = prefs.getInt("matches", 0);
            gf = prefs.getInt("gf", 0);
            ga = prefs.getInt("ga", 0);
            joyNormX = prefs.getFloat("joy_x", 0.115f);
            joyNormY = prefs.getFloat("joy_y", 0.81f);
            kickNormX = prefs.getFloat("kick_x", 0.91f);
            kickNormY = prefs.getFloat("kick_y", 0.82f);
            joyScale = prefs.getFloat("joy_scale", 1.0f);
            kickScale = prefs.getFloat("kick_scale", 1.0f);
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
            pauseButton.set(w - 78f*s, 18f*s, w - 18f*s, 78f*s);
            updateControlRects();
            resetPositions();
        }

        private void updateControlRects() {
            joyBaseX = clamp(joyNormX*w, joyRadius()+8*s, w-joyRadius()-8*s);
            joyBaseY = clamp(joyNormY*h, joyRadius()+8*s, h-joyRadius()-8*s);
            joyNormX = w > 0 ? joyBaseX/w : joyNormX;
            joyNormY = h > 0 ? joyBaseY/h : joyNormY;
            float kr = kickRadius();
            float kx = clamp(kickNormX*w, kr+8*s, w-kr-8*s);
            float ky = clamp(kickNormY*h, kr+8*s, h-kr-8*s);
            kickNormX = w > 0 ? kx/w : kickNormX;
            kickNormY = h > 0 ? ky/h : kickNormY;
            kickButton.set(kx-kr, ky-kr, kx+kr, ky+kr);
            if (joyPointer < 0) {
                joyX = joyBaseX;
                joyY = joyBaseY;
            }
        }

        private float joyRadius() { return 78f*s*joyScale; }
        private float joyKnobRadius() { return 36f*s*joyScale; }
        private float kickRadius() { return 67.5f*s*kickScale; }

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
            } else if (mode == CONTROLS) {
                drawControlsEditor(c);
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
            title(c, "SETTINGS", 78*s, 38);
            float bw = 420*s, x = (w-bw)/2f;
            menuButton(c, sounds ? "GAME SFX: ON" : "GAME SFX: OFF", "sounds", x, 150*s, bw, 62*s,
                    sounds ? Color.rgb(34,174,91) : Color.rgb(98,105,118));
            menuButton(c, vibration ? "VIBRATION: ON" : "VIBRATION: OFF", "vibration", x, 230*s, bw, 62*s,
                    vibration ? Color.rgb(34,174,91) : Color.rgb(98,105,118));
            menuButton(c, "EDIT CONTROLS", "controls", x, 310*s, bw, 66*s, Color.rgb(29,121,255));
            subtitle(c, "Move and resize joystick + kick button", 410*s, 17, Color.rgb(145,160,181));
            subtitle(c, "Custom game sounds are generated inside the game.", 445*s, 17, Color.rgb(145,160,181));
            menuButton(c, "BACK", "home", (w-260*s)/2f, 505*s, 260*s, 58*s, Color.rgb(48,56,70));
        }

        private void drawControlsEditor(Canvas c) {
            background(c);
            title(c, "CONTROL LAYOUT", 62*s, 33);
            subtitle(c, "Drag the joystick or KICK button. Changes are saved.", 94*s, 16, Color.rgb(160,175,195));
            float bw = 150*s, gap = 12*s, y = 120*s;
            float total = bw*4 + gap*3;
            float x = (w-total)/2f;
            menuButton(c, "JOY -", "joyminus", x, y, bw, 52*s, Color.rgb(48,56,70));
            menuButton(c, "JOY +", "joyplus", x+bw+gap, y, bw, 52*s, Color.rgb(48,56,70));
            menuButton(c, "KICK -", "kickminus", x+(bw+gap)*2, y, bw, 52*s, Color.rgb(48,56,70));
            menuButton(c, "KICK +", "kickplus", x+(bw+gap)*3, y, bw, 52*s, Color.rgb(48,56,70));
            stroke.setStrokeWidth(2*s);
            stroke.setColor(Color.rgb(70,80,92));
            c.drawRoundRect(new RectF(30*s, 205*s, w-30*s, h-82*s), 18*s, 18*s, stroke);
            drawEditorJoystick(c);
            drawEditorKick(c);
            menuButton(c, "RESET", "controlreset", 45*s, h-65*s, 175*s, 48*s, Color.rgb(125,58,65));
            menuButton(c, "SAVE & BACK", "controlsave", w-270*s, h-65*s, 225*s, 48*s, Color.rgb(34,174,91));
        }

        private void drawEditorJoystick(Canvas c) {
            float r = joyRadius();
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.argb(80,255,255,255));
            c.drawCircle(joyBaseX, joyBaseY, r, p);
            p.setColor(Color.argb(170,255,255,255));
            c.drawCircle(joyBaseX, joyBaseY, joyKnobRadius(), p);
            stroke.setStrokeWidth(editTarget==1 ? 5*s : 2*s);
            stroke.setColor(editTarget==1 ? Color.rgb(70,150,255) : Color.rgb(170,180,190));
            c.drawCircle(joyBaseX, joyBaseY, r+5*s, stroke);
            p.setColor(Color.WHITE); p.setTextSize(14*s); p.setTypeface(Typeface.DEFAULT_BOLD); p.setTextAlign(Paint.Align.CENTER);
            c.drawText("JOYSTICK", joyBaseX, joyBaseY-r-12*s, p);
        }

        private void drawEditorKick(Canvas c) {
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.argb(175,28,116,255));
            c.drawOval(kickButton,p);
            stroke.setStrokeWidth(editTarget==2 ? 5*s : 2*s);
            stroke.setColor(editTarget==2 ? Color.rgb(70,150,255) : Color.rgb(170,180,190));
            c.drawOval(new RectF(kickButton.left-5*s,kickButton.top-5*s,kickButton.right+5*s,kickButton.bottom+5*s),stroke);
            p.setTextAlign(Paint.Align.CENTER); p.setTypeface(Typeface.DEFAULT_BOLD); p.setTextSize(18*s); p.setColor(Color.WHITE);
            c.drawText("KICK", kickButton.centerX(), kickButton.centerY()+6*s,p);
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
            float jr = joyRadius();
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.argb(85,255,255,255));
            c.drawCircle(joyBaseX,joyBaseY,jr,p);
            p.setColor(Color.argb(150,255,255,255));
            float knobX = joyPointer >=0 ? joyX : joyBaseX;
            float knobY = joyPointer >=0 ? joyY : joyBaseY;
            c.drawCircle(knobX,knobY,joyKnobRadius(),p);
            p.setColor(Color.argb(165, 28,116,255));
            c.drawOval(kickButton,p);
            p.setTextAlign(Paint.Align.CENTER);
            p.setTypeface(Typeface.DEFAULT_BOLD);
            p.setTextSize(20*s*kickScale);
            p.setColor(Color.WHITE);
            c.drawText("KICK",kickButton.centerX(),kickButton.centerY()+7*s*kickScale,p);
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
            possessionLock = Math.max(0f, possessionLock-dt);
            wallSoundCooldown = Math.max(0f, wallSoundCooldown-dt);
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
            if (len(joyNX, joyNY) > 0.10f) {
                float jl = len(joyNX,joyNY);
                playerFacingX = joyNX/jl;
                playerFacingY = joyNY/jl;
            }
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
            if (!training) {
                updateCpu(dt);
                collideDiscs();
            }
            if (ballOwner == 1) {
                updatePlayerPossession(dt);
            } else if (ballOwner == 2 && !training) {
                updateCpuPossession(dt);
            } else {
                bx += bvx*dt;
                by += bvy*dt;
                float friction = (float)Math.pow(0.987,dt*60f);
                bvx *= friction;
                bvy *= friction;
                collideFreeBallWithDisc(px,py,pvx,pvy,1);
                if (!training) collideFreeBallWithDisc(cx,cy,cvx,cvy,2);
                handleBallWalls();
                tryAcquirePossession();
            }
            if (ballOwner == 1 && !training) {
                float stealDist = len(bx-cx,by-cy);
                if (stealDist < discR+ballR*0.85f && len(cvx, cvy) > 70*s) {
                    ballOwner = 0;
                    possessionLock = 0.12f;
                    bvx = cvx*0.40f - playerFacingX*90*s;
                    bvy = cvy*0.40f - playerFacingY*90*s;
                    playSfx(SFX_TOUCH);
                }
            } else if (ballOwner == 2) {
                float stealDist = len(bx-px,by-py);
                if (stealDist < discR+ballR*0.85f && len(pvx, pvy) > 80*s) {
                    ballOwner = 0;
                    possessionLock = 0.12f;
                    bvx = pvx*0.40f - cpuFacingX*90*s;
                    bvy = pvy*0.40f - cpuFacingY*90*s;
                    playSfx(SFX_TOUCH);
                }
            }
        }

        private void collideDiscs() {
            float dx=cx-px, dy=cy-py;
            float min=discR*2f;
            float d=len(dx,dy);
            if(d>0.001f && d<min){
                float nx=dx/d, ny=dy/d;
                float overlap=min-d;
                px-=nx*overlap*0.5f; py-=ny*overlap*0.5f;
                cx+=nx*overlap*0.5f; cy+=ny*overlap*0.5f;
                float rvx=cvx-pvx, rvy=cvy-pvy;
                float along=rvx*nx+rvy*ny;
                if(along<0f){
                    float impulse=-along*0.45f;
                    pvx-=nx*impulse; pvy-=ny*impulse;
                    cvx+=nx*impulse; cvy+=ny*impulse;
                }
                clampDisc(true);
                clampDisc(false);
            }
        }

        private void updatePlayerPossession(float dt) {
            float hold = discR + ballR + 5*s;
            float tx = px + playerFacingX*hold;
            float ty = py + playerFacingY*hold;
            float k = Math.min(1f, dt*20f);
            bx += (tx-bx)*k;
            by += (ty-by)*k;
            bvx = pvx;
            bvy = pvy;
            constrainOwnedBall(1);
            checkOwnedGoal();
        }

        private void updateCpuPossession(float dt) {
            float hold = discR + ballR + 5*s;
            float tx = cx + cpuFacingX*hold;
            float ty = cy + cpuFacingY*hold;
            float k = Math.min(1f, dt*20f);
            bx += (tx-bx)*k;
            by += (ty-by)*k;
            bvx = cvx;
            bvy = cvy;
            constrainOwnedBall(2);
            checkOwnedGoal();
        }

        private void constrainOwnedBall(int owner) {
            float gy1 = pitch.centerY()-goalHalf+ballR;
            float gy2 = pitch.centerY()+goalHalf-ballR;
            by = clamp(by, pitch.top+ballR, pitch.bottom-ballR);
            boolean inGoalMouth = by > gy1 && by < gy2;
            if (!inGoalMouth) bx = clamp(bx, pitch.left+ballR, pitch.right-ballR);
            else bx = clamp(bx, pitch.left-45*s, pitch.right+45*s);
            if (owner==1) {
                float d = len(bx-px,by-py);
                if (d > discR+ballR+20*s) ballOwner=0;
            } else {
                float d = len(bx-cx,by-cy);
                if (d > discR+ballR+20*s) ballOwner=0;
            }
        }

        private void checkOwnedGoal() {
            float gy1=pitch.centerY()-goalHalf, gy2=pitch.centerY()+goalHalf;
            boolean inGoal = by>gy1+ballR*0.2f && by<gy2-ballR*0.2f;
            if (!inGoal) return;
            if (bx < pitch.left-ballR*0.15f) scoreGoal(false);
            else if (bx > pitch.right+ballR*0.15f) scoreGoal(true);
        }

        private void tryAcquirePossession() {
            if (possessionLock > 0f || ballOwner != 0) return;
            float dp = len(bx-px,by-py);
            float dc = training ? 999999f : len(bx-cx,by-cy);
            float touch = discR+ballR+4*s;
            if (dp <= touch && dp <= dc+4*s && len(bvx-pvx,bvy-pvy) < 470*s) {
                ballOwner = 1;
                float dx=bx-px,dy=by-py,d=len(dx,dy);
                if(d>1){playerFacingX=dx/d;playerFacingY=dy/d;}
                playSfx(SFX_TOUCH);
            } else if (!training && dc <= touch && len(bvx-cvx,bvy-cvy) < 470*s) {
                ballOwner = 2;
                cpuPossessionTime = 0f;
                float dx=bx-cx,dy=by-cy,d=len(dx,dy);
                if(d>1){cpuFacingX=dx/d;cpuFacingY=dy/d;}
                cpuLaneTimer = 0f;
                playSfx(SFX_TOUCH);
            }
        }

        private void updateCpu(float dt) {
            if (ballOwner == 2) {
                updateCpuWithBall(dt);
                return;
            }
            float pred = difficulty==0 ? 0.08f : (difficulty==1 ? 0.18f : 0.30f);
            float pbx = ballOwner==1 ? bx : bx + bvx*pred;
            float pby = ballOwner==1 ? by : by + bvy*pred;
            pby = clamp(pby,pitch.top+discR,pitch.bottom-discR);
            float tx, ty;
            boolean playerHasBall = ballOwner==1;
            boolean danger = playerHasBall || bx > pitch.centerX()+pitch.width()*0.05f || bvx > 100*s;
            if (danger) {
                float ownGoalX = pitch.right;
                if (playerHasBall) {
                    float defendGap = difficulty==2 ? 78*s : 95*s;
                    tx = clamp(bx + defendGap, pitch.centerX(), pitch.right-60*s);
                    ty = clamp(by + (py < pitch.centerY() ? 22*s : -22*s), pitch.top+discR, pitch.bottom-discR);
                } else {
                    float gx = ownGoalX - 48*s;
                    float gy = pitch.centerY();
                    float dx = pbx-gx, dy=pby-gy;
                    float l = len(dx,dy); if(l<1)l=1;
                    tx = gx + dx/l*Math.min(150*s,l*0.55f);
                    ty = gy + dy/l*Math.min(150*s,l*0.55f);
                }
            } else {
                float targetGoalX = pitch.left;
                float dx = pbx-targetGoalX;
                float dy = pby-pitch.centerY();
                float l=len(dx,dy); if(l<1)l=1;
                tx = pbx + dx/l*(discR+ballR+12*s);
                ty = pby + dy/l*(discR+ballR+12*s);
                if (isPlayerBlockingLane(pbx,pby,pitch.left,pitch.centerY())) {
                    float offset = py < pitch.centerY() ? 85*s : -85*s;
                    ty = clamp(ty+offset,pitch.top+discR,pitch.bottom-discR);
                }
            }
            if (difficulty==0) {
                tx = tx*0.86f + (pitch.right-145*s)*0.14f;
                ty = ty*0.90f + pitch.centerY()*0.10f;
            }
            moveCpuToward(tx,ty,dt);
        }

        private void updateCpuWithBall(float dt) {
            cpuPossessionTime += dt;
            cpuLaneTimer -= dt;
            if (cpuLaneTimer <= 0f) {
                cpuLaneTimer = difficulty==2 ? 0.42f : 0.68f;
                if (isPlayerBlockingLane(bx,by,pitch.left,pitch.centerY())) {
                    cpuLaneY = py < pitch.centerY() ? pitch.bottom-105*s : pitch.top+105*s;
                } else {
                    float towardCorner = py < pitch.centerY() ? 0.67f : 0.33f;
                    cpuLaneY = pitch.top + pitch.height()*towardCorner;
                }
            }
            boolean blocked = isPlayerBlockingLane(bx,by,pitch.left,chooseCpuAimY());
            float shootX = pitch.left + pitch.width()*(difficulty==2 ? 0.42f : 0.35f);
            boolean closeEnough = cx < shootX;
            boolean heldLongEnough = cpuPossessionTime > (difficulty==2 ? 0.75f : 1.05f);
            boolean mustRelease = cpuPossessionTime > 2.1f;
            if (cpuKickCooldown<=0f && ((closeEnough && !blocked && heldLongEnough) || mustRelease)) {
                cpuShoot();
                return;
            }
            float tx = pitch.left + 100*s;
            float ty = clamp(cpuLaneY,pitch.top+discR,pitch.bottom-discR);
            if (blocked) tx = Math.max(tx, cx-150*s);
            moveCpuToward(tx,ty,dt);
        }

        private float chooseCpuAimY() {
            float topAim = pitch.centerY()-goalHalf*0.62f;
            float bottomAim = pitch.centerY()+goalHalf*0.62f;
            return py < pitch.centerY() ? bottomAim : topAim;
        }

        private boolean isPlayerBlockingLane(float x1,float y1,float x2,float y2) {
            float vx=x2-x1, vy=y2-y1;
            float vv=vx*vx+vy*vy;
            if(vv<1)return false;
            float t=((px-x1)*vx+(py-y1)*vy)/vv;
            if(t<0.05f||t>0.96f)return false;
            float qx=x1+t*vx, qy=y1+t*vy;
            float d=len(px-qx,py-qy);
            return d < discR*1.55f;
        }

        private void moveCpuToward(float tx,float ty,float dt) {
            float dx=tx-cx, dy=ty-cy, l=len(dx,dy);
            float speed = (difficulty==0 ? 205 : difficulty==1 ? 245 : 272)*s;
            float wantX=0,wantY=0;
            if(l>3*s){wantX=dx/l*speed;wantY=dy/l*speed;}
            if (len(wantX,wantY)>10*s) {
                float wl=len(wantX,wantY);
                cpuFacingX=wantX/wl;
                cpuFacingY=wantY/wl;
            }
            float response = difficulty==0 ? 4.0f : difficulty==1 ? 6.7f : 8.8f;
            float k=Math.min(1f,dt*response);
            cvx += (wantX-cvx)*k;
            cvy += (wantY-cvy)*k;
            cx += cvx*dt;
            cy += cvy*dt;
            clampDisc(false);
        }

        private void cpuShoot() {
            if (ballOwner != 2 || cpuKickCooldown>0f) return;
            float aimY = chooseCpuAimY();
            if (difficulty==2 && isPlayerBlockingLane(bx,by,pitch.left,aimY)) {
                aimY = pitch.centerY() - (aimY-pitch.centerY());
            }
            float spread = difficulty==0 ? 50*s : difficulty==1 ? 25*s : 10*s;
            aimY += (rng.nextFloat()*2f-1f)*spread;
            aimY = clamp(aimY,pitch.centerY()-goalHalf*0.78f,pitch.centerY()+goalHalf*0.78f);
            float kx=pitch.left-bx, ky=aimY-by, kl=len(kx,ky); if(kl<1)kl=1;
            float force=(difficulty==0?500:difficulty==1?555:600)*s;
            ballOwner=0;
            possessionLock=0.20f;
            bx += kx/kl*5*s;
            by += ky/kl*5*s;
            bvx=kx/kl*force + cvx*0.12f;
            bvy=ky/kl*force + cvy*0.12f;
            cpuKickCooldown = difficulty==2 ? 0.78f : 0.95f;
            cpuPossessionTime=0f;
            playSfx(SFX_KICK);
        }

        private void collideFreeBallWithDisc(float x, float y, float vx, float vy, int who) {
            if (ballOwner != 0) return;
            float dx=bx-x, dy=by-y;
            float min=discR+ballR;
            float d=len(dx,dy);
            if(d<min && d>0.001f){
                float nx=dx/d, ny=dy/d;
                float overlap=min-d;
                bx += nx*overlap;
                by += ny*overlap;
                float rel=(vx-bvx)*nx+(vy-bvy)*ny;
                float impulse=Math.max(55*s, rel*0.65f + 80*s);
                bvx += nx*impulse;
                bvy += ny*impulse;
                if (possessionLock<=0f && len(bvx-vx,bvy-vy)<430*s) {
                    ballOwner=who;
                    if(who==1){playerFacingX=nx;playerFacingY=ny;}
                    else{cpuFacingX=nx;cpuFacingY=ny;cpuPossessionTime=0f;}
                    playSfx(SFX_TOUCH);
                }
            }
        }

        private void handleBallWalls() {
            float gy1=pitch.centerY()-goalHalf, gy2=pitch.centerY()+goalHalf;
            boolean bounced=false;
            if(by-ballR<pitch.top){by=pitch.top+ballR;bvy=Math.abs(bvy)*0.82f;bounced=true;}
            if(by+ballR>pitch.bottom){by=pitch.bottom-ballR;bvy=-Math.abs(bvy)*0.82f;bounced=true;}
            boolean inGoal = by>gy1+ballR*0.2f && by<gy2-ballR*0.2f;
            if(!inGoal){
                if(bx-ballR<pitch.left){bx=pitch.left+ballR;bvx=Math.abs(bvx)*0.84f;bounced=true;}
                if(bx+ballR>pitch.right){bx=pitch.right-ballR;bvx=-Math.abs(bvx)*0.84f;bounced=true;}
            } else {
                float back=42*s;
                if(bx < pitch.left-back) scoreGoal(false);
                if(bx > pitch.right+back) scoreGoal(true);
            }
            if(bounced && wallSoundCooldown<=0f && len(bvx,bvy)>100*s){
                playSfx(SFX_WALL);
                wallSoundCooldown=0.07f;
            }
        }

        private void scoreGoal(boolean blue) {
            ballOwner=0;
            possessionLock=0.25f;
            if (training) {
                resetBallOnly();
                haptic(35);
                playSfx(SFX_GOAL);
                return;
            }
            if (blue) blueScore++; else redScore++;
            haptic(85);
            playSfx(SFX_GOAL);
            if (blueScore>=targetGoals || redScore>=targetGoals || goldenGoal) finishMatch();
            else resetPositions();
        }

        private void finishMatch() {
            if (mode==RESULT) return;
            mode=RESULT;
            ballOwner=0;
            if (!savedResult) {
                matches++;
                gf+=blueScore;
                ga+=redScore;
                if(blueScore>redScore)wins++; else if(blueScore<redScore)losses++; else draws++;
                prefs.edit().putInt("matches",matches).putInt("wins",wins).putInt("losses",losses)
                        .putInt("draws",draws).putInt("gf",gf).putInt("ga",ga).apply();
                savedResult=true;
                if (blueScore>redScore) playSfx(SFX_WIN);
                else if (blueScore<redScore) playSfx(SFX_LOSE);
            }
            joyPointer=-1;
            joyNX=joyNY=0;
            joyX=joyBaseX;
            joyY=joyBaseY;
        }

        private void resetPositions() {
            if(w<=0||h<=0)return;
            px=pitch.left+pitch.width()*0.24f; py=pitch.centerY(); pvx=pvy=0;
            cx=pitch.right-pitch.width()*0.24f; cy=pitch.centerY(); cvx=cvy=0;
            playerFacingX=1f;playerFacingY=0f;
            cpuFacingX=-1f;cpuFacingY=0f;
            resetBallOnly();
        }

        private void resetBallOnly(){
            bx=pitch.centerX();
            by=pitch.centerY();
            bvx=bvy=0;
            ballOwner=0;
            possessionLock=0.18f;
            cpuPossessionTime=0f;
        }

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
            joyPointer=-1;
            joyNX=joyNY=0;
            joyX=joyBaseX;
            joyY=joyBaseY;
            resetPositions();
            lastFrame=System.nanoTime();
            prefs.edit().putInt("difficulty",difficulty).putInt("target_goals",targetGoals).apply();
            playSfx(SFX_MENU);
        }

        private void doKick() {
            if(kickCooldown>0)return;
            float dx,dy,d;
            if (ballOwner==1) {
                float aimX=playerFacingX,aimY=playerFacingY;
                if (len(joyNX,joyNY)>0.15f) {
                    float l=len(joyNX,joyNY);
                    aimX=joyNX/l;aimY=joyNY/l;
                }
                ballOwner=0;
                possessionLock=0.22f;
                float force=640*s;
                bx=px+aimX*(discR+ballR+8*s);
                by=py+aimY*(discR+ballR+8*s);
                bvx=aimX*force+pvx*0.24f;
                bvy=aimY*force+pvy*0.24f;
                kickCooldown=0.28f;
                haptic(22);
                playSfx(SFX_KICK);
                return;
            }
            dx=bx-px;dy=by-py;d=len(dx,dy);
            if(d<discR+ballR+34*s){
                if(d<1)d=1;
                float force=640*s;
                bvx=dx/d*force+pvx*0.20f;
                bvy=dy/d*force+pvy*0.20f;
                possessionLock=0.22f;
                kickCooldown=0.28f;
                haptic(22);
                playSfx(SFX_KICK);
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
            if (mode==CONTROLS) return onControlsEditorTouch(e,action,idx);
            if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_POINTER_DOWN){
                float x=e.getX(idx), y=e.getY(idx);
                if(mode==GAME||mode==TRAINING){
                    if(pauseButton.contains(x,y)) {
                        previousMode=mode;
                        mode=PAUSE;
                        joyPointer=-1;
                        joyNX=joyNY=0;
                        joyX=joyBaseX;joyY=joyBaseY;
                        return true;
                    }
                    if(kickButton.contains(x,y)){doKick();return true;}
                    float jd=len(x-joyBaseX,y-joyBaseY);
                    if(jd<=joyRadius()*1.35f && joyPointer<0){
                        joyPointer=e.getPointerId(idx);
                        updateJoy(x,y);
                        return true;
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
                if(id==joyPointer){
                    joyPointer=-1;
                    joyNX=joyNY=0;
                    joyX=joyBaseX;
                    joyY=joyBaseY;
                }
                if(action==MotionEvent.ACTION_UP && !(mode==GAME||mode==TRAINING)) processHit(x,y);
                else if(action==MotionEvent.ACTION_UP && mode==TRAINING) processHit(x,y);
                return true;
            }
            if(action==MotionEvent.ACTION_CANCEL){
                joyPointer=-1;
                joyNX=joyNY=0;
                joyX=joyBaseX;
                joyY=joyBaseY;
                return true;
            }
            return true;
        }

        private boolean onControlsEditorTouch(MotionEvent e,int action,int idx) {
            if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_POINTER_DOWN){
                float x=e.getX(idx),y=e.getY(idx);
                if(editPointer<0){
                    editMoved=false;
                    float jd=len(x-joyBaseX,y-joyBaseY);
                    if(jd<=joyRadius()*1.15f){
                        editTarget=1;
                        editPointer=e.getPointerId(idx);
                        return true;
                    }
                    if(kickButton.contains(x,y)){
                        editTarget=2;
                        editPointer=e.getPointerId(idx);
                        return true;
                    }
                }
            }
            if(action==MotionEvent.ACTION_MOVE && editPointer>=0){
                int pi=e.findPointerIndex(editPointer);
                if(pi>=0){
                    float x=e.getX(pi),y=e.getY(pi);
                    if(editTarget==1){
                        float r=joyRadius();
                        joyBaseX=clamp(x,r+8*s,w-r-8*s);
                        joyBaseY=clamp(y,205*s+r,h-82*s-r);
                        joyNormX=joyBaseX/w;joyNormY=joyBaseY/h;
                        joyX=joyBaseX;joyY=joyBaseY;
                    }else if(editTarget==2){
                        float r=kickRadius();
                        float kx=clamp(x,r+8*s,w-r-8*s);
                        float ky=clamp(y,205*s+r,h-82*s-r);
                        kickNormX=kx/w;kickNormY=ky/h;
                        kickButton.set(kx-r,ky-r,kx+r,ky+r);
                    }
                    editMoved=true;
                }
                return true;
            }
            if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_POINTER_UP){
                int id=e.getPointerId(idx);
                float x=e.getX(idx),y=e.getY(idx);
                if(id==editPointer){
                    editPointer=-1;
                    saveControls();
                    editMoved=false;
                    return true;
                }
                if(action==MotionEvent.ACTION_UP && !editMoved)processHit(x,y);
                return true;
            }
            if(action==MotionEvent.ACTION_CANCEL){editPointer=-1;return true;}
            return true;
        }

        private void updateJoy(float x,float y){
            float dx=x-joyBaseX,dy=y-joyBaseY;
            float max=joyRadius(),d=len(dx,dy);
            if(d>max){dx=dx/d*max;dy=dy/d*max;}
            joyX=joyBaseX+dx;
            joyY=joyBaseY+dy;
            joyNX=dx/max;
            joyNY=dy/max;
        }

        private void processHit(float x,float y){
            for(int i=hits.size()-1;i>=0;i--){
                ButtonHit b=hits.get(i);
                if(b.r.contains(x,y)){click(b.id);return;}
            }
        }

        private void click(String id){
            if(id.equals("quick")){startMatch(false);return;}
            if(id.equals("setup")){playSfx(SFX_MENU);mode=SETUP;return;}
            if(id.equals("training")){startMatch(true);return;}
            if(id.equals("stats")){playSfx(SFX_MENU);mode=STATS;return;}
            if(id.equals("settings")){playSfx(SFX_MENU);mode=SETTINGS;return;}
            if(id.equals("controls")){playSfx(SFX_MENU);mode=CONTROLS;editTarget=0;return;}
            if(id.equals("home")){playSfx(SFX_MENU);mode=HOME;training=false;joyPointer=-1;joyNX=joyNY=0;return;}
            if(id.equals("start")){startMatch(false);return;}
            if(id.startsWith("diff")){difficulty=Integer.parseInt(id.substring(4));prefs.edit().putInt("difficulty",difficulty).apply();playSfx(SFX_MENU);return;}
            if(id.startsWith("goal")){targetGoals=Integer.parseInt(id.substring(4));prefs.edit().putInt("target_goals",targetGoals).apply();playSfx(SFX_MENU);return;}
            if(id.equals("resume")){playSfx(SFX_MENU);mode=previousMode;lastFrame=System.nanoTime();return;}
            if(id.equals("restart")){startMatch(previousMode==TRAINING);return;}
            if(id.equals("rematch")){startMatch(false);return;}
            if(id.equals("sounds")){sounds=!sounds;prefs.edit().putBoolean("sounds",sounds).apply();if(sounds)playSfx(SFX_MENU);return;}
            if(id.equals("vibration")){vibration=!vibration;prefs.edit().putBoolean("vibration",vibration).apply();haptic(25);playSfx(SFX_MENU);return;}
            if(id.equals("clearstats")){wins=losses=draws=matches=gf=ga=0;prefs.edit().putInt("wins",0).putInt("losses",0).putInt("draws",0).putInt("matches",0).putInt("gf",0).putInt("ga",0).apply();playSfx(SFX_MENU);return;}
            if(id.equals("resetball")){resetBallOnly();playSfx(SFX_MENU);return;}
            if(id.equals("joyminus")){joyScale=clamp(joyScale-0.10f,0.65f,1.45f);updateControlRects();saveControls();playSfx(SFX_MENU);return;}
            if(id.equals("joyplus")){joyScale=clamp(joyScale+0.10f,0.65f,1.45f);updateControlRects();saveControls();playSfx(SFX_MENU);return;}
            if(id.equals("kickminus")){kickScale=clamp(kickScale-0.10f,0.65f,1.45f);updateControlRects();saveControls();playSfx(SFX_MENU);return;}
            if(id.equals("kickplus")){kickScale=clamp(kickScale+0.10f,0.65f,1.45f);updateControlRects();saveControls();playSfx(SFX_MENU);return;}
            if(id.equals("controlreset")){joyNormX=0.115f;joyNormY=0.81f;kickNormX=0.91f;kickNormY=0.82f;joyScale=1f;kickScale=1f;updateControlRects();saveControls();playSfx(SFX_MENU);return;}
            if(id.equals("controlsave")){saveControls();playSfx(SFX_MENU);mode=SETTINGS;return;}
        }

        private void saveControls(){
            prefs.edit().putFloat("joy_x",joyNormX).putFloat("joy_y",joyNormY)
                    .putFloat("kick_x",kickNormX).putFloat("kick_y",kickNormY)
                    .putFloat("joy_scale",joyScale).putFloat("kick_scale",kickScale).apply();
        }

        boolean handleBack(){
            if(mode==GAME||mode==TRAINING){previousMode=mode;mode=PAUSE;joyPointer=-1;joyNX=joyNY=0;joyX=joyBaseX;joyY=joyBaseY;return true;}
            if(mode==PAUSE){mode=previousMode;lastFrame=System.nanoTime();return true;}
            if(mode==CONTROLS){saveControls();mode=SETTINGS;return true;}
            if(mode!=HOME){mode=HOME;return true;}
            return false;
        }

        private void playSfx(final int type){
            if(!sounds)return;
            final short[] pcm=makeSfx(type);
            if(pcm==null||pcm.length==0)return;
            new Thread(new Runnable(){
                @Override public void run(){
                    AudioTrack track=null;
                    try{
                        AudioAttributes attrs=new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build();
                        AudioFormat fmt=new AudioFormat.Builder().setEncoding(AudioFormat.ENCODING_PCM_16BIT).setSampleRate(22050).setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build();
                        int bytes=pcm.length*2;
                        track=new AudioTrack(attrs,fmt,bytes,AudioTrack.MODE_STATIC,AudioManager.AUDIO_SESSION_ID_GENERATE);
                        track.write(pcm,0,pcm.length);
                        track.play();
                        SystemClock.sleep((long)(pcm.length*1000f/22050f)+35);
                    }catch(Exception ignored){}finally{
                        if(track!=null){try{track.stop();}catch(Exception ignored){}try{track.release();}catch(Exception ignored){}}
                    }
                }
            },"cf-sfx").start();
        }

        private short[] makeSfx(int type){
            int ms;
            if(type==SFX_GOAL||type==SFX_WIN||type==SFX_LOSE)ms=420;
            else if(type==SFX_KICK)ms=105;
            else if(type==SFX_TOUCH)ms=45;
            else if(type==SFX_WALL)ms=38;
            else ms=55;
            int sr=22050;
            int n=sr*ms/1000;
            short[] out=new short[n];
            for(int i=0;i<n;i++){
                double t=i/(double)sr;
                double env=Math.max(0.0,1.0-i/(double)n);
                double v=0.0;
                if(type==SFX_MENU){v=Math.sin(2*Math.PI*760*t)*env*0.42;}
                else if(type==SFX_KICK){double f=118.0-52.0*(i/(double)n);double thump=Math.sin(2*Math.PI*f*t)*Math.pow(env,1.6)*0.80;double click=(rng.nextDouble()*2-1)*Math.pow(env,5.0)*0.22;v=thump+click;}
                else if(type==SFX_TOUCH){v=Math.sin(2*Math.PI*185*t)*Math.pow(env,2.2)*0.42+(rng.nextDouble()*2-1)*Math.pow(env,3.0)*0.12;}
                else if(type==SFX_WALL){v=Math.sin(2*Math.PI*520*t)*Math.pow(env,2.5)*0.33+Math.sin(2*Math.PI*880*t)*Math.pow(env,3.0)*0.13;}
                else if(type==SFX_GOAL){double f=t<0.13?392:(t<0.26?523:659);v=Math.sin(2*Math.PI*f*t)*env*0.48+Math.sin(2*Math.PI*(f*2)*t)*env*0.10;}
                else if(type==SFX_WIN){double f=t<0.14?523:(t<0.28?659:784);v=Math.sin(2*Math.PI*f*t)*env*0.52;}
                else if(type==SFX_LOSE){double f=t<0.14?330:(t<0.28?277:220);v=Math.sin(2*Math.PI*f*t)*env*0.42;}
                v=Math.max(-1.0,Math.min(1.0,v));
                out[i]=(short)(v*27000);
            }
            return out;
        }

        private String difficultyName(){return difficulty==0?"Easy":difficulty==1?"Normal":"Hard";}
        private String formatTime(float t){int sec=Math.max(0,(int)Math.ceil(t));return String.format(Locale.US,"%d:%02d",sec/60,sec%60);}
        private float len(float x,float y){return (float)Math.sqrt(x*x+y*y);}
        private float clamp(float v,float lo,float hi){return Math.max(lo,Math.min(hi,v));}

        static final class ButtonHit{
            final String id;
            final RectF r;
            ButtonHit(String id,RectF r){this.id=id;this.r=new RectF(r);}
        }
    }
}
