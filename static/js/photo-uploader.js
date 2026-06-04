'use strict';

/**
 * Rentify photo uploader — create (in-memory) + edit (server images).
 */
(function () {
  const MAX = 5;

  function csrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function initUploader(root) {
    const mode = root.dataset.mode || 'create';
    const productId = root.dataset.productId || '';
    const grid = root.querySelector('.rfy-photo-grid');
    const hiddenWrap = root.querySelector('.rfy-photo-hidden-inputs');
    const picker = root.querySelector('.rfy-photo-picker');
    const viewer = document.getElementById('rfyPhotoViewer');
    const viewerImg = viewer?.querySelector('img');
    const viewerClose = viewer?.querySelector('.rfy-photo-viewer-close');

    /** @type {{id?:number, file?:File, url:string, isCover:boolean, server?:boolean}[]} */
    let photos = [];

    if (mode === 'edit') {
      const jsonEl = root.querySelector('.rfy-photo-existing-json');
      try {
        const raw = jsonEl ? jsonEl.textContent : '[]';
        photos = JSON.parse(raw).map((p) => ({
          id: p.id,
          url: p.url,
          isCover: !!p.isCover,
          server: true,
        }));
      } catch (e) {
        photos = [];
      }
    }

    function coverIndex() {
      const i = photos.findIndex((p) => p.isCover);
      return i >= 0 ? i : 0;
    }

    function setCover(idx) {
      photos.forEach((p, i) => { p.isCover = i === idx; });
      if (mode === 'edit' && photos[idx]?.server && photos[idx].id) {
        fetch(`/listings/images/${photos[idx].id}/set-cover/`, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrf(),
          },
        }).catch(() => {});
      }
      render();
    }

    function removeAt(idx) {
      const p = photos[idx];
      if (!p) return;

      const doRemove = () => {
        if (p.url && p.url.startsWith('blob:')) URL.revokeObjectURL(p.url);
        photos.splice(idx, 1);
        if (photos.length && !photos.some((x) => x.isCover)) {
          photos[0].isCover = true;
        }
        render();
        syncHiddenInputs();
      };

      if (mode === 'edit' && p.server && p.id) {
        fetch(`/listings/images/${p.id}/delete/`, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrf(),
          },
        })
          .then((r) => r.json())
          .then((d) => {
            if (d.ok) {
              if (d.primary_id) {
                photos.forEach((ph) => {
                  ph.isCover = ph.id === d.primary_id;
                });
              }
              doRemove();
            }
          })
          .catch(doRemove);
      } else {
        doRemove();
      }
    }

    function addFiles(fileList) {
      const room = MAX - photos.length;
      if (room <= 0) return;
      Array.from(fileList)
        .slice(0, room)
        .forEach((file) => {
          if (!file.type.startsWith('image/')) return;
          const url = URL.createObjectURL(file);
          photos.push({
            file,
            url,
            isCover: photos.length === 0,
            server: false,
          });
        });
      if (photos.length && !photos.some((p) => p.isCover)) {
        photos[0].isCover = true;
      }
      render();
      syncHiddenInputs();
    }

    function syncHiddenInputs() {
      if (!hiddenWrap) return;
      hiddenWrap.innerHTML = '';
      const local = photos.filter((p) => p.file);
      local.forEach((p, i) => {
        const inp = document.createElement('input');
        inp.type = 'file';
        inp.name = `image_${i}`;
        inp.hidden = true;
        const dt = new DataTransfer();
        dt.items.add(p.file);
        inp.files = dt.files;
        hiddenWrap.appendChild(inp);
      });
    }

    function openViewer(url) {
      if (!viewer || !viewerImg) return;
      viewerImg.src = url;
      viewer.classList.add('open');
      document.body.style.overflow = 'hidden';
    }

    function closeViewer() {
      viewer?.classList.remove('open');
      document.body.style.overflow = '';
    }

    viewerClose?.addEventListener('click', closeViewer);
    viewer?.addEventListener('click', (e) => {
      if (e.target === viewer) closeViewer();
    });

    function render() {
      grid.innerHTML = '';
      const ordered = [...photos].sort((a, b) => (b.isCover ? 1 : 0) - (a.isCover ? 1 : 0));
      ordered.forEach((p) => {
        const idx = photos.indexOf(p);
        const el = document.createElement('div');
        el.className = 'rfy-photo-item has-image' + (p.isCover ? ' is-cover' : '');
        el.innerHTML = `
          <img src="${p.url}" alt="" class="${p.isCover ? 'photo-cover-preview' : ''}">
          <span class="rfy-photo-cover-badge"><i class="bi bi-star-fill"></i> Cover Photo</span>
          <div class="rfy-photo-overlay">
            ${!p.isCover ? `<button type="button" class="rfy-photo-act" data-act="cover"><i class="bi bi-star"></i> Set as Cover</button>` : ''}
            <button type="button" class="rfy-photo-act" data-act="view"><i class="bi bi-eye"></i> View</button>
            <button type="button" class="rfy-photo-act" data-act="change"><i class="bi bi-arrow-repeat"></i> Change</button>
            <button type="button" class="rfy-photo-act rfy-photo-act--danger" data-act="remove"><i class="bi bi-trash3"></i> Remove</button>
          </div>`;
        el.querySelector('[data-act="cover"]')?.addEventListener('click', (e) => {
          e.preventDefault();
          setCover(idx);
        });
        el.querySelector('[data-act="view"]')?.addEventListener('click', (e) => {
          e.preventDefault();
          openViewer(p.url);
        });
        el.querySelector('[data-act="change"]')?.addEventListener('click', (e) => {
          e.preventDefault();
          const inp = document.createElement('input');
          inp.type = 'file';
          inp.accept = 'image/*';
          inp.onchange = () => {
            const f = inp.files[0];
            if (!f) return;
            if (p.url.startsWith('blob:')) URL.revokeObjectURL(p.url);
            if (mode === 'edit' && p.server && p.id) {
              removeAt(idx);
              addFiles([f]);
              return;
            }
            p.file = f;
            p.url = URL.createObjectURL(f);
            render();
            syncHiddenInputs();
          };
          inp.click();
        });
        el.querySelector('[data-act="remove"]')?.addEventListener('click', (e) => {
          e.preventDefault();
          removeAt(idx);
        });
        grid.appendChild(el);
      });

      if (photos.length < MAX) {
        const add = document.createElement('div');
        add.className = 'rfy-photo-item';
        add.innerHTML = `
          <label class="rfy-photo-add">
            <i class="bi bi-plus-lg"></i>
            <span>Add Photo</span>
            <input type="file" accept="image/*" multiple hidden>
          </label>`;
        const inp = add.querySelector('input');
        inp.addEventListener('change', () => {
          if (inp.files?.length) addFiles(inp.files);
          inp.value = '';
        });
        grid.appendChild(add);
      }
    }

    picker?.addEventListener('change', () => {
      if (picker.files?.length) addFiles(picker.files);
      picker.value = '';
    });

    render();
    syncHiddenInputs();
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.rfy-photo-uploader').forEach(initUploader);
  });
})();
