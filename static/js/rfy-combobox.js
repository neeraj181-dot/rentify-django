'use strict';

/**
 * Searchable category select + location autocomplete comboboxes.
 */
(function () {
  function initCategory(box) {
    const native = box.querySelector('select.rfy-combobox-native');
    if (!native) return;
    const trigger = box.querySelector('.rfy-combobox-trigger');
    const panel = box.querySelector('.rfy-combobox-panel');
    const list = box.querySelector('.rfy-combobox-list');
    const searchInp = box.querySelector('.rfy-combobox-search input');
    const labelEl = box.querySelector('.rfy-combobox-label');

    const options = Array.from(native.options)
      .filter((o) => o.value)
      .map((o) => ({
        value: o.value,
        label: o.textContent.trim(),
        icon: o.dataset.icon || 'bi-grid',
      }));

    function renderList(filter) {
      const q = (filter || '').toLowerCase();
      list.innerHTML = '';
      const filtered = options.filter(
        (o) => !q || o.label.toLowerCase().includes(q) || o.value.includes(q)
      );
      if (!filtered.length) {
        list.innerHTML = '<div class="rfy-combobox-empty">No categories found</div>';
        return;
      }
      filtered.forEach((o) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'rfy-combobox-option';
        if (native.value === o.value) btn.classList.add('is-active');
        btn.innerHTML = `<i class="bi ${o.icon}"></i><span class="rfy-combobox-option-label">${o.label}</span>`;
        btn.addEventListener('click', () => select(o));
        list.appendChild(btn);
      });
    }

    function select(o) {
      native.value = o.value;
      native.dispatchEvent(new Event('change', { bubbles: true }));
      labelEl.innerHTML = `<i class="bi ${o.icon} ico-left"></i><span>${o.label}</span>`;
      labelEl.classList.remove('placeholder');
      close();
    }

    function open() {
      box.classList.add('is-open');
      renderList(searchInp?.value || '');
      searchInp?.focus();
    }
    function close() {
      box.classList.remove('is-open');
    }

    trigger?.addEventListener('click', () => {
      box.classList.contains('is-open') ? close() : open();
    });
    searchInp?.addEventListener('input', () => renderList(searchInp.value));

    document.addEventListener('click', (e) => {
      if (!box.contains(e.target)) close();
    });

    const cur = options.find((o) => o.value === native.value);
    if (cur) {
      labelEl.innerHTML = `<i class="bi ${cur.icon} ico-left"></i><span>${cur.label}</span>`;
      labelEl.classList.remove('placeholder');
    } else {
      labelEl.innerHTML = '<span class="placeholder">Select category</span>';
    }
  }

  function initLocation(box) {
    const native = box.querySelector('input.rfy-combobox-native');
    if (!native) return;
    const trigger = box.querySelector('.rfy-combobox-trigger');
    const panel = box.querySelector('.rfy-combobox-panel');
    const list = box.querySelector('.rfy-combobox-list');
    const searchInp = box.querySelector('.rfy-combobox-search input');
    const labelEl = box.querySelector('.rfy-combobox-label');

    let locations = [];
    const globalLoc = document.getElementById('rfy-locations-data');
    if (globalLoc) {
      try { locations = JSON.parse(globalLoc.textContent); } catch (e) { locations = []; }
    } else {
      try { locations = JSON.parse(box.dataset.locations || '[]'); } catch (e) { locations = []; }
    }

    function syncLabel() {
      const v = native.value.trim();
      if (v) {
        labelEl.innerHTML = `<i class="bi bi-geo-alt-fill ico-left"></i><span>${v}</span>`;
        labelEl.classList.remove('placeholder');
      } else {
        labelEl.innerHTML = '<span class="placeholder">City or area</span>';
      }
    }

    function renderList(filter) {
      const q = (filter || '').toLowerCase();
      list.innerHTML = '';
      let filtered = locations.filter((loc) => !q || loc.toLowerCase().includes(q));
      if (q && !filtered.some((l) => l.toLowerCase() === q)) {
        const custom = document.createElement('button');
        custom.type = 'button';
        custom.className = 'rfy-combobox-option';
        custom.innerHTML = `<i class="bi bi-pencil"></i><span>Use "${filter}"</span>`;
        custom.addEventListener('click', () => pick(filter));
        list.appendChild(custom);
      }
      if (!filtered.length && !q) {
        list.innerHTML = '<div class="rfy-combobox-empty">Type to search locations</div>';
        return;
      }
      filtered.slice(0, 25).forEach((loc) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'rfy-combobox-option';
        btn.innerHTML = `<i class="bi bi-geo-alt"></i><span>${loc}</span>`;
        btn.addEventListener('click', () => pick(loc));
        list.appendChild(btn);
      });
    }

    function pick(val) {
      native.value = val;
      native.dispatchEvent(new Event('change', { bubbles: true }));
      syncLabel();
      close();
    }

    function open() {
      box.classList.add('is-open');
      if (searchInp) searchInp.value = native.value;
      renderList(searchInp?.value || '');
      searchInp?.focus();
    }
    function close() {
      box.classList.remove('is-open');
      if (searchInp) native.value = searchInp.value.trim();
      syncLabel();
    }

    trigger?.addEventListener('click', () => {
      box.classList.contains('is-open') ? close() : open();
    });
    searchInp?.addEventListener('input', () => {
      native.value = searchInp.value;
      renderList(searchInp.value);
    });
    searchInp?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        pick(searchInp.value.trim());
      }
    });

    document.addEventListener('click', (e) => {
      if (!box.contains(e.target)) close();
    });

    syncLabel();
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.rfy-combobox[data-type="category"]').forEach(initCategory);
    document.querySelectorAll('.rfy-combobox[data-type="location"]').forEach(initLocation);
  });
})();
