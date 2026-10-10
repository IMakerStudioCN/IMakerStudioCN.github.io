import bpy, math, random, os
from mathutils import Vector
from math import sin, cos, pi
random.seed(17)
OUT = os.path.dirname(os.path.abspath(__file__))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
base = bpy.data.collections.get('Collection'); base.name = '00 | STUDIO'
COL = base
def collection(name):
    global COL
    COL=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(COL)
def put(o, name, mat=None, parent=None):
    o.name=name
    for c in list(o.users_collection): c.objects.unlink(o)
    COL.objects.link(o)
    if mat: o.data.materials.append(mat)
    if parent: o.parent=parent
    return o
def material(name, color, metallic=0, rough=.5, textured=False):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    nt=m.node_tree; n=nt.nodes; l=nt.links; p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metallic; p.inputs['Roughness'].default_value=rough
    if textured:
        tc=n.new('ShaderNodeTexCoord')
        noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=5; noise.inputs['Detail'].default_value=4
        l.new(tc.outputs['Generated'],noise.inputs['Vector'])
        ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.2; ramp.color_ramp.elements[1].position=.8
        ramp.color_ramp.elements[0].color=(*(v*.58 for v in color),1); ramp.color_ramp.elements[1].color=(*(v*1.3 for v in color),1)
        l.new(noise.outputs['Fac'],ramp.inputs[0]); l.new(ramp.outputs['Color'],p.inputs['Base Color'])
        fine=n.new('ShaderNodeTexNoise'); fine.inputs['Scale'].default_value=165; fine.inputs['Detail'].default_value=2
        l.new(tc.outputs['Object'],fine.inputs['Vector'])
        bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.23; bump.inputs['Distance'].default_value=.018
        l.new(fine.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs['Normal'],p.inputs['Normal'])
        mr=n.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value=rough-.1; mr.inputs['To Max'].default_value=rough+.14
        l.new(fine.outputs['Fac'],mr.inputs['Value']); l.new(mr.outputs['Result'],p.inputs['Roughness'])
    return m
paint=material('ARMOR | weathered olive ceramic paint',(.145,.181,.096),.55,.47,True)
darkpaint=material('ARMOR | dark olive panels',(.083,.107,.057),.5,.55,True)
edge=material('WEAR | exposed steel edges',(.18,.175,.14),.8,.44,True)
steel=material('TRACK | oxidized manganese steel',(.076,.065,.048),.83,.62,True)
rubber=material('RUBBER | carbon black',(.018,.021,.018),.03,.78,True)
black=material('RECESS | soot and shadow',(.006,.009,.01),.12,.78)
glass=material('OPTICS | coated blue glass',(.016,.125,.19),.72,.13)
canvas=material('STOWAGE | olive canvas',(.21,.225,.145),0,.91,True)
mark=material('MARKINGS | worn ivory',(.69,.72,.58),.1,.7)
red=material('TAIL LAMP | ruby',(.28,.014,.009),.25,.23)
lightmat=material('HEADLIGHT | lens',(.8,.82,.7),.3,.17)
def bevel(o,w=.03):
    if w:
        if edge.name not in o.data.materials: o.data.materials.append(edge)
        b=o.modifiers.new('Soft manufactured edges','BEVEL'); b.width=w; b.segments=2; b.material=len(o.data.materials)-1
        b=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return o
def cube(name,loc,dim,mat=paint,b=.025,parent=None,rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=put(bpy.context.object,name,mat,parent); o.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if rot: o.rotation_euler=rot
    return bevel(o,b)
def cyl(name,loc,r,depth,mat=paint,axis=(0,0,1),verts=48,b=.01,parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc)
    o=put(bpy.context.object,name,mat,parent); o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    for p in o.data.polygons: p.use_smooth=len(p.vertices)==4
    return bevel(o,b)
def rod(name,a,b,r=.025,mat=paint,parent=None):
    return cyl(name,(Vector(a)+Vector(b))/2,r,(Vector(b)-Vector(a)).length,mat,Vector(b)-Vector(a),24,.004,parent)
def mesh(name,verts,faces,mat=paint,b=.025,parent=None):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update(); o=bpy.data.objects.new(name,me); COL.objects.link(o); me.materials.append(mat)
    if parent: o.parent=parent
    return bevel(o,b)
def rings(name,lower,upper,z0,z1,mat=paint,b=.025,parent=None):
    v=[(x,y,z0) for x,y in lower]+[(x,y,z1) for x,y in upper]; n=len(lower)
    f=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,v,f,mat,b,parent)
def line(name,pts,r,mat=paint,parent=None):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.bevel_depth=r; cu.bevel_resolution=2
    sp=cu.splines.new('POLY'); sp.points.add(len(pts)-1)
    for p,v in zip(sp.points,pts): p.co=(*v,1)
    o=bpy.data.objects.new(name,cu); COL.objects.link(o); o.data.materials.append(mat)
    if parent: o.parent=parent
    return o
def torus(name,loc,major,minor,mat=steel,rot=None,parent=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=40,minor_segments=10,location=loc)
    o=put(bpy.context.object,name,mat,parent)
    if rot:o.rotation_euler=rot
    for p in o.data.polygons:p.use_smooth=True
    return o
def empty(name):
    o=bpy.data.objects.new(name,None); COL.objects.link(o); o.empty_display_size=.4; return o
def bolt(name,loc,axis=(0,0,1),r=.032,parent=None):return cyl(name,loc,r,.023,edge,axis,6,.002,parent)

collection('01 | HULL AND ARMOR')
root=empty('TANK | master control')
hull=rings('Lower hull welded tub',[(-2.95,-1.12),(2.95,-1.12),(2.95,1.12),(-2.95,1.12)],[(-3.42,-1.39),(3.3,-1.39),(3.3,1.39),(-3.42,1.39)],.73,1.67,paint,parent=root)
rings('Upper hull sloped glacis',[(-3.45,-1.43),(3.35,-1.43),(3.35,1.43),(-3.45,1.43)],[(-2.48,-1.40),(3.24,-1.40),(3.24,1.40),(-2.48,1.40)],1.56,2.02,paint,parent=root)
cube('Front lower applique armor',(-3.16,0,1.22),(.18,2.55,.52),darkpaint,.035,root,rot=(0,-.28,0))
for s in [-1,1]:
    cube('Track fender continuous',(.03,s*1.67,1.89),(6.93,.70,.13),paint,.024,root)
    for i in range(6):
        x=-2.76+i*1.105
        cube('Side skirt spaced armor %s %02d'%(s,i),(x,s*1.95,1.61),(1.05,.11,.68),darkpaint if i%3==0 else paint,.016,root)
        cube('Skirt lower rubber flap',(x,s*1.94,1.19),(1.045,.06,.25),rubber,.008,root)
        for xx in [x-.4,x+.4]:bolt('Skirt retaining fastener',(xx,s*2.014,1.80),(0,s,0),parent=root)
        cube('Skirt hinge',(x,s*1.98,1.965),(.27,.08,.07),edge,.01,root)
    for x in [-3.34,3.34]:cube('Mud guard flexible end',(x,s*1.65,1.31),(.075,.68,.8),rubber,.015,root,rot=(0,.13 if x<0 else -.13,0))

collection('02 | SUSPENSION AND ROAD WHEELS')
for s in [-1,1]:
    y=s*1.60
    for i in range(6):
        x=-2.25+i*.9; z=.78
        rod('Trailing suspension arm',(x+.23,s*1.18,1.1),(x,y,z),.095,darkpaint,root)
        cyl('Rubber roadwheel tire',(x,y,z),.515,.46,rubber,(0,1,0),64,.02,root)
        for ss in [-1,1]:
            yy=y+ss*.237
            cyl('Pressed steel wheel rim',(x,yy,z),.425,.035,paint,(0,1,0),64,.014,root)
            torus('Rim seam',(x,yy+ss*.02,z),.34,.012,edge,(pi/2,0,0),root)
            cyl('Axle hub',(x,yy+ss*.045,z),.162,.1,darkpaint,(0,1,0),40,.015,root)
            cyl('Hub cap',(x,yy+ss*.101,z),.104,.025,paint,(0,1,0),40,.006,root)
            for k in range(8):
                a=k*pi/4; bolt('Roadwheel hub bolt',(x+.23*cos(a),yy+ss*.03,z+.23*sin(a)),(0,ss,0),.024,root)
    for x in [-2.77,2.77]:
        z=.91
        cyl('Drive sprocket' if x>0 else 'Front idler',(x,y,z),.53,.39,steel,(0,1,0),64,.016,root)
        cyl('End wheel face',(x,y+s*.22,z),.42,.055,paint,(0,1,0),48,.014,root)
        cyl('End wheel hub',(x,y+s*.27,z),.17,.09,darkpaint,(0,1,0),40,.013,root)
        for k in range(12):
            a=k*pi/6
            cyl('Sprocket face recess',(x+.295*cos(a),y+s*.255,z+.295*sin(a)),.055,.01,black,(0,1,0),16,.002,root)
            if x>0:
                o=cube('Sprocket drive tooth',(x+.538*cos(a),y,z+.538*sin(a)),(.13,.42,.15),edge,.01,root);o.rotation_euler.y=-a
    for x in [-1.75,0,1.75]:cyl('Upper return roller',(x,y,1.42),.205,.40,rubber,(0,1,0),40,.012,root)

collection('03 | INDIVIDUAL TRACK LINKS')
# Closed capsule path, each shoe follows its own tangent.
a=2.77; radius=.65; zc=.91; straight=2*a; arc=pi*radius; total=2*straight+2*arc; count=88
def path(d):
    if d<straight:return (-a+d,zc+radius,0)
    d-=straight
    if d<arc:
        th=pi/2-d/radius; return (a+radius*cos(th),zc+radius*sin(th),pi/2-th)
    d-=arc
    if d<straight:return (a-d,zc-radius,pi)
    d-=straight; th=-pi/2-d/radius;return (-a+radius*cos(th),zc+radius*sin(th),pi/2-th)
parts=[]
parts.append(cube('Track shoe template',(0,0,0),(total/count*.93,.66,.10),steel,.009))
for yy in [-.165,.165]: parts.append(cube('Rubber traction pad',(0,yy,.068),(.133,.267,.044),rubber,.009))
for xx in [-.079,.079]:parts.append(cube('Steel grouser',(xx,0,.056),(.025,.65,.035),edge,.005))
for yy in [-.344,.344]:parts.append(cyl('Hinge pin',(0,yy,0),.034,.042,edge,(0,1,0),12,.004))
parts.append(cube('Inner guide tooth',(0,0,-.112),(.085,.09,.15),steel,.014))
bpy.ops.object.select_all(action='DESELECT')
for o in parts:
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join(); template=bpy.context.object
data=template.data; bpy.data.objects.remove(template,do_unlink=True)
for s in [-1,1]:
    for i in range(count):
        x,z,t=path(total*i/count);o=bpy.data.objects.new('Track %s | shoe %03d'%(s,i+1),data);COL.objects.link(o);o.location=(x,s*1.60,z);o.rotation_euler.y=t;o.parent=root

collection('04 | TURRET ASSEMBLY')
turret=empty('TURRET | rotate local Z');turret.parent=root
cyl('Turret bearing ring',(.1,0,2.075),1.22,.20,steel,verts=96,b=.025,parent=turret)
lower=[(-1.75,-.73),(-1.12,-1.26),(1.62,-1.20),(2.12,-.87),(2.12,.87),(1.62,1.20),(-1.12,1.26),(-1.75,.73)]
upper=[(-1.29,-.65),(-.91,-1.04),(1.49,-1.00),(1.88,-.73),(1.88,.73),(1.49,1.00),(-.91,1.04),(-1.29,.65)]
rings('Angular welded turret',lower,upper,2.15,3.03,paint,.045,turret)
for s in [-1,1]:
    lo=[(-1.83,s*.53),(-1.38,s*1.33),(.20,s*1.40),(.18,s*.84)]
    hi=[(-1.33,s*.54),(-1.02,s*1.09),(.17,s*1.14),(.12,s*.84)]
    if s<0:lo.reverse();hi.reverse()
    rings('Composite cheek armor',lo,hi,2.28,2.99,darkpaint,.025,turret)
    for x in [.47,.96,1.45]:
        cube('Turret side modular block',(x,s*1.178,2.65),(.445,.18,.51),paint,.023,turret,rot=(s*.12,0,0))
        for zz in [2.49,2.8]:bolt('Cheek armor bolt',(x,s*1.277,zz),(0,s,0),.032,turret)
    # welded edge bead and grab handles
    line('Turret weld seam',[(x,y,3.038) for x,y in upper[0:4]] if s<0 else [(x,y,3.038) for x,y in upper[4:8]],.008,edge,turret)
    for x in [.35,1.0]:line('Turret side grab rail',[(x-.18,s*1.16,2.99),(x-.18,s*1.29,3.08),(x+.18,s*1.29,3.08),(x+.18,s*1.16,2.99)],.016,edge,turret)

collection('05 | GUN AND MANTLET')
gun=empty('GUN | elevation pivot');gun.parent=turret
cube('Mantlet armored collar',(-1.60,0,2.64),(.57,.87,.58),darkpaint,.10,gun)
cyl('Gun trunnion housing',(-1.91,0,2.68),.25,.44,steel,(-1,0,0),64,.015,gun)
for i in range(5):cyl('Mantlet dust seal',(-1.80-i*.07,0,2.68),.26-i*.014,.045,rubber,(-1,0,0),48,.009,gun)
cyl('Main gun tube',(-4.08,0,2.68),.104,4.25,steel,(-1,0,0),64,.008,gun)
for x,dep,r in [(-2.57,1.0,.151),(-3.95,1.15,.131),(-5.24,1.23,.113)]:
    cyl('Segmented thermal sleeve',(x,0,2.68),r,dep,paint,(-1,0,0),64,.007,gun)
    for xx in [x-dep/2+.028,x+dep/2-.028]:cyl('Thermal sleeve clamp',(xx,0,2.68),r+.017,.055,darkpaint,(-1,0,0),64,.008,gun)
cyl('Bore evacuator',(-3.35,0,2.68),.208,.55,paint,(-1,0,0),64,.025,gun)
for xx in [-3.61,-3.09]:cyl('Evacuator steel ring',(xx,0,2.68),.215,.055,edge,(-1,0,0),64,.008,gun)
# Open muzzle annulus, with recessed dark bore.
vs=[]
for x,r in [(-6.22,.12),(-6.08,.12),(-6.22,.079),(-5.90,.079)]:
    vs.extend([(x,r*cos(i*2*pi/64),2.68+r*sin(i*2*pi/64)) for i in range(64)])
fs=[]
for i in range(64):
    j=(i+1)%64;fs.extend([(i,j,64+j,64+i),(i,128+i,128+j,j),(128+i,192+i,192+j,128+j)])
mesh('Open gun muzzle',vs,fs,edge,.002,gun)
cyl('Bore interior darkness',(-5.89,0,2.68),.078,.01,black,(-1,0,0),64,0,gun)
cube('Muzzle reference sensor',(-5.95,0,2.83),(.21,.14,.11),darkpaint,.013,gun)

collection('06 | DECK FITTINGS AND OPTICS')
for x,y,r in [(.70,-.55,.43),(-.40,.43,.37)]:
    cyl('Hatch gasket',(x,y,3.043),r+.034,.034,rubber,verts=64,parent=turret)
    cyl('Roof hatch lid',(x,y,3.089),r,.070,paint,verts=64,b=.013,parent=turret)
    line('Hatch lifting handle',[(x-.12,y,3.13),(x-.12,y,3.22),(x+.12,y,3.22),(x+.12,y,3.13)],.02,edge,turret)
    cube('Hatch hinge',(x+r-.05,y,3.135),(.11,.28,.095),darkpaint,.01,turret)
    for k in range(8):
        t=pi*k/4;bolt('Hatch perimeter bolt',(x+(r-.055)*cos(t),y+(r-.055)*sin(t),3.132),r=.018,parent=turret)
for i in range(6):
    t=i*2*pi/6; x=.70+.49*cos(t); y=-.55+.49*sin(t)
    cube('Commander periscope block',(x,y,3.11),(.19,.12,.13),darkpaint,.014,turret,rot=(0,0,t+pi/2))
    cube('Periscope lens',(x,y,3.18),(.128,.085,.012),glass,.004,turret,rot=(0,0,t+pi/2))
cube('Gunner optical housing',(-.82,-.60,3.18),(.48,.39,.32),darkpaint,.04,turret)
cube('Gunner optic dark bezel',(-1.069,-.60,3.19),(.018,.31,.22),black,.015,turret)
cube('Gunner blue optical window',(-1.08,-.60,3.19),(.008,.25,.15),glass,.012,turret)
cyl('Panoramic sight base',(.57,.54,3.15),.18,.23,darkpaint,verts=48,parent=turret)
cube('Panoramic sight head',(.57,.54,3.35),(.31,.32,.26),paint,.035,turret)
cube('Panoramic sight glass',(.407,.54,3.35),(.014,.24,.15),glass,.012,turret)
for s in [-1,1]:
    for k in range(4):
        loc=(-.30+k*.20,s*1.24,2.91+k*.005);axis=Vector((-.45,s*.55,.55)).normalized()
        cyl('Smoke launcher tube',loc,.059,.30,darkpaint,axis,32,.007,turret)
        cap=Vector(loc)+axis*.155;cyl('Smoke launcher cap',cap,.051,.013,black,axis,32,.002,turret)
    cyl('Aerial spring base',(1.43,s*.80,3.16),.073,.23,black,parent=turret)
    rod('Flexible radio aerial',(1.43,s*.80,3.27),(1.51,s*.83,4.57 if s<0 else 4.15),.010,steel,turret)
    for i in range(8):torus('Aerial spring winding',(1.43,s*.8,3.09+i*.015),.041,.008,edge,parent=turret)
# driver's hatch on exposed front deck
cube('Driver hatch',(-2.23,0,2.045),(.53,.68,.075),darkpaint,.04,root)
for y in [-.22,0,.22]:
    cube('Driver periscope guard',(-2.48,y,2.09),(.17,.17,.12),paint,.014,root)
    cube('Driver periscope glass',(-2.575,y,2.105),(.01,.125,.048),glass,.002,root)
# rear engine grilles
for y in [-.76,.76]:
    cube('Engine grille recessed frame',(2.62,y,2.043),(.86,1.08,.045),black,.01,root)
    for i in range(13):cube('Engine cooling louvre',(2.24+i*.062,y,2.075),(.033,1.02,.032),darkpaint,.003,root,rot=(0,.3,0))
    for x in [2.20,3.04]:
        for yy in [y-.49,y+.49]:bolt('Deck access screw',(x,yy,2.084),r=.02,parent=root)
for y in [-.59,.59]:
    cube('Rear exhaust recess',(3.335,y,1.56),(.10,.83,.36),black,.012,root)
    for i in range(5):cube('Exhaust horizontal slat',(3.397,y,1.43+i*.063),(.09,.8,.026),steel,.004,root)
for s in [-1,1]:
    cube('Headlamp housing',(-3.17,s*1.19,1.92),(.30,.32,.24),darkpaint,.04,root)
    cyl('Headlight round lens',(-3.331,s*1.19,1.93),.089,.022,lightmat,(-1,0,0),48,.006,root)
    for dy in [-.085,.085]:line('Headlight guard',[(-3.4,s*1.19+dy,1.83),(-3.43,s*1.19+dy,2.09),(-3.06,s*1.19+dy,2.09)],.015,edge,root)
    cube('Tail lamp frame',(3.39,s*1.17,1.82),(.07,.21,.14),black,.017,root)
    cube('Tail lamp',(3.431,s*1.17,1.82),(.023,.15,.082),red,.011,root)
    for xx in [-3.40,3.41]:
        cube('Tow shackle mount',(xx,s*.91,1.28),(.18,.20,.16),paint,.016,root)
        torus('Tow shackle',(xx+(-.10 if xx<0 else .10),s*.91,1.21),.105,.027,edge,(pi/2,0,0),root)
# tow cable along rear deck edge
for s in [-1,1]:
    pts=[(-1.6,s*1.47,2.02),(-.6,s*1.51,2.025),(1.2,s*1.5,2.03),(2.9,s*1.40,2.05),(3.12,s*1.16,2.06)]
    line('Braided tow cable',pts,.024,steel,root)
    for xx in [-1.4,.4,1.6]:cube('Cable retaining clip',(xx,s*1.49,2.035),(.09,.13,.08),paint,.009,root)

collection('07 | STOWAGE AND REAR BASKET')
cube('Turret bustle storage box',(2.01,0,2.65),(.47,1.87,.51),darkpaint,.035,turret)
for s in [-1,1]:cube('Stowage latch',(2.265,s*.55,2.66),(.04,.07,.17),edge,.005,turret)
# Open tubular basket with fine steel grid
for z in [2.35,2.79]:line('Basket perimeter',[(1.94,-1.01,z),(2.65,-1.01,z),(2.65,1.01,z),(1.94,1.01,z)],.023,edge,turret)
for y in [-1.01,1.01]:
    for x in [1.94,2.3,2.65]:rod('Basket vertical brace',(x,y,2.35),(x,y,2.79),.017,edge,turret)
for i in range(23):
    y=-.96+i*.087;rod('Basket mesh vertical',(2.65,y,2.36),(2.65,y,2.78),.0045,steel,turret)
for j in range(6):
    z=2.37+j*.079;rod('Basket mesh crosswire',(2.65,-1,z),(2.65,1,z),.0045,steel,turret)
for s in [-1,1]:
    for i in range(9):
        x=1.95+i*.085;rod('Basket side mesh',(x,s*1.01,2.36),(x,s*1.01,2.78),.0045,steel,turret)
    for j in range(5):rod('Basket side crosswire',(1.95,s*1.01,2.4+j*.085),(2.65,s*1.01,2.4+j*.085),.0045,steel,turret)
for y in [-.50,.12,.67]:
    o=cube('Canvas equipment bag',(2.35,y,2.65),(.43,.46,.40),canvas,.095,turret)
    for yy in [y-.14,y+.14]:cube('Canvas securing strap',(2.35,yy,2.853),(.37,.034,.015),rubber,.004,turret)
# external tools on rear hull
rod('Shovel wooden shaft',(1.95,-1.12,2.10),(3.12,-1.12,2.10),.025,canvas,root)
cube('Shovel steel blade',(3.07,-1.12,2.12),(.33,.24,.033),steel,.027,root)

collection('08 | MARKINGS AND SURFACE WEAR')
def lettering(name,body,loc,rot,size,parent):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.extrude=.0004;cu.align_x='CENTER';cu.align_y='CENTER'
    o=bpy.data.objects.new(name,cu);COL.objects.link(o);o.location=loc;o.rotation_euler=rot;o.data.materials.append(mark);o.parent=parent
lettering('Port tactical number','07',(.87,-1.285,2.66),(pi/2,0,0),.32,turret)
lettering('Starboard tactical number','07',(.87,1.285,2.66),(pi/2,0,pi),.32,turret)
lettering('Front identification','I / 07',(-3.282,0,1.30),(pi/2,0,-pi/2),.18,root)
for s in [-1,1]:
    # Sparse chips, concentrated around panel seams and fasteners.
    for i in range(105):
        x=random.uniform(-3.18,3.18); z=random.choice([random.uniform(1.30,1.36),random.uniform(1.85,1.92)])
        cube('Skirt paint chip',(x,s*2.008,z),(random.uniform(.008,.06),.002,random.uniform(.004,.012)),edge,0,root,rot=(0,random.uniform(-.4,.4),0))
    for i in range(20):
        x=random.uniform(.30,1.63);z=random.uniform(2.42,2.86)
        cube('Turret edge scuff',(x,s*1.277,z),(random.uniform(.01,.045),.0015,.006),edge,0,turret)

collection('00 | LIGHTING AND PRESENTATION')
ground=material('STUDIO | charcoal concrete',(.078,.087,.083),.16,.67,True)
cube('Studio ground',(0,0,.035),(200,200,.15),ground,.01)
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,color,size,target=(0,0,1)):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);COL.objects.link(o);o.location=loc;aim(o,target)
area('Key | broad warm softbox',(-4,-5,9),2300,(1,.89,.72),7)
area('Fill | cool overhead',(1,4,7),1900,(.70,.83,1),6)
area('Rim | rear strip',(6,-1,6),2500,(1,.95,.81),5)
area('Front soft fill',(-8,1,4),650,(.85,.92,1),4)
world=bpy.data.worlds.new('Neutral studio ambience');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.18,.22,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35;bpy.context.scene.world=world
def camera(name,loc,target,lens):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);COL.objects.link(o);o.location=loc;d.lens=lens;aim(o,target);return o
cam=camera('CAMERA | hero front three-quarter',(-11.8,-13.2,7.5),(-.8,0,1.85),48)
camera('CAMERA | rear detail',(10,-10,6),(0,0,1.8),53)
camera('CAMERA | side profile',(-.2,-15,4.2),(-1,0,1.9),50)
scene=bpy.context.scene;scene.camera=cam;scene.unit_settings.system='METRIC'
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    gpu=False
    for d in prefs.devices:
        d.use=d.type!='CPU';gpu=gpu or d.use
    if gpu:scene.cycles.device='GPU'
except Exception: pass
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(OUT,'tank_hero.png')
scene.view_settings.view_transform='AgX'
scene.render.film_transparent=False
scene['Design']='IRONCLAD / 07 - original modern MBT exterior study'
scene['Controls']='TANK | master control; TURRET | rotate local Z; GUN | elevation pivot'
# Move the gun control to the trunnion while preserving the assembled geometry.
gun_children=[(o,o.matrix_world.copy()) for o in gun.children]
gun.location=(-1.65,0,2.68)
bpy.context.view_layer.update()
for o,matrix in gun_children:o.matrix_world=matrix
# Use a sensible solid studio view when the file opens.
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active=None
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.region_3d.view_perspective='CAMERA'
            ar.spaces.active.shading.color_type='MATERIAL'
            ar.spaces.active.shading.light='STUDIO'
            ar.spaces.active.overlay.show_overlays=False
            ar.spaces.active.clip_end=500
readme=bpy.data.texts.new('ABOUT | IRONCLAD 07');readme.write(open(os.path.join(OUT,'README.txt')).read())
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Ironclad_07.blend'))
print('MODEL_SAVED',len(bpy.data.objects),'objects',flush=True)
bpy.ops.render.render(write_still=True)
print('RENDER_COMPLETE',flush=True)
