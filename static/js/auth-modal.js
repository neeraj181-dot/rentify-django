/* ============================================================
   RENTIFY — Auth Modal
   Handles: open/close, tab switching, AJAX login/register,
            password strength, show/hide password, field validation
   ============================================================ */
'use strict';

(function () {

  /* ── State ── */
  let overlay, modal;
  let returnUrl = '';

  /* ── Open / Close ── */
  function openModal(tab) {
    overlay = document.getElementById('rfyAuthModal');
    if (!overlay) return;
    returnUrl = window.location.pathname + window.location.search;
    switchTab(tab || 'login');
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
    // Focus first input after animation
    setTimeout(() => {
      const inp = overlay.querySelector('.rfy-panel.active .auth-input');
      if (inp) inp.focus();
    }, 320);
  }

  function closeModal() {
    if (!overlay) overlay = document.getElementById('rfyAuthModal');
    if (!overlay) return;
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  function switchTab(name) {
    document.querySelectorAll('.rfy-tab').forEach(t =>
      t.classList.toggle('active', t.dataset.tab === name)
    );
    document.querySelectorAll('.rfy-panel').forEach(p =>
      p.classList.toggle('active', p.id === `rfy-panel-${name}`)
    );
  }

  /* ── Toast ── */
  function toast(msg, type = 'info') {
    let wrap = document.getElementById('rfyToastWrap');
    if (!wrap) {
      wrap = document.createElement('div');
      wrap.id = 'rfyToastWrap';
      wrap.className = 'rfy-toast-wrap';
      document.body.appendChild(wrap);
    }
    const icons = { success: '✓', error: '✕', info: 'ℹ' };
    const t = document.createElement('div');
    t.className = `rfy-toast ${type}`;
    t.innerHTML = `<span style="font-size:1rem;">${icons[type] || 'ℹ'}</span><span>${msg}</span>`;
    wrap.appendChild(t);
    setTimeout(() => {
      t.style.transition = 'opacity .3s, transform .3s';
      t.style.opacity = '0';
      t.style.transform = 'translateX(12px)';
      setTimeout(() => t.remove(), 300);
    }, 3800);
  }

  /* ── Password strength ── */
  function calcStrength(pwd) {
    let score = 0;
    if (pwd.length >= 8)  score++;
    if (pwd.length >= 12) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;
    return score; // 0-5
  }

  function updateStrength(inputEl) {
    const bar   = inputEl.closest('.rfy-field')?.querySelector('.pwd-strength-fill');
    const label = inputEl.closest('.rfy-field')?.querySelector('.pwd-strength-label');
    if (!bar) return;
    const score = calcStrength(inputEl.value);
    const map = [
      { pct: '0%',   color: '#E4E4E7', text: '',          cls: '' },
      { pct: '20%',  color: '#EF4444', text: 'Very weak',  cls: 'color:#EF4444' },
      { pct: '40%',  color: '#F97316', text: 'Weak',        cls: 'color:#F97316' },
      { pct: '60%',  color: '#EAB308', text: 'Fair',        cls: 'color:#EAB308' },
      { pct: '80%',  color: '#22C55E', text: 'Strong',      cls: 'color:#22C55E' },
      { pct: '100%', color: '#16A34A', text: 'Very strong', cls: 'color:#16A34A' },
    ];
    const m = map[score];
    bar.style.width = m.pct;
    bar.style.backgroundColor = m.color;
    if (label) { label.textContent = m.text; label.style.cssText = m.cls; }
  }

  /* ── Show / hide password ── */
  function togglePwd(btn) {
    const wrap = btn.closest('.rfy-input-wrap');
    const inp  = wrap?.querySelector('.auth-input');
    if (!inp) return;
    const show = inp.type === 'password';
    inp.type = show ? 'text' : 'password';
    btn.innerHTML = show
      ? '<i class="bi bi-eye-slash"></i>'
      : '<i class="bi bi-eye"></i>';
  }

  /* ── Show field errors ── */
  function showErrors(panelId, errors) {
    const panel = document.getElementById(`rfy-panel-${panelId}`);
    if (!panel) return;
    // Clear old errors
    panel.querySelectorAll('.rfy-field-error').forEach(el => el.remove());
    panel.querySelectorAll('.auth-input.error').forEach(el => el.classList.remove('error'));

    Object.entries(errors).forEach(([field, errs]) => {
      const inp = panel.querySelector(`[name="${field}"]`);
      if (inp) {
        inp.classList.add('error');
        const errEl = document.createElement('div');
        errEl.className = 'rfy-field-error';
        errEl.innerHTML = `<i class="bi bi-exclamation-circle"></i> ${errs[0]?.message || errs[0]}`;
        inp.closest('.rfy-field')?.appendChild(errEl);
      }
    });

    // General error
    if (errors.__all__) {
      const errBanner = panel.querySelector('.rfy-general-error');
      if (errBanner) {
        errBanner.textContent = errors.__all__[0]?.message || errors.__all__[0];
        errBanner.style.display = 'flex';
      }
    }
  }

  /* ── AJAX submit ── */
  async function submitForm(formEl, panelId) {
    const btn = formEl.querySelector('.rfy-submit');
    btn.classList.add('loading');
    btn.disabled = true;

    // Clear old errors and general error banner first
    const panel = document.getElementById(`rfy-panel-${panelId}`);
    if (panel) {
      panel.querySelectorAll('.rfy-field-error').forEach(el => el.remove());
      panel.querySelectorAll('.auth-input.error').forEach(el => el.classList.remove('error'));
      const errBanner = panel.querySelector('.rfy-general-error');
      if (errBanner) {
        errBanner.style.display = 'none';
      }
    }

    const apiUrl = formEl.action;
    const data = new FormData(formEl);
    if (returnUrl) data.set('next', returnUrl);
    const payload = Object.fromEntries(data.entries());

    if (panelId === 'register') {
      console.log("Registration request:", payload);
      console.log("API URL:", apiUrl);
    }

    try {
      const csrfToken = formEl.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
      const resp = await fetch(apiUrl, {
        method: 'POST',
        headers: { 
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrfToken
        },
        credentials: 'same-origin',
        body: data,
      });

      // Handle non-200 responses
      if (!resp.ok) {
        const contentType = resp.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          const json = await resp.json();
          if (json.errors) {
            showErrors(panelId, json.errors);
            
            // Map validation errors to specific messages
            let toastMsg = 'Please check your details and try again.';
            
            if (json.errors.email) {
              const msg = (json.errors.email[0]?.message || json.errors.email[0] || '').toLowerCase();
              if (msg.includes('already exists') || msg.includes('registered')) {
                toastMsg = 'Email already exists';
              } else if (msg.includes('valid')) {
                toastMsg = 'Invalid email';
              }
            }
            if (json.errors.username) {
              const msg = (json.errors.username[0]?.message || json.errors.username[0] || '').toLowerCase();
              if (msg.includes('already taken') || msg.includes('exists') || msg.includes('registered')) {
                toastMsg = 'Username already taken';
              }
            }
            if (json.errors.password1 || json.errors.password2) {
              const msg = ((json.errors.password1?.[0]?.message || json.errors.password1?.[0] || '') +
                           (json.errors.password2?.[0]?.message || json.errors.password2?.[0] || '')).toLowerCase();
              if (msg.includes('short') || msg.includes('common') || msg.includes('weak') || msg.includes('numeric') || msg.includes('entirely')) {
                toastMsg = 'Password too weak';
              }
            }
            
            toast(toastMsg, 'error');
            return;
          } else {
            const errBanner = panel?.querySelector('.rfy-general-error') || formEl.querySelector('.rfy-general-error');
            const span = errBanner?.querySelector('span');
            const errMsg = json.error || 'Something went wrong. Please try again.';
            if (errBanner) {
              if (span) span.textContent = errMsg;
              else errBanner.textContent = errMsg;
              errBanner.style.display = 'flex';
            }
            toast(errMsg, 'error');
            return;
          }
        } else {
          // Non-JSON error from server (e.g. 500 HTML or 503)
          console.error("Server error response code:", resp.status);
          const errBanner = panel?.querySelector('.rfy-general-error') || formEl.querySelector('.rfy-general-error');
          const span = errBanner?.querySelector('span');
          const errMsg = "Cannot connect to server. Please check backend configuration.";
          if (errBanner) {
            if (span) span.textContent = errMsg;
            else errBanner.textContent = errMsg;
            errBanner.style.display = 'flex';
          }
          toast('Server unavailable', 'error');
          return;
        }
      }

      // 200 OK Response
      const json = await resp.json();

      if (json.ok) {
        if (window.rfyClearAuth) window.rfyClearAuth();
        // Show success tick briefly then redirect
        const formInner = panel?.querySelector('.rfy-form-inner');
        const successEl = panel?.querySelector('.rfy-success-state');
        if (formInner) formInner.style.display = 'none';
        if (successEl) successEl.style.display = 'block';
        setTimeout(() => { window.location.href = json.redirect || returnUrl || window.location.href; }, 900);
      } else {
        if (json.errors) {
          showErrors(panelId, json.errors);
        } else {
          const errBanner = panel?.querySelector('.rfy-general-error') || formEl.querySelector('.rfy-general-error');
          const span = errBanner?.querySelector('span');
          const errMsg = json.error || 'Something went wrong. Please try again.';
          if (errBanner) {
            if (span) span.textContent = errMsg;
            else errBanner.textContent = errMsg;
            errBanner.style.display = 'flex';
          }
          toast(errMsg, 'error');
        }
      }
    } catch (e) {
      console.error("Fetch request failed:", e);
      // Connection failed / server unavailable
      const errBanner = panel?.querySelector('.rfy-general-error') || formEl.querySelector('.rfy-general-error');
      const span = errBanner?.querySelector('span');
      const errMsg = "Cannot connect to server. Please check backend configuration.";
      if (errBanner) {
        if (span) span.textContent = errMsg;
        else errBanner.textContent = errMsg;
        errBanner.style.display = 'flex';
      }
      toast('Connection failed', 'error');
    } finally {
      btn.classList.remove('loading');
      btn.disabled = false;
    }
  }

  /* ── Real-time availability check ── */
  let checkTimers = {};
  function checkField(inp, field) {
    clearTimeout(checkTimers[field]);
    const val = inp.value.trim();
    if (!val || val.length < 3) return;

    checkTimers[field] = setTimeout(async () => {
      try {
        const r = await fetch(`/accounts/check/?field=${field}&value=${encodeURIComponent(val)}`);
        const d = await r.json();
        // Remove old hint
        inp.closest('.rfy-field')?.querySelector('.rfy-avail-hint')?.remove();
        const hint = document.createElement('div');
        hint.className = 'rfy-avail-hint rfy-field-hint';

        if (d.available) {
          hint.style.color = '#16A34A';
          hint.innerHTML = `<i class="bi bi-check-circle-fill"></i> ${field === 'email' ? 'Email' : 'Username'} is available`;
          inp.classList.remove('error'); inp.classList.add('success');
        } else {
          hint.style.color = '#EF4444';
          hint.innerHTML = `<i class="bi bi-x-circle-fill"></i> ${field === 'email' ? 'Email already registered' : 'Username taken'}`;
          inp.classList.add('error'); inp.classList.remove('success');
        }
        inp.closest('.rfy-field')?.appendChild(hint);
      } catch (e) {}
    }, 500);
  }

  /* ── Init ── */
  document.addEventListener('DOMContentLoaded', () => {

    overlay = document.getElementById('rfyAuthModal');
    if (!overlay) return;

    modal = overlay.querySelector('.rfy-modal');

    /* Close on backdrop click */
    overlay.addEventListener('click', e => {
      if (e.target === overlay) closeModal();
    });

    /* Close buttons */
    overlay.querySelectorAll('.rfy-modal-close').forEach(btn =>
      btn.addEventListener('click', closeModal)
    );

    /* Escape key */
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && overlay.classList.contains('open')) closeModal();
    });

    /* Tab buttons */
    overlay.querySelectorAll('.rfy-tab').forEach(tab => {
      tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    /* "data-modal" triggers everywhere on the page */
    document.querySelectorAll('[data-modal]').forEach(el => {
      el.addEventListener('click', e => {
        e.preventDefault();
        openModal(el.dataset.modal);
      });
    });

    /* Tab switch links inside modal */
    overlay.querySelectorAll('[data-switch-tab]').forEach(el => {
      el.addEventListener('click', e => {
        e.preventDefault();
        switchTab(el.dataset.switchTab);
      });
    });

    /* Password show/hide */
    overlay.querySelectorAll('.rfy-eye-btn').forEach(btn => {
      btn.addEventListener('click', () => togglePwd(btn));
    });

    /* Password strength */
    overlay.querySelectorAll('[data-strength]').forEach(inp => {
      inp.addEventListener('input', () => updateStrength(inp));
    });

    /* AJAX form submit */
    ['login', 'register'].forEach(panelId => {
      const form = overlay.querySelector(`#rfy-panel-${panelId} form`);
      if (!form) return;
      form.addEventListener('submit', e => {
        e.preventDefault();
        submitForm(form, panelId);
      });
    });

    /* Real-time checks for register */
    const usernameInp = overlay.querySelector('#reg-username');
    const emailInp    = overlay.querySelector('#reg-email');
    if (usernameInp) usernameInp.addEventListener('input', () => checkField(usernameInp, 'username'));
    if (emailInp)    emailInp.addEventListener('input',    () => checkField(emailInp, 'email'));

    /* Expose globally so nav buttons work */
    window.rfyOpenModal  = openModal;
    window.rfyCloseModal = closeModal;
  });

})();
