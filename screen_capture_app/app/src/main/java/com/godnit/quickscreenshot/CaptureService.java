package com.godnit.quickscreenshot;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.PixelFormat;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.media.Image;
import android.media.ImageReader;
import android.media.MediaScannerConnection;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.provider.MediaStore;
import android.util.DisplayMetrics;
import android.view.WindowManager;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicBoolean;

public class CaptureService extends Service {
    public static final String ACTION_START = "com.godnit.quickscreenshot.START";
    public static final String ACTION_CAPTURE = "com.godnit.quickscreenshot.CAPTURE";
    public static final String EXTRA_RESULT_CODE = "resultCode";
    public static final String EXTRA_RESULT_DATA = "resultData";

    private static final String CHANNEL_ID = "quick_capture_channel";
    private static final int NOTIFICATION_ID = 41;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final AtomicBoolean capturing = new AtomicBoolean(false);

    private NotificationManager notificationManager;
    private MediaProjection mediaProjection;
    private ImageReader imageReader;
    private VirtualDisplay virtualDisplay;

    @Override
    public void onCreate() {
        super.onCreate();
        notificationManager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        createChannel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent == null) return START_STICKY;
        String action = intent.getAction();

        if (ACTION_START.equals(action)) {
            startForeground(NOTIFICATION_ID, buildNotification("جاهز لالتقاط الشاشة"));
            int resultCode = intent.getIntExtra(EXTRA_RESULT_CODE, ActivityResultFallback.RESULT_CANCELED);
            Intent resultData = intent.getParcelableExtra(EXTRA_RESULT_DATA);
            if (resultCode == ActivityResultFallback.RESULT_OK && resultData != null) {
                if (mediaProjection != null) mediaProjection.stop();
                MediaProjectionManager mgr = (MediaProjectionManager) getSystemService(Context.MEDIA_PROJECTION_SERVICE);
                mediaProjection = mgr.getMediaProjection(resultCode, resultData);
                mediaProjection.registerCallback(new MediaProjection.Callback() {
                    @Override
                    public void onStop() {
                        cleanupCaptureObjects();
                        stopForeground(true);
                        stopSelf();
                    }
                }, handler);
            }
            return START_STICKY;
        }

        if (ACTION_CAPTURE.equals(action)) {
            if (mediaProjection == null) {
                toast("افتح التطبيق واضغط «تفعيل زر الالتقاط» أولاً");
                return START_STICKY;
            }
            captureAfterClosingShade();
        }

        return START_STICKY;
    }

    private void captureAfterClosingShade() {
        if (!capturing.compareAndSet(false, true)) return;

        try {
            stopForeground(true);
            notificationManager.cancel(NOTIFICATION_ID);
        } catch (Exception ignored) { }

        try {
            sendBroadcast(new Intent(Intent.ACTION_CLOSE_SYSTEM_DIALOGS));
        } catch (Exception ignored) { }

        handler.postDelayed(this::beginCapture, 600);
        handler.postDelayed(() -> {
            if (capturing.compareAndSet(true, false)) {
                cleanupCaptureObjects();
                restoreNotification();
                toast("تعذر أخذ اللقطة، حاول مرة أخرى");
            }
        }, 3500);
    }

    private void beginCapture() {
        if (!capturing.get() || mediaProjection == null) {
            capturing.set(false);
            restoreNotification();
            return;
        }

        DisplayMetrics metrics = new DisplayMetrics();
        WindowManager wm = (WindowManager) getSystemService(Context.WINDOW_SERVICE);
        wm.getDefaultDisplay().getRealMetrics(metrics);

        final int width = metrics.widthPixels;
        final int height = metrics.heightPixels;
        final int density = metrics.densityDpi;

        cleanupCaptureObjects();
        imageReader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2);
        imageReader.setOnImageAvailableListener(reader -> {
            if (!capturing.get()) return;
            Image image = null;
            try {
                image = reader.acquireLatestImage();
                if (image == null) return;

                Image.Plane plane = image.getPlanes()[0];
                ByteBuffer buffer = plane.getBuffer();
                int pixelStride = plane.getPixelStride();
                int rowStride = plane.getRowStride();
                int rowPadding = rowStride - pixelStride * width;
                int bitmapWidth = width + rowPadding / pixelStride;

                Bitmap raw = Bitmap.createBitmap(bitmapWidth, height, Bitmap.Config.ARGB_8888);
                raw.copyPixelsFromBuffer(buffer);
                Bitmap cropped = Bitmap.createBitmap(raw, 0, 0, width, height);
                if (raw != cropped) raw.recycle();

                String saved = saveBitmap(cropped);
                cropped.recycle();

                if (capturing.compareAndSet(true, false)) {
                    cleanupCaptureObjects();
                    restoreNotification();
                    toast(saved == null ? "فشل حفظ اللقطة" : "تم حفظ اللقطة 📸");
                }
            } catch (Exception e) {
                if (capturing.compareAndSet(true, false)) {
                    cleanupCaptureObjects();
                    restoreNotification();
                    toast("حدث خطأ أثناء الالتقاط");
                }
            } finally {
                if (image != null) image.close();
            }
        }, handler);

        virtualDisplay = mediaProjection.createVirtualDisplay(
                "QuickScreenshot",
                width,
                height,
                density,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
                imageReader.getSurface(),
                null,
                handler
        );
    }

    private String saveBitmap(Bitmap bitmap) {
        String stamp = new SimpleDateFormat("yyyyMMdd_HHmmss_SSS", Locale.US).format(new Date());
        String name = "Screenshot_" + stamp + ".png";

        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                ContentResolver resolver = getContentResolver();
                ContentValues values = new ContentValues();
                values.put(MediaStore.Images.Media.DISPLAY_NAME, name);
                values.put(MediaStore.Images.Media.MIME_TYPE, "image/png");
                values.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/QuickScreenshot");
                values.put(MediaStore.Images.Media.IS_PENDING, 1);

                Uri uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
                if (uri == null) return null;
                try (OutputStream out = resolver.openOutputStream(uri)) {
                    if (out == null || !bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)) return null;
                }
                values.clear();
                values.put(MediaStore.Images.Media.IS_PENDING, 0);
                resolver.update(uri, values, null, null);
                return uri.toString();
            }

            File publicDir = new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES), "QuickScreenshot");
            if (!publicDir.exists() && !publicDir.mkdirs()) {
                return saveFallback(bitmap, name);
            }
            File file = new File(publicDir, name);
            try (FileOutputStream out = new FileOutputStream(file)) {
                if (!bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)) return null;
            }
            MediaScannerConnection.scanFile(this, new String[]{file.getAbsolutePath()}, new String[]{"image/png"}, null);
            return file.getAbsolutePath();
        } catch (Exception e) {
            return saveFallback(bitmap, name);
        }
    }

    private String saveFallback(Bitmap bitmap, String name) {
        try {
            File base = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
            if (base == null) base = getFilesDir();
            File dir = new File(base, "QuickScreenshot");
            if (!dir.exists()) dir.mkdirs();
            File file = new File(dir, name);
            try (FileOutputStream out = new FileOutputStream(file)) {
                bitmap.compress(Bitmap.CompressFormat.PNG, 100, out);
            }
            return file.getAbsolutePath();
        } catch (Exception ignored) {
            return null;
        }
    }

    private Notification buildNotification(String text) {
        Intent capture = new Intent(this, CaptureService.class);
        capture.setAction(ACTION_CAPTURE);
        int piFlags = PendingIntent.FLAG_UPDATE_CURRENT;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) piFlags |= PendingIntent.FLAG_IMMUTABLE;
        PendingIntent capturePi = PendingIntent.getService(this, 7, capture, piFlags);

        Intent open = new Intent(this, MainActivity.class);
        int openFlags = PendingIntent.FLAG_UPDATE_CURRENT;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) openFlags |= PendingIntent.FLAG_IMMUTABLE;
        PendingIntent openPi = PendingIntent.getActivity(this, 8, open, openFlags);

        Notification.Builder builder = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(this, CHANNEL_ID)
                : new Notification.Builder(this);

        return builder
                .setSmallIcon(android.R.drawable.ic_menu_camera)
                .setContentTitle("لقطة سريعة")
                .setContentText(text)
                .setContentIntent(openPi)
                .setOngoing(true)
                .setOnlyAlertOnce(true)
                .setCategory(Notification.CATEGORY_SERVICE)
                .addAction(new Notification.Action.Builder(
                        android.R.drawable.ic_menu_camera,
                        "التقاط",
                        capturePi
                ).build())
                .build();
    }

    private void restoreNotification() {
        try {
            startForeground(NOTIFICATION_ID, buildNotification("جاهز لالتقاط الشاشة"));
        } catch (Exception ignored) { }
    }

    private void createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "التقاط الشاشة",
                    NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("زر سريع لالتقاط الشاشة");
            channel.setShowBadge(false);
            notificationManager.createNotificationChannel(channel);
        }
    }

    private void cleanupCaptureObjects() {
        try {
            if (virtualDisplay != null) virtualDisplay.release();
        } catch (Exception ignored) { }
        virtualDisplay = null;
        try {
            if (imageReader != null) imageReader.close();
        } catch (Exception ignored) { }
        imageReader = null;
    }

    private void toast(String message) {
        handler.post(() -> Toast.makeText(getApplicationContext(), message, Toast.LENGTH_SHORT).show());
    }

    @Override
    public void onDestroy() {
        cleanupCaptureObjects();
        try {
            if (mediaProjection != null) mediaProjection.stop();
        } catch (Exception ignored) { }
        mediaProjection = null;
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private static final class ActivityResultFallback {
        static final int RESULT_OK = -1;
        static final int RESULT_CANCELED = 0;
    }
}
