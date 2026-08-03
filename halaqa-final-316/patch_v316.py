from pathlib import Path
import re

root = Path('halaqa_apk_project')
html_path = root / 'app/src/main/assets/index.html'
build_path = root / 'app/build.gradle'
java_path = root / 'app/src/main/java/com/halaqa/followup/MainActivity.java'

html = html_path.read_text(encoding='utf-8')
html = html.replace("const FINAL_VERSION='3.1.5'", "const FINAL_VERSION='3.1.6'")
html = html.replace("const FX_VERSION='3.1.5'", "const FX_VERSION='3.1.6'")
html = html.replace('تم تثبيت الإصدار ٣.١.٥ — الوضع الليلي المتكامل', 'تم تثبيت الإصدار ٣.١.٦ — إصلاح صفحات PDF داخل التطبيق')
html_path.write_text(html, encoding='utf-8')

build = build_path.read_text(encoding='utf-8')
build = re.sub(r'versionCode\s+\d+', 'versionCode 19', build)
build = re.sub(r"versionName\s+'[^']+'", "versionName '3.1.6'", build)
build_path.write_text(build, encoding='utf-8')

java = java_path.read_text(encoding='utf-8')
java = java.replace('import android.graphics.pdf.PdfDocument;\n', '')
java = java.replace('import java.io.FileOutputStream;\n', '')
java = java.replace('    private ParcelFileDescriptor pendingPdfDescriptor;\n', '''    private ParcelFileDescriptor pendingPdfDescriptor;
    private PrintDocumentAdapter pendingPdfAdapter;
    private CancellationSignal pendingPdfCancellation;
    private boolean pendingPdfFinished = false;
''')
java = java.replace('            return "3.1.3";', '            return "3.1.6";')
java = java.replace('            pendingPdfDescriptor = getContentResolver().openFileDescriptor(uri, "w");', '''            pendingPdfFinished = false;
            pendingPdfDescriptor = getContentResolver().openFileDescriptor(uri, "w");''')
java = java.replace('            ps.setDefaultTextEncodingName("UTF-8");', '''            ps.setDefaultTextEncodingName("UTF-8");
            ps.setUseWideViewPort(true);
            ps.setLoadWithOverviewMode(true);
            ps.setTextZoom(100);''')
java = java.replace('                    view.postDelayed(() -> writeAttachedWebViewPdf(view), 550);', '''                    view.evaluateJavascript(
                            "(document.fonts&&document.fonts.ready?document.fonts.ready:Promise.resolve()).then(()=>true)",
                            value -> view.postDelayed(() -> writeAttachedWebViewPdf(view), 260)
                    );''')

start = java.index('    private void writeAttachedWebViewPdf(WebView source) {')
end = java.index('    private void finishDirectPdf(', start)
method = r'''    // Android PDF engine v3.1.6: use WebView's print adapter directly.
    // Chromium now paginates the exact HTML/CSS at A4 size instead of drawing
    // one long phone-width bitmap and cutting it into arbitrary slices.
    private void writeAttachedWebViewPdf(WebView source) {
        try {
            if (pendingPdfDescriptor == null) {
                finishDirectPdf(false, "تعذر الوصول إلى ملف PDF");
                return;
            }

            PrintAttributes.MediaSize mediaSize = pendingPdfLandscape
                    ? PrintAttributes.MediaSize.ISO_A4.asLandscape()
                    : PrintAttributes.MediaSize.ISO_A4.asPortrait();

            PrintAttributes attributes = new PrintAttributes.Builder()
                    .setMediaSize(mediaSize)
                    .setResolution(new PrintAttributes.Resolution(
                            "halaqa_pdf_600", "Halaqa PDF 600dpi", 600, 600))
                    .setMinMargins(PrintAttributes.Margins.NO_MARGINS)
                    .setColorMode(PrintAttributes.COLOR_MODE_COLOR)
                    .build();

            pendingPdfCancellation = new CancellationSignal();
            pendingPdfAdapter = source.createPrintDocumentAdapter(pendingPdfName);
            Bundle extras = new Bundle();

            pendingPdfAdapter.onLayout(
                    attributes,
                    attributes,
                    pendingPdfCancellation,
                    new PrintDocumentAdapter.LayoutResultCallback() {
                        @Override
                        public void onLayoutFinished(PrintDocumentInfo info, boolean changed) {
                            if (info == null || pendingPdfAdapter == null || pendingPdfDescriptor == null) {
                                runOnUiThread(() -> finishDirectPdf(false, "تعذر تخطيط صفحات PDF"));
                                return;
                            }
                            runOnUiThread(() -> {
                                try {
                                    pendingPdfAdapter.onWrite(
                                            new PageRange[]{PageRange.ALL_PAGES},
                                            pendingPdfDescriptor,
                                            pendingPdfCancellation,
                                            new PrintDocumentAdapter.WriteResultCallback() {
                                                @Override
                                                public void onWriteFinished(PageRange[] pages) {
                                                    runOnUiThread(() -> finishDirectPdf(true, "تم حفظ تقرير PDF كاملًا"));
                                                }

                                                @Override
                                                public void onWriteFailed(CharSequence error) {
                                                    runOnUiThread(() -> finishDirectPdf(false, "تعذر كتابة صفحات PDF"));
                                                }

                                                @Override
                                                public void onWriteCancelled() {
                                                    runOnUiThread(() -> finishDirectPdf(false, "تم إلغاء إنشاء PDF"));
                                                }
                                            }
                                    );
                                } catch (Exception ex) {
                                    finishDirectPdf(false, "تعذر إنشاء صفحات PDF");
                                }
                            });
                        }

                        @Override
                        public void onLayoutFailed(CharSequence error) {
                            runOnUiThread(() -> finishDirectPdf(false, "تعذر تخطيط صفحات PDF"));
                        }

                        @Override
                        public void onLayoutCancelled() {
                            runOnUiThread(() -> finishDirectPdf(false, "تم إلغاء إنشاء PDF"));
                        }
                    },
                    extras
            );
        } catch (Exception ex) {
            finishDirectPdf(false, "تعذر إنشاء ملف PDF");
        }
    }

'''
java = java[:start] + method + java[end:]

old_finish = '''    private void finishDirectPdf(boolean success, String message) {
        try {
            if (pendingPdfDescriptor != null) pendingPdfDescriptor.close();
        } catch (Exception ignored) {}
        pendingPdfDescriptor = null;
        pendingPdfHtml = "";
'''
new_finish = '''    private void finishDirectPdf(boolean success, String message) {
        if (pendingPdfFinished) return;
        pendingPdfFinished = true;
        try {
            if (pendingPdfCancellation != null && !success) pendingPdfCancellation.cancel();
        } catch (Exception ignored) {}
        pendingPdfCancellation = null;
        pendingPdfAdapter = null;
        try {
            if (pendingPdfDescriptor != null) pendingPdfDescriptor.close();
        } catch (Exception ignored) {}
        pendingPdfDescriptor = null;
        pendingPdfHtml = "";
'''
if old_finish not in java:
    raise SystemExit('finishDirectPdf block not found')
java = java.replace(old_finish, new_finish, 1)

java = java.replace('        printingMainHtmlDocument = false;\n        destroyPrintWebView();', '''        printingMainHtmlDocument = false;
        try { if (pendingPdfCancellation != null) pendingPdfCancellation.cancel(); } catch (Exception ignored) {}
        pendingPdfCancellation = null;
        pendingPdfAdapter = null;
        try { if (pendingPdfDescriptor != null) pendingPdfDescriptor.close(); } catch (Exception ignored) {}
        pendingPdfDescriptor = null;
        destroyPrintWebView();''')

java_path.write_text(java, encoding='utf-8')

assert "FINAL_VERSION='3.1.6'" in html
assert "FX_VERSION='3.1.6'" in html
assert 'versionCode 19' in build
assert "versionName '3.1.6'" in build
assert 'Android PDF engine v3.1.6' in java
assert 'createPrintDocumentAdapter(pendingPdfName)' in java
assert 'PageRange.ALL_PAGES' in java
assert 'source.draw(page.getCanvas())' not in java
assert 'sliceHeight' not in java
assert 'return "3.1.6";' in java
print('Applied Halaqa 3.1.6 native PDF pagination fix')
