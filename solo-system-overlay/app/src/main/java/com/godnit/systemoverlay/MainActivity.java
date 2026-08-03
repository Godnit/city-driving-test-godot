package com.godnit.systemoverlay;

import android.app.Activity;
import android.app.AlarmManager;
import android.app.PendingIntent;
import android.app.TimePickerDialog;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.text.DateFormat;
import java.util.Calendar;
import java.util.Date;

public class MainActivity extends Activity {
    private EditText missionInput;
    private TextView selectedTimeText;
    private Button permissionButton;
    private int selectedHour;
    private int selectedMinute;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Calendar now = Calendar.getInstance();
        selectedHour = now.get(Calendar.HOUR_OF_DAY);
        selectedMinute = (now.get(Calendar.MINUTE) + 2) % 60;
        if (selectedMinute < now.get(Calendar.MINUTE)) selectedHour = (selectedHour + 1) % 24;
        buildInterface();
    }

    @Override
    protected void onResume() {
        super.onResume();
        updatePermissionButton();
    }

    private void buildInterface() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.rgb(5, 9, 20));

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(20), dp(36), dp(20), dp(28));
        root.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        scroll.addView(root, new ScrollView.LayoutParams(-1, -2));

        TextView system = label("S Y S T E M", 14, Color.rgb(83, 231, 255));
        system.setGravity(Gravity.CENTER);
        root.addView(system, matchWrap(dp(8)));

        TextView title = label("نظام التدريب العائم", 30, Color.WHITE);
        title.setGravity(Gravity.CENTER);
        title.setTypeface(null, 1);
        root.addView(title, matchWrap(dp(6)));

        TextView subtitle = label("حدد وقت المهمة وستظهر نافذة النظام فوق أي تطبيق.", 15, Color.rgb(171, 191, 214));
        subtitle.setGravity(Gravity.CENTER);
        root.addView(subtitle, matchWrap(dp(28)));

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18), dp(20), dp(18), dp(20));
        card.setBackground(panelBackground());
        root.addView(card, new LinearLayout.LayoutParams(-1, -2));

        TextView missionLabel = label("المهمة", 13, Color.rgb(83, 231, 255));
        card.addView(missionLabel, matchWrap(dp(8)));

        missionInput = new EditText(this);
        missionInput.setText("تدريب القوة اليومية");
        missionInput.setTextColor(Color.WHITE);
        missionInput.setHintTextColor(Color.GRAY);
        missionInput.setTextSize(18);
        missionInput.setSingleLine(true);
        missionInput.setPadding(dp(14), dp(12), dp(14), dp(12));
        missionInput.setBackground(fieldBackground());
        card.addView(missionInput, matchWrap(dp(18)));

        TextView timeLabel = label("وقت ظهور النظام", 13, Color.rgb(83, 231, 255));
        card.addView(timeLabel, matchWrap(dp(8)));

        selectedTimeText = label(formatTime(selectedHour, selectedMinute), 28, Color.WHITE);
        selectedTimeText.setGravity(Gravity.CENTER);
        selectedTimeText.setPadding(dp(12), dp(13), dp(12), dp(13));
        selectedTimeText.setBackground(fieldBackground());
        selectedTimeText.setOnClickListener(v -> openTimePicker());
        card.addView(selectedTimeText, matchWrap(dp(16)));

        Button chooseTime = actionButton("اختيار الوقت", false);
        chooseTime.setOnClickListener(v -> openTimePicker());
        card.addView(chooseTime, matchWrap(dp(10)));

        permissionButton = actionButton("السماح بالظهور فوق التطبيقات", false);
        permissionButton.setOnClickListener(v -> requestOverlayPermission());
        card.addView(permissionButton, matchWrap(dp(10)));

        Button schedule = actionButton("تفعيل المهمة", true);
        schedule.setOnClickListener(v -> scheduleMission());
        card.addView(schedule, matchWrap(dp(10)));

        Button preview = actionButton("تجربة الشاشة الآن", false);
        preview.setOnClickListener(v -> launchOverlay(false));
        card.addView(preview, matchWrap(0));

        TextView note = label("نسخة أولى آمنة: عند انتهاء العدّاد تتحول النافذة إلى وضع عقوبة بصري لمدة دقيقة، ولا تقفل المكالمات أو الهاتف.", 13, Color.rgb(139, 158, 181));
        note.setGravity(Gravity.CENTER);
        root.addView(note, matchWrap(dp(18)));

        setContentView(scroll);
        updatePermissionButton();
    }

    private void openTimePicker() {
        TimePickerDialog dialog = new TimePickerDialog(this, (view, hour, minute) -> {
            selectedHour = hour;
            selectedMinute = minute;
            selectedTimeText.setText(formatTime(hour, minute));
        }, selectedHour, selectedMinute, false);
        dialog.show();
    }

    private void requestOverlayPermission() {
        if (Settings.canDrawOverlays(this)) {
            Toast.makeText(this, "الإذن مفعّل بالفعل", Toast.LENGTH_SHORT).show();
            return;
        }
        Intent intent = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:" + getPackageName()));
        startActivity(intent);
    }

    private void updatePermissionButton() {
        if (permissionButton == null) return;
        boolean granted = Settings.canDrawOverlays(this);
        permissionButton.setText(granted ? "✓ إذن الظهور مفعّل" : "السماح بالظهور فوق التطبيقات");
    }

    private void scheduleMission() {
        if (!Settings.canDrawOverlays(this)) {
            requestOverlayPermission();
            Toast.makeText(this, "فعّل الإذن ثم ارجع واضغط تفعيل المهمة", Toast.LENGTH_LONG).show();
            return;
        }

        Calendar trigger = Calendar.getInstance();
        trigger.set(Calendar.HOUR_OF_DAY, selectedHour);
        trigger.set(Calendar.MINUTE, selectedMinute);
        trigger.set(Calendar.SECOND, 0);
        trigger.set(Calendar.MILLISECOND, 0);
        if (trigger.getTimeInMillis() <= System.currentTimeMillis()) {
            trigger.add(Calendar.DAY_OF_YEAR, 1);
        }

        String mission = cleanMission();
        Intent intent = new Intent(this, AlarmReceiver.class);
        intent.putExtra("mission", mission);
        PendingIntent pending = PendingIntent.getBroadcast(
                this, 901, intent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        AlarmManager alarmManager = (AlarmManager) getSystemService(ALARM_SERVICE);
        try {
            alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger.getTimeInMillis(), pending);
        } catch (SecurityException ex) {
            alarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger.getTimeInMillis(), pending);
        }

        getSharedPreferences("system", MODE_PRIVATE).edit()
                .putString("mission", mission)
                .putLong("next_time", trigger.getTimeInMillis())
                .apply();

        String date = DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.SHORT)
                .format(new Date(trigger.getTimeInMillis()));
        Toast.makeText(this, "تم تفعيل المهمة: " + date, Toast.LENGTH_LONG).show();
    }

    private void launchOverlay(boolean fromAlarm) {
        if (!Settings.canDrawOverlays(this)) {
            requestOverlayPermission();
            return;
        }
        Intent service = new Intent(this, OverlayService.class);
        service.putExtra("mission", cleanMission());
        service.putExtra("from_alarm", fromAlarm);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) startForegroundService(service);
        else startService(service);
    }

    private String cleanMission() {
        String mission = missionInput.getText().toString().trim();
        return mission.isEmpty() ? "مهمة التدريب اليومية" : mission;
    }

    private Button actionButton(String text, boolean primary) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextSize(16);
        button.setAllCaps(false);
        button.setTypeface(null, 1);
        button.setTextColor(primary ? Color.rgb(3, 18, 29) : Color.WHITE);
        GradientDrawable background = new GradientDrawable();
        background.setCornerRadius(dp(8));
        background.setColor(primary ? Color.rgb(83, 231, 255) : Color.rgb(20, 37, 58));
        background.setStroke(dp(1), primary ? Color.rgb(185, 247, 255) : Color.rgb(57, 103, 139));
        button.setBackground(background);
        button.setMinHeight(dp(52));
        return button;
    }

    private TextView label(String text, float size, int color) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextSize(size);
        view.setTextColor(color);
        view.setLineSpacing(0, 1.15f);
        return view;
    }

    private GradientDrawable panelBackground() {
        GradientDrawable drawable = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[]{Color.rgb(13, 25, 43), Color.rgb(7, 14, 28)});
        drawable.setCornerRadius(dp(14));
        drawable.setStroke(dp(1), Color.rgb(48, 120, 154));
        return drawable;
    }

    private GradientDrawable fieldBackground() {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(Color.rgb(7, 15, 29));
        drawable.setCornerRadius(dp(8));
        drawable.setStroke(dp(1), Color.rgb(38, 75, 104));
        return drawable;
    }

    private LinearLayout.LayoutParams matchWrap(int bottomMargin) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.bottomMargin = bottomMargin;
        return params;
    }

    private String formatTime(int hour, int minute) {
        Calendar calendar = Calendar.getInstance();
        calendar.set(Calendar.HOUR_OF_DAY, hour);
        calendar.set(Calendar.MINUTE, minute);
        return new java.text.SimpleDateFormat("hh:mm a", java.util.Locale.getDefault())
                .format(calendar.getTime());
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
