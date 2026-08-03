from pathlib import Path
import re

html_path=Path('halaqa_apk_project/app/src/main/assets/index.html')
build_path=Path('halaqa_apk_project/app/build.gradle')
h2c_path=Path('node_modules/html2canvas/dist/html2canvas.min.js')
jspdf_path=Path('node_modules/jspdf/dist/jspdf.umd.min.js')

html=html_path.read_text(encoding='utf-8')
h2c=h2c_path.read_text(encoding='utf-8').replace('</script','<\\/script')
jspdf=jspdf_path.read_text(encoding='utf-8').replace('</script','<\\/script')

html=html.replace("const FINAL_VERSION='3.1.3'", "const FINAL_VERSION='3.1.4'")
html=html.replace("const FX_VERSION='3.1.3'", "const FX_VERSION='3.1.4'")
html=html.replace('تم تثبيت الإصدار ٣.١.٣ — إصلاح التصدير الأسبوعي المعزول','تم تثبيت الإصدار ٣.١.٤ — إنشاء PDF مباشر دون شاشة الطباعة')
html=html.replace('نظام التصدير المعزول ٣.١.٣: تُفتح صفحة طباعة مستقلة لا تحتوي كود التقرير الشهري القديم، وتُطبع المعاينة نفسها حرفيًا.','نظام PDF المباشر ٣.١.٤: يُنشأ الملف من المعاينة نفسها دون فتح شاشة الطباعة، لذلك لا يمكن أن يتحول التقرير الأسبوعي إلى شهري.')
html=html.replace('>حفظ ملف PDF</button>','>إنشاء ملف PDF مباشر</button>')

patch=r'''
<script id="html2canvas-embedded-v141">__H2C__</script>
<script id="jspdf-embedded-v421">__JSPDF__</script>
<script id="direct-pdf-export-v314">
(() => {
  'use strict';
  const VERSION='3.1.4';
  const $=(s,r=document)=>r.querySelector(s);
  const metrics=landscape=>landscape
    ? {cssW:1123,cssH:794,pdfW:841.89,pdfH:595.28,orientation:'landscape'}
    : {cssW:794,cssH:1123,pdfW:595.28,pdfH:841.89,orientation:'portrait'};
  const safeName=v=>String(v||'تقرير_دفتر_المتابعة').replace(/[\\/:*?"<>|]+/g,'_').replace(/\s+/g,'_');
  const waitFrame=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  function fileName(snapshot){return safeName(snapshot?.title)+'.pdf'}
  function ensureLibraries(){
    if(typeof window.html2canvas!=='function')throw new Error('مكوّن تصوير التقرير غير متاح');
    if(!window.jspdf?.jsPDF)throw new Error('مكوّن إنشاء PDF غير متاح');
  }
  async function buildBlob(snapshot){
    if(!snapshot?.report)throw new Error('لا توجد معاينة جاهزة');
    ensureLibraries();
    const landscape=snapshot.state?.scope==='all';
    const m=metrics(landscape);
    const holder=document.createElement('div');
    holder.id='direct-pdf-render-root';
    holder.style.cssText=`position:fixed;left:0;top:0;width:${m.cssW}px;background:#fff;z-index:-2147483647;pointer-events:none;overflow:visible;direction:rtl`;
    holder.innerHTML=snapshot.report;
    document.body.appendChild(holder);
    const pages=[...holder.querySelectorAll('.fx-page')];
    if(!pages.length){holder.remove();throw new Error('تعذر قراءة صفحات التقرير')}
    pages.forEach(page=>{
      page.style.width=m.cssW+'px';page.style.height=m.cssH+'px';page.style.minHeight=m.cssH+'px';page.style.maxHeight=m.cssH+'px';
      page.style.margin='0';page.style.boxSizing='border-box';page.style.overflow='hidden';page.style.boxShadow='none';
    });
    try{
      if(document.fonts?.ready)await document.fonts.ready;
      await waitFrame();
      const {jsPDF}=window.jspdf;
      const pdf=new jsPDF({orientation:m.orientation,unit:'pt',format:'a4',compress:true,putOnlyUsedFonts:true});
      for(let i=0;i<pages.length;i++){
        try{toast(`إنشاء PDF: الصفحة ${toArabicDigits(i+1)} من ${toArabicDigits(pages.length)}`)}catch(_){}
        const canvas=await window.html2canvas(pages[i],{
          backgroundColor:'#ffffff',scale:2,useCORS:true,allowTaint:false,logging:false,
          width:m.cssW,height:m.cssH,windowWidth:m.cssW,windowHeight:m.cssH,
          scrollX:0,scrollY:0,imageTimeout:0,removeContainer:true
        });
        if(i>0)pdf.addPage('a4',m.orientation);
        pdf.addImage(canvas.toDataURL('image/jpeg',0.95),'JPEG',0,0,m.pdfW,m.pdfH,undefined,'FAST');
      }
      return pdf.output('blob');
    } finally {holder.remove()}
  }
  async function save(){
    const snapshot=window.FreshExporter?.snapshot?.();
    if(!snapshot)return toast('أنشئ المعاينة أولًا');
    if(window.AndroidApp&&typeof AndroidApp.saveHtmlAsPdf==='function'){
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
  }
  function install(){
    if(window.FreshExporter){window.FreshExporter.save=save;window.printPreparedReport=save}
    const warning=$('#freshExportModal .fx-warning');if(warning)warning.textContent='نظام PDF المباشر ٣.١.٤: يُنشأ الملف من المعاينة نفسها دون فتح شاشة الطباعة، لذلك لا يمكن أن يتحول التقرير الأسبوعي إلى شهري.';
    const button=$('#freshPreviewModal .primary-btn');if(button)button.textContent='إنشاء ملف PDF مباشر';
  }
  window.DirectPdfExporter={version:VERSION,buildBlob,save,fileName};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(install,0));else setTimeout(install,0);
})();
</script>
'''.replace('__H2C__',h2c).replace('__JSPDF__',jspdf)

if 'direct-pdf-export-v314' not in html:
    pos=html.rfind('</body>')
    if pos<0: raise SystemExit('Missing closing body tag')
    html=html[:pos]+patch+'\n'+html[pos:]

html_path.write_text(html,encoding='utf-8')
build=build_path.read_text(encoding='utf-8')
build=re.sub(r'versionCode\s+\d+','versionCode 17',build)
build=re.sub(r"versionName\s+'[^']+'","versionName '3.1.4'",build)
build_path.write_text(build,encoding='utf-8')

assert html.count('direct-pdf-export-v314')==1
assert "FINAL_VERSION='3.1.4'" in html
assert 'window.FreshExporter.save=save' in html
assert 'window.print()' not in patch
assert 'versionCode 17' in build
assert "versionName '3.1.4'" in build
print('Applied Halaqa 3.1.4 direct PDF export')
