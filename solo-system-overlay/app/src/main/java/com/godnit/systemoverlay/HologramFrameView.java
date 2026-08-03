package com.godnit.systemoverlay;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.SystemClock;
import android.view.View;

public class HologramFrameView extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private boolean penalty;

    public HologramFrameView(Context context) {
        super(context);
        setLayerType(View.LAYER_TYPE_SOFTWARE, null);
    }

    public void setPenalty(boolean penalty) {
        this.penalty = penalty;
        invalidate();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        int width = getWidth();
        int height = getHeight();
        if (width <= 0 || height <= 0) return;

        int main = penalty ? Color.rgb(255, 72, 105) : Color.rgb(61, 205, 255);
        int bright = penalty ? Color.rgb(255, 171, 184) : Color.rgb(190, 247, 255);
        float density = getResources().getDisplayMetrics().density;
        float inset = 4f * density;
        float corner = 26f * density;

        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(1f * density);
        paint.setColor(main);
        paint.setAlpha(170);
        paint.setShadowLayer(10f * density, 0f, 0f, main);
        canvas.drawRect(inset, inset, width - inset, height - inset, paint);

        paint.setStrokeWidth(2f * density);
        paint.setColor(bright);
        paint.setAlpha(230);
        drawCorner(canvas, inset, inset, corner, true, true);
        drawCorner(canvas, width - inset, inset, corner, false, true);
        drawCorner(canvas, inset, height - inset, corner, true, false);
        drawCorner(canvas, width - inset, height - inset, corner, false, false);

        paint.clearShadowLayer();
        paint.setStrokeWidth(1f);
        paint.setColor(main);
        paint.setAlpha(25);
        float scanStep = 6f * density;
        for (float y = inset + scanStep; y < height - inset; y += scanStep) {
            canvas.drawLine(inset, y, width - inset, y, paint);
        }

        long now = SystemClock.uptimeMillis();
        float usableHeight = Math.max(1f, height - (inset * 2f));
        float scanY = inset + ((now % 1700L) / 1700f) * usableHeight;
        paint.setColor(bright);
        paint.setAlpha(120);
        paint.setStrokeWidth(2.2f * density);
        paint.setShadowLayer(8f * density, 0f, 0f, main);
        canvas.drawLine(inset + 2f, scanY, width - inset - 2f, scanY, paint);

        paint.clearShadowLayer();
        paint.setStyle(Paint.Style.FILL);
        for (int i = 0; i < 14; i++) {
            float seedX = ((i * 83 + 17) % 100) / 100f;
            float speed = 0.00005f + (i % 5) * 0.000014f;
            float seedY = (i * 0.137f + now * speed) % 1f;
            float x = inset + seedX * (width - inset * 2f);
            float y = inset + seedY * (height - inset * 2f);
            paint.setColor(i % 3 == 0 ? bright : main);
            paint.setAlpha(60 + (i % 4) * 28);
            canvas.drawCircle(x, y, (0.7f + (i % 3) * 0.45f) * density, paint);
        }

        postInvalidateDelayed(16L);
    }

    private void drawCorner(Canvas canvas, float x, float y, float length,
                            boolean toRight, boolean down) {
        float horizontalEnd = x + (toRight ? length : -length);
        float verticalEnd = y + (down ? length : -length);
        canvas.drawLine(x, y, horizontalEnd, y, paint);
        canvas.drawLine(x, y, x, verticalEnd, paint);
    }
}
