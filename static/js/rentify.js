'use strict';

/* ══════════════════════════════════════════
   AUTH MODAL
══════════════════════════════════════════ */
const Modal = {
  overlay: null,
  box: null,

  init() {
    this.overlay = document.getElementById('auth-modal');
    if (!this.overlay) return;
    this.box = this.overlay.querySelector('.modal-box');

    // Close on backdrop click
    this.overlay.addEventListener('click', e => {
      if (e.target === this.overlay) this.close();
    });

    // Close button
    this.overlay.querySelectorAll('.modal-close').forEach(btn =>
      btn.addEventListener('click', () => this.close())
    );

    // Escape key
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') this.close();
    });

    // Tab switcher
    this.overlay.querySelectorAll('.modal-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const target = tab.dataset.tab;
        this.overlay.querySelectorAll('.modal-tab').forEach(t => t.classList.toggle('active', t === tab));
        this.overlay.querySelectorAll('.modal-panel').forEach(p => p.classList.toggle('active', p.id === target));
      });
    });

    // Open triggers on landing page
    document.querySelectorAll('[data-open-modal]').forEach(el => {
      el.addEventListener('click', e => {
        e.preventDefault();
        const tab = el.dataset.openModal || 'login-panel';
        this.open(tab);
      });
    });
  },

  open(tab = 'login-panel') {
    if (!this.overlay) return;
    this.overlay.querySelectorAll('.modal-tab').forEach(t =>
      t.classList.toggle('active', t.dataset.tab === tab)
    );
    this.overlay.querySelectorAll('.modal-panel').forEach(p =>
      p.classList.toggle('active', p.id === tab)
    );
    this.overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  },

  close() {
    if (!this.overlay) return;
    this.overlay.classList.remove('open');
    document.body.style.overflow = '';
  }
};

/* ══════════════════════════════════════════
   PUBLIC NAV — scroll effect
══════════════════════════════════════════ */
function initPubNav() {
  const nav = document.querySelector('.pub-nav');
  if (!nav) return;
  const update = () => nav.classList.toggle('scrolled', window.scrollY > 30);
  update();
  window.addEventListener('scroll', update, { passive: true });
}

/* ══════════════════════════════════════════
   SCROLL ANIMATIONS
══════════════════════════════════════════ */
function initScrollAnim() {
  const els = document.querySelectorAll('.anim');
  if (!els.length) return;
  const io = new IntersectionObserver(entries => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        // Stagger delay based on position in parent
        const siblings = entry.target.parentElement?.querySelectorAll('.anim');
        let idx = 0;
        siblings?.forEach((s, si) => { if (s === entry.target) idx = si; });
        entry.target.style.transitionDelay = `${idx * 0.07}s`;
        entry.target.classList.add('in');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08 });
  els.forEach(el => io.observe(el));
}

/* ══════════════════════════════════════════
   IMAGE SLOT PREVIEWS
══════════════════════════════════════════ */
function initImageSlots() {
  document.querySelectorAll('.img-slot, .image-upload-slot').forEach(slot => {
    const input = slot.querySelector('input[type=file]');
    const preview = slot.querySelector('.preview, .preview-img');
    if (!input) return;
    input.addEventListener('change', () => {
      const file = input.files[0];
      if (file && preview) {
        const r = new FileReader();
        r.onload = e => {
          preview.src = e.target.result;
          preview.style.display = 'block';
          const icon = slot.querySelector('.slot-icon, .upload-icon');
          if (icon) icon.style.display = 'none';
          const lbl = slot.querySelector('.slot-lbl, .upload-text');
          if (lbl) lbl.style.display = 'none';
        };
        r.readAsDataURL(file);
      }
    });
  });
}

/* ══════════════════════════════════════════
   AI PRICE + DESCRIPTION
══════════════════════════════════════════ */
function initAI() {
  const priceBtn = document.getElementById('ai-price-btn');
  const descBtn  = document.getElementById('ai-desc-btn');

  priceBtn?.addEventListener('click', async () => {
    const title = document.getElementById('id_title')?.value.trim();
    if (!title) { toast('Enter a product title first', 'warn'); return; }
    priceBtn.disabled = true;
    priceBtn.innerHTML = '<span class="spinner"></span> Thinking…';
    try {
      const r = await fetch(`/api/ai/price-suggestion/?title=${encodeURIComponent(title)}`);
      const d = await r.json();
      const s = d.suggestion;
      setIfEmpty('id_price_per_day', s.daily);
      setIfEmpty('id_price_per_week', s.weekly);
      setIfEmpty('id_price_per_month', s.monthly);
      setIfEmpty('id_security_deposit', s.deposit);
      toast(`AI suggests ₹${s.daily}/day for "${title}"`, 'success');
    } catch { toast('Could not fetch suggestion', 'error'); }
    priceBtn.disabled = false;
    priceBtn.innerHTML = '<i class="bi bi-stars me-1"></i> AI Price';
  });

  descBtn?.addEventListener('click', async () => {
    const title    = document.getElementById('id_title')?.value.trim();
    const category = document.getElementById('id_category')?.value || '';
    if (!title) { toast('Enter a title first', 'warn'); return; }
    descBtn.disabled = true;
    descBtn.innerHTML = '<span class="spinner"></span> Writing…';
    try {
      const r = await fetch(`/api/ai/description/?title=${encodeURIComponent(title)}&category=${encodeURIComponent(category)}`);
      const d = await r.json();
      const f = document.getElementById('id_description');
      if (f && d.description) { f.value = d.description; toast('Description ready!', 'success'); }
    } catch { toast('Failed', 'error'); }
    descBtn.disabled = false;
    descBtn.innerHTML = '<i class="bi bi-magic me-1"></i> Generate Description';
  });
}

function setIfEmpty(id, val) {
  const el = document.getElementById(id);
  if (el && !el.value) el.value = val;
}

/* ══════════════════════════════════════════
   BOOKING PRICE CALCULATOR
══════════════════════════════════════════ */
function initBookingCalc() {
  const start = document.getElementById('id_start_date');
  const end   = document.getElementById('id_end_date');
  const pid   = document.getElementById('booking-product-id')?.value;
  const box   = document.getElementById('booking-summary');
  if (!start || !end || !pid) return;

  async function calc() {
    if (!start.value || !end.value) return;
    try {
      const r = await fetch(`/bookings/api/calculate/?product_id=${pid}&start_date=${start.value}&end_date=${end.value}`);
      const d = await r.json();
      if (d.error || !box) return;
      box.innerHTML = `
        <div style="background:var(--canvas);border:1.5px solid var(--rule);border-radius:var(--r-lg);padding:1.25rem;margin-top:1rem;">
          <div class="d-flex justify-content-between mb-2" style="font-size:.875rem;">
            <span style="color:var(--ink-3)">Duration</span><strong>${d.total_days} day${d.total_days > 1 ? 's' : ''}</strong>
          </div>
          <div class="d-flex justify-content-between mb-2" style="font-size:.875rem;">
            <span style="color:var(--ink-3)">Rental cost</span><strong>₹${d.rental_cost.toFixed(2)}</strong>
          </div>
          <div class="d-flex justify-content-between mb-3" style="font-size:.875rem;">
            <span style="color:var(--ink-3)">Deposit</span><strong>₹${d.deposit.toFixed(2)}</strong>
          </div>
          <div style="border-top:2px solid var(--rule);padding-top:.85rem;display:flex;justify-content:space-between;align-items:center;">
            <span style="font-weight:700;">Total</span>
            <span style="font-size:1.2rem;font-weight:900;color:var(--p);">₹${d.total.toFixed(2)}</span>
          </div>
        </div>`;
    } catch (e) {}
  }
  start.addEventListener('change', calc);
  end.addEventListener('change', calc);
}

/* ══════════════════════════════════════════
   WISHLIST TOGGLE
══════════════════════════════════════════ */
function initWishlist() {
  document.querySelectorAll('.wl-btn[data-pid]').forEach(btn => {
    btn.addEventListener('click', async e => {
      e.preventDefault(); e.stopPropagation();
      try {
        const r = await fetch(`/wishlist/toggle/${btn.dataset.pid}/`, {
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
          credentials: 'same-origin'
        });
        const d = await r.json();
        const ico = btn.querySelector('i');
        if (d.in_wishlist) {
          btn.classList.add('on');
          ico?.classList.replace('bi-heart', 'bi-heart-fill');
          if (ico) ico.style.color = '#EF4444';
        } else {
          btn.classList.remove('on');
          ico?.classList.replace('bi-heart-fill', 'bi-heart');
          if (ico) ico.style.color = '';
        }
      } catch { window.location = '/accounts/login/'; }
    });
  });
}

/* ══════════════════════════════════════════
   STAR RATING WIDGET
══════════════════════════════════════════ */
function initStars() {
  const w = document.querySelector('.star-widget');
  if (!w) return;
  const stars = w.querySelectorAll('.star-btn');
  const inp   = document.getElementById('rating-value');
  const paint = val => stars.forEach(s => {
    const i = s.querySelector('i');
    const on = +s.dataset.val <= +val;
    i.className = on ? 'bi bi-star-fill' : 'bi bi-star';
    i.style.color = on ? '#F59E0B' : '#D1D5DB';
  });
  stars.forEach(s => {
    s.addEventListener('mouseenter', () => paint(s.dataset.val));
    s.addEventListener('mouseleave', () => paint(inp?.value || 0));
    s.addEventListener('click', () => { if (inp) inp.value = s.dataset.val; paint(s.dataset.val); });
  });
}

/* ══════════════════════════════════════════
   CHAT POLLING
══════════════════════════════════════════ */
function initChat() {
  const chatEl = document.getElementById('chat-messages');
  const convId = document.getElementById('conv-id')?.value;
  if (!chatEl || !convId) return;
  chatEl.scrollTop = chatEl.scrollHeight;

  let lastId = 0;
  chatEl.querySelectorAll('.msg[data-id]').forEach(m => {
    lastId = Math.max(lastId, +m.dataset.id);
  });

  setInterval(async () => {
    try {
      const r = await fetch(`/messaging/${convId}/poll/?after=${lastId}`, { credentials: 'same-origin' });
      const d = await r.json();
      if (d.messages?.length) {
        d.messages.forEach(m => {
          const div = document.createElement('div');
          div.className = `msg ${m.is_mine ? 'mine' : 'theirs'}`;
          div.dataset.id = m.id;
          div.innerHTML = `${esc(m.content)}<div class="msg-time">${m.time}</div>`;
          chatEl.appendChild(div);
          lastId = Math.max(lastId, m.id);
        });
        chatEl.scrollTop = chatEl.scrollHeight;
      }
    } catch (e) {}
  }, 3000);
}

function esc(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

/* ══════════════════════════════════════════
   TOAST
══════════════════════════════════════════ */
function toast(msg, type = 'info') {
  let c = document.getElementById('__toasts');
  if (!c) {
    c = document.createElement('div');
    c.id = '__toasts';
    c.style.cssText = 'position:fixed;bottom:1.25rem;right:1.25rem;z-index:99999;display:flex;flex-direction:column;gap:.5rem;pointer-events:none;';
    document.body.appendChild(c);
  }
  const colours = { success: '#16A34A', error: '#DC2626', warn: '#D97706', info: '#2563EB' };
  const t = document.createElement('div');
  t.style.cssText = `background:var(--surface);border-left:4px solid ${colours[type]||colours.info};padding:.75rem 1.2rem;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.15);font-size:.875rem;max-width:300px;pointer-events:auto;animation:fadeUp .3s var(--ease);color:var(--ink);`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity .3s'; setTimeout(() => t.remove(), 300); }, 3500);
}

/* ══════════════════════════════════════════
   AUTO-DISMISS DJANGO MESSAGES
══════════════════════════════════════════ */
function autoDismiss() {
  document.querySelectorAll('.alert[data-auto]').forEach(el => {
    setTimeout(() => { el.style.transition = 'opacity .4s'; el.style.opacity = '0'; setTimeout(() => el.remove(), 400); }, 4500);
  });
}

/* ══════════════════════════════════════════
   DROPDOWN (app nav user menu)
══════════════════════════════════════════ */
function initDropdowns() {
  document.querySelectorAll('[data-dropdown]').forEach(trigger => {
    const menu = document.getElementById(trigger.dataset.dropdown);
    if (!menu) return;
    trigger.addEventListener('click', e => {
      e.stopPropagation();
      const open = menu.classList.contains('dd-open');
      document.querySelectorAll('.dd-menu').forEach(m => m.classList.remove('dd-open'));
      if (!open) menu.classList.add('dd-open');
    });
  });
  document.addEventListener('click', () => {
    document.querySelectorAll('.dd-menu').forEach(m => m.classList.remove('dd-open'));
  });
}

/* ══════════════════════════════════════════
   INIT
══════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  Modal.init();
  initPubNav();
  initScrollAnim();
  initImageSlots();
  initAI();
  initBookingCalc();
  initWishlist();
  initStars();
  initChat();
  autoDismiss();
  initDropdowns();
});
