package com.halaqa.followup;

import android.app.Activity;
import android.print.PrintManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.print.PrintAttributes;
import android.print.PrintDocumentAdapter;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {
    private static final int REQUEST_OPEN_FILE = 1001;
    private static final int REQUEST_SAVE_FILE = 1002;

    private WebView webView;
    private ValueCallback<Uri[]> fileChooserCallback;
    private byte[] pendingSaveBytes;
    private String pendingSaveName = "backup.json";
    private String pendingSaveMime = "application/json";
    private boolean cleanPrintOnResume = false;
    private boolean printActivityStarted = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().setStatusBarColor(Color.parseColor("#0D6263"));
        getWindow().setNavigationBarColor(Color.parseColor("#EDF4F2"));
        getWindow().getDecorView().setLayoutDirection(View.LAYOUT_DIRECTION_RTL);

        webView = new WebView(this);
        webView.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        webView.setBackgroundColor(Color.parseColor("#EDF4F2"));
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setDefaultTextEncodingName("UTF-8");
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);

        webView.addJavascriptInterface(new AndroidBridge(), "AndroidApp");
        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileChooserCallback != null) {
                    fileChooserCallback.onReceiveValue(null);
                }
                fileChooserCallback = callback;
                Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/json");
                try {
                    startActivityForResult(intent, REQUEST_OPEN_FILE);
                } catch (Exception ex) {
                    fileChooserCallback = null;
                    Toast.makeText(MainActivity.this, "تعذر فتح مدير الملفات", Toast.LENGTH_LONG).show();
                    return false;
                }
                return true;
            }
        });

        webView.loadUrl("file:///android_asset/index.html");
    }

    private final class AndroidBridge {
        @JavascriptInterface
        public void saveTextFile(String fileName, String content, String mimeType) {
            pendingSaveName = sanitizeFileName(fileName);
            pendingSaveMime = (mimeType == null || mimeType.isEmpty()) ? "text/plain" : mimeType;
            pendingSaveBytes = content == null ? new byte[0] : content.getBytes(StandardCharsets.UTF_8);
            runOnUiThread(() -> {
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType(pendingSaveMime);
                intent.putExtra(Intent.EXTRA_TITLE, pendingSaveName);
                try {
                    startActivityForResult(intent, REQUEST_SAVE_FILE);
                } catch (Exception ex) {
                    Toast.makeText(MainActivity.this, "تعذر فتح نافذة الحفظ", Toast.LENGTH_LONG).show();
                }
            });
        }

        private void startPrint(String jobName, boolean landscape) {
            runOnUiThread(() -> {
                try {
                    PrintManager printManager = (PrintManager) getSystemService(Context.PRINT_SERVICE);
                    String name = (jobName == null || jobName.trim().isEmpty()) ? "تقرير دفتر المتابعة" : jobName;
                    PrintDocumentAdapter adapter = webView.createPrintDocumentAdapter(name);
                    PrintAttributes.MediaSize mediaSize = landscape
                            ? PrintAttributes.MediaSize.ISO_A4.asLandscape()
                            : PrintAttributes.MediaSize.ISO_A4;
                    PrintAttributes attributes = new PrintAttributes.Builder()
                            .setMediaSize(mediaSize)
                            .setColorMode(PrintAttributes.COLOR_MODE_COLOR)
                            .setMinMargins(PrintAttributes.Margins.NO_MARGINS)
                            .build();
                    cleanPrintOnResume = true;
                    printActivityStarted = false;
                    printManager.print(name, adapter, attributes);
                } catch (Exception ex) {
                    cleanPrintOnResume = false;
                    Toast.makeText(MainActivity.this, "تعذر فتح شاشة حفظ PDF", Toast.LENGTH_LONG).show();
                    webView.evaluateJavascript("window.finishNativePrint && window.finishNativePrint()", null);
                }
            });
        }

        @JavascriptInterface
        public void printPage(String jobName) {
            startPrint(jobName, false);
        }

        @JavascriptInterface
        public void printPageLandscape(String jobName) {
            startPrint(jobName, true);
        }

        @JavascriptInterface
        public String appVersion() {
            return "1.1.0";
        }
    }

    private static String sanitizeFileName(String name) {
        if (name == null || name.trim().isEmpty()) return "backup.json";
        return name.replaceAll("[\\\\/:*?\"<>|]", "_");
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (cleanPrintOnResume) printActivityStarted = true;
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (cleanPrintOnResume && printActivityStarted && webView != null) {
            cleanPrintOnResume = false;
            printActivityStarted = false;
            webView.postDelayed(() -> webView.evaluateJavascript(
                    "window.finishNativePrint && window.finishNativePrint()", null), 250);
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_OPEN_FILE) {
            Uri result = (resultCode == RESULT_OK && data != null) ? data.getData() : null;
            if (fileChooserCallback != null) {
                fileChooserCallback.onReceiveValue(result == null ? null : new Uri[]{result});
                fileChooserCallback = null;
            }
            return;
        }
        if (requestCode == REQUEST_SAVE_FILE) {
            if (resultCode == RESULT_OK && data != null && data.getData() != null && pendingSaveBytes != null) {
                try (OutputStream output = getContentResolver().openOutputStream(data.getData())) {
                    if (output == null) throw new IllegalStateException("No output stream");
                    output.write(pendingSaveBytes);
                    output.flush();
                    Toast.makeText(this, "تم حفظ النسخة الاحتياطية", Toast.LENGTH_SHORT).show();
                } catch (Exception ex) {
                    Toast.makeText(this, "تعذر حفظ الملف", Toast.LENGTH_LONG).show();
                }
            }
            pendingSaveBytes = null;
        }
    }

    @Override
    public void onBackPressed() {
        if (webView == null) {
            super.onBackPressed();
            return;
        }
        webView.evaluateJavascript(
                "(window.androidHandleBack ? window.androidHandleBack() : 'none')",
                value -> {
                    if (value == null || value.contains("none")) {
                        if (webView.canGoBack()) webView.goBack();
                        else MainActivity.super.onBackPressed();
                    }
                });
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.removeJavascriptInterface("AndroidApp");
            webView.destroy();
        }
        super.onDestroy();
    }
}
