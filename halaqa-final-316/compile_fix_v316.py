from pathlib import Path
import re

path = Path('halaqa_apk_project/app/src/main/java/com/halaqa/followup/MainActivity.java')
java = path.read_text(encoding='utf-8')

pattern = re.compile(
    r'\n\s*private void writeAttachedWebViewPdf\(WebView source\) \{.*?\n\s*private void finishDirectPdf\(',
    re.S,
)
replacement = '''

    // Legacy native renderer is intentionally disabled in 3.1.6.
    // The active route creates the finished PDF with the same jsPDF engine
    // as the HTML version, then transfers only the completed bytes to Android.
    private void writeAttachedWebViewPdf(WebView source) {
        finishDirectPdf(false, "استخدم نظام PDF المباشر الجديد");
    }

    private void finishDirectPdf('''
java, count = pattern.subn(replacement, java, count=1)
if count != 1:
    raise SystemExit('Legacy PDF renderer block not found')

path.write_text(java, encoding='utf-8')
assert 'new PrintDocumentAdapter.LayoutResultCallback()' not in java
assert 'new PrintDocumentAdapter.WriteResultCallback()' not in java
assert 'Legacy native renderer is intentionally disabled in 3.1.6' in java
print('Removed inaccessible legacy PrintDocumentAdapter callbacks')
