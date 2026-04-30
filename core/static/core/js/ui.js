/* ── Campeonato X2 — UI ──────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initMessages();
  initClassificationReveal();
  initKdBars();
  initTypeCards();
  initDuoSelectors();
  initFormSubmit();
});

/* ── Navbar mobile toggle ──────────────────────────────── */
function initNavbar() {
  const toggle = document.querySelector('.navbar__toggle');
  const links  = document.querySelector('.navbar__links');
  if (!toggle || !links) return;

  toggle.addEventListener('click', () => {
    const open = links.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(open));
  });
}

/* ── Auto-dismiss Django messages ─────────────────────── */
function initMessages() {
  document.querySelectorAll('.alert-msg').forEach(msg => {
    const close = msg.querySelector('.alert-msg__close');
    const dismiss = () => {
      msg.style.transition = `opacity 300ms`;
      msg.style.opacity = '0';
      setTimeout(() => msg.remove(), 300);
    };

    setTimeout(dismiss, 4000);
    if (close) close.addEventListener('click', dismiss);
  });
}

/* ── Classification table row reveal ─────────────────── */
function initClassificationReveal() {
  const rows = document.querySelectorAll('.cr');
  if (!rows.length) return;

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      rows.forEach(row => row.classList.add('is-visible'));
    });
  });
}

/* ── Player K/D progress bars ─────────────────────────── */
function initKdBars() {
  const cards = document.querySelectorAll('.player-card');
  if (!cards.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const bar = entry.target.querySelector('.kd-bar-fill');
      if (!bar) return;
      const kd = parseFloat(bar.dataset.kd) || 0;
      bar.style.width = Math.min((kd / 3.0) * 100, 100) + '%';
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.25 });

  cards.forEach(card => observer.observe(card));
}

/* ── Type card selector (Pontos Corridos / Mata Mata) ── */
function initTypeCards() {
  const cards   = document.querySelectorAll('.type-card');
  const notice  = document.getElementById('mm-notice');

  if (!cards.length) return;

  cards.forEach(card => {
    card.addEventListener('click', () => activateType(card.dataset.tipo));
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        activateType(card.dataset.tipo);
      }
    });
  });

  function activateType(tipo) {
    if (tipo === 'MATA_MATA') {
      showMataMataNota();
      return;
    }
    cards.forEach(c => {
      const isActive = c.dataset.tipo === tipo;
      c.classList.toggle('is-active', isActive);
      c.setAttribute('aria-checked', String(isActive));
    });
    if (notice) notice.classList.remove('is-visible');
  }

  function showMataMataNota() {
    if (!notice) return;
    notice.classList.add('is-visible');
    clearTimeout(notice._timer);
    notice._timer = setTimeout(() => notice.classList.remove('is-visible'), 3500);
  }
}

/* ── Duo selectors + player stats rendering ───────────── */
function initDuoSelectors() {
  const selects = document.querySelectorAll('[data-duo-select]');
  if (!selects.length) return;

  const duosData  = parseJsonScript('duos-data') || {};
  const prevStats = parseJsonScript('prev-stats-data') || {};

  selects.forEach(select => {
    const targetId = select.dataset.playersTarget;
    const target   = targetId ? document.getElementById(targetId) : null;
    const team     = select.dataset.team;
    const rowsEl   = team ? document.getElementById(`team${team}-rows`) : null;
    const nameEl   = team ? document.getElementById(`team${team}-name`) : null;
    const cardEl   = team ? document.querySelector(`[data-team-card="${team}"]`) : null;

    const update = () => {
      const duo = duosData[select.value];
      if (duo) {
        const sub = `${duo.j1.nome.toUpperCase()} · ${duo.j2.nome.toUpperCase()}`;
        if (target) {
          target.textContent = sub;
          target.classList.add('has-value');
        }
        if (nameEl) {
          const opt = select.options[select.selectedIndex];
          nameEl.textContent = opt ? opt.text : '—';
        }
        if (cardEl) cardEl.classList.add('is-active');
        if (rowsEl) renderStatRows(rowsEl, [duo.j1, duo.j2], prevStats);
      } else {
        if (target) {
          target.textContent = '';
          target.classList.remove('has-value');
        }
        if (nameEl) nameEl.textContent = '—';
        if (cardEl) cardEl.classList.remove('is-active');
        if (rowsEl) renderStatEmpty(rowsEl, team);
      }
    };

    select.addEventListener('change', update);
    update();
  });
}

function renderStatRows(container, players, prevStats) {
  container.innerHTML = '';
  players.forEach(p => {
    const kKey = `stat_${p.id}_kills`;
    const dKey = `stat_${p.id}_deaths`;
    const k = prevStats[kKey] != null ? prevStats[kKey] : '';
    const d = prevStats[dKey] != null ? prevStats[dKey] : '';

    const row = document.createElement('div');
    row.className = 'player-stat-row';
    row.innerHTML = `
      <span class="player-stat-row__name">${escapeHtml(p.nome)}</span>
      <div class="player-stat-row__inputs">
        <label class="stat-field stat-field--k">
          <span class="stat-field__label">K</span>
          <input type="number" class="stat-field__input"
                 name="${escapeHtml(kKey)}"
                 min="0" max="999" placeholder="0"
                 value="${escapeHtml(k)}"
                 aria-label="Kills de ${escapeHtml(p.nome)}">
        </label>
        <label class="stat-field stat-field--d">
          <span class="stat-field__label">D</span>
          <input type="number" class="stat-field__input"
                 name="${escapeHtml(dKey)}"
                 min="0" max="999" placeholder="0"
                 value="${escapeHtml(d)}"
                 aria-label="Deaths de ${escapeHtml(p.nome)}">
        </label>
      </div>
    `;
    container.appendChild(row);
  });
}

function renderStatEmpty(container, team) {
  container.innerHTML =
    `<p class="player-stats-empty t-mono">// Selecione a dupla ${team || ''}</p>`;
}

function parseJsonScript(id) {
  const el = document.getElementById(id);
  if (!el) return null;
  try { return JSON.parse(el.textContent); }
  catch { return null; }
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/* ── Form submit loading state ────────────────────────── */
function initFormSubmit() {
  const form = document.querySelector('.match-form');
  if (!form) return;

  form.addEventListener('submit', () => {
    const btn  = form.querySelector('.submit-btn');
    const text = form.querySelector('.submit-btn__text');
    if (!btn || !text) return;

    text.textContent = 'PROCESSANDO';
    text.classList.add('loading-dots');
    btn.disabled = true;
    btn.classList.add('is-loading');
  });
}
