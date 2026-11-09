"""Generate original, low-poly, genuinely skinned TRAVESÍA companion GLB assets.

No external character asset is copied. Each GLB contains a 12-joint skin and
Idle, Wave, Dance, AdventureHop, Walk, and Turn animation clips.
"""
from __future__ import annotations
import json, math, struct
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "frontend" / "assets" / "companions3d"
OUT.mkdir(parents=True, exist_ok=True)

NODES = [
    {"name":"Root", "translation":[0,0,0], "children":[1]},
    {"name":"Hips", "translation":[0,1.0,0], "children":[2,8,10]},
    {"name":"Spine", "translation":[0,.22,0], "children":[3,4,6]},
    {"name":"Head", "translation":[0,.52,0], "children":[]},
    {"name":"LeftUpperArm", "translation":[-.34,.18,0], "children":[5]},
    {"name":"LeftLowerArm", "translation":[-.32,-.14,0], "children":[]},
    {"name":"RightUpperArm", "translation":[.34,.18,0], "children":[7]},
    {"name":"RightLowerArm", "translation":[.32,-.14,0], "children":[]},
    {"name":"LeftUpperLeg", "translation":[-.16,-.03,0], "children":[9]},
    {"name":"LeftLowerLeg", "translation":[0,-.42,0], "children":[]},
    {"name":"RightUpperLeg", "translation":[.16,-.03,0], "children":[11]},
    {"name":"RightLowerLeg", "translation":[0,-.42,0], "children":[]},
]
PARENTS = [-1,0,1,2,2,4,2,6,1,8,1,10]
JOINT_GLOBAL = []
for i,n in enumerate(NODES):
    p=PARENTS[i]
    local=n["translation"]
    if p < 0: JOINT_GLOBAL.append(local[:])
    else: JOINT_GLOBAL.append([JOINT_GLOBAL[p][k]+local[k] for k in range(3)])

CHARACTERS = {
    "sprout": {"base":(0.27,.60,.32,1),"light":(.64,.81,.48,1),"accent":(.95,.75,.35,1),"style":"leaf"},
    "mira": {"base":(.63,.43,.77,1),"light":(.91,.76,.96,1),"accent" :(.98,.58,.72,1),"style":"wings"},
    "orbit": {"base":(.28,.58,.68,1),"light":(.65,.89,.91,1),"accent":(.97,.67,.34,1),"style":"antenna"},
    "paws": {"base":(.84,.57,.43,1),"light":(.98,.82,.68,1),"accent":(.34,.25,.25,1),"style":"cat"},
    "pip": {"base":(.95,.72,.31,1),"light":(1,.90,.58,1),"accent" :(1,.48,.20,1),"style":"bird"},
    "roo": {"base":(.78,.39,.27,1),"light":(.98,.74,.55,1),"accent":(.96,.82,.50,1),"style":"fox"},
    # Original soft-plush octopus inspired by the user's modelling references; no franchise character is copied.
    "bloop": {"base":(.12,.57,.62,1),"light":(.52,.84,.82,1),"accent":(.98,.54,.40,1),"style":"octopus"},
}
# Fix a deliberately simple data definition typo without affecting generated colors.
CHARACTERS["roo"]["light"] = (.98,.74,.55,1)

def vec_norm(v):
    l=math.sqrt(sum(x*x for x in v)) or 1
    return [x/l for x in v]
def rotate_from_y(v):
    # quaternion rotating +Y onto vector v
    d=vec_norm(v); dot=d[1]
    if dot < -0.999999: q=[1,0,0,0]
    else:
        cross=[d[2],0,-d[0]]
        q=vec_norm([cross[0],cross[1],cross[2],1+dot])
    x,y,z,w=q
    return [[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
            [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
            [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
def mat_vec(m,v): return [sum(m[i][j]*v[j] for j in range(3)) for i in range(3)]

def q_axis(axis,angle):
    s=math.sin(angle/2); return [axis[0]*s,axis[1]*s,axis[2]*s,math.cos(angle/2)]
def q_from_z(angle): return q_axis([0,0,1],angle)
def q_from_y(angle): return q_axis([0,1,0],angle)

class Builder:
    def __init__(self):
        self.blob=bytearray(); self.views=[]; self.accessors=[]; self.vertices=[]; self.normals=[]; self.colors=[]; self.joints=[]; self.weights=[]; self.indices=[]
    def align(self, a=4):
        while len(self.blob)%a: self.blob.append(0)
    def buffer_view(self,data,target=None):
        self.align(4); offset=len(self.blob); self.blob.extend(data)
        d={"buffer":0,"byteOffset":offset,"byteLength":len(data)}
        if target: d["target"]=target
        idx=len(self.views); self.views.append(d); return idx
    def accessor(self,values,component_type,typ,count,target=None,normalized=False,minmax=False):
        if component_type==5126: fmt='f'; size=4
        elif component_type==5123: fmt='H'; size=2
        elif component_type==5121: fmt='B'; size=1
        else: raise ValueError(component_type)
        flat=[]
        for row in values:
            if isinstance(row,(list,tuple)): flat.extend(row)
            else: flat.append(row)
        data=struct.pack('<'+fmt*len(flat),*flat)
        view=self.buffer_view(data,target)
        item_count={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16}[typ]
        acc={"bufferView":view,"componentType":component_type,"count":count,"type":typ}
        if normalized: acc["normalized"]=True
        if minmax and count:
            rows=[flat[i*item_count:(i+1)*item_count] for i in range(count)]
            acc["min"]=[min(r[j] for r in rows) for j in range(item_count)]
            acc["max"]=[max(r[j] for r in rows) for j in range(item_count)]
        idx=len(self.accessors); self.accessors.append(acc); return idx
    def add_ellipsoid(self,center,radii,joint,color,rotation=None,segments=12,rings=8):
        rotation=rotation or [[1,0,0],[0,1,0],[0,0,1]]
        start=len(self.vertices)
        for iy in range(rings+1):
            phi=math.pi*iy/rings
            for ix in range(segments+1):
                theta=2*math.pi*ix/segments
                unit=[math.sin(phi)*math.cos(theta), math.cos(phi), math.sin(phi)*math.sin(theta)]
                local=[unit[k]*radii[k] for k in range(3)]
                pos=mat_vec(rotation,local); pos=[pos[k]+center[k] for k in range(3)]
                nlocal=vec_norm([unit[k]/max(radii[k],1e-6) for k in range(3)])
                normal=vec_norm(mat_vec(rotation,nlocal))
                self.vertices.append(pos); self.normals.append(normal); self.colors.append(color)
                self.joints.append([joint,0,0,0]); self.weights.append([1,0,0,0])
        stride=segments+1
        for iy in range(rings):
            for ix in range(segments):
                a=start+iy*stride+ix; b=a+stride
                self.indices.extend([a,b,a+1,b,b+1,a+1])
    def segment(self,a,b,r,joint,color,depth=None):
        d=[b[i]-a[i] for i in range(3)]; length=math.sqrt(sum(x*x for x in d))
        rot=rotate_from_y(d)
        center=[(a[i]+b[i])/2 for i in range(3)]
        self.add_ellipsoid(center,[r,length/2+r*.40,depth if depth is not None else r],joint,color,rot,segments=10,rings=7)
    def joint_sphere(self,center,r,joint,color): self.add_ellipsoid(center,[r,r,r],joint,color,segments=10,rings=7)

def build_character(slug,c):
    b=Builder(); base=c['base']; light=c['light']; accent=c['accent']; style=c['style']; dark=(.13,.16,.19,1); eye=(.09,.12,.13,1)
    # Character body. Bloop is an original eight-tentacled plush creature; others are little humanoid companions.
    gl=JOINT_GLOBAL
    if style == 'octopus':
        b.add_ellipsoid([0,1.30,0],[.43,.43,.36],2,base,segments=22,rings=16)
        b.add_ellipsoid([0,1.60,.005],[.405,.34,.36],3,light,segments=22,rings=16)
        # Large friendly eyes, glints, blush and a tiny curved smile.
        for x in (-.135,.135):
            b.add_ellipsoid([x,1.55,.329],[.083,.103,.052],3,(.035,.075,.09,1),segments=14,rings=10)
            b.add_ellipsoid([x-.022,1.584,.374],[.024,.029,.014],3,(1,1,1,1),segments=10,rings=7)
            b.add_ellipsoid([x*1.82,1.405,.315],[.061,.035,.018],3,(1.0,.48,.49,1),segments=10,rings=6)
        b.add_ellipsoid([0,1.405,.367],[.052,.021,.016],3,(.16,.18,.19,1),segments=12,rings=7)
        # Eight rounded, tapering tentacles; four are articulated through the rig's limb joints.
        anchors=[gl[4],gl[5],gl[6],gl[7],gl[8],gl[9],gl[10],gl[11]]
        ends=[(-.70,1.02,.10),(-.76,.78,.20),(-.48,.50,.32),(-.20,.43,.39),(.70,1.02,.10),(.76,.78,.20),(.48,.50,.32),(.20,.43,.39)]
        for i,(start,end,joint) in enumerate(zip(anchors,ends,range(4,12))):
            mid=[start[0]*.48+end[0]*.52,start[1]*.48+end[1]*.52,start[2]*.48+end[2]*.52]
            col=base if i%2==0 else light
            b.segment(start,mid,.115,joint,col,.115)
            b.segment(mid,end,.075,joint,light,.078)
            b.joint_sphere(end,.077,joint,base)
            # tiny matte suckers visible on the front tentacles
            if i in (1,2,3,4,5,6):
                for k in (0.27,0.48,0.68):
                    pt=[start[d]+(end[d]-start[d])*k for d in range(3)]
                    pt[2]+=.073
                    b.add_ellipsoid(pt,[.022,.020,.012],joint,accent,segments=8,rings=5)
    else:
        b.add_ellipsoid([0,1.22,0],[.30,.40,.215],2,base)
        b.add_ellipsoid([0,1.18,.186],[.20,.25,.055],2,light,segments=12,rings=8)
        b.add_ellipsoid([0,1.78,.015],[.29,.28,.265],3,light)
        b.add_ellipsoid([0,1.68,.246],[.105,.07,.055],3,light)
        for x in [-.092,.092]:
            b.add_ellipsoid([x,1.815,.247],[.035,.045,.024],3,eye,segments=10,rings=7)
            b.add_ellipsoid([x-.008,1.833,.268],[.010,.014,.007],3,(1,1,1,1),segments=8,rings=5)
        b.add_ellipsoid([0,1.704,.301],[.023,.016,.012],3,accent,segments=8,rings=5)
        if style in ('leaf','cat','fox'):
            ear_col=accent if style!='cat' else base
            for x in (-.17,.17):
                b.add_ellipsoid([x,2.045,0],[.075,.19,.07],3,ear_col)
                if style=='cat': b.add_ellipsoid([x,2.045,.055],[.035,.115,.018],3,light)
        if style=='wings':
            for x,sgn in [(-.35,-1),(.35,1)]:
                b.add_ellipsoid([x,1.28,-.16],[.21,.28,.075],2,accent,rotation=[[math.cos(sgn*.4),-math.sin(sgn*.4),0],[math.sin(sgn*.4),math.cos(sgn*.4),0],[0,0,1]])
                b.add_ellipsoid([x*1.25,1.05,-.15],[.14,.19,.06],2,light)
        if style=='antenna':
            b.segment([0,2.00,0],[0,2.18,0],.025,3,accent); b.joint_sphere([0,2.20,0],.065,3,accent)
        if style=='bird': b.add_ellipsoid([0,1.68,.32],[.09,.055,.095],3,accent)
        if style in ('cat','fox'):
            b.segment([.23,1.02,-.03],[.42,1.12,-.02],.09,1,accent); b.segment([.42,1.12,-.02],[.50,1.31,-.02],.085,1,accent)
        b.segment(gl[4],gl[5],.105,4,base,.105); b.segment(gl[5],[gl[5][0]-.08,gl[5][1]-.09,gl[5][2]],.085,5,base,.085)
        b.joint_sphere([gl[5][0]-.08,gl[5][1]-.10,gl[5][2]],.09,5,light)
        b.segment(gl[6],gl[7],.105,6,base,.105); b.segment(gl[7],[gl[7][0]+.08,gl[7][1]-.09,gl[7][2]],.085,7,base,.085)
        b.joint_sphere([gl[7][0]+.08,gl[7][1]-.10,gl[7][2]],.09,7,light)
        b.segment(gl[8],gl[9],.13,8,base,.14); b.segment(gl[9],[gl[9][0],.17,gl[9][2]],.10,9,base,.12)
        b.add_ellipsoid([gl[9][0]+.045,.09,.065],[.14,.075,.19],9,accent)
        b.segment(gl[10],gl[11],.13,10,base,.14); b.segment(gl[11],[gl[11][0],.17,gl[11][2]],.10,11,base,.12)
        b.add_ellipsoid([gl[11][0]+.045,.09,.065],[.14,.075,.19],11,accent)
    # Convert to accessors
    pos_acc=b.accessor(b.vertices,5126,'VEC3',len(b.vertices),34962, minmax=True)
    norm_acc=b.accessor(b.normals,5126,'VEC3',len(b.normals),34962)
    color_acc=b.accessor(b.colors,5126,'VEC4',len(b.colors),34962)
    joints_acc=b.accessor(b.joints,5121,'VEC4',len(b.joints),34962)
    weights_acc=b.accessor(b.weights,5126,'VEC4',len(b.weights),34962)
    idx_component=5123 if max(b.indices)<65536 else 5125
    indices_acc=b.accessor(b.indices,idx_component,'SCALAR',len(b.indices),34963,minmax=True)
    # Inverse bind matrices (column-major translation matrices; bind rotations are identity)
    ibm=[]
    for p in JOINT_GLOBAL:
        x,y,z=p; ibm.append([1,0,0,0, 0,1,0,0, 0,0,1,0, -x,-y,-z,1])
    ibm_acc=b.accessor(ibm,5126,'MAT4',len(ibm))
    # Animated tracks by node index: per-node rotation angles around Z/Y and root translation.
    animations=[]
    def add_anim(name,times,tracks,root_y=None,loop='REPEAT'):
        samplers=[]; channels=[]
        time_acc=b.accessor([[t] for t in times],5126,'SCALAR',len(times),minmax=True)
        for node,axis,angles in tracks:
            qvalues=[q_from_z(a) if axis=='z' else q_from_y(a) for a in angles]
            out=b.accessor(qvalues,5126,'VEC4',len(qvalues))
            samplers.append({"input":time_acc,"output":out,"interpolation":"LINEAR"})
            channels.append({"sampler":len(samplers)-1,"target":{"node":node,"path":"rotation"}})
        if root_y is not None:
            vectors=[[0,y,0] for y in root_y]
            out=b.accessor(vectors,5126,'VEC3',len(vectors))
            samplers.append({"input":time_acc,"output":out,"interpolation":"LINEAR"})
            channels.append({"sampler":len(samplers)-1,"target":{"node":0,"path":"translation"}})
        animations.append({"name":name,"samplers":samplers,"channels":channels})
    add_anim('Idle',[0,.5,1,1.5,2],[(2,'z',[0,.025,0,-.025,0]),(3,'y',[0,.025,0,-.025,0]),(4,'z',[0,.025,0,-.025,0]),(6,'z',[0,-.025,0,.025,0])])
    add_anim('Wave',[0,.2,.4,.6,.8,1.0,1.2,1.4,1.6],[(6,'z',[0,.7,1.05,.8,1.1,.8,1.1,.45,0]),(7,'z',[0,.1,-.4,.55,-.4,.55,-.4,.1,0]),(2,'z',[0,.05,.08,0,-.05,0,.04,0,0])])
    add_anim('Dance',[0,.4,.8,1.2,1.6],[(2,'z',[0,.18,0,-.18,0]),(4,'z',[0,1.15,.3,.9,0]),(6,'z',[0,-.9,-.25,-1.15,0]),(8,'z',[0,-.45,.15,.45,0]),(10,'z',[0,.45,-.15,-.45,0]),(3,'y',[0,.13,0,-.13,0])])
    add_anim('AdventureHop',[0,.2,.4,.6,.8,1.0,1.2],[(4,'z',[0,.75,1.0,.4,.9,.55,0]),(6,'z',[0,-.75,-1.0,-.4,-.9,-.55,0]),(8,'z',[0,-.25,.15,.3,-.15,0,0]),(10,'z',[0,.25,-.15,-.3,.15,0,0])],root_y=[0,.24,.08,0,.22,.08,0])
    # A genuine alternating gait: opposite leg swings, bent knees, counter-swinging arms and gentle weight rise.
    add_anim('Walk',[0,.2,.4,.6,.8,1.0,1.2],[(8,'z',[0,.38,0,-.38,0,.38,0]),(9,'z',[0,-.34,0,.08,0,-.34,0]),(10,'z',[0,-.38,0,.38,0,-.38,0]),(11,'z',[0,.08,0,-.34,0,.08,0]),(4,'z',[0,-.22,0,.22,0,-.22,0]),(6,'z',[0,.22,0,-.22,0,.22,0]),(2,'z',[0,.018,0,-.018,0,.018,0])],root_y=[0,.035,0,.035,0,.035,0])
    add_anim('Turn',[0,.2,.4,.6,.8],[(0,'y',[0,.45,.98,1.35,1.5708]),(2,'z',[0,.035,0,-.025,0])])
    add_anim('Point',[0,.2,.4,.6,.8,1.0],[(6,'z',[0,-.45,-.8,-.65,-.25,0]),(7,'z',[0,-.25,-.35,-.2,-.1,0]),(2,'z',[0,.04,.07,.03,-.01,0])])
    # Mesh and glTF scene. Vertex colors make these genuinely 3D, not billboards.
    gltf={"asset":{"version":"2.0","generator":"TRAVESÍA Original Companion Rig Generator 1.0"},
          "scene":0,"scenes":[{"nodes":[0,12]}],"nodes":NODES+[ {"name":"CompanionSkinnedMesh","mesh":0,"skin":0} ],
          "meshes":[{"name":slug.title()+"SkinnedMesh","primitives":[{"attributes":{"POSITION":pos_acc,"NORMAL":norm_acc,"COLOR_0":color_acc,"JOINTS_0":joints_acc,"WEIGHTS_0":weights_acc},"indices":indices_acc,"material":0,"mode":4}]}],
          "skins":[{"name":"CompanionSkeleton","inverseBindMatrices":ibm_acc,"skeleton":0,"joints":list(range(12))}],
          "materials":[{"name":"SoftMatteVertexColor","pbrMetallicRoughness":{"baseColorFactor":[1,1,1,1],"metallicFactor":0,"roughnessFactor":.78},"doubleSided":True}],
          "animations":animations,"buffers":[{"byteLength":0}],"bufferViews":b.views,"accessors":b.accessors}
    # Pack GLB JSON and BIN chunks; one self-contained file per character.
    b.align(4); binary=bytes(b.blob); gltf['buffers'][0]['byteLength']=len(binary)
    raw_json=json.dumps(gltf,separators=(',',':')).encode(); raw_json+=b' '*((4-len(raw_json)%4)%4)
    binary+=b'\x00'*((4-len(binary)%4)%4)
    total=12+8+len(raw_json)+8+len(binary)
    glb=struct.pack('<4sII',b'glTF',2,total)+struct.pack('<I4s',len(raw_json),b'JSON')+raw_json+struct.pack('<I4s',len(binary),b'BIN\x00')+binary
    (OUT/f'{slug}.glb').write_bytes(glb)
    print(f'{slug}: {len(glb):,} bytes, {len(b.vertices)} vertices, {len(animations)} clips, 12 joints')

if __name__=='__main__':
    for name, cfg in CHARACTERS.items(): build_character(name,cfg)
