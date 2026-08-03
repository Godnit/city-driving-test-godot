from pathlib import Path

html_path = Path('halaqa_apk_project/app/src/main/assets/index.html')
s = html_path.read_text(encoding='utf-8')

css = r'''
<style id="phase4-sticky-account-css">
#page-sheet .sheet-control-card{position:sticky;top:0;z-index:92;margin-top:0;border-radius:0 0 20px 20px;box-shadow:0 10px 28px rgba(4,48,47,.18);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px)}
#page-sheet .sheet-control-card .sheet-switch{max-width:720px;margin-inline:auto}
#page-sheet .sheet-control-card .switch-btn{min-height:52px;font-weight:900}
.cloud-account-button{position:relative}.cloud-account-button::after{content:"";position:absolute;width:9px;height:9px;border-radius:50%;inset-inline-start:7px;bottom:7px;background:#d7a52e;border:2px solid var(--card,#fff)}
.cloud-account-button.cloud-online::after{background:#2fb879}.cloud-account-button.cloud-error::after{background:#d95656}
.cloud-sync-strip{display:flex;align-items:center;justify-content:space-between;gap:10px;border:1px solid var(--line);border-radius:16px;padding:10px 13px;background:var(--soft);font-size:13px;margin-top:10px}.cloud-sync-strip b{font-size:14px}
.cloud-sync-dot{width:10px;height:10px;border-radius:50%;background:#d7a52e;display:inline-block;margin-inline-end:7px}.cloud-sync-dot.online{background:#2fb879}.cloud-sync-dot.error{background:#d95656}
.cloud-account-panel{display:grid;gap:14px}.cloud-account-panel .account-card{border:1px solid var(--line);background:var(--soft);border-radius:18px;padding:15px}.cloud-account-panel h3{margin:0 0 8px;font-size:19px}.cloud-account-panel p{margin:0;color:var(--muted);line-height:1.8}
.cloud-login-grid{display:grid;gap:10px;margin-top:14px}.cloud-login-grid input{width:100%;min-height:48px;border:1px solid var(--line);border-radius:14px;background:var(--card);color:var(--text);padding:0 13px;font:inherit}.cloud-actions{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}.cloud-actions button{min-height:48px;border-radius:14px;font-weight:800}.cloud-disabled-note{border:1px dashed #c49a36;background:rgba(210,165,52,.12);padding:12px;border-radius:14px;line-height:1.8}
[data-theme="dark"] #page-sheet .sheet-control-card{background:rgba(13,49,47,.96)}[data-theme="dark"] .cloud-account-button::after{border-color:#143b39}
@media(max-width:560px){#page-sheet .sheet-control-card{top:0;padding:9px 10px}#page-sheet .sheet-control-card .switch-btn{min-height:48px;font-size:16px}.cloud-actions{grid-template-columns:1fr}}
</style>
'''
if 'phase4-sticky-account-css' not in s:
    s = s.replace('</head>', css + '\n</head>', 1)

old_tools = '''        <button class="ghost-btn" onclick="openHolidaySettings()">إعدادات العطلة</button>
        <button class="icon-btn" aria-label="إعدادات التطبيق" title="إعدادات التطبيق واسم المعلم" onclick="openTeacherSettings(false)">⚙️</button>'''
new_tools = '''        <button class="ghost-btn" onclick="openHolidaySettings()">إعدادات العطلة</button>
        <button id="cloudAccountButton" class="icon-btn cloud-account-button" aria-label="حساب المسجد والمزامنة" title="حساب المسجد والمزامنة" onclick="openCloudAccountModal()">☁️</button>
        <button class="icon-btn" aria-label="إعدادات التطبيق" title="إعدادات التطبيق واسم المعلم" onclick="openTeacherSettings(false)">⚙️</button>'''
if 'cloudAccountButton' not in s:
    if old_tools not in s:
        raise SystemExit('header tools anchor missing')
    s = s.replace(old_tools, new_tools, 1)

old_save = '''    <div class="save-actions"><span id="globalSaveIndicator" class="global-save-indicator">محفوظ تلقائيًا ✓</span><button id="undoButton" class="undo-btn" type="button" onclick="undoLastChange()">↶ تراجع عن آخر تعديل</button></div>'''
if 'cloudSyncStrip' not in s:
    s = s.replace(old_save, old_save + '''\n    <div id="cloudSyncStrip" class="cloud-sync-strip"><span><i id="cloudSyncDot" class="cloud-sync-dot"></i><b id="cloudSyncTitle">الوضع المحلي</b></span><span id="cloudSyncText">البيانات محفوظة على هذا الجهاز</span></div>''', 1)

modal = r'''
<div id="cloudAccountModal" class="modal no-print" aria-hidden="true"><div class="modal-card large-modal" role="dialog" aria-modal="true" aria-labelledby="cloudAccountTitle"><div class="modal-head"><h2 id="cloudAccountTitle">حساب المسجد والمزامنة</h2><button class="close-btn" onclick="closeModal('cloudAccountModal')">×</button></div><div class="cloud-account-panel"><div class="account-card"><h3>مزامنة حساب المسجد</h3><p>لكل مدرس حساب مستقل، ومدير المسجد يستطيع مشاهدة جميع الحلقات والطلاب والتقارير.</p><div id="cloudAccountState" class="cloud-disabled-note">يلزم ربط التطبيق بمشروع Firebase خاص بالمسجد قبل تفعيل المزامنة.</div></div><div class="account-card"><h3>تسجيل الدخول</h3><div class="cloud-login-grid"><input id="cloudEmail" type="email" inputmode="email" autocomplete="username" placeholder="البريد الإلكتروني"><input id="cloudPassword" type="password" autocomplete="current-password" placeholder="كلمة المرور"></div><div class="cloud-actions"><button class="primary-btn" type="button" onclick="cloudAccountAction('login')">تسجيل الدخول</button><button class="secondary-btn" type="button" onclick="cloudAccountAction('create-mosque')">إنشاء حساب مسجد</button></div></div><div class="account-card"><h3>الحالة الحالية</h3><p id="cloudDetailedStatus">يعمل التطبيق محليًا، ولن تتأثر البيانات الحالية أثناء تجهيز المزامنة.</p></div></div></div></div>
'''
if 'id="cloudAccountModal"' not in s:
    pos = s.rfind('</body>')
    s = s[:pos] + modal + '\n' + s[pos:]

js = r'''
<script id="phase4-sticky-account-js">
(()=>{'use strict';const positions={memorization:0,review:0};let switching=false;function sheetTop(){const e=document.querySelector('#page-sheet .sheet-control-card');return e?e.getBoundingClientRect().top+scrollY:0}const previous=window.setSheetKind;window.setSheetKind=function(kind){kind=normalizeKind(kind);if(switching||kind===sheetKind)return previous(kind);positions[sheetKind]=Math.max(0,scrollY-sheetTop());switching=true;previous(kind);requestAnimationFrame(()=>requestAnimationFrame(()=>{scrollTo({top:sheetTop()+Math.max(0,positions[kind]||0),behavior:'auto'});switching=false}))};window.openCloudAccountModal=function(){openModal('cloudAccountModal');updateCloudAccountUI()};window.cloudAccountAction=async function(action){const bridge=window.HalaqaCloud;if(!bridge||!bridge.configured)return toast('يلزم أولًا ربط التطبيق بمشروع المزامنة الخاص بالمسجد');const email=document.getElementById('cloudEmail')?.value?.trim(),password=document.getElementById('cloudPassword')?.value||'';try{if(action==='login')await bridge.signIn(email,password);else await bridge.createMosqueAdmin(email,password);updateCloudAccountUI()}catch(error){console.error(error);toast(error?.message||'تعذر تنفيذ العملية')}};window.updateCloudAccountUI=function(){const bridge=window.HalaqaCloud,status=bridge?.status?.()||{mode:'local',label:'الوضع المحلي',detail:'البيانات محفوظة على هذا الجهاز'};document.getElementById('cloudAccountButton')?.classList.toggle('cloud-online',status.mode==='online');document.getElementById('cloudAccountButton')?.classList.toggle('cloud-error',status.mode==='error');document.getElementById('cloudSyncDot')?.classList.toggle('online',status.mode==='online');document.getElementById('cloudSyncDot')?.classList.toggle('error',status.mode==='error');const title=document.getElementById('cloudSyncTitle'),text=document.getElementById('cloudSyncText'),detail=document.getElementById('cloudDetailedStatus'),state=document.getElementById('cloudAccountState');if(title)title.textContent=status.label||'الوضع المحلي';if(text)text.textContent=status.detail||'';if(detail)detail.textContent=status.longDetail||status.detail||'';if(state)state.textContent=bridge?.configured?'تم ربط الخدمة السحابية. يمكنك تسجيل الدخول.':'يلزم ربط التطبيق بمشروع Firebase خاص بالمسجد قبل تفعيل المزامنة.'};window.HalaqaCloud=window.HalaqaCloud||{configured:false,status(){return{mode:'local',label:'الوضع المحلي',detail:'لم يتم ربط حساب مسجد بعد',longDetail:'البيانات الحالية محفوظة محليًا، وسيتم ترحيل نسخة منها بعد تفعيل الحساب.'}}};addEventListener('online',updateCloudAccountUI);addEventListener('offline',updateCloudAccountUI);setTimeout(updateCloudAccountUI,300)})();
</script>
'''
if 'phase4-sticky-account-js' not in s:
    pos = s.rfind('</body>')
    s = s[:pos] + js + '\n' + s[pos:]

html_path.write_text(s, encoding='utf-8')
assert 'position:sticky' in s
assert 'cloudAccountButton' in s
assert 'phase4-sticky-account-js' in s
print('Applied phase 4 alpha UI and sticky tabs')
