from pathlib import Path
import re

html_path=Path('halaqa_apk_project/app/src/main/assets/index.html')
main_path=Path('halaqa_apk_project/app/src/main/java/com/halaqa/followup/MainActivity.java')
build_path=Path('halaqa_apk_project/app/build.gradle')
s=html_path.read_text(encoding='utf-8')

old='''  function browserPrint(snapshot){
    try{sessionStorage.setItem('halaqa_return_after_fx_print','1')}catch(_){}
    document.open();document.write(snapshot.document);document.close();
    setTimeout(()=>{try{window.focus();window.print()}catch(_){location.reload()}},450);
    setTimeout(()=>{window.onafterprint=()=>location.reload()},50);
  }'''
new='''  function browserPrint(snapshot){
    if(!snapshot||!snapshot.document)return toast('لا توجد معاينة جاهزة للطباعة');
    const printName=`halaqa_report_${snapshot.id||Date.now()}`;
    let popup=null;
    try{popup=window.open('about:blank',printName)}catch(_){}
    if(popup){
      try{
        popup.document.open();popup.document.write(snapshot.document);popup.document.close();
        const trigger=()=>{try{popup.onafterprint=()=>{try{popup.close()}catch(_){}};popup.focus();popup.print()}catch(_){try{popup.close()}catch(__){}isolatedFramePrint(snapshot)}};
        setTimeout(trigger,650);return;
      }catch(_){try{popup.close()}catch(__){}}
    }
    isolatedFramePrint(snapshot);
  }
  function isolatedFramePrint(snapshot){
    const old=document.getElementById('halaqa-isolated-print-frame');if(old)old.remove();
    const frame=document.createElement('iframe');frame.id='halaqa-isolated-print-frame';frame.setAttribute('aria-hidden','true');frame.style.cssText='position:fixed;left:-10000px;top:0;width:794px;height:1123px;border:0;background:#fff;opacity:.01;pointer-events:none';document.body.appendChild(frame);
    const cleanup=()=>setTimeout(()=>{try{frame.remove()}catch(_){}},800);
    frame.onload=()=>setTimeout(()=>{try{frame.contentWindow.onafterprint=cleanup;frame.contentWindow.focus();frame.contentWindow.print();setTimeout(cleanup,3000)}catch(_){cleanup();toast('تعذر فتح شاشة حفظ PDF')}},450);
    const doc=frame.contentDocument;doc.open();doc.write(snapshot.document);doc.close();
  }'''
if old not in s: raise SystemExit('old same-window browserPrint not found')
s=s.replace(old,new,1)
s=s.replace("const FX_VERSION='3.1.0'","const FX_VERSION='3.1.3'")
s=s.replace("const FINAL_VERSION='3.1.2'","const FINAL_VERSION='3.1.3'")
s=s.replace('تم تثبيت الإصدار ٣.١.٢ — إصلاح درجات المراجعة والعطلة','تم تثبيت الإصدار ٣.١.٣ — إصلاح التصدير الأسبوعي المعزول')
s=s.replace('هذا نظام تصدير جديد مستقل. الاختيارات لا تُقرأ من أي تقرير سابق، وملف PDF يُنشأ من المعاينة نفسها دون إعادة بناء.','نظام التصدير المعزول ٣.١.٣: تُفتح صفحة طباعة مستقلة لا تحتوي كود التقرير الشهري القديم، وتُطبع المعاينة نفسها حرفيًا.')
old_doc="return `<!doctype html><html lang=\"ar\" dir=\"rtl\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>${safe(title(state))}</title><style>${pageCss}</style><style>html,body{margin:0!important;padding:0!important;background:#fff!important}.fx-preview-paper{width:auto!important;box-shadow:none!important}@page{size:A4 ${landscape?'landscape':'portrait'};margin:0}</style></head><body>${report}</body></html>`;"
new_doc="return `<!doctype html><html lang=\"ar\" dir=\"rtl\" data-export-period=\"${state.period}\" data-export-week=\"${state.week}\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><meta name=\"halaqa-export-period\" content=\"${state.period}\"><title>${safe(title(state))}</title><style>${pageCss}</style><style>html,body{margin:0!important;padding:0!important;background:#fff!important}.fx-preview-paper{width:auto!important;box-shadow:none!important}@page{size:A4 ${landscape?'landscape':'portrait'};margin:0}</style></head><body>${report}</body></html>`;"
if old_doc not in s: raise SystemExit('standalone document template not found')
s=s.replace(old_doc,new_doc,1)
html_path.write_text(s,encoding='utf-8')

j=main_path.read_text(encoding='utf-8').replace('return "3.1.0";','return "3.1.3";').replace('direct-pdf-v310','direct-pdf-v313')
main_path.write_text(j,encoding='utf-8')

b=build_path.read_text(encoding='utf-8')
b=re.sub(r'versionCode\s+\d+','versionCode 16',b)
b=re.sub(r"versionName\s+'[^']+'","versionName '3.1.3'",b)
build_path.write_text(b,encoding='utf-8')

assert "FINAL_VERSION='3.1.3'" in s
assert 'function isolatedFramePrint' in s
assert "window.open('about:blank',printName)" in s
assert 'data-export-period' in s
assert 'document.open();document.write(snapshot.document);document.close();' not in s
assert 'versionCode 16' in b and "versionName '3.1.3'" in b
print('Applied Halaqa 3.1.3 isolated weekly export fix')
