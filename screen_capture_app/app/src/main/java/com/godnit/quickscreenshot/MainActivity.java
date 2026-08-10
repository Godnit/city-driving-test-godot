package com.godnit.quickscreenshot;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.media.projection.MediaProjectionManager;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private static final int REQ_CAPTURE = 1001;
    private static final int REQ_STORAGE = 1002;
    private MediaProjectionManager projectionManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        projectionManager = (MediaProjectionManager) getSystemService(Context.MEDIA_PROJECTION_SERVICE);
        setContentView(buildUi());
    }

    private View buildUi() {
        int pad = dp(24);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(pad, pad, pad, pad);
        root.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        root.setBackgroundColor(Color.rgb(246, 248, 252));

        TextView title = new TextView(this);
        title.setText("📸 لقطة سريعة");
        title.setTextSize(28);
        title.setTextColor(Color.rgb(24, 34, 55));
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, 0, 0, dp(14));
        root.addView(title, new LinearLayout.LayoutParams(-1, -2));

        TextView info = new TextView(this);
        info.setText("فعّل الخدمة مرة واحدة، ثم استخدم زر «التقاط» من الإشعارات. عند الضغط ستُغلق لوحة الإشعارات أولاً ثم تُحفظ اللقطة في الصور.");
        info.setTextSize(17);
        info.setTextColor(Color.rgb(65, 76, 96));
        info.setGravity(Gravity.CENTER);
        info.setLineSpacing(0, 1.25f);
        info.setPadding(0, 0, 0, dp(24));
        root.addView(info, new LinearLayout.LayoutParams(-1, -2));

        Button enable = new Button(this);
        enable.setText("تفعيل زر الالتقاط");
        enable.setTextSize(18);
        enable.setAllCaps(false);
        enable.setOnClickListener(v -> prepareAndRequestCapture());
        LinearLayout.LayoutParams bp = new LinearLayout.LayoutParams(-1, dp(58));
        bp.setMargins(0, 0, 0, dp(14));
        root.addView(enable, bp);

        TextView note = new TextView(this);
        note.setText("ملاحظة: أندرويد نفسه سيطلب السماح بالتقاط الشاشة عند التفعيل. هذا الإذن لا يمكن تجاوزه من أي تطبيق.");
        note.setTextSize(14);
        note.setTextColor(Color.rgb(105, 113, 128));
        note.setGravity(Gravity.CENTER);
        root.addView(note, new LinearLayout.LayoutParams(-1, -2));

        return root;
    }

    private void prepareAndRequestCapture() {
        if (Build.VERSION.SDK_INT <= Build.VERSION_CODES.P &&
                checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, REQ_STORAGE);
            return;
        }
        requestProjection();
    }

    private void requestProjection() {
        startActivityForResult(projectionManager.createScreenCaptureIntent(), REQ_CAPTURE);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQ_STORAGE) {
            requestProjection();
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQ_CAPTURE) return;

        if (resultCode != RESULT_OK || data == null) {
            Toast.makeText(this, "لم يتم منح إذن التقاط الشاشة", Toast.LENGTH_LONG).show();
            return;
        }

        Intent service = new Intent(this, CaptureService.class);
        service.setAction(CaptureService.ACTION_START);
        service.putExtra(CaptureService.EXTRA_RESULT_CODE, resultCode);
        service.putExtra(CaptureService.EXTRA_RESULT_DATA, data);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(service);
        } else {
            startService(service);
        }

        Toast.makeText(this, "تم التفعيل 👍 افتح الإشعارات واضغط «التقاط»", Toast.LENGTH_LONG).show();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
