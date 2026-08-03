package com.godnit.systemoverlay;

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
    private TextView stateText;
    private TextView countdownText;
    private TextView messageText;
    private ProgressBar progressBar;
    private int secondsLeft = ACCEPT_SECONDS;
    private boolean penaltyMode;

    private final Runnable timer = new Runnable() {
        @Override
        public void run() {
            if (overlayView == null) return;
            if (secondsLeft <= 0) {
                if (!penaltyMode) {
                    enterPenaltyMode();
                } else {
                    closeOverlay();
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
        int width = getResources().getDisplayMetrics().widthPixels - dp(18);

        windowParams = new WindowManager.LayoutParams(
                width,
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE |
                        WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT);
        windowParams.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
        windowParams.y = dp(54);

        FrameLayout outer = new FrameLayout(this);
        outer.setPadding(dp(2), dp(2), dp(2), dp(2));
        outer.setBackground(glowBorder(false));

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setGravity(Gravity.CENTER_HORIZONTAL);
        panel.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        panel.setPadding(dp(18), dp(10), dp(18), dp(18));
        panel.setBackground(panelBackground(false));
        outer.addView(panel, new FrameLayout.LayoutParams(-1, -2));

        TextView handle = text("—  اسحب لتحريك النافذة  —", 12, Color.rgb(106, 159, 186));
        handle.setGravity(Gravity.CENTER);
        handle.setPadding(0, dp(4), 0, dp(8));
        panel.addView(handle, linearParams(-1, -2, dp(2)));
        attachDrag(handle);

        TextView system = text("◇  S Y S T E M  ◇", 15, Color.rgb(83, 231, 255));
        system.setGravity(Gravity.CENTER);
        system.setTypeface(null, 1);
        system.setLetterSpacing(0.12f);
        panel.addView(system, linearParams(-1, -2, dp(5)));

        stateText = text("إشعار مهمة عاجلة", 23, Color.WHITE);
        stateText.setGravity(Gravity.CENTER);
        stateText.setTypeface(null, 1);
        panel.addView(stateText, linearParams(-1, -2, dp(10)));

        View divider = new View(this);
        divider.setBackgroundColor(Color.rgb(55, 123, 153));
        panel.addView(divider, linearParams(-1, dp(1), dp(14)));

        TextView missionLabel = text("[ المهمة اليومية ]", 13, Color.rgb(83, 231, 255));
        missionLabel.setGravity(Gravity.CENTER);
        panel.addView(missionLabel, linearParams(-1, -2, dp(7)));

        TextView missionText = text(mission, 21, Color.WHITE);
        missionText.setGravity(Gravity.CENTER);
        missionText.setTypeface(null, 1);
        missionText.setPadding(dp(10), dp(7), dp(10), dp(7));
        panel.addView(missionText, linearParams(-1, -2, dp(8)));

        messageText = text("ابدأ المهمة قبل انتهاء الوقت لتجنب وضع العقوبة.", 14,
                Color.rgb(183, 204, 224));
        messageText.setGravity(Gravity.CENTER);
        panel.addView(messageText, linearParams(-1, -2, dp(12)));

        countdownText = text("05:00", 38, Color.rgb(185, 247, 255));
        countdownText.setGravity(Gravity.CENTER);
        countdownText.setTypeface(null, 1);
        countdownText.setLetterSpacing(0.08f);
        panel.addView(countdownText, linearParams(-1, -2, dp(8)));

        progressBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progressBar.setMax(ACCEPT_SECONDS);
        progressBar.setProgress(ACCEPT_SECONDS);
        progressBar.setProgressTintList(ColorStateList.valueOf(Color.rgb(83, 231, 255)));
        progressBar.setProgressBackgroundTintList(ColorStateList.valueOf(Color.rgb(18, 41, 61)));
        panel.addView(progressBar, linearParams(-1, dp(5), dp(16)));

        LinearLayout actions = new LinearLayout(this);
        actions.setOrientation(LinearLayout.HORIZONTAL);
        actions.setGravity(Gravity.CENTER);
        actions.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        panel.addView(actions, linearParams(-1, -2, 0));

        Button startButton = button("بدأت المهمة", true);
        LinearLayout.LayoutParams startParams = new LinearLayout.LayoutParams(0, dp(50), 1f);
        startParams.setMarginEnd(dp(6));
        actions.addView(startButton, startParams);

        Button hideButton = button("إخفاء", false);
        LinearLayout.LayoutParams hideParams = new LinearLayout.LayoutParams(0, dp(50), 0.55f);
        hideParams.setMarginStart(dp(6));
        actions.addView(hideButton, hideParams);

        startButton.setOnClickListener(v -> {
            handler.removeCallbacks(timer);
            stateText.setText("تم قبول المهمة");
            stateText.setTextColor(Color.rgb(105, 255, 177));
            messageText.setText("ابدأ الآن. لقد سجّل النظام استجابتك.");
            countdownText.setText("✓");
            countdownText.setTextColor(Color.rgb(105, 255, 177));
            progressBar.setProgress(ACCEPT_SECONDS);
            progressBar.setProgressTintList(ColorStateList.valueOf(Color.rgb(105, 255, 177)));
            handler.postDelayed(this::closeOverlay, 1800);
        });
        hideButton.setOnClickListener(v -> closeOverlay());

        overlayView = outer;
        secondsLeft = ACCEPT_SECONDS;
        penaltyMode = false;
        try {
            windowManager.addView(overlayView, windowParams);
            handler.removeCallbacks(timer);
            handler.post(timer);
        } catch (RuntimeException error) {
            overlayView = null;
            stopSelf();
        }
    }

    private void enterPenaltyMode() {
        penaltyMode = true;
        secondsLeft = 60;
        stateText.setText("وضع العقوبة التجريبي");
        stateText.setTextColor(Color.rgb(255, 106, 124));
        messageText.setText("انتهى وقت الاستجابة. سيبقى التحذير دقيقة واحدة.");
        countdownText.setTextColor(Color.rgb(255, 125, 137));
        progressBar.setMax(60);
        progressBar.setProgressTintList(ColorStateList.valueOf(Color.rgb(255, 87, 110)));
        if (overlayView != null) overlayView.setBackground(glowBorder(true));
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
                .setContentText("النافذة العائمة مفعّلة")
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
        button.setTextColor(primary ? Color.rgb(3, 18, 29) : Color.WHITE);
        GradientDrawable background = new GradientDrawable();
        background.setCornerRadius(dp(7));
        background.setColor(primary ? Color.rgb(83, 231, 255) : Color.rgb(20, 37, 58));
        background.setStroke(dp(1), primary ? Color.rgb(185, 247, 255) : Color.rgb(59, 106, 139));
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
                        ? new int[]{Color.rgb(43, 12, 24), Color.rgb(18, 6, 16)}
                        : new int[]{Color.rgb(12, 27, 47), Color.rgb(5, 12, 25)});
        drawable.setCornerRadius(dp(12));
        return drawable;
    }

    private GradientDrawable glowBorder(boolean penalty) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(penalty ? Color.rgb(157, 42, 64) : Color.rgb(53, 172, 210));
        drawable.setCornerRadius(dp(14));
        drawable.setStroke(dp(1), penalty ? Color.rgb(255, 109, 128) : Color.rgb(168, 244, 255));
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

    private void closeOverlayOnly() {
        handler.removeCallbacks(timer);
        if (overlayView != null && windowManager != null) {
            try {
                windowManager.removeView(overlayView);
            } catch (RuntimeException ignored) {
            }
        }
        overlayView = null;
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
