from pathlib import Path
import re

html_path=Path('halaqa_apk_project/app/src/main/assets/index.html')
build_path=Path('halaqa_apk_project/app/build.gradle')
s=html_path.read_text(encoding='utf-8')

s=s.replace("const FINAL_VERSION='3.1.1'", "const FINAL_VERSION='3.1.2'")
s=s.replace('تم تثبيت الإصدار ٣.١.١ — إصلاح العطلة والمجموع','تم تثبيت الإصدار ٣.١.٢ — إصلاح درجات المراجعة والعطلة')

old="const hasContent=kind==='review'?(ensureReviewItems(r).some(x=>x.startSurah||x.endSurah)):Boolean(r.surah);"
new="const hasContent=kind==='review'?((Array.isArray(r.reviewItems)&&r.reviewItems.some(x=>x&&(x.startSurah||x.endSurah||x.from||x.to)))||Boolean(r.surah)):Boolean(r.surah);"
if old not in s:
    raise SystemExit('Broken review grade expression not found')
s=s.replace(old,new)

s=s.replace('window.getRecitation = function (studentId, kind, date) {','window.getRecitation = getRecitation = function (studentId, kind, date) {')
s=s.replace('window.recitationHasData = function (record) {','window.recitationHasData = recitationHasData = function (record) {')
s=s.replace('window.weekStats = function (studentId, start, kind = null) {','window.weekStats = weekStats = function (studentId, start, kind = null) {')
s=s.replace('window.updateWeekTotal = function (weekBlock) {','window.updateWeekTotal = updateWeekTotal = function (weekBlock) {')

css='''
<style id="review-grade-color-fix-v312">
.review-grade-row .grade-select.grade-excellent{background:#e5f7ed!important;color:#08734f!important;border-color:#61b58e!important;font-weight:900}
.review-grade-row .grade-select.grade-verygood{background:#e7f2ff!important;color:#15569a!important;border-color:#78aee1!important;font-weight:900}
.review-grade-row .grade-select.grade-good{background:#fff5d9!important;color:#8b5b00!important;border-color:#d6b65d!important;font-weight:900}
.review-grade-row .grade-select.grade-weak{background:#ffe9e7!important;color:#a12b22!important;border-color:#d9837c!important;font-weight:900}
.review-grade-row .grade-select.grade-notmemorized{background:#f2e9ff!important;color:#663399!important;border-color:#aa88c8!important;font-weight:900}
</style>
'''
if 'review-grade-color-fix-v312' not in s:
    before,sep,after=s.rpartition('</body>')
    if not sep:
        raise SystemExit('Closing body tag not found')
    s=before+css+sep+after

html_path.write_text(s,encoding='utf-8')

b=build_path.read_text(encoding='utf-8')
b=re.sub(r'versionCode\s+\d+','versionCode 15',b)
b=re.sub(r"versionName\s+'[^']+'","versionName '3.1.2'",b)
build_path.write_text(b,encoding='utf-8')

assert "FINAL_VERSION='3.1.2'" in s
assert 'ensureReviewItems(r).some' not in s
assert s.count('review-grade-color-fix-v312')==1
assert 'versionCode 15' in b
assert "versionName '3.1.2'" in b
print('Applied Halaqa 3.1.2 review grade fix')
