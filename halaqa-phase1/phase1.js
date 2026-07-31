/* المرحلة الأولى: فصل المراجعة عن الحفظ، عدة سور في اليوم، والعودة إلى اليوم الحالي */
(() => {
  'use strict';

  const originalDayRow = window.dayRow;
  const originalChooseSurah = window.chooseSurah;
  const originalClearSelectedSurah = window.clearSelectedSurah;
  const originalCurrentSurahPickerValue = window.currentSurahPickerValue;
  const originalUpdateMonthLabels = window.updateMonthLabels;
  const originalRenderAll = window.renderAll;

  function injectPhaseOneInterface() {
    const monthControls = document.querySelector('.compact-month');
    if (monthControls && !document.getElementById('todayButton')) {
      const button = document.createElement('button');
      button.type = 'button';
      button.id = 'todayButton';
      button.className = 'today-button';
      button.textContent = 'اليوم';
      button.title = 'الانتقال إلى اليوم الحالي';
      button.setAttribute('onclick', 'goToToday()');
      monthControls.appendChild(button);
    }

    const quickNav = document.querySelector('.quick-date-nav');
    if (quickNav && !document.getElementById('quickTodayButton')) {
      const button = document.createElement('button');
      button.type = 'button';
      button.id = 'quickTodayButton';
      button.className = 'quick-today-button';
      button.textContent = 'اليوم';
      button.setAttribute('onclick', 'goQuickToday()');
      quickNav.insertAdjacentElement('afterend', button);
    }
  }

  function currentHijriMonthParts() {
    return getHijriParts(new Date());
  }

  window.goToToday = function () {
    closeSurahPicker();
    hijriCursor = currentHijriMonthParts();
    quickDate = isoToday();
    renderAll();
    setTimeout(() => {
      const row = document.querySelector(`[data-date="${isoToday()}"]`);
      if (row) row.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 80);
    toast('تم الانتقال إلى اليوم الحالي');
  };

  window.goQuickToday = function () {
    quickDate = isoToday();
    hijriCursor = currentHijriMonthParts();
    renderAll();
    toast('تم الانتقال إلى اليوم الحالي');
  };

  window.updateMonthLabels = function () {
    originalUpdateMonthLabels();
    const current = currentHijriMonthParts();
    const button = document.getElementById('todayButton');
    if (button) button.classList.toggle('hidden', current.y === hijriCursor.y && current.m === hijriCursor.m);
    const quickButton = document.getElementById('quickTodayButton');
    if (quickButton) quickButton.classList.toggle('hidden', quickDate === isoToday());
  };

  function normalizeReviewItem(item) {
    return {
      id: item?.id || uid(),
      startSurah: String(item?.startSurah || item?.surah || '').replace(/^سورة\s+/, '').trim(),
      endSurah: String(item?.endSurah || item?.toSurah || '').replace(/^سورة\s+/, '').trim(),
      from: String(item?.from || ''),
      to: String(item?.to || '')
    };
  }

  function ensureReviewItems(recitation) {
    if (!recitation) return [];
    if (!Array.isArray(recitation.reviewItems)) recitation.reviewItems = [];
    recitation.reviewItems = recitation.reviewItems.map(normalizeReviewItem);
    if (!recitation.reviewItems.length && recitation.surah) {
      recitation.reviewItems.push(normalizeReviewItem({
        startSurah: recitation.surah,
        endSurah: recitation.reviewEndSurah || '',
        from: recitation.from,
        to: recitation.to
      }));
    }
    return recitation.reviewItems;
  }

  function migrateReviewRecords() {
    let changed = false;
    db.recitations.forEach(r => {
      if (normalizeKind(r.kind) !== 'review') return;
      const before = JSON.stringify(r.reviewItems || []);
      ensureReviewItems(r);
      if (before !== JSON.stringify(r.reviewItems || [])) changed = true;
    });
    if (changed) persist();
  }

  const baseRecitationHasData = window.recitationHasData;
  window.recitationHasData = function (r) {
    if (!r) return false;
    if (normalizeKind(r.kind) === 'review') {
      const items = ensureReviewItems(r);
      return Boolean(r.grade || items.some(x => x.startSurah || x.endSurah || x.from || x.to));
    }
    return baseRecitationHasData(r);
  };

  const baseRecitationAmount = window.recitationAmount;
  window.recitationAmount = function (r) {
    if (!r) return '—';
    if (normalizeKind(r.kind) !== 'review') return baseRecitationAmount(r);
    const items = ensureReviewItems(r).filter(x => x.startSurah || x.endSurah);
    if (!items.length) return 'المقدار غير محدد';
    return items.map(item => {
      if (item.startSurah && item.endSurah && item.endSurah !== item.startSurah) {
        return `من سورة ${item.startSurah} إلى سورة ${item.endSurah}`;
      }
      return `سورة ${item.startSurah || item.endSurah}`;
    }).join('، ');
  };

  window.recitationText = function (r) {
    if (!recitationHasData(r)) return '—';
    const grade = r.grade ? ` — ${GRADES[r.grade]?.label || r.grade}` : '';
    if (normalizeKind(r.kind) === 'review') return `${esc(recitationAmount(r))}${grade}`;
    const amount = recitationAmount(r);
    return `${esc(r.surah || 'سورة غير محددة')}${amount && amount !== 'المقدار غير محدد' ? ` (${esc(amount)})` : ''}${grade}`;
  };

  function reviewItemAt(date, index) {
    const r = ensureRecitation(currentStudentId, 'review', date);
    const items = ensureReviewItems(r);
    return { r, items, item: items[index] };
  }

  window.openReviewSurahPicker = function (event, button, date, index, field) {
    event.stopPropagation();
    if (isHoliday(date)) return toast('لا تُسجّل المراجعة في يوم العطلة');
    const portal = document.getElementById('surahPickerPortal');
    activeSurahButton = button;
    portal.dataset.mode = 'reviewItem';
    portal.dataset.date = date;
    portal.dataset.kind = 'review';
    portal.dataset.index = String(index);
    portal.dataset.field = field;
    document.getElementById('surahSearch').value = '';
    renderSurahOptions('');
    portal.classList.add('open');
    positionSurahPicker(button);
  };

  window.currentSurahPickerValue = function () {
    const portal = document.getElementById('surahPickerPortal');
    if (portal?.dataset.mode === 'reviewItem') {
      const { item } = reviewItemAt(portal.dataset.date, Number(portal.dataset.index));
      return item?.[portal.dataset.field] || '';
    }
    return originalCurrentSurahPickerValue();
  };

  window.chooseSurah = function (value) {
    const portal = document.getElementById('surahPickerPortal');
    if (portal?.dataset.mode !== 'reviewItem') return originalChooseSurah(value);
    const date = portal.dataset.date;
    const index = Number(portal.dataset.index);
    const field = portal.dataset.field;
    const { r, item } = reviewItemAt(date, index);
    if (!item) return closeSurahPicker();
    rememberUndo(field === 'endSurah' ? 'اختيار نهاية نطاق المراجعة' : 'اختيار سورة المراجعة');
    item[field] = value;
    r.updatedAt = new Date().toISOString();
    persist();
    closeSurahPicker();
    refreshRelatedViews();
    renderSheet();
    toast('تم حفظ سورة المراجعة');
  };

  window.clearSelectedSurah = function () {
    const portal = document.getElementById('surahPickerPortal');
    if (portal?.dataset.mode !== 'reviewItem') return originalClearSelectedSurah();
    const date = portal.dataset.date;
    const index = Number(portal.dataset.index);
    const field = portal.dataset.field;
    const { r, item } = reviewItemAt(date, index);
    if (item) {
      rememberUndo('مسح سورة من المراجعة');
      item[field] = '';
      r.updatedAt = new Date().toISOString();
      persist();
    }
    closeSurahPicker();
    refreshRelatedViews();
    renderSheet();
  };

  window.addReviewItem = function (date) {
    if (!currentStudentId) return;
    rememberUndo('إضافة سورة إلى المراجعة');
    const r = ensureRecitation(currentStudentId, 'review', date);
    ensureReviewItems(r).push(normalizeReviewItem({}));
    r.updatedAt = new Date().toISOString();
    persist();
    renderSheet();
    refreshRelatedViews();
  };

  window.removeReviewItem = function (date, index) {
    const { r, items } = reviewItemAt(date, index);
    if (!items[index]) return;
    rememberUndo('حذف سورة من المراجعة');
    items.splice(index, 1);
    r.updatedAt = new Date().toISOString();
    persist();
    renderSheet();
    refreshRelatedViews();
  };

  function reviewItemHtml(item, index, date) {
    const start = item.startSurah || 'اختر السورة';
    const end = item.endSurah || 'إضافة إلى سورة';
    return `<div class="review-item-row">
      <span class="review-item-number">${toArabicDigits(index + 1)}</span>
      <button type="button" class="review-surah-button ${item.startSurah ? 'has-value' : ''}" onclick="openReviewSurahPicker(event,this,'${date}',${index},'startSurah')"><span>${esc(start)}</span><b>⌄</b></button>
      <span class="review-range-word">إلى</span>
      <button type="button" class="review-surah-button end ${item.endSurah ? 'has-value' : ''}" onclick="openReviewSurahPicker(event,this,'${date}',${index},'endSurah')"><span>${esc(end)}</span><b>⌄</b></button>
      <button type="button" class="review-remove" onclick="removeReviewItem('${date}',${index})" title="حذف هذا السطر">×</button>
    </div>`;
  }

  function reviewDayRow(date, dayName) {
    const iso = isoDate(date);
    const r = getRecitation(currentStudentId, 'review', iso) || { kind: 'review', reviewItems: [] };
    const items = ensureReviewItems(r);
    const a = getAttendance(currentStudentId, iso) || {};
    const hasNote = getNotesFor(currentStudentId, iso).length > 0;
    const weeklyHoliday = isWeeklyHoliday(date);
    const suddenHoliday = isSuddenHoliday(iso);
    const holiday = weeklyHoliday || suddenHoliday;
    const holidayText = weeklyHoliday ? 'عطلة أسبوعية' : (suddenHoliday ? 'عطلة مفاجئة' : 'عطلة');
    const gradeOpts = '<option value="">اختر التقدير</option>' + Object.entries(GRADES).map(([k, g]) => `<option value="${k}" ${r.grade === k ? 'selected' : ''}>${g.label} — ${g.score}</option>`).join('');
    const flagButton = key => `<button class="flag ${key} ${a[key] ? 'active' : ''}" onclick="toggleFlag('${iso}','${key}',this)" title="${FLAG_INFO[key].label} — خصم ${FLAG_INFO[key].deduction}">${FLAG_INFO[key].label}</button>`;
    const holidayButton = `<button type="button" class="holiday-toggle ${holiday ? 'active' : ''} ${weeklyHoliday ? 'weekly' : ''}" onclick="toggleSuddenHoliday('${iso}')">${holidayText}</button>`;
    const itemsHtml = items.length ? items.map((item, index) => reviewItemHtml(item, index, iso)).join('') : '<div class="review-empty">لم تُحدد سور المراجعة لهذا اليوم.</div>';
    return `<div id="day-${iso}" class="day-row review-day ${holiday ? 'is-holiday' : ''}" data-date="${iso}">
      <div class="review-day-head"><div><strong>${dayName}</strong><small>${hijriShort(date)}</small></div>${holidayButton}</div>
      ${holiday ? `<div class="holiday-banner">☀ ${holidayText} — لا درجات ولا حضور ولا خصومات</div>` : `
        <div class="review-main-card">
          <div class="review-items-title"><span>سور المراجعة</span><small>اختر سورة واحدة، نطاقًا من سورة إلى سورة، أو أضف عدة سور.</small></div>
          <div class="review-items-list">${itemsHtml}</div>
          <button type="button" class="review-add-button" onclick="addReviewItem('${iso}')">＋ إضافة سورة أخرى</button>
          <div class="review-grade-row"><label>تقدير المراجعة</label><select data-field="grade" class="grade-select ${r.grade ? 'grade-' + r.grade : ''}" onchange="changeGradeFromSelect(this)">${gradeOpts}</select></div>
          <div class="review-flags"><div class="review-flags-label">الحضور والخصومات</div><div class="flags-cell">${flagButton('absent')}${flagButton('excused')}${flagButton('late')}${flagButton('trouble')}</div></div>
          <div class="review-note-row"><button type="button" class="note-btn ${hasNote ? 'has-note' : ''}" onclick="openNoteModal('${iso}')"><span class="note-label">${hasNote ? 'ملاحظات اليوم' : 'إضافة ملاحظة'}</span></button></div>
        </div>`}
    </div>`;
  }

  window.dayRow = function (date, dayName) {
    if (sheetKind === 'review') return reviewDayRow(date, dayName);
    const html = originalDayRow(date, dayName);
    const iso = isoDate(date);
    return html.replace('<div class="day-row ', `<div id="day-${iso}" class="day-row `).replace('<div class="day-row"', `<div id="day-${iso}" class="day-row"`);
  };

  function retrySignature(r) {
    if (normalizeKind(r.kind) === 'review') {
      return JSON.stringify(ensureReviewItems(r).map(x => [x.startSurah, x.endSurah, x.from, x.to]));
    }
    return [r.surah || '', r.from || '', r.to || ''].join('|');
  }

  window.pendingRetries = function (studentId, kind = null) {
    const resolved = new Set(db.resolvedRetries || []);
    const weak = db.recitations
      .filter(r => r.studentId === studentId && (!kind || normalizeKind(r.kind) === normalizeKind(kind)) && ['weak', 'notmemorized'].includes(r.grade) && recitationHasData(r))
      .sort((a, b) => a.date.localeCompare(b.date));
    return weak.filter(r => {
      if (resolved.has(r.id)) return false;
      const signature = retrySignature(r);
      return !db.recitations.some(x => x.studentId === r.studentId && normalizeKind(x.kind) === normalizeKind(r.kind) && x.date > r.date && gradeScore(x.grade) > 0 && retrySignature(x) === signature);
    }).sort((a, b) => b.date.localeCompare(a.date));
  };

  window.retryPanelHtml = function (studentId, kind = null) {
    const items = pendingRetries(studentId, kind);
    if (!items.length) return '';
    return `<div class="retry-panel"><div class="retry-head"><h4>المقادير المطلوبة للإعادة${kind ? ` — ${normalizeKind(kind) === 'review' ? 'المراجعة' : 'الحفظ'}` : ''}</h4><span class="retry-count">${toArabicDigits(items.length)}</span></div><div class="retry-list">${items.slice(0, 8).map(r => `<div class="retry-item"><div><div class="retry-title">${normalizeKind(r.kind) === 'review' ? 'مراجعة' : 'حفظ'} — ${normalizeKind(r.kind) === 'review' ? esc(recitationAmount(r)) : `سورة ${esc(r.surah || 'غير محددة')}`}</div><div class="retry-meta">${normalizeKind(r.kind) === 'review' ? '' : `${esc(recitationAmount(r))} • `}${GRADES[r.grade]?.label || ''} • ${hijriDateLabel(dateFromISO(r.date))}</div></div><div class="retry-actions"><button class="retry-schedule" onclick="scheduleRetry('${r.id}')">جدولة الإعادة</button><button class="retry-done" onclick="resolveRetry('${r.id}')">تمت الإعادة</button></div></div>`).join('')}</div></div>`;
  };

  window.scheduleRetry = function (id) {
    const source = db.recitations.find(r => r.id === id);
    if (!source) return;
    const kind = normalizeKind(source.kind);
    const dates = monthScheduleDates().filter(d => !isHoliday(d));
    let target = dates.find(d => d > source.date && !recitationHasData(getRecitation(source.studentId, kind, d)));
    if (!target) target = dates.find(d => !recitationHasData(getRecitation(source.studentId, kind, d)));
    if (!target) return toast('لا يوجد يوم فارغ في الشهر المختار');
    rememberUndo('جدولة إعادة');
    const r = ensureRecitation(source.studentId, kind, target);
    if (kind === 'review') {
      r.reviewItems = ensureReviewItems(source).map(item => ({ ...item, id: uid() }));
      r.surah = '';
      r.from = '';
      r.to = '';
    } else {
      Object.assign(r, { surah: source.surah, from: source.from, to: source.to });
    }
    r.grade = '';
    r.updatedAt = new Date().toISOString();
    currentStudentId = source.studentId;
    sheetKind = kind;
    persist();
    renderAll();
    goPage('sheet');
    setTimeout(() => document.querySelector(`.day-row[data-date="${target}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 160);
    toast('تم وضع الإعادة في أول يوم فارغ');
  };

  window.renderSheet = function () {
    populateStudentSelects();
    updateMonthLabels();
    const area = document.getElementById('sheetArea');
    const student = selectedStudent();
    if (!student) {
      area.innerHTML = `<div class="card empty-state"><div style="font-size:42px">👥</div><h3>ابدأ بإضافة طالب</h3><p>اضغط زر ＋ في الأعلى، ثم افتح كشف الحفظ أو المراجعة.</p><button class="primary-btn" onclick="openStudentModal()">إضافة أول طالب</button></div>`;
      return;
    }
    const start = periodStart(hijriCursor.y, hijriCursor.m);
    const kindLabel = sheetKind === 'memorization' ? 'المحفوظ' : 'المراجعة';
    let weeks = '';
    for (let w = 0; w < 4; w++) {
      const ws = addDays(start, w * 7);
      const stat = weekStats(student.id, ws, sheetKind);
      let rows = '';
      for (let d = 0; d < 5; d++) rows += dayRow(addDays(ws, d), DAY_NAMES[d]);
      weeks += `<div class="week-block" data-start="${isoDate(ws)}"><div class="week-title"><span>${WEEK_NAMES[w]}</span><span>${hijriDateLabel(ws)} — ${hijriDateLabel(addDays(ws, 4))}</span></div>${rows}<div class="week-total"><span class="weekBreakdown">الدرجات ${toArabicDigits(stat.gradeTotal)} − الخصومات ${toArabicDigits(stat.deduction)}</span><span>المجموع: <strong class="weekScore">${toArabicDigits(stat.net)} / ${toArabicDigits(stat.gradedCount * 5)}</strong></span></div></div>`;
    }
    const curriculum = sheetKind === 'memorization' ? curriculumCardHtml(student) : '';
    area.innerHTML = `${retryPanelHtml(student.id, sheetKind)}${curriculum}<div class="sheet-frame"><div class="sheet-headline"><h3>جدول ${kindLabel} الشهري</h3><div class="headline-student-name">${esc(student.name)}</div><p>رقم الطالب: <b>${esc(student.studentNumber)}</b> — ${hijriMonthLabel(hijriCursor.y, hijriCursor.m)}</p></div>${weeks}</div>`;
  };

  window.renderAll = function () {
    originalRenderAll();
    updateMonthLabels();
  };

  injectPhaseOneInterface();
  migrateReviewRecords();
  renderAll();
})();
