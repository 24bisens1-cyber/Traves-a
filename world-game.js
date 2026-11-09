/* TRAVESÍA Portal Run — cursor-reactive mini-game, click ripples, and motion-safe effects. */
(function () {
  'use strict';
  const markup = () => `<section class="world-game" id="worldGame" aria-labelledby="worldGameTitle">
  <div class="world-game-topline"><span class="game-live-dot"></span> TRAVESÍA ARCADE <span class="game-topline-sep">/</span> INTERACTIVE WORLD</div>
  <div class="world-game-heading"><div><p class="game-eyebrow">A LITTLE TRAVEL ADVENTURE</p><h2 id="worldGameTitle">Portal <em>Run.</em></h2><p class="game-intro">Collect seven tiny travel charms in 30 seconds. Follow the floating route, tap each glowing charm and unlock a new postcard.</p></div><div class="game-mission"><span class="mission-icon">✦</span><div><b>MISSION 01</b><small>COLLECT 7 TRAVEL CHARMS</small></div></div></div>
  <div class="game-scorebar" aria-label="Game statistics"><div class="game-score-stat"><strong id="gameScore">00</strong><span>CHARMS</span></div><div class="game-score-stat"><strong id="gameTime">30<span>s</span></strong><span>TIME LEFT</span></div><div class="game-score-stat game-best-stat"><strong id="gameBest">00</strong><span>PERSONAL BEST</span></div><div class="game-progress" aria-label="Travel charm progress"><span id="gameProgress"></span></div></div>
  <div class="game-stage" id="gameStage" tabindex="0" role="application" aria-label="Portal Run game field. Move the pointer to shift the island scene, click the background to make a little ripple, and tap the glowing travel charm to collect it." data-game-state="ready">
    <div class="game-stage-stars" aria-hidden="true"></div><div class="game-spotlight" aria-hidden="true"></div>
    <div class="game-world" id="gameWorld" aria-hidden="true"><div class="game-scene-sun"></div><div class="game-scene-cloud cloud-one"></div><div class="game-scene-cloud cloud-two"></div><div class="game-scene-mountain mountain-back"></div><div class="game-scene-mountain mountain-front"></div><div class="game-travel-portal"><span>TAKE THE SCENIC ROUTE</span></div><div class="game-scene-island"><div class="game-scene-path"></div><i class="island-palm palm-one"></i><i class="island-palm palm-two"></i></div><div class="game-floating-postcard postcard-left"><img src="assets/destinations/kyoto.webp" alt=""></div><div class="game-floating-postcard postcard-right"><img src="assets/destinations/goa.webp" alt=""></div><span class="game-world-pin pin-a">✦</span><span class="game-world-pin pin-b">⌁</span><span class="game-world-pin pin-c">♡</span></div>
    <div class="game-station station-one" aria-hidden="true">✧</div><div class="game-station station-two" aria-hidden="true">✳</div><div class="game-station station-three" aria-hidden="true">✦</div>
    <button class="travel-charm-target" id="gameTarget" type="button" aria-label="Collect the travel charm" disabled><span>✦</span></button>
    <div class="game-target-callout" id="gameTargetCallout">TRAVEL CHARM AHEAD <span>↗</span></div><div class="game-cursor" id="gameCursor" aria-hidden="true"><span></span></div><div class="game-stage-caption"><span class="caption-pulse"></span><span id="gameStageCaption">POSTCARD FIELD READY</span><span class="caption-right">MOVE · CLICK · DISCOVER</span></div>
    <div class="game-win-overlay" id="gameWinOverlay" hidden><div class="win-stamp">✦</div><p>POSTCARD UNLOCKED</p><h3>You found a new somewhere.</h3><span>Seven travel charms collected. Your next destination is waiting.</span><button type="button" id="gameExplore">Explore destinations ↗</button></div>
  </div>
  <div class="game-bottom"><div class="game-controls"><button type="button" class="game-primary" id="gameStart"><span>▶</span> Launch run</button><button type="button" class="game-secondary" id="gameReset">Reset field ↺</button><span class="game-status" id="gameStatus" role="status" aria-live="polite">Ready when you are. Your first travel charm is waiting.</span></div><div class="game-control-hint"><kbd>CLICK</kbd> CHARM TO COLLECT <span>·</span> CLICK FIELD TO PULSE</div></div>
</section>`;
  const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
  function init() {
    const stage = document.getElementById('gameStage');
    if (!stage || stage.dataset.initialized === 'true') return;
    stage.dataset.initialized = 'true';
    const target = document.getElementById('gameTarget');
    const start = document.getElementById('gameStart');
    const reset = document.getElementById('gameReset');
    const scoreNode = document.getElementById('gameScore');
    const timeNode = document.getElementById('gameTime');
    const bestNode = document.getElementById('gameBest');
    const progress = document.getElementById('gameProgress');
    const status = document.getElementById('gameStatus');
    const caption = document.getElementById('gameStageCaption');
    const cursor = document.getElementById('gameCursor');
    const world = document.getElementById('gameWorld');
    const overlay = document.getElementById('gameWinOverlay');
    const explore = document.getElementById('gameExplore');
    if (![target,start,reset,scoreNode,timeNode,bestNode,progress,status,caption,cursor,world,overlay].every(Boolean)) return;
    let score = 0, time = 30, active = false, timer = null, lastPointer = 0;
    let best = 0;
    try { best = Number(localStorage.getItem('citypulsex.portal-run.best') || 0) || 0; } catch (_) {}
    bestNode.textContent = String(best).padStart(2,'0');
    const motionOK = !document.body.classList.contains('reduce-motion') && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const setStatus = (message) => { status.textContent = message; };
    const update = () => {
      scoreNode.textContent = String(score).padStart(2,'0');
      timeNode.innerHTML = `${time}<span>s</span>`;
      progress.style.width = `${Math.min(100,score / 7 * 100)}%`;
      stage.dataset.gameState = active ? 'running' : (score >= 7 ? 'won' : 'ready');
    };
    const moveTarget = () => {
      const x = 12 + Math.random() * 76, y = 17 + Math.random() * 65;
      target.style.left = `${x}%`; target.style.top = `${y}%`;
      target.style.setProperty('--target-turn', `${Math.round(Math.random()*50-25)}deg`);
      const callout = document.getElementById('gameTargetCallout');
      if (callout) { callout.style.left = `${clamp(x+2,14,77)}%`; callout.style.top = `${clamp(y-12,10,78)}%`; }
    };
    const burst = (x,y,good=false) => {
      const ripple = document.createElement('span'); ripple.className = good ? 'game-ripple is-good' : 'game-ripple';
      ripple.style.left = `${x}px`; ripple.style.top = `${y}px`; stage.appendChild(ripple);
      if (motionOK) {
        for (let i=0; i<(good?9:5); i++) {
          const spark = document.createElement('span'); spark.className = 'game-burst-spark';
          const angle = Math.PI*2*i/(good?9:5), dist = 20 + Math.random()*43;
          spark.style.setProperty('--spark-x', `${Math.cos(angle)*dist}px`);
          spark.style.setProperty('--spark-y', `${Math.sin(angle)*dist}px`);
          spark.style.left = `${x}px`; spark.style.top = `${y}px`; stage.appendChild(spark);
          window.setTimeout(()=>spark.remove(),700);
        }
      }
      window.setTimeout(()=>ripple.remove(),750);
    };
    const stop = () => { active=false; if(timer)window.clearInterval(timer); timer=null; target.disabled=true; start.disabled=false; start.innerHTML='<span>▶</span> Play again'; update(); };
    const win = () => {
      stop(); score = 7; update(); overlay.hidden=false; caption.textContent='POSTCARD UNLOCKED';
      setStatus('Postcard unlocked! Your next adventure is ready.');
      stage.classList.add('is-won');
      if(score>best){best=score;bestNode.textContent=String(best).padStart(2,'0');try{localStorage.setItem('citypulsex.portal-run.best',String(best));}catch(_){}}
    };
    const end = () => {
      stop(); caption.textContent='RUN COMPLETE';
      if(score>best){best=score;bestNode.textContent=String(best).padStart(2,'0');try{localStorage.setItem('citypulsex.portal-run.best',String(best));}catch(_){}}
      setStatus(score>=7 ? 'Postcard unlocked! Nice run, explorer.' : `Run complete: ${score} of 7 charms. Run it again and beat your score.`);
      if(score>=7){overlay.hidden=false;stage.classList.add('is-won');}
      else start.innerHTML='<span>↻</span> Run it back';
    };
    const launch = () => {
      if(timer)window.clearInterval(timer); score=0; time=30; active=true; target.disabled=false; overlay.hidden=true;
      stage.classList.remove('is-won'); caption.textContent='POSTCARD FIELD ACTIVE'; start.disabled=true; start.textContent='Run in progress…';
      setStatus('Go! Collect seven charms before the timer hits zero.'); update(); moveTarget();
      timer=window.setInterval(()=>{ if(!stage.isConnected){window.clearInterval(timer);timer=null;return;} time=Math.max(0,time-1);update();if(time===0)end(); },1000);
    };
    target.addEventListener('click',(event)=>{
      event.stopPropagation(); if(!active)return;
      const r=stage.getBoundingClientRect(); const tr=target.getBoundingClientRect();
      burst(tr.left-r.left+tr.width/2,tr.top-r.top+tr.height/2,true);
      score++; if(score>=7){win();return;} update(); moveTarget();
      setStatus(`${7-score} charm${7-score===1?'':'s'} left — keep going.`);
      target.classList.remove('target-hit'); void target.offsetWidth; target.classList.add('target-hit');
    });
    start.addEventListener('click',launch);
    reset.addEventListener('click',()=>{if(timer)window.clearInterval(timer);timer=null;score=0;time=30;active=false;target.disabled=true;start.disabled=false;start.innerHTML='<span>▶</span> Launch run';overlay.hidden=true;stage.classList.remove('is-won');caption.textContent='POSTCARD FIELD READY';setStatus('Field reset. Ready when you are.');update();moveTarget();});
    if(explore)explore.addEventListener('click',()=>{if(typeof window.cityPulseSetView==='function')window.cityPulseSetView('explore');else document.querySelector('[data-view="explore"]')?.click();});
    stage.addEventListener('pointermove',(event)=>{
      const r=stage.getBoundingClientRect(), x=clamp((event.clientX-r.left)/r.width,0,1), y=clamp((event.clientY-r.top)/r.height,0,1);
      stage.style.setProperty('--pointer-x',`${x*100}%`);stage.style.setProperty('--pointer-y',`${y*100}%`);
      stage.style.setProperty('--shift-x',`${(0.5-x)*24}px`);stage.style.setProperty('--shift-y',`${(0.5-y)*18}px`);
      world.style.setProperty('--tilt-x',`${(x-.5)*9}deg`);world.style.setProperty('--tilt-y',`${(.5-y)*7}deg`);
      cursor.style.left=`${event.clientX-r.left}px`;cursor.style.top=`${event.clientY-r.top}px`;cursor.classList.add('is-visible');
      lastPointer=Date.now();
    });
    stage.addEventListener('pointerleave',()=>{cursor.classList.remove('is-visible');stage.style.setProperty('--shift-x','0px');stage.style.setProperty('--shift-y','0px');world.style.setProperty('--tilt-x','0deg');world.style.setProperty('--tilt-y','0deg');});
    stage.addEventListener('click',(event)=>{
      if(event.target.closest('button,.game-win-overlay'))return;
      const r=stage.getBoundingClientRect(),x=event.clientX-r.left,y=event.clientY-r.top;burst(x,y,false);
      stage.classList.remove('pulse-hit');void stage.offsetWidth;stage.classList.add('pulse-hit');
      if(Date.now()-lastPointer>2500)caption.textContent='YOU JUST BENT THE FIELD';
    });
    stage.addEventListener('keydown',(event)=>{
      if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' '].includes(event.key)){event.preventDefault();}
      if(event.key===' '||event.key==='Enter'){if(!active)launch();else target.click();}
      if(event.key.startsWith('Arrow')){
        const left=parseFloat(target.style.left)||50, top=parseFloat(target.style.top)||50;
        target.style.left=`${clamp(left+(event.key==='ArrowLeft'?-4:event.key==='ArrowRight'?4:0),8,90)}%`;
        target.style.top=`${clamp(top+(event.key==='ArrowUp'?-4:event.key==='ArrowDown'?4:0),10,88)}%`;
        stage.focus();
      }
    });
    const hero = document.querySelector('.hero-art');
    if(hero){hero.addEventListener('pointermove',(event)=>{const r=hero.getBoundingClientRect(),x=(event.clientX-r.left)/r.width,y=(event.clientY-r.top)/r.height;hero.style.setProperty('--hero-pointer-x',`${x*100}%`);hero.style.setProperty('--hero-pointer-y',`${y*100}%`);hero.style.setProperty('--hero-drift-x',`${(0.5-x)*12}px`);hero.style.setProperty('--hero-drift-y',`${(0.5-y)*12}px`);hero.style.setProperty('--hero-note-drift-x',`${(0.5-x)*5}px`);hero.style.setProperty('--hero-note-drift-y',`${(0.5-y)*5}px`);});hero.addEventListener('pointerleave',()=>{hero.style.setProperty('--hero-drift-x','0px');hero.style.setProperty('--hero-drift-y','0px');});}
    moveTarget();update();
  }
  window.CityPulseWorldGame = { markup, init };
})();
