// ---- Hero slider (autoplay, sin dependencias externas) --------------------
function initHeroSlider() {
  const root = document.querySelector('[data-hero-slider]');
  if (!root) return;
  const slides = root.querySelectorAll('.hero-slide');
  const dotsWrap = root.querySelector('[data-hero-dots]');
  if (!slides.length) return;

  let current = 0;
  let timer;

  const dots = [];
  if (dotsWrap) {
    slides.forEach((_, i) => {
      const dot = document.createElement('button');
      dot.className = 'h-2.5 rounded-full transition-all duration-300 bg-white/40 hover:bg-white/70';
      dot.style.width = '10px';
      dot.setAttribute('aria-label', `Ir a la imagen ${i + 1}`);
      dot.addEventListener('click', () => show(i, true));
      dotsWrap.appendChild(dot);
      dots.push(dot);
    });
  }

  function show(index, userTriggered) {
    slides[current].classList.remove('is-active');
    if (dots[current]) { dots[current].style.width = '10px'; dots[current].classList.remove('bg-gold'); dots[current].classList.add('bg-white/40'); }
    current = (index + slides.length) % slides.length;
    slides[current].classList.add('is-active');
    if (dots[current]) { dots[current].style.width = '28px'; dots[current].classList.add('bg-gold'); dots[current].classList.remove('bg-white/40'); }
    if (userTriggered) restart();
  }

  function restart() {
    clearInterval(timer);
    timer = setInterval(() => show(current + 1), 5500);
  }

  show(0);
  restart();
}

// ---- Galería con lightbox simple ------------------------------------------
function initLightbox() {
  const triggers = document.querySelectorAll('[data-lightbox-src]');
  if (!triggers.length) return;

  const overlay = document.createElement('div');
  overlay.id = 'lightbox';
  overlay.className = 'fixed inset-0 z-[200] hidden items-center justify-center bg-black/90 p-4 md:p-10';
  overlay.innerHTML = `
    <button class="liquid-glass absolute top-5 right-5 h-11 w-11 rounded-full flex items-center justify-center text-white/90 hover:text-gold text-2xl leading-none transition-colors" data-lightbox-close>&times;</button>
    <img class="max-h-full max-w-full rounded-2xl shadow-2xl" data-lightbox-img alt="">
  `;
  document.body.appendChild(overlay);
  const img = overlay.querySelector('[data-lightbox-img]');

  function open(src) {
    img.src = src;
    overlay.classList.remove('hidden');
    overlay.classList.add('flex');
    document.body.style.overflow = 'hidden';
  }
  function close() {
    overlay.classList.add('hidden');
    overlay.classList.remove('flex');
    document.body.style.overflow = '';
  }

  triggers.forEach(t => t.addEventListener('click', () => open(t.dataset.lightboxSrc)));
  overlay.addEventListener('click', (e) => { if (e.target === overlay || e.target.hasAttribute('data-lightbox-close')) close(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
}

// ---- Cotizador de enganche / mensualidad -----------------------------------
function initCotizador() {
  const form = document.querySelector('[data-cotizador]');
  if (!form) return;

  const precio = parseFloat(form.dataset.precio || '0');
  const enganchePctMin = parseFloat(form.dataset.enganchePct || '10');

  const engancheInput = form.querySelector('[data-enganche-pct]');
  const plazoSelect = form.querySelector('[data-plazo]');
  const engancheOut = form.querySelector('[data-out-enganche]');
  const engancheMontoOut = form.querySelector('[data-out-enganche-monto]');
  const restanteOut = form.querySelector('[data-out-restante]');
  const mensualidadOut = form.querySelector('[data-out-mensualidad]');
  const tasaOut = form.querySelector('[data-out-tasa]');
  const totalOut = form.querySelector('[data-out-total]');

  function fmt(n) {
    return n.toLocaleString('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 });
  }

  /** Cuota fija (amortización francesa). Si interes anual es 0 → P / n. */
  function cuotaMensual(principal, meses, interesAnualPct) {
    if (!principal || !meses) return 0;
    const i = (interesAnualPct || 0) / 100 / 12;
    if (i <= 0) return principal / meses;
    const factor = Math.pow(1 + i, meses);
    return principal * (i * factor) / (factor - 1);
  }

  function calcular() {
    const pct = Math.max(enganchePctMin, parseFloat(engancheInput.value || enganchePctMin));
    engancheInput.value = pct;
    engancheOut.textContent = `${pct}%`;

    const montoEnganche = precio * (pct / 100);
    const restante = precio - montoEnganche;
    const plazo = parseInt(plazoSelect.value, 10);
    const opt = plazoSelect.selectedOptions[0];
    const interes = parseFloat(opt?.dataset?.interes || '0');
    const mensualidad = cuotaMensual(restante, plazo, interes);
    const total = montoEnganche + mensualidad * plazo;

    engancheMontoOut.textContent = fmt(montoEnganche);
    restanteOut.textContent = fmt(restante);
    mensualidadOut.textContent = fmt(mensualidad);
    if (tasaOut) {
      tasaOut.textContent = interes > 0 ? `${interes}% anual` : 'Sin interés';
    }
    if (totalOut) {
      totalOut.textContent = fmt(total);
    }
  }

  engancheInput.addEventListener('input', calcular);
  plazoSelect.addEventListener('change', calcular);
  calcular();
}

// ---- Preview de nombre de archivo en inputs file ---------------------------
function initFileInputs() {
  document.querySelectorAll('[data-file-input]').forEach((input) => {
    const label = document.querySelector(`[data-file-label="${input.id}"]`);
    if (!label) return;
    const original = label.textContent;
    input.addEventListener('change', () => {
      label.textContent = input.files.length ? input.files[0].name : original;
    });
  });
}

// ---- Splash de entrada: aparicion suave tipo "Hello" + cristal dorado -----
function initSplash() {
  const splash = document.querySelector('[data-splash]');
  if (!splash) return;

  if (sessionStorage.getItem('marnez_splash_seen')) {
    splash.remove();
    return;
  }

  document.body.style.overflow = 'hidden';
  const bg = splash.querySelector('[data-splash-bg]');
  const word = splash.querySelector('[data-splash-word]');

  requestAnimationFrame(() => {
    bg.classList.add('is-in');
    setTimeout(() => word.classList.add('is-in'), 300);
  });

  // Fase 1: el contenido se apaga suavemente hasta dejar un panel solido
  setTimeout(() => {
    splash.classList.add('splash-fade-content');
  }, 2800);

  // Fase 2: con todo ya invisible, se disuelve el panel completo (sin corte visible)
  setTimeout(() => {
    splash.classList.add('splash-exit');
    document.body.style.overflow = '';
    sessionStorage.setItem('marnez_splash_seen', '1');
    setTimeout(() => { splash.classList.add('splash-hidden'); splash.remove(); }, 1200);
  }, 3800);
}

// ---- Selector de tema claro/oscuro (persistido en localStorage) -----------
// El switch del navbar (Alpine) llama a esto para persistir la eleccion;
// el logo del footer se resuelve solo via CSS (html.light), sin JS.
window.marnezSetTheme = function (isLight) {
  document.documentElement.classList.toggle('light', isLight);
  localStorage.setItem('marnez_theme', isLight ? 'light' : 'dark');
};

// ---- Boton "volver arriba" en el footer ------------------------------------
function initBackToTop() {
  document.querySelectorAll('[data-back-to-top]').forEach((btn) => {
    btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initSplash();
  initHeroSlider();
  initLightbox();
  initCotizador();
  initFileInputs();
  initBackToTop();
});
