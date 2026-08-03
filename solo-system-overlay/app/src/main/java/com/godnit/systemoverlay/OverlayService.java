package com.godnit.systemoverlay;

import android.animation.AnimatorSet;
import android.animation.ObjectAnimator;
import android.animation.ValueAnimator;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.provider.Settings;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.view.animation.DecelerateInterpolator;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import java.util.Locale;

public class OverlayService extends Service {
    private static final String CHANNEL_ID = "system_overlay";
    private static final int NOTIFICATION_ID = 33;
    private static final int ACCEPT_SECONDS = 300;

    private final Handler handler = new Handler();
    private WindowManager windowManager;
    private View overlayView;
    private WindowManager.LayoutParams windowParams;
    private LinearLayout panelView;
    private HologramFrameView hologramView;
    private TextView stateText;
    private TextView countdownText;
    private TextView messageText;
    private ProgressBar progressBar;
    private ValueAnimator titlePulse;
    private int secondsLeft = ACCEPT_SECONDS;
    private boolean penaltyMode;
    private boolean closing;

    private final Runnable timer = new Runnable() {
        @Override
        public void run() {
            if (overlayView == null || closing) return;
            if (secondsLeft <= 0) {
                if (!penaltyMode) {
                    enterPenaltyMode();
                } else {
                    animateClose();
                    return;
                }
            }
            updateTimerUi();
            secondsLeft--;
            handler.postDelayed(this, 1000);
        }
    };

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        startForeground(NOTIFICATION_ID, buildNotification());
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String mission = intent == null ? null : intent.getStringExtra("mission");
        if (mission == null || mission.trim().isEmpty()) mission = "مهمة التدريب اليومية";

        if (!Settings.canDrawOverlays(this)) {
            stopSelf();
            return START_NOT_STICKY;
        }

        if (overlayView != null) closeOverlayOnly();
        showOverlay(mission);
        return START_NOT_STICKY;
    }

    private void showOverlay(String mission) {
        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
        int width = getResources().getDisplayMetrics().widthPixels - dp(12);

        windowParams = new WindowManager.LayoutParams(
                width,
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE |
                        WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT);
        windowParams.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
        windowParams.y = dp(44);

        FrameLayout outer = new FrameLayout(this);
        outer.setPadding(dp(3), dp(3), dp(3), dp(3));

        hologramView = new HologramFrameView(this);
        outer.addView(hologramView, new FrameLayout.LayoutParams(-1, -1));

        LinearLayout panel = new LinearLayout(this);
        panelView = panel;
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setGravity(Gravity.CENTER_HORIZONTAL);
        panel.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        panel.setPadding(dp(18), dp(8), dp(18), dp(19));
        panel.setBackground(panelBackground(false));
        FrameLayout.LayoutParams panelParams = new FrameLayout.LayoutParams(-1, -2);
        panelParams.setMargins(dp(7), dp(7), dp(7), dp(7));
        outer.addView(panel, panelParams);

        View topGlow = new View(this);
        topGlow.setBackgroundColor(Color.rgb(146, 239, 255));
        topGlow.setAlpha(0.95f);
        panel.addView(topGlow, linearParams(-1, dp(2), dp(8)));

        TextView handle = text("⌁  اسحب لتحريك النظام  ⌁", 11, Color.rgb(94, 164, 195));
        handle.setGravity(Gravity.CENTER);
        handle.setPadding(0, dp(2), 0, dp(4));
        panel.addView(handle, linearParams(-1, -2, dp(1)));
        attachDrag(handle);

        TextView alert = text("!", 24, Color.rgb(198, 250, 255));
        alert.setGravity(Gravity.CENTER);
        alert.setTypeface(null, 1);
        alert.setBackground(alertBackground(false));
        LinearLayout.LayoutParams alertParams = linearParams(dp(48), dp(48), dp(5));
        alertParams.gravity = Gravity.CENTER_HORIZONTAL;
        panel.addView(alert, alertParams);

        TextView system = text("S Y S T E M", 16, Color.rgb(93, 221, 255));
        system.setGravity(Gravity.CENTER);
        system.setTypeface(null, 1);
        system.setLetterSpacing(0.18f);
        system.setShadowLayer(dp(7), 0f, 0f, Color.rgb(42, 182, 255));
        panel.addView(system, linearParams(-1, -2, dp(5)));

        stateText = text("إشعار النظام", 25, Color.WHITE);
        stateText.setGravity(Gravity.CENTER);
        stateText.setTypeface(null, 1);
        stateText.setShadowLayer(dp(5), 0f, 0f, Color.rgb(50, 166, 231));
        panel.addView(stateText, linearParams(-1, -2, dp(10)));

        View divider = new View(this);
        divider.setBackground(dividerBackground(false));
        panel.addView(divider, linearParams(-1, dp(1), dp(13)));

        TextView missionLabel = text("[ المهمة اليومية ]", 13, Color.rgb(104, 225, 255));
        missionLabel.setGravity(Gravity.CENTER);
        missionLabel.setTypeface(null, 1);
        panel.addView(missionLabel, linearParams(-1, -2, dp(7)));

        TextView missionText = text("", 22, Color.WHITE);
        missionText.setGravity(Gravity.CENTER);
        missionText.setTypeface(null, 1);
        missionText.setPadding(dp(10), dp(6), dp(10), dp(6));
        missionText.setShadowLayer(dp(4), 0f, 0f, Color.rgb(41, 137, 213));
        panel.addView(missionText, linearParams(-1, -2, dp(7)));

        messageText = text("", 14, Color.rgb(188, 218, 237));
        messageText.setGravity(Gravity.CENTER);
        panel.addView(messageText, linearParams(-1, -2, dp(12)));

        LinearLayout timeBox = new LinearLayout(this);
        timeBox.setOrientation(LinearLayout.VERTICAL);
        timeBox.setGravity(Gravity.CENTER);
        timeBox.setPadding(dp(10), dp(8), dp(10), dp(9));
        timeBox.setBackground(timeBackground(false));
        panel.addView(timeBox, linearParams(-1, -2, dp(12)));

        TextView timeLabel = text("الوقت المتبقي للقبول", 11, Color.rgb(104, 203, 232));
        timeLabel.setGravity(Gravity.CENTER);
        timeBox.addView(timeLabel, linearParams(-1, -2, dp(1)));

        countdownText = text("05:00", 39, Color.rgb(204, 250, 255));
        countdownText.setGravity(Gravity.CENTER);
        countdownText.setTypeface(null, 1);
        countdownText.setLetterSpacing(0.10f);
        countdownText.setShadowLayer(dp(8), 0f, 0f, Color.rgb(45, 196, 255));
        timeBox.addView(countdownText, linearParams(-1, -2, dp(4)));

        progressBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progressBar.setMax(ACCEPT_SECONDS);
        progressBar.setProgress(ACCEPT_SECONDS);
        progressBar.setProgressTintList(ColorStateList.valueOf(Color.rgb(82, 218, 255)));
        progressBar.setProgressBackgroundTintList(ColorStateList.valueOf(Color.rgb(13, 45, 66)));
        timeBox.addView(progressBar, linearParams(-1, dp(4), 0));

        LinearLayout actions = new LinearLayout(this);
        actions.setOrientation(LinearLayout.HORIZONTAL);
        actions.setGravity(Gravity.CENTER);
        actions.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        panel.addView(actions, linearParams(-1, -2, 0));

        Button startButton = button("قبول المهمة", true);
        LinearLayout.LayoutParams startParams = new LinearLayout.LayoutParams(0, dp(50), 1f);
        startParams.setMarginEnd(dp(6));
        actions.addView(startButton, startParams);

        Button hideButton = button("إخفاء", false);
        LinearLayout.LayoutParams hideParams = new LinearLayout.LayoutParams(0, dp(50), 0.48f);
        hideParams.setMarginStart(dp(6));
        actions.addView(hideButton, hideParams);

        startButton.setOnClickListener(v -> acceptMission());
        hideButton.setOnClickListener(v -> animateClose());

        overlayView = outer;
        secondsLeft = ACCEPT_SECONDS;
        penaltyMode = false;
        closing = false;

        prepareChildrenForReveal(panel);
        outer.setAlpha(0f);
        outer.setScaleX(0.78f);
        outer.setScaleY(0.10f);
        outer.setTranslationY(-dp(70));
        outer.setPivotY(0f);

        try {
            windowManager.addView(overlayView, windowParams);
            playOpeningAnimation(outer, panel, system, alert, topGlow);
            handler.postDelayed(() -> typeText(missionText, mission, 26L), 560L);
            handler.postDelayed(() -> typeText(messageText,
                    "ابدأ المهمة قبل انتهاء الوقت، وإلا سيبدأ وضع العقوبة.", 14L), 940L);
            handler.removeCallbacks(timer);
            handler.postDelayed(timer, 1100L);
        } catch (RuntimeException error) {
            overlayView = null;
            stopSelf();
        }
    }

    private void prepareChildrenForReveal(LinearLayout panel) {
        for (int i = 0; i < panel.getChildCount(); i++) {
            View child = panel.getChildAt(i);
            child.setAlpha(0f);
            child.setTranslationY(dp(10));
        }
    }

    private void playOpeningAnimation(View outer, LinearLayout panel, TextView system,
                                      TextView alert, View topGlow) {
        ObjectAnimator alpha = ObjectAnimator.ofFloat(outer, View.ALPHA, 0f, 1f);
        ObjectAnimator scaleX = ObjectAnimator.ofFloat(outer, View.SCALE_X, 0.78f, 1.03f, 1f);
        ObjectAnimator scaleY = ObjectAnimator.ofFloat(outer, View.SCALE_Y, 0.10f, 1.08f, 1f);
        ObjectAnimator translate = ObjectAnimator.ofFloat(outer, View.TRANSLATION_Y, -dp(70), dp(6), 0f);
        AnimatorSet opening = new AnimatorSet();
        opening.playTogether(alpha, scaleX, scaleY, translate);
        opening.setDuration(470L);
        opening.setInterpolator(new DecelerateInterpolator(1.7f));
        opening.start();

        for (int i = 0; i < panel.getChildCount(); i++) {
            View child = panel.getChildAt(i);
            child.animate()
                    .alpha(1f)
                    .translationY(0f)
                    .setStartDelay(190L + (i * 48L))
                    .setDuration(260L)
                    .setInterpolator(new DecelerateInterpolator())
                    .start();
        }

        alert.setScaleX(0f);
        alert.setScaleY(0f);
        alert.animate().scaleX(1f).scaleY(1f)
                .setStartDelay(260L).setDuration(360L)
                .setInterpolator(new DecelerateInterpolator(1.9f)).start();

        topGlow.setScaleX(0f);
        topGlow.animate().scaleX(1f).setStartDelay(120L).setDuration(420L).start();

        titlePulse = ObjectAnimator.ofFloat(system, View.ALPHA, 0.58f, 1f, 0.72f, 1f);
        titlePulse.setDuration(1600L);
        titlePulse.setRepeatCount(ValueAnimator.INFINITE);
        titlePulse.setRepeatMode(ValueAnimator.REVERSE);
        titlePulse.setStartDelay(700L);
        titlePulse.start();

        handler.postDelayed(() -> flicker(outer), 430L);
    }

    private void flicker(View view) {
        if (view == null || closing) return;
        view.animate().alpha(0.55f).setDuration(35L).withEndAction(() ->
                view.animate().alpha(1f).setDuration(65L).withEndAction(() ->
                        view.animate().alpha(0.78f).setDuration(30L).withEndAction(() ->
                                view.animate().alpha(1f).setDuration(80L).start()).start()).start()).start();
    }

    private void typeText(TextView target, String value, long delay) {
        if (target == null || value == null) return;
        target.setText("");
        final int[] index = {0};
        Runnable writer = new Runnable() {
            @Override
            public void run() {
                if (overlayView == null || closing) return;
                if (index[0] < value.length()) {
                    index[0]++;
                    target.setText(value.substring(0, index[0]));
                    handler.postDelayed(this, delay);
                }
            }
        };
        handler.post(writer);
    }

    private void acceptMission() {
        if (closing) return;
        handler.removeCallbacks(timer);
        stateText.setText("تم قبول المهمة");
        stateText.setTextColor(Color.rgb(113, 255, 189));
        stateText.setShadowLayer(dp(8), 0f, 0f, Color.rgb(55, 255, 172));
        messageText.setText("سجّل النظام استجابتك. ابدأ التدريب الآن.");
        countdownText.setText("✓");
        countdownText.setTextColor(Color.rgb(113, 255, 189));
        countdownText.setShadowLayer(dp(9), 0f, 0f, Color.rgb(55, 255, 172));
        progressBar.setProgress(ACCEPT_SECONDS);
        progressBar.setProgressTintList(ColorStateList.valueOf(Color.rgb(105, 255, 177)));
        if (hologramView != null) {
            hologramView.animate().alpha(0.55f).setDuration(100L)
                    .withEndAction(() -> hologramView.animate().alpha(1f).setDuration(180L).start()).start();
        }
        handler.postDelayed(this::animateClose, 1900L);
    }

    private void enterPenaltyMode() {
        penaltyMode = true;
        secondsLeft = 60;
        if (hologramView != null) hologramView.setPenalty(true);
        if (panelView != null) panelView.setBackground(panelBackground(true));
        stateText.setText("فشل في قبول المهمة");
        stateText.setTextColor(Color.rgb(255, 112, 135));
        stateText.setShadowLayer(dp(8), 0f, 0f, Color.rgb(255, 44, 90));
        messageText.setText("بدأ وضع العقوبة التجريبي. لن يختفي التحذير لمدة دقيقة.");
        countdownText.setTextColor(Color.rgb(255, 145, 159));
        countdownText.setShadowLayer(dp(9), 0f, 0f, Color.rgb(255, 48, 88));
        progressBar.setMax(60);
        progressBar.setProgressTintList(ColorStateList.valueOf(Color.rgb(255, 76, 111)));

        ObjectAnimator shake = ObjectAnimator.ofFloat(overlayView, View.TRANSLATION_X,
                0f, -dp(10), dp(9), -dp(7), dp(6), -dp(3), 0f);
        shake.setDuration(470L);
        shake.start();
        flicker(overlayView);
    }

    private void updateTimerUi() {
        int minutes = Math.max(0, secondsLeft) / 60;
        int seconds = Math.max(0, secondsLeft) % 60;
        countdownText.setText(String.format(Locale.US, "%02d:%02d", minutes, seconds));
        progressBar.setProgress(Math.max(0, secondsLeft));
    }

    private void attachDrag(View handle) {
        handle.setOnTouchListener(new View.OnTouchListener() {
            private float downY;
            private int originalY;

            @Override
            public boolean onTouch(View view, MotionEvent event) {
                switch (event.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        downY = event.getRawY();
                        originalY = windowParams.y;
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        int maxY = getResources().getDisplayMetrics().heightPixels - dp(150);
                        windowParams.y = Math.max(0,
                                Math.min(maxY, originalY + Math.round(event.getRawY() - downY)));
                        if (overlayView != null) windowManager.updateViewLayout(overlayView, windowParams);
                        return true;
                    default:
                        return true;
                }
            }
        });
    }

    private Notification buildNotification() {
        Intent openApp = new Intent(this, MainActivity.class);
        PendingIntent contentIntent = PendingIntent.getActivity(
                this, 11, openApp, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        Notification.Builder builder = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(this, CHANNEL_ID)
                : new Notification.Builder(this);
        return builder
                .setSmallIcon(com.godnit.systemoverlay.R.drawable.ic_system)
                .setContentTitle("نظام التدريب يعمل")
                .setContentText("شاشة النظام العائمة مفعّلة")
                .setContentIntent(contentIntent)
                .setOngoing(true)
                .setCategory(Notification.CATEGORY_REMINDER)
                .build();
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID, "نظام التدريب", NotificationManager.IMPORTANCE_LOW);
            channel.setDescription("تشغيل شاشة المهام العائمة");
            channel.setShowBadge(false);
            NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            manager.createNotificationChannel(channel);
        }
    }

    private Button button(String value, boolean primary) {
        Button button = new Button(this);
        button.setText(value);
        button.setTextSize(15);
        button.setAllCaps(false);
        button.setTypeface(null, 1);
        button.setTextColor(primary ? Color.rgb(2, 18, 31) : Color.rgb(218, 247, 255));
        GradientDrawable background = new GradientDrawable(
                GradientDrawable.Orientation.LEFT_RIGHT,
                primary
                        ? new int[]{Color.rgb(87, 216, 255), Color.rgb(177, 247, 255)}
                        : new int[]{Color.argb(210, 12, 38, 59), Color.argb(210, 17, 53, 77)});
        background.setCornerRadius(dp(3));
        background.setStroke(dp(1), primary ? Color.WHITE : Color.rgb(87, 183, 219));
        button.setBackground(background);
        return button;
    }

    private TextView text(String value, float size, int color) {
        TextView text = new TextView(this);
        text.setText(value);
        text.setTextSize(size);
        text.setTextColor(color);
        text.setLineSpacing(0, 1.12f);
        return text;
    }

    private GradientDrawable panelBackground(boolean penalty) {
        GradientDrawable drawable = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                penalty
                        ? new int[]{Color.argb(244, 42, 7, 21), Color.argb(242, 15, 3, 13)}
                        : new int[]{Color.argb(242, 5, 26, 48), Color.argb(244, 2, 11, 26)});
        drawable.setCornerRadius(dp(2));
        drawable.setStroke(dp(1), penalty ? Color.rgb(194, 49, 80) : Color.rgb(58, 151, 193));
        return drawable;
    }

    private GradientDrawable alertBackground(boolean penalty) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setShape(GradientDrawable.RECTANGLE);
        drawable.setColor(penalty ? Color.argb(100, 255, 42, 88) : Color.argb(90, 60, 195, 255));
        drawable.setStroke(dp(1), penalty ? Color.rgb(255, 94, 120) : Color.rgb(141, 237, 255));
        drawable.setCornerRadius(dp(2));
        return drawable;
    }

    private GradientDrawable timeBackground(boolean penalty) {
        GradientDrawable drawable = new GradientDrawable(
                GradientDrawable.Orientation.LEFT_RIGHT,
                penalty
                        ? new int[]{Color.argb(125, 94, 12, 35), Color.argb(65, 30, 2, 14)}
                        : new int[]{Color.argb(130, 8, 55, 83), Color.argb(65, 2, 18, 34)});
        drawable.setCornerRadius(dp(2));
        drawable.setStroke(dp(1), penalty ? Color.rgb(170, 45, 74) : Color.rgb(44, 124, 166));
        return drawable;
    }

    private GradientDrawable dividerBackground(boolean penalty) {
        GradientDrawable drawable = new GradientDrawable(
                GradientDrawable.Orientation.LEFT_RIGHT,
                penalty
                        ? new int[]{Color.TRANSPARENT, Color.rgb(255, 77, 110), Color.TRANSPARENT}
                        : new int[]{Color.TRANSPARENT, Color.rgb(113, 223, 255), Color.TRANSPARENT});
        return drawable;
    }

    private LinearLayout.LayoutParams linearParams(int width, int height, int bottomMargin) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(width, height);
        params.bottomMargin = bottomMargin;
        return params;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private void animateClose() {
        if (closing || overlayView == null) return;
        closing = true;
        handler.removeCallbacks(timer);
        overlayView.animate()
                .alpha(0f)
                .scaleX(0.82f)
                .scaleY(0.12f)
                .translationY(-dp(45))
                .setDuration(260L)
                .setInterpolator(new DecelerateInterpolator())
                .withEndAction(this::closeOverlay)
                .start();
    }

    private void closeOverlayOnly() {
        handler.removeCallbacksAndMessages(null);
        if (titlePulse != null) {
            titlePulse.cancel();
            titlePulse = null;
        }
        if (overlayView != null) overlayView.animate().cancel();
        if (overlayView != null && windowManager != null) {
            try {
                windowManager.removeView(overlayView);
            } catch (RuntimeException ignored) {
            }
        }
        overlayView = null;
        panelView = null;
        hologramView = null;
    }

    private void closeOverlay() {
        closeOverlayOnly();
        stopForeground(true);
        stopSelf();
    }

    @Override
    public void onDestroy() {
        closeOverlayOnly();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
