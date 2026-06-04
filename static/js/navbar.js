/* Rentify shared navbar interactions */
(function () {
  function toggleDD(id) {
    const el = document.getElementById(id);
    if (!el) return;
    const open = el.classList.contains('open');
    document.querySelectorAll('.rfy-notif-dd,.rfy-user-dd,.loc-dropdown').forEach(d => d.classList.remove('open'));
    if (!open) el.classList.add('open');
  }
  window.toggleDD = toggleDD;

  document.addEventListener('click', () => {
    document.querySelectorAll('.rfy-notif-dd,.rfy-user-dd,.loc-dropdown').forEach(d => d.classList.remove('open'));
  });
  document.querySelectorAll('.rfy-notif-dd,.rfy-user-dd,.loc-dropdown').forEach(d => {
    d.addEventListener('click', e => e.stopPropagation());
  });

  const notifBtn = document.getElementById('notifBtn');
  if (notifBtn) notifBtn.addEventListener('click', e => { e.stopPropagation(); toggleDD('notifDD'); });

  const profileBtn = document.getElementById('profileBtn');
  if (profileBtn) profileBtn.addEventListener('click', e => { e.stopPropagation(); toggleDD('profileDD'); });

  const burger = document.getElementById('burgerBtn');
  const mMenu = document.getElementById('mobileMenu');
  if (burger && mMenu) {
    burger.addEventListener('click', () => mMenu.classList.add('open'));
  }
  window.closeMobileMenu = () => { if (mMenu) mMenu.classList.remove('open'); };

  const nav = document.getElementById('mainNav');
  if (nav && nav.classList.contains('nav-visitor') && document.body.classList.contains('page-home')) {
    const onScroll = () => nav.classList.toggle('solid', window.scrollY > 30);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  document.querySelectorAll('.rfy-loc').forEach(btn => {
    const dd = btn.querySelector('.loc-dropdown');
    if (!dd?.id) return;
    btn.addEventListener('click', e => {
      e.stopPropagation();
      toggleDD(dd.id);
    });
  });

  if (!window.wlToggle) {
    window.wlToggle = function (btn) {
      const pid = btn.dataset.pid;
      fetch('/wishlist/toggle/' + pid + '/', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin'
      }).then(r => r.json()).then(d => {
        const i = btn.querySelector('i');
        if (d.in_wishlist) {
          btn.classList.add('on');
          if (i) { i.className = 'bi bi-heart-fill'; i.style.color = '#FF5272'; }
        } else {
          btn.classList.remove('on');
          if (i) { i.className = 'bi bi-heart'; i.style.color = ''; }
        }
      }).catch(() => { if (window.rfyOpenModal) window.rfyOpenModal('login'); });
    };
  }
})();
