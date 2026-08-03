from pathlib import Path
import re

root = Path('halaqa_apk_project')
html_path = root / 'app/src/main/assets/index.html'
build_path = root / 'app/build.gradle'
java_path = root / 'app/src/main/java/com/halaqa/followup/MainActivity.java'

html = html_path.read_text(encoding='utf-8')
html = html.replace("const FINAL_VERSION='3.1.5'", "const FINAL_VERSION='3.1.6'")
html = html.replace("const FX_VERSION='3.1.5'", "const FX_VERSION='3.1.6'")
html = html.replace('تم تثبيت الإصدار ٣.١.٥ — الوضع الليلي المتكامل', 'تم تثبيت الإصدار ٣.١.٦ — إصلاح PDF داخل التطبيق')

old_save = """    if(window.AndroidApp&&typeof AndroidApp.saveHtmlAsPdf==='function'){
      closeModal('freshPreviewModal');toast('اختر مكان حفظ ملف PDF');
      AndroidApp.saveHtmlAsPdf(fileName(snapshot),snapshot.document,snapshot.state?.scope==='all');return;
    }
    const button=$('#freshPreviewModal .primary-btn'),old=button?.textContent;
    try{
      if(button){button.disabled=true;button.textContent='جارٍ إنشاء ملف PDF…'}
      const blob=await buildBlob(snapshot),url=URL.createObjectURL(blob),a=document.createElement('a');
      a.href=url;a.download=fileName(snapshot);a.style.display='none';document.body.appendChild(a);a.click();a.remove();
      setTimeout(()=>URL.revokeObjectURL(url),20000);
      toast('تم إنشاء ملف PDF المطابق للمعاينة');
    }catch(error){console.error(error);toast(error?.message||'تعذر إنشاء ملف PDF')}
    finally{if(button){button.disabled=false;button.textContent=old||'إنشاء ملف PDF مباشر'}}
"""
new_save = """    const button=$('#freshPreviewModal .primary-btn'),old=button?.textContent;
    try{
      if(button){button.disabled=true;button.textContent='جارٍ إنشاء ملف PDF…'}
      const blob=await buildBlob(snapshot);
      if(window.AndroidApp&&typeof AndroidApp.saveBase64File==='function'){
        const base64=await new Promise((resolve,reject)=>{
          const reader=new FileReader();
          reader.onerror=()=>reject(reader.error||new Error('تعذر تجهيز ملف PDF'));
          reader.onload=()=>resolve(String(reader.result||'').split(',')[1]||'');
          reader.readAsDataURL(blob);
        });
        if(!base64)throw new Error('تعذر تجهيز بيانات ملف PDF');
        closeModal('freshPreviewModal');toast('اختر مكان حفظ ملف PDF');
        AndroidApp.saveBase64File(fileName(snapshot),base64,'application/pdf');
        return;
      }
      const url=URL.createObjectURL(blob),a=document.createElement('a');
      a.href=url;a.download=fileName(snapshot);a.style.display='none';document.body.appendChild(a);a.click();a.remove();
      setTimeout(()=>URL.revokeObjectURL(url),20000);
      toast('تم إنشاء ملف PDF المطابق للمعاينة');
    }catch(error){console.error(error);toast(error?.message||'تعذر إنشاء ملف PDF')}
    finally{if(button){button.disabled=false;button.textContent=old||'إنشاء ملف PDF مباشر'}}
"""
if old_save not in html:
    raise SystemExit('Direct PDF save block not found')
html = html.replace(old_save, new_save, 1)
html_path.write_text(html, encoding='utf-8')

build = build_path.read_text(encoding='utf-8')
build = re.sub(r'versionCode\s+\d+', 'versionCode 19', build)
build = re.sub(r"versionName\s+'[^']+'", "versionName '3.1.6'", build)
build_path.write_text(build, encoding='utf-8')

java = java_path.read_text(encoding='utf-8')
if 'import android.util.Base64;' not in java:
    java = java.replace('import android.provider.Settings;', 'import android.provider.Settings;\nimport android.util.Base64;')

anchor = '''        @JavascriptInterface
        public void printPage(String jobName) {'''
method = '''        @JavascriptInterface
        public void saveBase64File(String fileName, String base64Content, String mimeType) {
            try {
                pendingSaveName = sanitizeFileName(fileName);
                pendingSaveMime = (mimeType == null || mimeType.isEmpty())
                        ? "application/octet-stream" : mimeType;
                pendingSaveBytes = Base64.decode(
                        base64Content == null ? "" : base64Content,
                        Base64.DEFAULT
                );
            } catch (Exception ex) {
                pendingSaveBytes = null;
                runOnUiThread(() -> Toast.makeText(
                        MainActivity.this,
                        "تعذر تجهيز الملف للحفظ",
                        Toast.LENGTH_LONG
                ).show());
                return;
            }
            runOnUiThread(() -> {
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType(pendingSaveMime);
                intent.putExtra(Intent.EXTRA_TITLE, pendingSaveName);
                try {
                    startActivityForResult(intent, REQUEST_SAVE_FILE);
                } catch (Exception ex) {
                    pendingSaveBytes = null;
                    Toast.makeText(
                            MainActivity.this,
                            "تعذر فتح نافذة الحفظ",
                            Toast.LENGTH_LONG
                    ).show();
                }
            });
        }

'''
if 'public void saveBase64File(' not in java:
    if anchor not in java:
        raise SystemExit('Java bridge insertion anchor missing')
    java = java.replace(anchor, method + anchor, 1)

java = java.replace('            return "3.1.3";', '            return "3.1.6";')
old_toast = '                    Toast.makeText(this, "تم حفظ النسخة الاحتياطية", Toast.LENGTH_SHORT).show();'
new_toast = '''                    String savedMessage = "application/pdf".equals(pendingSaveMime)
                            ? "تم حفظ ملف PDF كاملًا"
                            : "تم حفظ الملف";
                    Toast.makeText(this, savedMessage, Toast.LENGTH_SHORT).show();'''
if old_toast not in java:
    raise SystemExit('Save result message anchor missing')
java = java.replace(old_toast, new_toast, 1)

old_clear = '''            pendingSaveBytes = null;
        }
    }

    @Override
    public void onBackPressed()'''
new_clear = '''            pendingSaveBytes = null;
            pendingSaveMime = null;
            pendingSaveName = null;
        }
    }

    @Override
    public void onBackPressed()'''
if old_clear not in java:
    raise SystemExit('Save state cleanup anchor missing')
java = java.replace(old_clear, new_clear, 1)
java_path.write_text(java, encoding='utf-8')

assert "FINAL_VERSION='3.1.6'" in html
assert "FX_VERSION='3.1.6'" in html
assert 'AndroidApp.saveBase64File' in html
assert html.rfind('AndroidApp.saveBase64File') > html.rfind('AndroidApp.saveHtmlAsPdf')
assert 'versionCode 19' in build
assert "versionName '3.1.6'" in build
assert 'public void saveBase64File' in java
assert 'Base64.decode' in java
assert 'return "3.1.6";' in java
print('Applied Halaqa 3.1.6 website-identical PDF bridge')
