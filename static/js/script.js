// ========================= //
//   SHARED UTILITIES        //
// ========================= //

// Toast notifications
function showToast(message, type = 'info', duration = 3000) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'toastIn 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// Modal open/close
function openModal(id) {
  document.getElementById(id)?.classList.add('open');
}

function closeModal(id) {
  document.getElementById(id)?.classList.remove('open');
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});

// Tabs
function initTabs(tabGroupId) {
  const tabs = document.querySelectorAll(`[data-tab-group="${tabGroupId}"] .tab-btn`);
  const panels = document.querySelectorAll(`[data-tab-panel="${tabGroupId}"]`);

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      panels.forEach(p => p.style.display = 'none');
      tab.classList.add('active');
      const target = document.getElementById(tab.dataset.target);
      if (target) { target.style.display = ''; target.classList.add('animate-slide'); }
    });
  });

  if (tabs.length) tabs[0].click();
}

// Stagger animations on load
function staggerAnimations(selector, delay = 80) {
  const items = document.querySelectorAll(selector);
  items.forEach((el, i) => {
    el.style.opacity = '0';
    setTimeout(() => {
      el.style.animation = 'fadeSlideIn 0.4s ease forwards';
    }, i * delay);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  staggerAnimations('.stat-card', 100);
  staggerAnimations('.card', 80);
});

// ========================= //
//   DRAG AND DROP ENGINE    //
// ========================= //

let draggedItem = null;
let draggedData = null;

function initDragDrop() {
  // Make draggable items draggable
  document.querySelectorAll('[data-draggable]').forEach(el => {
    el.addEventListener('dragstart', handleDragStart);
    el.addEventListener('dragend', handleDragEnd);
    el.setAttribute('draggable', 'true');
  });

  // Drop zones
  document.querySelectorAll('[data-drop-zone]').forEach(zone => {
    zone.addEventListener('dragover', handleDragOver);
    zone.addEventListener('dragleave', handleDragLeave);
    zone.addEventListener('drop', handleDrop);
  });
}

function handleDragStart(e) {
  draggedItem = this;
  draggedData = {
    classId: this.dataset.classId,
    className: this.dataset.className,
    subjectName: this.dataset.subjectName,
    teacherName: this.dataset.teacherName,
    chipType: this.dataset.chipType || 'theory'
  };
  e.dataTransfer.effectAllowed = 'move';
  setTimeout(() => this.style.opacity = '0.4', 0);
}

function handleDragEnd(e) {
  if (draggedItem) draggedItem.style.opacity = '1';
  document.querySelectorAll('.cal-cell').forEach(c => c.classList.remove('drop-hover'));
}

function handleDragOver(e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'move';
  this.classList.add('drop-hover');
}

function handleDragLeave(e) {
  this.classList.remove('drop-hover');
}

async function handleDrop(e) {
  e.preventDefault();
  this.classList.remove('drop-hover');

  if (!draggedData) return;

  const timeslotId = this.dataset.timeslotId;
  const dayName = this.dataset.day;

  if (!timeslotId) {
    showToast('Cannot schedule in a break slot', 'error');
    return;
  }

  // Build the form data and POST to create-timetable
  const body = new URLSearchParams({
    class_id: draggedData.classId,
    timeslot_id: timeslotId,
    entry_type: draggedData.chipType
  });

  try {
    const resp = await fetch('/create-timetable', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
      redirect: 'manual'
    });

    if (resp.ok || resp.type === 'opaqueredirect') {
      // Render chip in the cell
      renderChipInCell(this, draggedData);
      // Remove from sidebar if present
      if (draggedItem && draggedItem.closest('.sidebar-panel')) {
        draggedItem.remove();
      }
      showToast(`${draggedData.className} scheduled!`, 'success');
      setTimeout(() => location.reload(), 800);
    } else {
      const json = await resp.json().catch(() => ({}));
      showToast(json.error || 'Scheduling failed', 'error');
    }
  } catch (err) {
    showToast('Could not connect to server', 'error');
  }

  draggedItem = null;
  draggedData = null;
}

function renderChipInCell(cell, data) {
  const chip = document.createElement('div');
  chip.className = `class-chip ${data.chipType === 'lab' ? 'lab-chip' : ''}`;
  chip.innerHTML = `<span>📚</span><span>${data.subjectName}</span>`;
  cell.appendChild(chip);
}

// ========================= //
//   TEACHER SLOT SELECTOR   //
// ========================= //

function initSlotSelector() {
  const slots = document.querySelectorAll('.slot-btn:not(.break-slot)');
  const selectedSlots = new Set();
  const hiddenInput = document.getElementById('selectedSlotsInput');

  slots.forEach(btn => {
    btn.addEventListener('click', () => {
      const slotId = btn.dataset.slotId;
      if (selectedSlots.has(slotId)) {
        selectedSlots.delete(slotId);
        btn.classList.remove('selected');
      } else {
        selectedSlots.add(slotId);
        btn.classList.add('selected');
      }
      if (hiddenInput) hiddenInput.value = [...selectedSlots].join(',');
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initDragDrop();
  if (document.querySelector('.slot-btn')) initSlotSelector();
});