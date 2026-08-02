from pathlib import Path
import re

root = Path('halaqa_apk_project')
html_path = root / 'app/src/main/assets/index.html'
build_path = root / 'app/build.gradle'
hotfix_path = Path('halaqa-final-311/hotfix311.html')

html = html_path.read_text(encoding='utf-8')
hotfix = hotfix_path.read_text(encoding='utf-8')

html = html.replace("const FINAL_VERSION='3.1.0'", "const FINAL_VERSION='3.1.1'")
html = html.replace('تم تثبيت الإصدار ٣.١.٠ — نظام تصدير جديد', 'تم تثبيت الإصدار ٣.١.١ — إصلاح العطلة والمجموع')
if 'holiday-grade-hotfix-v311' not in html:
    pos = html.rfind('</body>')
    if pos < 0:
        raise SystemExit('Missing closing body tag')
    html = html[:pos] + hotfix + '\n' + html[pos:]
html_path.write_text(html, encoding='utf-8')

build = build_path.read_text(encoding='utf-8')
build = re.sub(r'versionCode\s+\d+', 'versionCode 14', build)
build = re.sub(r"versionName\s+'[^']+'", "versionName '3.1.1'", build)
build_path.write_text(build, encoding='utf-8')

assert html.count('holiday-grade-hotfix-v311') == 1
assert "const FINAL_VERSION='3.1.1'" in html
assert 'versionCode 14' in build
assert "versionName '3.1.1'" in build
print('Applied Halaqa 3.1.1 holiday and totals fix')
