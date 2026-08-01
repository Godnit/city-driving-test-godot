from pathlib import Path

root = Path('halaqa_apk_project')
html_path = root / 'app/src/main/assets/index.html'
java_path = root / 'app/src/main/java/com/halaqa/followup/MainActivity.java'
gradle_path = root / 'app/build.gradle'

s = html_path.read_text(encoding='utf-8')
s = s.replace("const FINAL_VERSION='3.0.1'", "const FINAL_VERSION='3.0.2'")
s = s.replace(
    "return `<article class=\"final-report ${s.content==='guardian'?'guardian-report':''}\"><section class=\"report-page\">${body}</section></article>`}",
    "return `<article class=\"final-report ${s.content==='guardian'?'guardian-report':''}\" data-report-period=\"weekly\" data-report-week=\"${s.week}\"><section class=\"report-page\">${body}</section></article>`}"
)
s = s.replace(
    "return `<article class=\"final-report ${s.content==='guardian'?'guardian-report':''}\"><section class=\"report-page\">${first}</section></article>`}",
    "return `<article class=\"final-report ${s.content==='guardian'?'guardian-report':''}\" data-report-period=\"monthly\"><section class=\"report-page\">${first}</section></article>`}"
)
s = s.replace(
    "return `<article class=\"final-report\">${pages.join('')}</article>`}",
    "return `<article class=\"final-report\" data-report-period=\"monthly\">${pages.join('')}</article>`}"
)
s = s.replace(
    "return `<article class=\"final-report all-students\"><section class=\"report-page landscape\">",
    "return `<article class=\"final-report all-students\" data-report-period=\"${weekly?'weekly':'monthly'}\" data-report-week=\"${weekly?s.week:''}\"><section class=\"report-page landscape\">"
)
old = """  window.printPreparedReport=function(){
    if(!preparedReport.html)return toast('أنشئ معاينة التقرير أولًا');
    const docHtml=standalonePrintDocument();
    closeModal('reportPreviewModal');
    document.title=preparedReport.title;
"""
new = """  window.printPreparedReport=function(){
    if(!preparedReport.html)return toast('أنشئ معاينة التقرير أولًا');
    const fixedState=normalizePdfExportState({...preparedReport.state});
    const freshHtml=buildReport(fixedState);
    if(!freshHtml)return toast('تعذر تجهيز التقرير المحدد');
    preparedReport={html:freshHtml,state:fixedState,title:reportTitle(fixedState)};
    const docHtml=standalonePrintDocument();
    closeModal('reportPreviewModal');
    document.title=preparedReport.title;
"""
if old not in s:
    raise RuntimeError('printPreparedReport block not found')
s = s.replace(old, new)
old_init = """  function initFinal(){injectHeaderThemeButton();injectSettings();injectExportUI();injectBackupPreview();ensureFinalSettings();applyTheme();syncSettingsForm();persist();setTimeout(ensureTeacherSetup,160)}
"""
new_init = """  function showVersionNotice(){try{const k='halaqa_version_notice_'+FINAL_VERSION;if(!localStorage.getItem(k)){localStorage.setItem(k,'1');setTimeout(()=>toast('تم تثبيت الإصدار ٣.٠.٢ — إصلاح التصدير الأسبوعي'),650)}}catch(_){}}
  function initFinal(){injectHeaderThemeButton();injectSettings();injectExportUI();injectBackupPreview();ensureFinalSettings();applyTheme();syncSettingsForm();persist();showVersionNotice();setTimeout(ensureTeacherSetup,160)}
"""
if old_init not in s:
    raise RuntimeError('initFinal block not found')
s = s.replace(old_init, new_init)
for required in ["FINAL_VERSION='3.0.2'", "freshHtml=buildReport(fixedState)", 'data-report-period="weekly"', 'showVersionNotice']:
    if required not in s:
        raise RuntimeError('Missing HTML marker: ' + required)
html_path.write_text(s, encoding='utf-8')

j = java_path.read_text(encoding='utf-8')
if 'private boolean printingMainHtmlDocument' not in j:
    j = j.replace(
        '    private boolean printHtmlIssued = false;\n',
        '    private boolean printHtmlIssued = false;\n    private boolean printingMainHtmlDocument = false;\n'
    )
start = j.index('        @JavascriptInterface\n        public void printHtml(')
end = j.index('        @JavascriptInterface\n        public String appVersion()', start)
new_block = '''        @JavascriptInterface
        public void printHtml(String jobName, String html, boolean landscape) {
            runOnUiThread(() -> {
                try {
                    destroyPrintWebView();
                    printHtmlIssued = false;
                    printingMainHtmlDocument = true;
                    cleanPrintOnResume = false;
                    printActivityStarted = false;

                    final String name = (jobName == null || jobName.trim().isEmpty())
                            ? "تقرير دفتر المتابعة" : jobName;
                    final String document = (html == null || html.trim().isEmpty())
                            ? "<html dir='rtl'><body>لا توجد بيانات للتقرير</body></html>" : html;

                    webView.setWebViewClient(new WebViewClient() {
                        @Override
                        public void onPageFinished(WebView view, String url) {
                            if (!printingMainHtmlDocument || printHtmlIssued) return;
                            printHtmlIssued = true;
                            view.postDelayed(() -> startHtmlPrint(view, name, landscape), 380);
                        }
                    });
                    webView.loadDataWithBaseURL(
                            "https://halaqa.local/weekly-print-v302/",
                            document,
                            "text/html",
                            "UTF-8",
                            null
                    );
                } catch (Exception ex) {
                    restoreAppAfterHtmlPrint();
                    Toast.makeText(MainActivity.this, "تعذر تجهيز تقرير PDF", Toast.LENGTH_LONG).show();
                }
            });
        }

        private void startHtmlPrint(WebView source, String name, boolean landscape) {
            try {
                PrintManager printManager = (PrintManager) getSystemService(Context.PRINT_SERVICE);
                PrintDocumentAdapter adapter = source.createPrintDocumentAdapter(name);
                PrintAttributes.MediaSize media = landscape
                        ? PrintAttributes.MediaSize.ISO_A4.asLandscape()
                        : PrintAttributes.MediaSize.ISO_A4.asPortrait();
                PrintAttributes attributes = new PrintAttributes.Builder()
                        .setMediaSize(media)
                        .setColorMode(PrintAttributes.COLOR_MODE_COLOR)
                        .setMinMargins(PrintAttributes.Margins.NO_MARGINS)
                        .build();
                cleanPrintOnResume = true;
                printActivityStarted = false;
                printManager.print(name, adapter, attributes);
            } catch (Exception ex) {
                cleanPrintOnResume = false;
                restoreAppAfterHtmlPrint();
                Toast.makeText(MainActivity.this, "تعذر فتح شاشة حفظ PDF", Toast.LENGTH_LONG).show();
            }
        }

'''
j = j[:start] + new_block + j[end:]
j = j.replace('            return "3.0.1";', '            return "3.0.2";')
helper = '''    private void restoreAppAfterHtmlPrint() {
        printingMainHtmlDocument = false;
        printHtmlIssued = false;
        cleanPrintOnResume = false;
        printActivityStarted = false;
        if (webView != null) {
            webView.setWebViewClient(new WebViewClient());
            webView.loadUrl("file:///android_asset/index.html");
        }
    }

'''
if 'private void restoreAppAfterHtmlPrint()' not in j:
    j = j.replace('    private void destroyPrintWebView() {', helper + '    private void destroyPrintWebView() {')
old_resume = '''        if (cleanPrintOnResume && printActivityStarted && webView != null) {
            cleanPrintOnResume = false;
            printActivityStarted = false;
            webView.postDelayed(() -> {
                webView.evaluateJavascript("window.finishNativePrint && window.finishNativePrint()", null);
                destroyPrintWebView();
            }, 250);
        }
'''
new_resume = '''        if (cleanPrintOnResume && printActivityStarted && webView != null) {
            cleanPrintOnResume = false;
            printActivityStarted = false;
            webView.postDelayed(() -> {
                if (printingMainHtmlDocument) {
                    restoreAppAfterHtmlPrint();
                } else {
                    webView.evaluateJavascript("window.finishNativePrint && window.finishNativePrint()", null);
                    destroyPrintWebView();
                }
            }, 250);
        }
'''
if old_resume not in j:
    raise RuntimeError('onResume block not found')
j = j.replace(old_resume, new_resume)
j = j.replace(
    '    protected void onDestroy() {\n        destroyPrintWebView();',
    '    protected void onDestroy() {\n        printingMainHtmlDocument = false;\n        destroyPrintWebView();'
)
for required in ['printingMainHtmlDocument = true', 'weekly-print-v302', 'return "3.0.2"', 'restoreAppAfterHtmlPrint()']:
    if required not in j:
        raise RuntimeError('Missing Java marker: ' + required)
java_path.write_text(j, encoding='utf-8')

g = gradle_path.read_text(encoding='utf-8')
g = g.replace('versionCode 11', 'versionCode 12').replace("versionName '3.0.1'", "versionName '3.0.2'")
if 'versionCode 12' not in g or "versionName '3.0.2'" not in g:
    raise RuntimeError('Gradle version update failed')
gradle_path.write_text(g, encoding='utf-8')

print('Patched Halaqa 3.0.2 successfully')
