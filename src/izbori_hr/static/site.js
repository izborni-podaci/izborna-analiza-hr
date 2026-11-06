/* Filters and sorting for the tables and the list of flagged stations, and the theme. The pages work without it. */
(() => {
  const fold = (s) => String(s).toLowerCase().replace(/đ/g, 'dj').normalize('NFD').replace(/[̀-ͯ]/g, '');
  const lang = document.documentElement.lang || 'hr';
  const fmt = new Intl.NumberFormat(lang === 'en' ? 'en' : 'hr');

  // On a phone the navigation rows scroll sideways: start with the current page's link in view.
  document.querySelectorAll('.round-nav, .main-nav').forEach((nav) => {
    const here = nav.querySelector('[aria-current]');
    if (here && nav.scrollWidth > nav.clientWidth) {
      nav.scrollLeft = Math.max(0, here.offsetLeft - nav.offsetLeft - (nav.clientWidth - here.offsetWidth) / 2);
    }
  });

  // Light or dark, remembered on this device; until chosen, the system's setting decides.
  const toggle = document.querySelector('[data-theme-toggle]');
  if (toggle) {
    const root = document.documentElement;
    const isDark = () => (root.dataset.theme
      ? root.dataset.theme === 'dark'
      : window.matchMedia('(prefers-color-scheme: dark)').matches);
    const label = () => { toggle.textContent = isDark() ? toggle.dataset.light : toggle.dataset.dark; };
    toggle.hidden = false;
    label();
    toggle.addEventListener('click', () => {
      root.dataset.theme = isDark() ? 'light' : 'dark';
      try { localStorage.setItem('theme', root.dataset.theme); } catch (e) { /* private window: this page only */ }
      label();
    });
  }

  // Search on the home page: municipalities and polling places from search.json, loaded on first use. Every result
  // opens its page across all elections.
  const search = document.querySelector('form[data-search]');
  if (search) {
    const input = search.querySelector('input');
    const out = search.querySelector('[data-search-results]');
    const base = search.dataset.base || '';
    const placeBase = search.dataset.placeBase || base;  // the places' pages are Croatian only
    let items = null;
    let loading = null;
    let hits = [];
    const load = () => {
      if (!loading) {
        loading = fetch(search.dataset.index)
          .then((r) => r.json())
          .then((j) => {
            const d = search.dataset;
            // [folded label, folded label with former numbers, [label, url, sub-line]]
            const mun = j.m.map((m) => {
              const f = fold(m[0]);
              return [f, f, [m[0], `${base}m/${m[1]}.html`, d.munSub.replace('{n}', m[2])]];
            });
            const st = j.s.map((s) => {
              const m = j.m[s[0]];
              const label = `${m[0]} · ${d.bm} ${s[1]}${s[2] ? ` · ${s[2]}` : ''}`;
              let sub = (s[4] ? d.flagged.replace('{k}', s[4]) : d.clean).replace('{n}', s[5]);
              if (s[6]) sub += ` · ${d.former.replace('{n}', s[6])}`;
              const f = fold(label);
              return [f, s[6] ? `${f} ${fold(`${d.bm} ${s[6]}`)}` : f, [label, `${placeBase}s/${s[3]}.html`, sub]];
            });
            items = mun.concat(st);
          })
          .catch(() => { items = []; });
      }
      return loading;
    };
    const render = () => {
      out.textContent = '';
      const q = fold(input.value.trim());
      if (!q || !items) return;
      const words = q.split(/\s+/);
      const numbers = words.filter((w) => /^\d+$/.test(w));
      hits = items.filter(([, f]) => words.every((w) => f.includes(w)));
      if (numbers.length) {  // "split 25": station 25 before 125 and 250, and before a place that used to be 25
        const exact = (f) => numbers.every((n) => new RegExp(`(^|\\D)${n}(\\D|$)`).test(f));
        const rank = ([now, all]) => (exact(now) ? 0 : exact(all) ? 1 : 2);
        hits = hits.map((h, i) => [rank(h), i, h]).sort((a, b) => a[0] - b[0] || a[1] - b[1]).map((x) => x[2]);
      }
      hits = hits.slice(0, 12);
      if (!hits.length) {
        const p = document.createElement('p');
        p.textContent = out.dataset.none;
        out.append(p);
        return;
      }
      const ul = document.createElement('ul');
      hits.forEach(([, , it]) => {
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = it[1];
        a.textContent = it[0];
        li.append(a);
        if (it[2]) {
          const s = document.createElement('span');
          s.className = 'small muted';
          s.textContent = it[2];
          li.append(s);
        }
        ul.append(li);
      });
      out.append(ul);
    };
    input.addEventListener('focus', load, { once: true });
    input.addEventListener('input', () => { load().then(render); });
    search.addEventListener('submit', (e) => {
      e.preventDefault();
      load().then(() => {
        render();
        if (hits.length) location.href = hits[0][2][1];
      });
    });
    if (location.hash === '#pretraga') input.focus();
  }

  document.querySelectorAll('input[data-filter]').forEach((input) => {
    const table = document.querySelector(input.dataset.filter);
    if (!table) return;
    const rows = [...table.tBodies[0].rows];
    const texts = rows.map((r) => fold(r.dataset.text || r.textContent));
    input.addEventListener('input', () => {
      const q = fold(input.value.trim());
      rows.forEach((r, i) => { r.hidden = Boolean(q) && !texts[i].includes(q); });
    });
  });

  // The flagged stations: by constituency, kind of check, municipality and text. #sum_mismatch picks a kind of
  // check, #c-IV a constituency, #m-14-osijek a municipality (links from the other pages).
  document.querySelectorAll('form[data-filter-cards]').forEach((form) => {
    const box = document.querySelector(form.dataset.filterCards);
    if (!box) return;
    const cards = [...box.querySelectorAll('.card')];
    const texts = cards.map((c) => fold(c.dataset.text || ''));
    const f = (n) => form.querySelector(`[data-f="${n}"]`);
    const out = form.querySelector('output');
    const inGroup = {};
    f('type').querySelectorAll('optgroup[data-g]').forEach((og) => {
      inGroup[`g-${og.dataset.g}`] = [...og.querySelectorAll('option')].map((o) => o.value)
        .filter((v) => !v.startsWith('g-'));
    });
    const has = (card, ty) => {
      const types = card.dataset.types.split(' ');
      return inGroup[ty] ? types.some((x) => inGroup[ty].includes(x)) : types.includes(ty);
    };
    const apply = () => {
      const contest = f('contest') ? f('contest').value : '';
      const ty = f('type').value;
      const m = f('mun').value;
      const q = fold(f('q').value.trim());
      let shown = 0;
      cards.forEach((c, i) => {
        const ok = (!contest || c.dataset.contest === contest) && (!ty || has(c, ty))
          && (!m || c.dataset.mun === m) && (!q || texts[i].includes(q));
        c.hidden = !ok;
        if (ok) shown += 1;
      });
      if (out) out.textContent = out.dataset.shown.replace('{n}', fmt.format(shown));
    };
    ['contest', 'type', 'mun'].forEach((n) => { if (f(n)) f(n).addEventListener('change', apply); });
    f('q').addEventListener('input', apply);
    const wanted = decodeURIComponent(location.hash.slice(1));
    const pick = (sel, value) => {
      if (sel && [...sel.options].some((o) => o.value === value)) { sel.value = value; return true; }
      return false;
    };
    if (wanted.startsWith('c-')) pick(f('contest'), wanted.slice(2));
    else if (wanted.startsWith('m-')) pick(f('mun'), wanted.slice(2));
    else if (wanted) pick(f('type'), wanted);
    apply();
  });

  // Click a column header marked data-sort: largest first, click again for smallest first.
  document.querySelectorAll('table').forEach((table) => {
    const heads = [...table.querySelectorAll('thead th')];
    heads.forEach((th, col) => {
      if (!th.hasAttribute('data-sort')) return;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'sort';
      button.append(...th.childNodes);
      th.append(button);
      button.addEventListener('click', () => {
        const desc = th.getAttribute('aria-sort') !== 'descending';
        heads.forEach((h) => h.removeAttribute('aria-sort'));
        th.setAttribute('aria-sort', desc ? 'descending' : 'ascending');
        const body = table.tBodies[0];
        const value = (r) => {
          const v = parseFloat(r.cells[col]?.dataset.v);
          return Number.isNaN(v) ? null : v;
        };
        const rows = [...body.rows].filter((r) => !r.classList.contains('total'));
        rows.sort((a, b) => {
          const x = value(a);
          const y = value(b);
          if (x === null || y === null) return (x === null) - (y === null);  // empty values last
          return desc ? y - x : x - y;
        });
        body.prepend(...rows);
      });
    });
  });
})();
