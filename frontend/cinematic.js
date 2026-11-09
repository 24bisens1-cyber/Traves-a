/* TRAVESÍA motion system: purposeful, lightweight interactions across every view. */
(() => {
  'use strict';
  const reduceMotion = () => document.body.classList.contains('reduce-motion') || window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const page = () => document.querySelector('#page');
  let revealObserver = null;
  let scrollFrame = 0;
  let pointerFrame = 0;
  let sceneScrollFrame = 0;
  let revealFrame = 0;
  const seen = new WeakSet();

  function progressTrack() {
    if (document.querySelector('.cinematic-progress')) return document.querySelector('.cinematic-progress');
    const bar = document.createElement('div');
    bar.className = 'cinematic-progress';
    bar.setAttribute('aria-hidden', 'true');
    document.body.appendChild(bar);
    return bar;
  }

  function updateProgress() {
    scrollFrame = 0;
    const root = document.documentElement;
    const max = Math.max(1, root.scrollHeight - window.innerHeight);
    const pct = Math.min(100, Math.max(0, (window.scrollY / max) * 100));
    progressTrack().style.width = `${pct}%`;
  }

  function queueProgress() {
    if (!scrollFrame) scrollFrame = requestAnimationFrame(updateProgress);
  }

  function updateReveals() {
    revealFrame = 0;
    if (reduceMotion()) return;
    document.querySelectorAll('[data-reveal]:not(.is-in-view)').forEach((node) => {
      const rect = node.getBoundingClientRect();
      if (rect.bottom > 0 && rect.top < window.innerHeight - 28) {
        node.classList.add('is-in-view');
        if (revealObserver) revealObserver.unobserve(node);
      }
    });
  }

  function queueReveals() {
    if (!revealFrame) revealFrame = requestAnimationFrame(updateReveals);
  }

  function revealNodes(root) {
    if (!root || !(root instanceof Element || root instanceof Document)) return;
    const selectors = '.hero, .world-game, .section-head, .destination-card, .feature-card, .panel, .experience-card, .buddy-card, .pulse-panel, .split-panel, .split-summary, .split-ledger, .story-chapter, .atlas-destination-card, .split-person, .split-balance';
    const nodes = [];
    if (root instanceof Element && root.matches(selectors)) nodes.push(root);
    nodes.push(...root.querySelectorAll(selectors));
    nodes.forEach((node) => {
      if (seen.has(node)) return;
      seen.add(node);
      node.setAttribute('data-reveal', '');
      if (revealObserver && !reduceMotion()) revealObserver.observe(node);
      else node.classList.add('is-in-view');
    });
    queueReveals();
  }

  function attachTilt(root) {
    if (!root || !(root instanceof Element || root instanceof Document)) return;
    root.querySelectorAll('.destination-card, .feature-card, .story-chapter, .experience-card, .split-person, .friend-character-choice, .atlas-destination-card').forEach((card) => {
      if (card.dataset.cinematicTilt === '1') return;
      card.dataset.cinematicTilt = '1';
      card.addEventListener('pointermove', (event) => {
        if (reduceMotion() || event.pointerType === 'touch' || window.innerWidth < 761) return;
        const r = card.getBoundingClientRect();
        const x = (event.clientX - r.left) / Math.max(1, r.width);
        const y = (event.clientY - r.top) / Math.max(1, r.height);
        const tiltX = (0.5 - y) * 5;
        const tiltY = (x - 0.5) * 6;
        card.style.setProperty('--cp-tilt-x', `${tiltX.toFixed(2)}deg`);
        card.style.setProperty('--cp-tilt-y', `${tiltY.toFixed(2)}deg`);
        card.style.setProperty('--cp-spot-x', `${(x * 100).toFixed(1)}%`);
        card.style.setProperty('--cp-spot-y', `${(y * 100).toFixed(1)}%`);
      });
      card.addEventListener('pointerleave', () => {
        card.style.setProperty('--cp-tilt-x', '0deg');
        card.style.setProperty('--cp-tilt-y', '0deg');
        card.style.setProperty('--cp-spot-x', '50%');
        card.style.setProperty('--cp-spot-y', '50%');
      });
    });
  }

  function addGlobeParticles(root) {
    const field = root?.querySelector?.('.globe-particle-field');
    if (!field || field.dataset.ready === '1') return;
    field.dataset.ready = '1';
    const palette = ['#b5fff0', '#c9b8ff', '#d7ff72', '#83dfff'];
    for (let i = 0; i < 28; i += 1) {
      const particle = document.createElement('span');
      const seed = (i * 37 + 13) % 97;
      particle.style.setProperty('--particle-x', `${(seed * 1.03) % 100}%`);
      particle.style.setProperty('--particle-y', `${(seed * 2.17 + 11) % 100}%`);
      particle.style.setProperty('--particle-size', `${i % 7 === 0 ? 4 : 2 + (i % 2)}px`);
      particle.style.setProperty('--particle-duration', `${6 + (i % 7)}s`);
      particle.style.setProperty('--particle-delay', `${-(i % 9)}s`);
      particle.style.setProperty('--particle-color', palette[i % palette.length]);
      field.appendChild(particle);
    }
  }

  function heroParallax(root) {
    const stage = root?.querySelector?.('#heroMapStage');
    if (!stage || stage.dataset.cinematicPointer === '1') return;
    stage.dataset.cinematicPointer = '1';
    let pending = null;
    stage.addEventListener('pointermove', (event) => {
      if (reduceMotion() || event.pointerType === 'touch') return;
      const rect = stage.getBoundingClientRect();
      const x = (event.clientX - rect.left) / Math.max(1, rect.width);
      const y = (event.clientY - rect.top) / Math.max(1, rect.height);
      if (pending) cancelAnimationFrame(pending);
      pending = requestAnimationFrame(() => {
        stage.style.setProperty('--hero-pointer-x', `${(x * 100).toFixed(1)}%`);
        stage.style.setProperty('--hero-pointer-y', `${(y * 100).toFixed(1)}%`);
        stage.style.setProperty('--map-x', `${(x * 100).toFixed(1)}%`);
        stage.style.setProperty('--map-y', `${(y * 100).toFixed(1)}%`);
      });
    });
    stage.addEventListener('pointerleave', () => {
      stage.style.setProperty('--hero-pointer-x', '50%');
      stage.style.setProperty('--hero-pointer-y', '50%');
      stage.style.setProperty('--map-x', '50%');
      stage.style.setProperty('--map-y', '50%');
    });
    addGlobeParticles(root);
  }

  function updateScrollScenes() {
    sceneScrollFrame = 0;
    if (reduceMotion()) return;
    const targets = document.querySelectorAll('.scene-main-card img, .scene-float-card, .story-chapter-art, .game-travel-portal, .game-floating-postcard');
    const viewport = Math.max(1, window.innerHeight);
    targets.forEach((node) => {
      const rect = node.getBoundingClientRect();
      if (rect.bottom < -80 || rect.top > viewport + 80) return;
      const centre = rect.top + rect.height / 2;
      const offset = Math.max(-1, Math.min(1, (centre - viewport * .5) / (viewport * .72)));
      const lift = Math.round(offset * -9);
      const scale = (1.035 - Math.abs(offset) * .012).toFixed(3);
      node.style.setProperty('--cp-scroll-lift', `${lift}px`);
      node.style.setProperty('--cp-scroll-scale', scale);
    });
  }

  function queueSceneScroll() {
    if (!sceneScrollFrame) sceneScrollFrame = requestAnimationFrame(updateScrollScenes);
  }

  function enhance(root = page()) {
    if (!root) return;
    revealNodes(root);
    attachTilt(root);
    heroParallax(root);
    queueProgress();
    queueSceneScroll();
  }

  function boot() {
    if (!document.body) return;
    document.body.classList.add('cinematic-enabled');
    if ('IntersectionObserver' in window) {
      revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-in-view');
            revealObserver.unobserve(entry.target);
          }
        });
      }, { threshold: 0.08, rootMargin: '0px 0px -35px 0px' });
    }
    enhance(document);
    window.addEventListener('scroll', queueProgress, { passive: true });
    window.addEventListener('scroll', queueSceneScroll, { passive: true });
    window.addEventListener('scroll', queueReveals, { passive: true });
    window.addEventListener('resize', queueProgress, { passive: true });
    window.addEventListener('resize', queueSceneScroll, { passive: true });
    window.addEventListener('resize', queueReveals, { passive: true });
    const host = page();
    if (host && 'MutationObserver' in window) {
      new MutationObserver((records) => {
        for (const record of records) {
          record.addedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE) enhance(node);
          });
        }
      }).observe(host, { childList: true, subtree: true });
    }
    // The original navigation remains in charge of routes; this only refreshes motion after a view swap.
    document.addEventListener('click', (event) => {
      if (event.target.closest('[data-view]')) window.setTimeout(() => enhance(page()), 80);
    }, true);
    updateProgress();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
  window.CityPulseMotion = { refresh: enhance };
})();
