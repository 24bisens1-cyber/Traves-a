/* Self-contained, dependency-free GLB 2.0 companion viewer.
 * Supports the TRAVESÍA rig format: indexed vertex-colour mesh, one skin,
 * JOINTS_0/WEIGHTS_0, LINEAR translation/rotation/scale animation channels.
 * Static until an explicit user action starts a clip. */
(() => {
  'use strict';
  const rigs = new WeakMap();
  const componentInfo = {
    5120: { Type: Int8Array, bytes: 1 }, 5121: { Type: Uint8Array, bytes: 1 },
    5122: { Type: Int16Array, bytes: 2 }, 5123: { Type: Uint16Array, bytes: 2 },
    5125: { Type: Uint32Array, bytes: 4 }, 5126: { Type: Float32Array, bytes: 4 }
  };
  const compCount = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT2: 4, MAT3: 9, MAT4: 16 };
  const I = () => new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
  function mul(a, b) {
    const o = new Float32Array(16);
    for (let c=0;c<4;c++) for (let r=0;r<4;r++) o[c*4+r] = a[r]*b[c*4] + a[4+r]*b[c*4+1] + a[8+r]*b[c*4+2] + a[12+r]*b[c*4+3];
    return o;
  }
  function translate(x,y,z) { const m=I();m[12]=x;m[13]=y;m[14]=z;return m; }
  function perspective(fov, aspect, near, far) {
    const f=1/Math.tan(fov/2), nf=1/(near-far);
    return new Float32Array([f/aspect,0,0,0,0,f,0,0,0,0,(far+near)*nf,-1,0,0,2*far*near*nf,0]);
  }
  function normalizeQuat(q) { const n=Math.hypot(q[0],q[1],q[2],q[3])||1;return q.map(v=>v/n); }
  function compose(t, q, s) {
    const [x,y,z,w]=normalizeQuat(q), x2=x+x,y2=y+y,z2=z+z, xx=x*x2,xy=x*y2,xz=x*z2,yy=y*y2,yz=y*z2,zz=z*z2,wx=w*x2,wy=w*y2,wz=w*z2;
    return new Float32Array([
      (1-(yy+zz))*s[0], (xy+wz)*s[0], (xz-wy)*s[0], 0,
      (xy-wz)*s[1], (1-(xx+zz))*s[1], (yz+wx)*s[1], 0,
      (xz+wy)*s[2], (yz-wx)*s[2], (1-(xx+yy))*s[2], 0,
      t[0],t[1],t[2],1
    ]);
  }
  function asArrayBuffer(value) {
    if (value instanceof ArrayBuffer) return value;
    if (ArrayBuffer.isView(value)) return value.buffer.slice(value.byteOffset, value.byteOffset + value.byteLength);
    throw Error('GLB response did not provide binary data (' + Object.prototype.toString.call(value) + ', ' + String(value) + ')');
  }
  function parseGlb(buffer) {
    buffer=asArrayBuffer(buffer);
    const view=new DataView(buffer); if(view.getUint32(0,true)!==0x46546c67) throw Error('Asset is not a GLB file');
    if(view.getUint32(4,true)!==2) throw Error('Only glTF 2.0 GLB assets are supported');
    let off=12,json=null,bin=null;
    while(off+8<=buffer.byteLength){const len=view.getUint32(off,true),type=view.getUint32(off+4,true);off+=8;if(off+len>buffer.byteLength)throw Error('Corrupt GLB chunk length');const chunk=buffer.slice(off,off+len);off+=len;if(type===0x4e4f534a)json=JSON.parse(new TextDecoder().decode(chunk).replace(/[\u0000\u0020]+$/g,''));else if(type===0x004e4942)bin=chunk;}
    if(!json||!bin||!json.meshes?.length||!json.skins?.length)throw Error('GLB must include a mesh and a skin');
    function accessor(index){
      const a=json.accessors[index], bv=json.bufferViews[a.bufferView], info=componentInfo[a.componentType],count=compCount[a.type];
      if(!a||!bv||!info)throw Error('Unsupported GLB accessor');
      const start=(bv.byteOffset||0)+(a.byteOffset||0),stride=bv.byteStride||info.bytes*count;
      if(stride===info.bytes*count)return new info.Type(bin,start,a.count*count);
      const out=new info.Type(a.count*count),dv=new DataView(asArrayBuffer(bin));
      for(let i=0;i<a.count;i++)for(let j=0;j<count;j++){const at=start+i*stride+j*info.bytes;let v;if(a.componentType===5126)v=dv.getFloat32(at,true);else if(a.componentType===5123)v=dv.getUint16(at,true);else if(a.componentType===5121)v=dv.getUint8(at);else if(a.componentType===5125)v=dv.getUint32(at,true);else if(a.componentType===5122)v=dv.getInt16(at,true);else v=dv.getInt8(at);out[i*count+j]=v;}
      return out;
    }
    const primitive=json.meshes[0].primitives[0],attrs=primitive.attributes,skin=json.skins[0];
    const geometry={positions:accessor(attrs.POSITION),normals:accessor(attrs.NORMAL),colors:attrs.COLOR_0!==undefined?accessor(attrs.COLOR_0):null,joints:accessor(attrs.JOINTS_0),weights:accessor(attrs.WEIGHTS_0),indices:accessor(primitive.indices),indexType:json.accessors[primitive.indices].componentType};
    const nodes=json.nodes.map(n=>({name:n.name||'',translation:(n.translation||[0,0,0]).slice(),rotation:(n.rotation||[0,0,0,1]).slice(),scale:(n.scale||[1,1,1]).slice(),children:(n.children||[]).slice(),mesh:n.mesh,skin:n.skin}));
    const parents=Array(nodes.length).fill(-1);nodes.forEach((n,i)=>n.children.forEach(c=>parents[c]=i));
    const inverse=accessor(skin.inverseBindMatrices),jointCount=skin.joints.length;
    const inverseBind=[];for(let i=0;i<jointCount;i++)inverseBind.push(new Float32Array(inverse.slice(i*16,(i+1)*16)));
    const animations=(json.animations||[]).map(anim=>{
      const channels=anim.channels.map(ch=>{const sampler=anim.samplers[ch.sampler];return {node:ch.target.node,path:ch.target.path,times:accessor(sampler.input),values:accessor(sampler.output),components:compCount[json.accessors[sampler.output].type],interpolation:sampler.interpolation||'LINEAR'};});
      const duration=Math.max(0,...channels.map(c=>c.times[c.times.length-1]||0));return {name:anim.name||'Animation',channels,duration};
    });
    return {json,geometry,nodes,parents,joints:skin.joints.slice(),inverseBind,animations,accessor};
  }
  const VERT=`attribute vec3 aPosition;attribute vec3 aNormal;attribute vec4 aColor;attribute vec4 aJoints;attribute vec4 aWeights;uniform mat4 uMvp;uniform mat4 uJoints[16];varying vec4 vColor;varying vec3 vNormal;varying vec3 vPosition;void main(){int j0=int(aJoints.x);int j1=int(aJoints.y);int j2=int(aJoints.z);int j3=int(aJoints.w);vec4 p=vec4(0.0);vec3 n=vec3(0.0);p+=uJoints[j0]*vec4(aPosition,1.0)*aWeights.x;p+=uJoints[j1]*vec4(aPosition,1.0)*aWeights.y;p+=uJoints[j2]*vec4(aPosition,1.0)*aWeights.z;p+=uJoints[j3]*vec4(aPosition,1.0)*aWeights.w;n+=mat3(uJoints[j0])*aNormal*aWeights.x;n+=mat3(uJoints[j1])*aNormal*aWeights.y;n+=mat3(uJoints[j2])*aNormal*aWeights.z;n+=mat3(uJoints[j3])*aNormal*aWeights.w;vColor=aColor;vNormal=n;vPosition=p.xyz;gl_Position=uMvp*p;}`;
  const FRAG=`precision mediump float;varying vec4 vColor;varying vec3 vNormal;varying vec3 vPosition;void main(){vec3 n=normalize(vNormal);float light=0.52+0.36*max(dot(n,normalize(vec3(-0.36,0.66,1.0))),0.0)+0.15*max(n.y,0.0);float rim=pow(1.0-max(dot(n,vec3(0.0,0.0,1.0)),0.0),2.0);vec3 col=vColor.rgb*light+vec3(0.12,0.28,0.23)*rim;gl_FragColor=vec4(col,vColor.a);}`;
  function compile(gl,type,src){const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s)||'Shader compilation failed');return s;}
  function createProgram(gl){const p=gl.createProgram();gl.attachShader(p,compile(gl,gl.VERTEX_SHADER,VERT));gl.attachShader(p,compile(gl,gl.FRAGMENT_SHADER,FRAG));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p)||'Shader link failed');return p;}
  function mount(container, slug, fallbackImage, onStatus, options={}) {
    if(!container)return null;
    const previous=rigs.get(container);if(previous)previous.dispose();
    let disposed=false,frame=0,resizeObserver=null,canvas=null,ctx=null,asset=null,current=null,startedAt=0,finishedReported=false,schedule=()=>{},idleTimer=0,lookX=0,lookY=0,mountedAt=performance.now(),redraw=()=>{};
    const report=(message,ok)=>{if(typeof onStatus==='function')onStatus(message,ok);};
    const portrait=(show)=>{if(fallbackImage)fallbackImage.hidden=!show;};
    const cleanup=()=>{disposed=true;cancelAnimationFrame(frame);if(idleTimer)clearInterval(idleTimer);if(resizeObserver)resizeObserver.disconnect();if(canvas)canvas.remove();rigs.delete(container);};
    function play(kind){
      if(!asset)return false;
      const name=({hello:'Wave',greet:'Wave',wave:'Wave',dance:'Dance',celebrate:'Dance',hop:'AdventureHop',idle:'Idle',walk:'Walk',turn:'Turn',point:'Point'})[String(kind).toLowerCase()]||'Wave';
      const clip=asset.animations.find(a=>a.name===name);if(!clip)return false;
      current={clip,startedAt:performance.now(),looping:(name==='Idle'||name==='Walk')};finishedReported=false;report(`Playing ${clip.name} · ${clip.channels.length} tracks`,true);schedule();return true;
    }
    const entry={play,lookAt(x=0,y=0){lookX=Math.max(-1,Math.min(1,Number(x)||0));lookY=Math.max(-1,Math.min(1,Number(y)||0));if(asset&&!disposed)redraw();},dispose:cleanup};rigs.set(container,entry);
    const url=options.assetUrl||`assets/companions3d/${encodeURIComponent(slug)}.glb`;
    fetch(url).then(r=>{if(!r.ok)throw Error(`GLB request failed (${r.status})`);return r.arrayBuffer();}).then(arrayBuffer=>{
      if(disposed)return;asset=parseGlb(arrayBuffer);
      if(asset.joints.length>32)throw Error('Rig contains too many joints for the bundled renderer');
      const geo=asset.geometry,base=asset.nodes.map(n=>({translation:n.translation.slice(),rotation:n.rotation.slice(),scale:n.scale.slice()}));
      const world=asset.nodes.map(()=>I());
      function framePose(now){
        const trs=base.map(n=>({translation:n.translation.slice(),rotation:n.rotation.slice(),scale:n.scale.slice()}));
        if(current){
          const state=current;const clip=state.clip;const elapsed=Math.max(0,(now-state.startedAt)/1000);const t=state.looping&&clip.duration>0?(elapsed%clip.duration):Math.min(clip.duration,elapsed);
          for(const ch of clip.channels){
            const times=ch.times,values=ch.values,cs=ch.components;let v;
            if(times.length<=1)v=Array.from(values.slice(0,cs));
            else {let lo=0;while(lo<times.length-2&&times[lo+1]<t)lo++;const hi=lo+1,span=times[hi]-times[lo],u=span>0?Math.max(0,Math.min(1,(t-times[lo])/span)):0;
              if(ch.interpolation==='STEP')v=Array.from(values.slice(lo*cs,(lo+1)*cs));
              else {const a=Array.from(values.slice(lo*cs,(lo+1)*cs)),b=Array.from(values.slice(hi*cs,(hi+1)*cs));v=a.map((x,i)=>x+(b[i]-x)*u);if(ch.path==='rotation')v=normalizeQuat(v);}
            }
            if(ch.path==='translation')trs[ch.node].translation=v;else if(ch.path==='rotation')trs[ch.node].rotation=v;else if(ch.path==='scale')trs[ch.node].scale=v;
          }
          if(elapsed>=clip.duration&&!state.looping){current=null;if(!finishedReported){finishedReported=true;requestAnimationFrame(()=>{if(!disposed)report('3D rig ready · animation finished',true);});}}
        }
        // Subtle breathing keeps the companion alive without translating it around the homepage.
        if(!current)trs[2].translation[1]+=Math.sin((now-mountedAt)*Math.PI*2/2200)*.008;
        // Small, clamped head look lets Bloop acknowledge the pointer while its body stays put.
        const yaw=[0,Math.sin(-lookX*.16/2),0,Math.cos(lookX*.16/2)];
        const pitch=[Math.sin(lookY*.12/2),0,0,Math.cos(lookY*.12/2)];
        const qmul=(a,b)=>[a[3]*b[0]+a[0]*b[3]+a[1]*b[2]-a[2]*b[1],a[3]*b[1]-a[0]*b[2]+a[1]*b[3]+a[2]*b[0],a[3]*b[2]+a[0]*b[1]-a[1]*b[0]+a[2]*b[3],a[3]*b[3]-a[0]*b[0]-a[1]*b[1]-a[2]*b[2]];
        trs[3].rotation=normalizeQuat(qmul(trs[3].rotation,qmul(yaw,pitch)));
        function calc(i){world[i]=compose(trs[i].translation,trs[i].rotation,trs[i].scale);const p=asset.parents[i];if(p>=0)world[i]=mul(world[p],world[i]);asset.nodes[i].children.forEach(calc);}
        asset.json.scenes[asset.json.scene||0].nodes.forEach(calc);
        const matrices=[];for(let k=0;k<asset.joints.length;k++)matrices.push(mul(world[asset.joints[k]],asset.inverseBind[k]));return matrices;
      }
      canvas=document.createElement('canvas');canvas.className='citypulsex-glb-canvas';canvas.setAttribute('role','img');canvas.setAttribute('aria-label','Rigged 3D travel companion; use Say hello, Dance break or Adventure hop to play animation clips');canvas.style.cssText='width:100%;height:100%;display:block;background:transparent;';
      ctx=canvas.getContext('2d',{alpha:true,desynchronized:true});if(!ctx)throw Error('Canvas rendering is unavailable in this browser');container.replaceChildren(canvas);portrait(false);
      let cssW=320,cssH=280,dpr=1;
      function resize(){if(disposed||!canvas)return;const box=container.getBoundingClientRect();cssW=Math.max(1,box.width||320);cssH=Math.max(1,box.height||280);dpr=Math.min(window.devicePixelRatio||1,1.5);canvas.width=Math.round(cssW*dpr);canvas.height=Math.round(cssH*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);renderFrame(performance.now());}
      function transformPoint(pos,m){return [m[0]*pos[0]+m[4]*pos[1]+m[8]*pos[2]+m[12],m[1]*pos[0]+m[5]*pos[1]+m[9]*pos[2]+m[13],m[2]*pos[0]+m[6]*pos[1]+m[10]*pos[2]+m[14]];}
      function renderFrame(now){
        if(disposed||!ctx||!asset)return;const matrices=framePose(now);ctx.clearRect(0,0,cssW,cssH);
        const f=1/Math.tan(.68/2),aspect=cssW/Math.max(1,cssH),positions=geo.positions,normals=geo.normals,colors=geo.colors,js=geo.joints,weights=geo.weights,n=positions.length/3,screen=new Array(n),shade=new Float32Array(n),rgb=new Array(n),distance=new Float32Array(n);
        for(let i=0;i<n;i++){
          const pi=i*3,qi=i*4;let p=[positions[pi],positions[pi+1],positions[pi+2]],normal=[normals[pi],normals[pi+1],normals[pi+2]],sum=[0,0,0],sn=[0,0,0],weightSum=0;
          // Bloop's eyelids are procedural so the original GLB needs no external rig package.
          if(slug==='bloop'&&colors){const cr=colors[qi],cg=colors[qi+1],cb=colors[qi+2],darkEye=cr<.15&&cg<.18&&cb<.20,glint=cr>.92&&cg>.92&&cb>.92;const eyeVertex=(darkEye||glint)&&p[2]>.26&&p[1]>1.42&&p[1]<1.68&&Math.abs(p[0])>.045&&Math.abs(p[0])<.23;if(eyeVertex){const t=(now-mountedAt)%4400;let open=1;if(t>=2550&&t<2625)open=1-.9*(t-2550)/75;else if(t>=2625&&t<2665)open=.1;else if(t>=2665&&t<2735)open=.1+.9*(t-2665)/70;p[1]=1.55+(p[1]-1.55)*open;}}
          for(let k=0;k<4;k++){const w=weights[qi+k];if(w<=0)continue;const ji=js[qi+k],m=matrices[ji];const pp=transformPoint(p,m);sum[0]+=pp[0]*w;sum[1]+=pp[1]*w;sum[2]+=pp[2]*w;sn[0]+=(m[0]*normal[0]+m[4]*normal[1]+m[8]*normal[2])*w;sn[1]+=(m[1]*normal[0]+m[5]*normal[1]+m[9]*normal[2])*w;sn[2]+=(m[2]*normal[0]+m[6]*normal[1]+m[10]*normal[2])*w;weightSum+=w;}
          if(weightSum===0){sum=p;sn=normal;}else if(Math.abs(weightSum-1)>1e-5){sum=sum.map(v=>v/weightSum);sn=sn.map(v=>v/weightSum);}
          const y=sum[1]-1.04,zView=sum[2]-4.15,depth=-zView,ndcX=(f/aspect*sum[0])/depth,ndcY=(f*y)/depth;
          screen[i]=[(ndcX+1)*cssW/2,(1-ndcY)*cssH/2];distance[i]=depth;
          const length=Math.hypot(...sn)||1;sn=sn.map(v=>v/length);const dot=Math.max(0,(-.25*sn[0]+.55*sn[1]+.80*sn[2])/Math.hypot(.25,.55,.8));shade[i]=.55+.48*dot+.12*Math.max(0,sn[1]);
          rgb[i]=colors?[colors[qi],colors[qi+1],colors[qi+2],colors[qi+3]]:[.65,.82,.70,1];
        }
        const inds=geo.indices,faces=[];for(let k=0;k<inds.length;k+=3){const a=inds[k],b=inds[k+1],c=inds[k+2];if(!screen[a]||!screen[b]||!screen[c])continue;faces.push([a,b,c,(distance[a]+distance[b]+distance[c])/3]);}
        // Painter's order keeps the small mesh legible in browsers without WebGL.
        faces.sort((a,b)=>b[3]-a[3]);
        for(const face of faces){const [a,b,c]=face;const col=[0,1,2].map(j=>Math.round(Math.min(1,Math.max(0,(rgb[a][j]+rgb[b][j]+rgb[c][j])/3*((shade[a]+shade[b]+shade[c])/3)))*255));const alpha=Math.min(1,Math.max(0,(rgb[a][3]+rgb[b][3]+rgb[c][3])/3));ctx.beginPath();ctx.moveTo(screen[a][0],screen[a][1]);ctx.lineTo(screen[b][0],screen[b][1]);ctx.lineTo(screen[c][0],screen[c][1]);ctx.closePath();ctx.fillStyle=`rgba(${col[0]},${col[1]},${col[2]},${alpha})`;ctx.fill();ctx.lineJoin='round';ctx.lineWidth=.7;ctx.strokeStyle=ctx.fillStyle;ctx.stroke();}
      }
      redraw=()=>renderFrame(performance.now());
      schedule=()=>{if(disposed||!current||frame)return;const tick=(now)=>{frame=0;if(disposed)return;renderFrame(now);if(current)frame=requestAnimationFrame(tick);else renderFrame(performance.now());};frame=requestAnimationFrame(tick);};
      if(typeof ResizeObserver!=='undefined'){resizeObserver=new ResizeObserver(resize);resizeObserver.observe(container);}else window.addEventListener('resize',resize);
      resize();renderFrame(performance.now());idleTimer=window.setInterval(()=>{if(!disposed&&!current)renderFrame(performance.now());},180);report(`3D rig ready · ${asset.joints.length} joints · ${asset.animations.length} clips · self-contained renderer`,true);
    }).catch(err=>{if(disposed)return;console.warn('TRAVESÍA local GLB viewer:',err);portrait(true);canvas?.remove();report(`3D playback unavailable: ${err.message}`,false);});
    return entry;
  }
  window.CityPulseGLBViewer={mount,parseGlb};
})();
