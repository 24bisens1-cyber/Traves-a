/* TRAVESÍA 3D companion runtime: local glTF skins with embedded animation clips. */
(function () {
  'use strict';
  const rigs = new WeakMap();
  const reduced = () => document.body.classList.contains('reduce-motion') || window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function mount(container, slug, fallbackImage, onStatus) {
    if (!container) return null;
    // Self-contained GLB renderer runs without a third-party CDN.
    if (window.CityPulseGLBViewer && typeof window.CityPulseGLBViewer.mount === 'function') {
      return window.CityPulseGLBViewer.mount(container, slug, fallbackImage, onStatus);
    }
    const previous = rigs.get(container); if (previous) previous.dispose();
    const report = (message, ok) => { if (typeof onStatus === 'function') onStatus(message, ok); };
    if (fallbackImage) fallbackImage.hidden = true;
    if (!window.THREE || !window.THREE.GLTFLoader || !THREE.WebGLRenderer) {
      if (fallbackImage) fallbackImage.hidden = false;
      report('3D renderer unavailable; using the portrait fallback.', false); return null;
    }

    let renderer, scene, camera, mixer, model, frame = 0, disposed = false, currentAction = null, availableClips = [];
    const clock = new THREE.Clock();
    let resizeObserver = null;
    const resize = () => {
      if (!renderer || disposed || !camera) return;
      const w = Math.max(1, container.clientWidth), h = Math.max(1, container.clientHeight);
      camera.aspect = w / h; camera.updateProjectionMatrix(); renderer.setSize(w, h, false);
    };
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
      renderer.setSize(container.clientWidth || 320, container.clientHeight || 280, false);
      renderer.outputEncoding = THREE.sRGBEncoding;
      renderer.setClearColor(0x000000, 0);
      renderer.domElement.setAttribute('aria-label', 'Animated, rigged 3D travel companion');
      renderer.domElement.setAttribute('role', 'img');
      container.replaceChildren(renderer.domElement);
      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(31, (container.clientWidth || 320) / (container.clientHeight || 280), 0.1, 50);
      camera.position.set(0, 1.13, 4.25); camera.lookAt(0, 1.08, 0);
      scene.add(new THREE.HemisphereLight(0xfff9e9, 0x6e8a78, 2.0));
      const key = new THREE.DirectionalLight(0xffffff, 2.1); key.position.set(-2.5, 4.2, 3.5); scene.add(key);
      const rim = new THREE.DirectionalLight(0x9fcfc2, 1.15); rim.position.set(2, 2.5, -2.5); scene.add(rim);
      const ground = new THREE.Mesh(new THREE.CircleGeometry(.73, 64), new THREE.MeshBasicMaterial({ color: 0x7eab8a, transparent: true, opacity: .13, depthWrite: false }));
      ground.rotation.x = -Math.PI / 2; ground.position.y = .015; scene.add(ground);
      const ring = new THREE.Mesh(new THREE.TorusGeometry(.72, .008, 5, 80), new THREE.MeshBasicMaterial({ color: 0x7baf8a, transparent: true, opacity: .62 }));
      ring.rotation.x = Math.PI / 2; ring.position.y = .026; scene.add(ring);

      const loader = new THREE.GLTFLoader();
      const assetUrl = `assets/companions3d/${encodeURIComponent(slug)}.glb`;
      const play = (kind) => {
        if (!mixer || !availableClips.length) return false;
        const targetName = ({ hello: 'Wave', dance: 'Dance', hop: 'AdventureHop' })[kind] || 'Idle';
        const clip = availableClips.find(c => c.name === targetName) || availableClips.find(c => c.name === 'Idle');
        if (!clip) return false;
        if (currentAction) currentAction.fadeOut(.1);
        currentAction = mixer.clipAction(clip); currentAction.reset();
        if (targetName === 'Idle') currentAction.setLoop(THREE.LoopRepeat, Infinity);
        else currentAction.setLoop(THREE.LoopOnce, 1);
        currentAction.clampWhenFinished = targetName !== 'Idle';
        currentAction.fadeIn(.12).play();
        return true;
      };
      mixer?.removeEventListener('finished', onAnimationFinished);
      function onAnimationFinished(event) {
        if (!currentAction || event.action !== currentAction || disposed) return;
        mixer.stopAllAction(); currentAction = null;
      }
      const entry = { play, dispose: () => {
        disposed = true; cancelAnimationFrame(frame);
        if (resizeObserver) resizeObserver.disconnect(); else window.removeEventListener('resize', resize);
        if (mixer) { mixer.removeEventListener('finished', onAnimationFinished); mixer.stopAllAction(); }
        if (renderer) { renderer.dispose(); renderer.domElement.remove(); }
        if (model) scene.remove(model);
        rigs.delete(container);
      }};
      rigs.set(container, entry);
      loader.load(assetUrl, (gltf) => {
        if (disposed) return;
        availableClips = gltf.animations || [];
        model = gltf.scene; model.position.set(0, 0, 0); model.scale.setScalar(.93);
        model.traverse((obj) => {
          if (!obj.isMesh) return;
          obj.castShadow = true; obj.receiveShadow = true;
          if (obj.material) { obj.material.side = THREE.DoubleSide; obj.material.needsUpdate = true; }
        });
        scene.add(model); mixer = new THREE.AnimationMixer(model); mixer.addEventListener('finished', onAnimationFinished);
        // Keep the character posed and still until the user explicitly requests an action.
        currentAction = null;
        if (fallbackImage) fallbackImage.hidden = true;
        const boneCount = model.getObjectByProperty('type', 'SkinnedMesh')?.skeleton?.bones?.length || 12;
        report(`3D rig ready · ${boneCount} joints · ${availableClips.length} animation clips`, true);
      }, undefined, (error) => {
        console.warn('TRAVESÍA 3D companion failed to load:', error);
        if (fallbackImage) fallbackImage.hidden = false;
        report('3D asset could not load; portrait fallback is available.', false);
      });
      if (typeof ResizeObserver !== 'undefined') { resizeObserver = new ResizeObserver(resize); resizeObserver.observe(container); }
      else window.addEventListener('resize', resize);
      const animate = () => {
        if (disposed) return;
        frame = requestAnimationFrame(animate);
        const delta = Math.min(clock.getDelta(), .05);
        if (mixer && currentAction && !reduced()) mixer.update(delta);
        renderer.render(scene, camera);
      };
      animate();
      return entry;
    } catch (error) {
      console.warn('TRAVESÍA companion renderer initialization failed:', error);
      if (fallbackImage) fallbackImage.hidden = false;
      report('WebGL is unavailable; portrait fallback is available.', false);
      if (renderer) renderer.dispose();
      return null;
    }
  }
  window.CityPulse3DCompanions = { mount };
})();
