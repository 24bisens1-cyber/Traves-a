/* TRAVESÍA custom WebGL globe. No 3D model or third-party JS dependency required.
   The procedural map is a visual illustration, not a GIS or satellite layer. */
(() => {
  "use strict";
  const places = [
    {name:"Goa, India", lat:15.4909, lon:73.8278, label:"Goa"},
    {name:"Kyoto, Japan", lat:35.0116, lon:135.7681, label:"Kyoto"},
    {name:"Antarctica", lat:-77.8419, lon:166.6863, label:"Antarctica"},
    {name:"Sydney, Australia", lat:-33.8688, lon:151.2093, label:"Sydney"},
    {name:"Rome, Italy", lat:41.9028, lon:12.4964, label:"Rome"},
    {name:"Bali, Indonesia", lat:-8.4095, lon:115.1889, label:"Bali"},
  ];
  const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const $ = (s, root=document) => root.querySelector(s);
  const shader = (gl, type, source) => {
    const obj = gl.createShader(type); gl.shaderSource(obj, source); gl.compileShader(obj);
    if (!gl.getShaderParameter(obj, gl.COMPILE_STATUS)) { const message=gl.getShaderInfoLog(obj); gl.deleteShader(obj); throw new Error(message || "WebGL shader error"); }
    return obj;
  };
  function program(gl, vs, fs) {
    const p=gl.createProgram(); gl.attachShader(p,shader(gl,gl.VERTEX_SHADER,vs)); gl.attachShader(p,shader(gl,gl.FRAGMENT_SHADER,fs)); gl.linkProgram(p);
    if(!gl.getProgramParameter(p,gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p)||"Could not link WebGL shader program.");
    return p;
  }
  const VERTEX = `attribute vec3 aPosition; attribute vec2 aUv; uniform mat4 uMvp; uniform mat4 uModel; varying vec2 vUv; varying vec3 vNormal; void main(){vUv=aUv;vNormal=mat3(uModel)*aPosition;gl_Position=uMvp*vec4(aPosition,1.0);}`;
  const FRAGMENT = `precision mediump float; uniform sampler2D uTexture; varying vec2 vUv; varying vec3 vNormal; void main(){vec3 n=normalize(vNormal);vec3 light=normalize(vec3(-0.45,0.42,1.0));float diffuse=max(dot(n,light),0.0);float rim=pow(1.0-max(dot(n,vec3(0.0,0.0,1.0)),0.0),2.1);vec4 tex=texture2D(uTexture,vUv);vec3 col=tex.rgb*(0.54+diffuse*0.62);col=mix(col,vec3(0.28,0.89,0.75),rim*0.23);gl_FragColor=vec4(col,tex.a);}`;
  const MARK_VS = `attribute vec3 aPosition; uniform mat4 uMvp; uniform mat4 uModel; uniform float uPointSize; varying float vFront; void main(){vec4 p=uModel*vec4(aPosition,1.0);vFront=step(0.0,p.z);gl_Position=uMvp*vec4(aPosition,1.0);gl_PointSize=uPointSize;}`;
  const MARK_FS = `precision mediump float; varying float vFront; void main(){vec2 c=gl_PointCoord-vec2(0.5);float d=length(c);if(d>0.5||vFront<0.5)discard;float halo=1.0-smoothstep(0.12,0.5,d);gl_FragColor=vec4(0.98,0.77,0.48,halo);}`;
  function mat4Multiply(a,b){const o=new Float32Array(16);for(let c=0;c<4;c++)for(let r=0;r<4;r++)o[c*4+r]=a[r]*b[c*4]+a[4+r]*b[c*4+1]+a[8+r]*b[c*4+2]+a[12+r]*b[c*4+3];return o;}
  function perspective(fov, aspect, near, far){const f=1/Math.tan(fov/2),nf=1/(near-far);return new Float32Array([f/aspect,0,0,0,0,f,0,0,0,0,(far+near)*nf,-1,0,0,2*far*near*nf,0]);}
  function rotateX(a){const c=Math.cos(a),s=Math.sin(a);return new Float32Array([1,0,0,0,0,c,s,0,0,-s,c,0,0,0,0,1]);}
  function rotateY(a){const c=Math.cos(a),s=Math.sin(a);return new Float32Array([c,0,-s,0,0,1,0,0,s,0,c,0,0,0,0,1]);}
  function translateZ(z){return new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,z,1]);}
  function sphereMesh(rows=52, cols=88){const pos=[],uv=[],idx=[];for(let r=0;r<=rows;r++){const v=r/rows,lat=Math.PI/2-v*Math.PI;for(let c=0;c<=cols;c++){const u=c/cols,lon=u*Math.PI*2-Math.PI,cl=Math.cos(lat);pos.push(cl*Math.sin(lon),Math.sin(lat),cl*Math.cos(lon));uv.push(u,v);}}for(let r=0;r<rows;r++)for(let c=0;c<cols;c++){const a=r*(cols+1)+c,b=a+cols+1;idx.push(a,b,a+1,b,b+1,a+1);}return {pos:new Float32Array(pos),uv:new Float32Array(uv),idx:new Uint16Array(idx)};}
  function xyz(lat,lon){const a=lat*Math.PI/180,b=lon*Math.PI/180,cos=Math.cos(a);return [cos*Math.sin(b),Math.sin(a),cos*Math.cos(b)];}
  function makeTexture(){
    const c=document.createElement("canvas");c.width=1440;c.height=720;const g=c.getContext("2d");
    const sea=g.createLinearGradient(0,0,c.width,c.height);sea.addColorStop(0,"#173c47");sea.addColorStop(.45,"#24636a");sea.addColorStop(1,"#193b50");g.fillStyle=sea;g.fillRect(0,0,c.width,c.height);
    for(let lat=-75;lat<=75;lat+=15){const y=(90-lat)/180*c.height;g.beginPath();g.moveTo(0,y);g.lineTo(c.width,y);g.strokeStyle="rgba(166,225,211,.10)";g.lineWidth=1;g.stroke();}
    for(let lon=-180;lon<=180;lon+=15){const x=(lon+180)/360*c.width;g.beginPath();g.moveTo(x,0);g.lineTo(x,c.height);g.strokeStyle="rgba(166,225,211,.10)";g.stroke();}
    const poly=(coords,color="#b5d4b1")=>{g.beginPath();coords.forEach(([lon,lat],i)=>{const x=(lon+180)/360*c.width,y=(90-lat)/180*c.height;i?g.lineTo(x,y):g.moveTo(x,y);});g.closePath();const land=g.createLinearGradient(0,0,c.width,c.height);land.addColorStop(0,color);land.addColorStop(1,"#819f8d");g.fillStyle=land;g.fill();g.strokeStyle="rgba(238,241,207,.55)";g.lineWidth=2;g.stroke();};
    // Simplified continent outlines for an illustrative globe texture; not authoritative coastlines.
    poly([[-168,68],[-145,72],[-125,61],[-112,54],[-98,50],[-82,26],[-96,15],[-108,25],[-118,32],[-130,50],[-150,58]]);
    poly([[-80,12],[-67,7],[-51,-2],[-44,-17],[-53,-34],[-70,-56],[-78,-38],[-83,-10]]);
    poly([[-52,82],[-25,76],[-35,60],[-48,58],[-61,70]]);
    poly([[-12,72],[35,71],[62,58],[90,65],[130,54],[162,60],[178,48],[150,35],[132,15],[105,7],[80,8],[60,28],[48,40],[31,35],[20,55],[3,60]],"#cad7ad");
    poly([[-18,35],[5,37],[31,28],[42,7],[35,-15],[18,-35],[3,-33],[-10,-3],[-17,16]]);
    poly([[35,32],[52,11],[48,-13],[35,-25],[25,-10],[28,12]]);
    poly([[112,-11],[131,-11],[153,-25],[146,-40],[118,-35],[113,-21]]);
    poly([[130,33],[143,45],[146,36],[139,30]]);
    poly([[95,20],[115,7],[122,-8],[109,-8],[100,4]]);
    poly([[43,-12],[50,-17],[49,-25],[44,-22]]);
    // Polar ice caps, slightly translucent, and subtle speckle-like coast details.
    g.fillStyle="rgba(232,242,223,.88)";g.fillRect(0,0,c.width,22);g.fillRect(0,c.height-22,c.width,22);
    for(let i=0;i<2600;i++){const x=Math.random()*c.width,y=Math.random()*c.height;g.fillStyle=`rgba(207,237,220,${Math.random()*.055})`;g.fillRect(x,y,1.5,1.5);}
    return c;
  }
  function showFallback(canvas,message="This browser is using the lightweight 2D globe renderer. Drag to rotate and choose a destination."){
    canvas.dataset.globeReady="0";
    canvas.dataset.globeStatus="fallback-2d";
    const hero=canvas.closest(".hero-art");
    if(hero&&!hero.querySelector(".globe-unavailable")){
      const notice=document.createElement("div");notice.className="globe-unavailable";notice.textContent=message;hero.appendChild(notice);
    }
    // Keep destination exploration interactive even when WebGL is disabled or unavailable.
    let surface=canvas;
    let ctx=canvas.getContext("2d");
    if(!ctx&&hero){
      // A WebGL context cannot be changed into 2D after shader failure. Add a separate
      // overlay surface so the textured globe still renders in that failure mode.
      surface=document.createElement("canvas");surface.className="globe-fallback-canvas";
      surface.setAttribute("role","img");surface.setAttribute("aria-label","Interactive 2D globe fallback. Drag to rotate and select a destination.");
      hero.appendChild(surface);canvas.classList.add("globe-source-hidden");ctx=surface.getContext("2d");
    }
    if(!ctx){canvas.dataset.globeStatus="fallback";return;}
    if(surface===canvas)canvas.classList.add("globe-fallback-canvas");
    canvas.dataset.globeRenderer="canvas-2d";
    const texture=makeTexture();
    let rx=-.12,ry=-.62,dragging=false,lastX=0,lastY=0,lastTime=0;
    let width=1,height=1,dpr=1,frame=0;
    function resize(){const rect=surface.getBoundingClientRect();dpr=Math.min(window.devicePixelRatio||1,1.5);width=Math.max(1,Math.round(rect.width*dpr));height=Math.max(1,Math.round(rect.height*dpr));if(surface.width!==width||surface.height!==height){surface.width=width;surface.height=height;}ctx.setTransform(dpr,0,0,dpr,0,0);}
    function rotatePoint(point){const [x,y,z]=point,cx=Math.cos(rx),sx=Math.sin(rx),cy=Math.cos(ry),sy=Math.sin(ry);const yy=cx*y-sx*z,zz=sx*y+cx*z,xx=cy*x+sy*zz,z2=-sy*x+cy*zz;return {x:xx,y:yy,z:z2};}
    function drawWrapped(sx,sy,sw,sh,dx,dy,dw,dh){sx=((sx%texture.width)+texture.width)%texture.width;const first=Math.min(sw,texture.width-sx);ctx.drawImage(texture,sx,sy,first,sh,dx,dy,dw*(first/sw),dh);if(first<sw)ctx.drawImage(texture,0,sy,sw-first,sh,dx+dw*(first/sw),dy,dw*(1-first/sw),dh);}
    function updateHotspots(cx,cy,r){if(!hero)return;const rect=surface.getBoundingClientRect(),host=hero.getBoundingClientRect();places.forEach(place=>{let b=hero.querySelector(`.globe-hotspot[data-place="${place.label}"]`);if(!b){b=document.createElement("button");b.type="button";b.className="globe-hotspot";b.dataset.place=place.label;b.textContent=place.label;b.setAttribute("aria-label",`Explore ${place.name}`);b.addEventListener("click",ev=>{ev.stopPropagation();window.cityPulseOpenDestination?.(place.name,b);});hero.appendChild(b);}const q=rotatePoint(xyz(place.lat,place.lon));if(q.z<-.08){b.hidden=true;return;}const x=rect.left-host.left+cx+q.x*r,y=rect.top-host.top+cy-q.y*r;if(x<16||x>host.width-16||y<16||y>host.height-16){b.hidden=true;return;}b.hidden=false;b.style.left=`${x}px`;b.style.top=`${y}px`;});}
    function draw(now){if(!surface.isConnected)return;if(!dragging&&!reducedMotion&&now-lastTime>28)ry+=.0008*(now-lastTime);lastTime=now;const cw=surface.clientWidth,ch=surface.clientHeight;ctx.clearRect(0,0,cw,ch);const cx=cw*.49,cy=ch*.51,r=Math.min(cw*.43,ch*.43);if(r<30){requestAnimationFrame(draw);return;}
      const halo=ctx.createRadialGradient(cx,cy,r*.78,cx,cy,r*1.32);halo.addColorStop(0,"rgba(102,229,210,.18)");halo.addColorStop(1,"rgba(102,229,210,0)");ctx.fillStyle=halo;ctx.fillRect(cx-r*1.35,cy-r*1.35,r*2.7,r*2.7);
      ctx.save();ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.clip();const ocean=ctx.createRadialGradient(cx-r*.28,cy-r*.36,r*.05,cx,cy,r*1.08);ocean.addColorStop(0,"#367f86");ocean.addColorStop(.62,"#1d586b");ocean.addColorStop(1,"#102b48");ctx.fillStyle=ocean;ctx.fillRect(cx-r,cy-r,r*2,r*2);
      const rows=Math.max(72,Math.floor(r*1.2)),syStep=texture.height/rows,dyStep=(r*2)/rows,offset=((ry/(Math.PI*2))*texture.width);
      for(let i=0;i<rows;i++){const yy=-r+(i+.5)*dyStep,n=yy/r,half=r*Math.sqrt(Math.max(0,1-n*n));if(half<1)continue;const sourceY=i*syStep,sourceX=offset+(n*texture.width*.055),sourceW=texture.width*.5;drawWrapped(sourceX,sourceY,sourceW,syStep,cx-half,cy-r+i*dyStep,half*2,dyStep+1);}
      const shade=ctx.createRadialGradient(cx-r*.42,cy-r*.35,r*.08,cx,cy,r*1.14);shade.addColorStop(0,"rgba(255,255,255,.20)");shade.addColorStop(.42,"rgba(16,36,55,.02)");shade.addColorStop(1,"rgba(2,12,30,.60)");ctx.fillStyle=shade;ctx.fillRect(cx-r,cy-r,r*2,r*2);ctx.restore();
      ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.lineWidth=2;ctx.strokeStyle="rgba(170,255,231,.62)";ctx.shadowColor="rgba(103,246,220,.58)";ctx.shadowBlur=18;ctx.stroke();ctx.shadowBlur=0;
      updateHotspots(cx,cy,r);frame++;canvas.dataset.frameRendered=String(frame);canvas.dataset.rotation=String(ry);requestAnimationFrame(draw);}
    surface.addEventListener("pointerdown",e=>{dragging=true;lastX=e.clientX;lastY=e.clientY;surface.setPointerCapture?.(e.pointerId);});
    surface.addEventListener("pointermove",e=>{if(!dragging)return;const dx=e.clientX-lastX,dy=e.clientY-lastY;lastX=e.clientX;lastY=e.clientY;ry+=dx*.006;rx=Math.max(-1.15,Math.min(1.15,rx+dy*.005));});
    const stop=()=>{dragging=false;};surface.addEventListener("pointerup",stop);surface.addEventListener("pointercancel",stop);surface.addEventListener("pointerleave",stop);surface.addEventListener("dblclick",()=>{rx=-.12;ry=-.62;});
    resize();if(window.ResizeObserver){new ResizeObserver(resize).observe(surface);}else window.addEventListener("resize",resize);requestAnimationFrame(draw);
  }
  function init(canvas){
    if(!canvas||canvas.dataset.globeStatus)return;
    canvas.dataset.globeStatus="initializing";
    let gl;try{gl=canvas.getContext("webgl",{alpha:true,antialias:true,powerPreference:"low-power"});}catch(_){gl=null;}
    if(!gl){showFallback(canvas);return;}
    let globeProgram,markProgram,mesh;try{globeProgram=program(gl,VERTEX,FRAGMENT);markProgram=program(gl,MARK_VS,MARK_FS);mesh=sphereMesh();}catch(err){console.warn("TRAVESÍA WebGL globe unavailable:",err);showFallback(canvas,"The interactive globe could not start in this browser. Destination discovery and trip planning are still available.");return;}
    canvas.dataset.globeReady="1";
    canvas.dataset.globeStatus="ready";
    canvas.dataset.globeRenderer="webgl";
    const getAttrib=(p,name)=>gl.getAttribLocation(p,name), getUniform=(p,name)=>gl.getUniformLocation(p,name);
    const position=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,position);gl.bufferData(gl.ARRAY_BUFFER,mesh.pos,gl.STATIC_DRAW);
    const uv=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,uv);gl.bufferData(gl.ARRAY_BUFFER,mesh.uv,gl.STATIC_DRAW);
    const indices=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,indices);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,mesh.idx,gl.STATIC_DRAW);
    const tex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tex);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,0);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,makeTexture());gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.REPEAT);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    const markerPosition=gl.createBuffer();const markerPos=new Float32Array(places.flatMap(p=>xyz(p.lat,p.lon)));gl.bindBuffer(gl.ARRAY_BUFFER,markerPosition);gl.bufferData(gl.ARRAY_BUFFER,markerPos,gl.STATIC_DRAW);
    const markers=[];const hero=canvas.closest(".hero-art");
    places.forEach((place,i)=>{const b=document.createElement("button");b.type="button";b.className="globe-hotspot";b.textContent=place.label;b.setAttribute("aria-label",`Explore ${place.name}`);b.addEventListener("click",ev=>{ev.stopPropagation();window.cityPulseOpenDestination?.(place.name,b);});hero.appendChild(b);markers.push({el:b,place});});
    let rx=-0.12,ry=-0.62,dragging=false,lastX=0,lastY=0,lastTime=0,spin=true;
    const mvp=new Float32Array(16),model=new Float32Array(16);let width=1,height=1,pixelRatio=1,lastRender=0;
    function resize(){const rect=canvas.getBoundingClientRect();pixelRatio=Math.min(window.devicePixelRatio||1,1.25);width=Math.max(1,Math.round(rect.width*pixelRatio));height=Math.max(1,Math.round(rect.height*pixelRatio));if(canvas.width!==width||canvas.height!==height){canvas.width=width;canvas.height=height;}gl.viewport(0,0,width,height);}
    function transformPoint(p){const [x,y,z]=p,cx=Math.cos(rx),sx=Math.sin(rx),cy=Math.cos(ry),sy=Math.sin(ry);const yy=cx*y-sx*z,zz=sx*y+cx*z,xx=cy*x+sy*zz,z2=-sy*x+cy*zz;const denom=3.15-z2;if(z2<-.05||denom<=0)return null;const f=1/Math.tan(Math.PI/8),aspect=width/height,nx=(f/aspect*xx)/denom,ny=(f*yy)/denom;return {x:(nx+1)*.5*width/pixelRatio,y:(1-ny)*.5*height/pixelRatio,z:z2};}
    function updateHotspots(){markers.forEach(({el,place})=>{const pt=transformPoint(xyz(place.lat,place.lon));if(!pt||pt.x<12||pt.x>canvas.clientWidth-12||pt.y<12||pt.y>canvas.clientHeight-12){el.hidden=true;return;}el.hidden=false;el.style.left=`${pt.x}px`;el.style.top=`${pt.y}px`;});}
    function draw(now){if(!canvas.isConnected)return;if(document.hidden||now-lastRender<33){requestAnimationFrame(draw);return;}lastRender=now;const dt=Math.min(.05,Math.max(0,(now-lastTime)/1000||0));lastTime=now;if(spin&&!dragging&&!reducedMotion)ry+=dt*.075;const asp=width/height,proj=perspective(Math.PI/4,asp,.1,100),view=translateZ(-3.15);const rot=mat4Multiply(rotateY(ry),rotateX(rx));model.set(rot);const matrix=mat4Multiply(proj,mat4Multiply(view,rot));mvp.set(matrix);
      gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);gl.enable(gl.CULL_FACE);gl.cullFace(gl.BACK);gl.useProgram(globeProgram);
      gl.bindBuffer(gl.ARRAY_BUFFER,position);const aPos=getAttrib(globeProgram,"aPosition");gl.enableVertexAttribArray(aPos);gl.vertexAttribPointer(aPos,3,gl.FLOAT,false,0,0);
      gl.bindBuffer(gl.ARRAY_BUFFER,uv);const aUv=getAttrib(globeProgram,"aUv");gl.enableVertexAttribArray(aUv);gl.vertexAttribPointer(aUv,2,gl.FLOAT,false,0,0);
      gl.uniformMatrix4fv(getUniform(globeProgram,"uMvp"),false,mvp);gl.uniformMatrix4fv(getUniform(globeProgram,"uModel"),false,model);gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,tex);gl.uniform1i(getUniform(globeProgram,"uTexture"),0);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,indices);gl.drawElements(gl.TRIANGLES,mesh.idx.length,gl.UNSIGNED_SHORT,0);
      gl.disable(gl.CULL_FACE);gl.useProgram(markProgram);gl.bindBuffer(gl.ARRAY_BUFFER,markerPosition);const ma=getAttrib(markProgram,"aPosition");gl.enableVertexAttribArray(ma);gl.vertexAttribPointer(ma,3,gl.FLOAT,false,0,0);gl.uniformMatrix4fv(getUniform(markProgram,"uMvp"),false,mvp);gl.uniformMatrix4fv(getUniform(markProgram,"uModel"),false,model);gl.uniform1f(getUniform(markProgram,"uPointSize"),Math.max(7,Math.min(12,pixelRatio*7)));gl.drawArrays(gl.POINTS,0,places.length);updateHotspots();canvas.dataset.frameRendered=String((Number(canvas.dataset.frameRendered)||0)+1);canvas.dataset.rotation=String(ry);requestAnimationFrame(draw);}
    canvas.addEventListener("pointerdown",e=>{dragging=true;spin=false;lastX=e.clientX;lastY=e.clientY;canvas.setPointerCapture?.(e.pointerId);canvas.style.cursor="grabbing";});
    canvas.addEventListener("pointermove",e=>{if(!dragging)return;const dx=e.clientX-lastX,dy=e.clientY-lastY;lastX=e.clientX;lastY=e.clientY;ry+=dx*.006;rx=Math.max(-1.2,Math.min(1.2,rx+dy*.005));});
    const endDrag=()=>{dragging=false;spin=!reducedMotion;canvas.style.cursor="grab";};canvas.addEventListener("pointerup",endDrag);canvas.addEventListener("pointercancel",endDrag);canvas.addEventListener("pointerleave",()=>{if(dragging)endDrag();});
    canvas.addEventListener("dblclick",()=>{rx=-.12;ry=-.62;spin=!reducedMotion;});
    resize();const observer=new ResizeObserver(resize);observer.observe(canvas);if(!reducedMotion){canvas.addEventListener("pointerenter",()=>{spin=false;});canvas.addEventListener("pointerleave",()=>{if(!dragging)spin=true;});}
    requestAnimationFrame(draw);
  }
  function scan(){const canvas=$("#citypulseGlobe");if(canvas)init(canvas);}
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",scan);else scan();
  new MutationObserver(()=>{const canvas=$("#citypulseGlobe");if(canvas&&!canvas.dataset.globeStatus)init(canvas);}).observe(document.querySelector("#page")||document.body,{childList:true,subtree:true});
})();
