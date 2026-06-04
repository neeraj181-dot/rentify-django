'use strict';

/**
 * Rentify location picker — geolocation, search, session + localStorage sync.
 */
(function () {
  const STORAGE_KEY = 'rfy-location';
  let popularData = [];
  let selectedCity = '';
  let searchTimer = null;

  function csrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function updateAllLabels(city) {
    document.querySelectorAll('.loc-label').forEach((el) => {
      el.textContent = city || 'Select city';
    });
    document.querySelectorAll('#navLocationField, input[name="location"][data-nav-loc]').forEach((inp) => {
      inp.value = city || '';
    });
  }

  function highlightSelected(root) {
    root.querySelectorAll('.loc-preset').forEach((row) => {
      row.classList.toggle('is-selected', (row.dataset.city || '') === selectedCity);
    });
  }

  function renderPopular(list, root) {
    const wrap = root.querySelector('.loc-popular-list');
    if (!wrap) return;
    if (!list.length) {
      wrap.innerHTML = '<div class="loc-empty">No listings in popular cities yet</div>';
      return;
    }
    wrap.innerHTML = list.map(({ city, count }) => `
      <button type="button" class="loc-preset" data-city="${escapeAttr(city)}">
        <i class="bi bi-geo-alt"></i>
        <span class="loc-preset-name">${escapeHtml(city)}</span>
        <span class="loc-preset-count">${count}</span>
      </button>`).join('');
    bindPresetClicks(wrap);
    highlightSelected(root);
  }

  function renderSearch(list, root) {
    const wrap = root.querySelector('.loc-search-results');
    const outer = root.querySelector('.loc-search-results-wrap');
    if (!wrap || !outer) return;
    if (!list.length) {
      wrap.innerHTML = '<div class="loc-empty">No matching cities</div>';
      outer.style.display = 'block';
      return;
    }
    wrap.innerHTML = list.map(({ city, count }) => `
      <button type="button" class="loc-preset" data-city="${escapeAttr(city)}">
        <i class="bi bi-geo-alt"></i>
        <span class="loc-preset-name">${escapeHtml(city)}</span>
        <span class="loc-preset-count">${count}</span>
      </button>`).join('');
    bindPresetClicks(wrap);
    outer.style.display = 'block';
    highlightSelected(root);
  }

  function bindPresetClicks(container) {
    container.querySelectorAll('.loc-preset').forEach((btn) => {
      btn.addEventListener('click', () => selectCity(btn.dataset.city));
    });
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function escapeAttr(s) {
    return escapeHtml(s).replace(/"/g, '&quot;');
  }

  async function syncSession(city) {
    try {
      await fetch('/listings/api/set-location/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrf(),
        },
        body: JSON.stringify({ location: city || '' }),
      });
    } catch (e) { /* best-effort */ }
  }

  function browseUrl(city) {
    const path = window.location.pathname;
    const url = new URL(window.location.href);
    if (city) url.searchParams.set('location', city);
    else url.searchParams.delete('location');
    if (path === '/' || path.startsWith('/browse') || path.startsWith('/search') || path.includes('/category/')) {
      if (path === '/') return '/browse/' + (city ? '?location=' + encodeURIComponent(city) : '');
      return url.pathname + url.search;
    }
    return '/browse/' + (city ? '?location=' + encodeURIComponent(city) : '');
  }

  async function selectCity(city, options = {}) {
    const { reload = true } = options;
    selectedCity = city || '';
    if (city) localStorage.setItem(STORAGE_KEY, city);
    else localStorage.removeItem(STORAGE_KEY);
    updateAllLabels(city);
    document.querySelectorAll('.loc-dropdown').forEach((d) => d.classList.remove('open'));
    document.querySelectorAll('.rfy-loc').forEach((r) => highlightSelected(r));
    await syncSession(city);
    if (reload) window.location.href = browseUrl(city);
  }

  window.setLocation = (name) => selectCity(name);

  function detectLocation(btn) {
    const status = btn?.querySelector('.loc-gps-status') || btn?.parentElement?.querySelector('.loc-gps-status');
    if (!navigator.geolocation) {
      if (status) status.textContent = 'Not supported';
      return;
    }
    if (btn) btn.disabled = true;
    if (status) status.textContent = 'Detecting…';

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const r = await fetch(
            `/listings/api/reverse-geocode/?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}`,
            { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } }
          );
          const d = await r.json();
          if (!r.ok || !d.city) throw new Error(d.error || 'Geocode failed');
          if (status) status.textContent = 'Found!';
          await selectCity(d.city);
        } catch (err) {
          if (status) status.textContent = 'Pick manually';
          if (btn) btn.disabled = false;
        }
      },
      () => {
        if (status) status.textContent = 'Denied — pick a city';
        if (btn) btn.disabled = false;
      },
      { enableHighAccuracy: false, timeout: 12000, maximumAge: 300000 }
    );
  }

  window.detectLocation = () => {
    const btn = document.querySelector('.loc-use-gps');
    detectLocation(btn);
  };

  async function loadLocations(q, root) {
    try {
      const r = await fetch('/listings/api/locations/?q=' + encodeURIComponent(q || ''), {
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      const d = await r.json();
      if (!q) {
        popularData = d.popular || [];
        document.querySelectorAll('.rfy-loc').forEach((locRoot) => renderPopular(popularData, locRoot));
      } else if (root) {
        renderSearch(d.results || [], root);
      }
      selectedCity = d.selected || localStorage.getItem(STORAGE_KEY) || '';
      document.querySelectorAll('.rfy-loc').forEach(highlightSelected);
    } catch (e) {
      document.querySelectorAll('.loc-popular-list').forEach((wrap) => {
        wrap.innerHTML = '<div class="loc-empty">Could not load cities</div>';
      });
    }
  }

  function initWidget(locRoot) {
    const searchInp = locRoot.querySelector('.loc-search-input');
    searchInp?.addEventListener('input', () => {
      clearTimeout(searchTimer);
      const q = searchInp.value.trim();
      searchTimer = setTimeout(() => {
        const resultsWrap = locRoot.querySelector('.loc-search-results-wrap');
        if (!q) {
          if (resultsWrap) resultsWrap.style.display = 'none';
          renderPopular(popularData, locRoot);
        } else {
          loadLocations(q, locRoot);
        }
      }, 220);
    });

    locRoot.querySelector('.loc-use-gps')?.addEventListener('click', (e) => {
      e.stopPropagation();
      detectLocation(e.currentTarget);
    });

    locRoot.querySelector('.loc-clear')?.addEventListener('click', (e) => {
      e.stopPropagation();
      selectCity('');
    });
  }

  async function init() {
    const saved = localStorage.getItem(STORAGE_KEY);
    const serverCity = (document.querySelector('.loc-label')?.textContent || '').trim();
    const validServer = serverCity && serverCity !== 'Select city' && serverCity !== 'India';

    if (saved && saved !== validServer) {
      updateAllLabels(saved);
      await syncSession(saved);
      selectedCity = saved;
    } else if (validServer) {
      selectedCity = serverCity;
      localStorage.setItem(STORAGE_KEY, serverCity);
    } else if (saved) {
      updateAllLabels(saved);
      selectedCity = saved;
    }

    await loadLocations('');
    document.querySelectorAll('.rfy-loc').forEach(initWidget);
  }

  document.addEventListener('DOMContentLoaded', init);
})();
