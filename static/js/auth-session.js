/* Rentify — server-validated session (Django). Never trust localStorage for auth. */
'use strict';

(function () {
  const AUTH_KEYS = [
    'rentify_token', 'rfy-access-token', 'rfy-refresh-token',
    'rfy-user', 'rfy_user', 'access_token', 'refresh_token',
    'authToken', 'user', 'rentify_user', 'rentify_auth',
  ];

  function getCsrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function clearAuthStorage() {
    AUTH_KEYS.forEach((k) => {
      try {
        localStorage.removeItem(k);
        sessionStorage.removeItem(k);
      } catch (e) { /* private mode */ }
    });
  }

  function setVerifying(on) {
    document.documentElement.classList.toggle('auth-verifying', on);
    if (on) document.documentElement.classList.remove('auth-ready');
  }

  async function verifySession() {
    setVerifying(true);
    clearAuthStorage();

    const serverAuthed = document.body?.dataset.serverAuth === 'true';

    try {
      const resp = await fetch('/accounts/api/session/', {
        method: 'GET',
        credentials: 'same-origin',
        headers: { Accept: 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
      });

      if (!resp.ok) {
        clearAuthStorage();
        if (serverAuthed) {
          await forceLogoutAndReload();
        }
        return;
      }

      const data = await resp.json();

      if (!data.authenticated) {
        clearAuthStorage();
        sessionStorage.removeItem('rfy-session-verified');
        if (serverAuthed) {
          await forceLogoutAndReload();
        }
        return;
      }

      sessionStorage.setItem('rfy-session-verified', '1');
      window.dispatchEvent(new CustomEvent('rentify:auth', { detail: data }));
    } catch (err) {
      console.warn('Rentify auth verification failed:', err);
      clearAuthStorage();
    } finally {
      setVerifying(false);
      document.documentElement.classList.add('auth-ready');
    }
  }

  async function forceLogoutAndReload() {
    try {
      await fetch('/accounts/api/logout/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCsrf(),
        },
      });
    } catch (e) { /* still reload */ }
    clearAuthStorage();
    window.location.reload();
  }

  document.addEventListener('DOMContentLoaded', verifySession);

  window.rfyClearAuth = clearAuthStorage;
  window.rfyLogout = async function () {
    clearAuthStorage();
    try {
      await fetch('/accounts/api/logout/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCsrf(),
        },
      });
    } catch (e) { /* fall through */ }
    window.location.href = '/';
  };
})();
