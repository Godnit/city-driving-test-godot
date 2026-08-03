package com.godnit.systemoverlay;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

public class AlarmReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        String mission = intent.getStringExtra("mission");
        if (mission == null || mission.trim().isEmpty()) {
            mission = context.getSharedPreferences("system", Context.MODE_PRIVATE)
                    .getString("mission", "مهمة التدريب اليومية");
        }

        Intent service = new Intent(context, OverlayService.class);
        service.putExtra("mission", mission);
        service.putExtra("from_alarm", true);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.startForegroundService(service);
        } else {
            context.startService(service);
        }
    }
}
