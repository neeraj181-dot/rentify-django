/** City suggestions by state + prevent duplicate form submit (PRG helper). */
(function () {
  const citiesByState = window.RFY_CITIES_BY_STATE || {};
  const stateEl = document.getElementById('id_state');
  const cityEl = document.getElementById('id_city');
  const datalist = document.getElementById('rfy-city-suggestions');

  function refreshCitySuggestions() {
    if (!stateEl || !cityEl || !datalist) return;
    const state = stateEl.value;
    const cities = citiesByState[state] || [];
    datalist.innerHTML = cities.map((c) => `<option value="${c}">`).join('');
    cityEl.setAttribute('list', cities.length ? 'rfy-city-suggestions' : '');
  }

  stateEl?.addEventListener('change', refreshCitySuggestions);
  refreshCitySuggestions();

  const form = document.getElementById('listingForm');
  if (!form) return;

  form.addEventListener('submit', function () {
    const btn = form.querySelector('.listing-submit-btn');
    if (btn && !btn.classList.contains('is-submitting')) {
      btn.classList.add('is-submitting');
      btn.disabled = true;
      const icon = btn.querySelector('i');
      if (icon) {
        icon.className = 'bi bi-hourglass-split';
      }
    }
  });
})();
