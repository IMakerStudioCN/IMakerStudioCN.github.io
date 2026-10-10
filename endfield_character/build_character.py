import bpy, math, os, random, json
from math import sin, cos, pi, sqrt
from mathutils import Vector, Matrix
random.seed(17)
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name!='Collection': bpy.data.collections.remove(c)
COL=bpy.data.collections.get('Collection'); COL.name='00 | Character control'
root=bpy.data.objects.new('OPERATOR | master control',None); COL.objects.link(root)
root.empty_display_type='PLAIN_AXES'; root.empty_display_size=.2
root.location.z=-.016
def collection(name):
    global COL
    COL=bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if COL.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(COL)
    return COL
def link_obj(o,name,material=None):
    o.name=name
    for c in list(o.users_collection): c.objects.unlink(o)
    COL.objects.link(o)
    if material: o.data.materials.append(material)
    if root: o.parent=root
    return o
def mat(name,color,metallic=0,rough=.5):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color[:3],1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color[:3],1)
    p.inputs['Metallic'].default_value=metallic; p.inputs['Roughness'].default_value=rough
    return m
def fabric(name,color,rough=.7,scale=420):
    m=mat(name,color,0,rough); n=m.node_tree.nodes; l=m.node_tree.links; p=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=scale; tex.inputs['Detail'].default_value=2
    bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.16; bump.inputs['Distance'].default_value=.00032
    l.new(tex.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs['Normal'],p.inputs['Normal'])
    p.inputs['Sheen Weight'].default_value=.14
    return m
def mesh(name,verts,faces,material,smooth=True,sub=0):
    d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new(name,d);link_obj(o,name,material)
    if smooth:
        for p in d.polygons:p.use_smooth=True
    if sub:
        mod=o.modifiers.new('Surface refinement','SUBSURF');mod.levels=sub;mod.render_levels=sub
    return o
def uv(name,loc,scale,material,segments=48,rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
    o=bpy.context.object;o.scale=scale;link_obj(o,name,material)
    for p in o.data.polygons:p.use_smooth=True
    return o
def cube(name,loc,scale,material,bevel=.005):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);link_obj(o,name,material)
    if bevel:
        b=o.modifiers.new('Soft manufactured edges','BEVEL');b.width=bevel;b.segments=3
        n=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return o
def curve(name,points,radius,material):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=16;d.bevel_depth=radius;d.bevel_resolution=3
    s=d.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for b,p in zip(s.bezier_points,points):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,d);link_obj(o,name,material);return o
def rod(name,a,b,radius,material):
    a=Vector(a);b=Vector(b);delta=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=radius,depth=delta.length,location=(a+b)/2)
    o=bpy.context.object;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();link_obj(o,name,material)
    for p in o.data.polygons:p.use_smooth=True
    return o
def loft(name,rings,material,N=64,sub=1):
    # (z, x radius, y radius, x center, y center)
    v=[]
    for z,rx,ry,cx,cy in rings:
        for j in range(N):
            a=j*2*pi/N;v.append((cx+rx*cos(a),cy+ry*sin(a),z))
    f=[tuple(reversed(range(N)))]
    for i in range(len(rings)-1):
        for j in range(N):f.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
    f.append(tuple((len(rings)-1)*N+j for j in range(N)))
    return mesh(name,v,f,material,True,sub)
def limb(name,centers,radii,material,N=32,sub=1):
    v=[]
    for i,(c,r) in enumerate(zip(centers,radii)):
        c=Vector(c);t=Vector(centers[min(i+1,len(centers)-1)])-Vector(centers[max(i-1,0)])
        t.normalize();e1=Vector((0,1,0));e2=t.cross(e1).normalized()
        rx,ry=(r,r) if isinstance(r,(float,int)) else r
        for j in range(N):
            a=2*pi*j/N;v.append(c+e1*(cos(a)*ry)+e2*(sin(a)*rx))
    f=[tuple(reversed(range(N)))]
    for i in range(len(centers)-1):
        for j in range(N):f.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
    f.append(tuple((len(centers)-1)*N+j for j in range(N)))
    return mesh(name,v,f,material,True,sub)
def text_obj(name,body,loc,size,material,rot=(pi/2,0,0)):
    d=bpy.data.curves.new(name,'FONT');d.body=body;d.size=size;d.align_x='CENTER';d.align_y='CENTER';d.extrude=.00008
    o=bpy.data.objects.new(name,d);link_obj(o,name,material);o.location=loc;o.rotation_euler=rot;return o

skin=mat('Skin | warm porcelain',(.79,.595,.486),0,.57)
skin.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value=.065
jacket=fabric('Shell | warm light grey technical weave',(.48,.50,.47),.67)
ivory=mat('Trim | light grey polymer',(.64,.665,.61),.12,.48)
black=fabric('Sleeves | graphite technical fabric',(.018,.023,.024),.63)
lining=fabric('Hood | black padded nylon',(.025,.029,.027),.78)
dark=fabric('Harness | charcoal woven webbing',(.022,.026,.023),.75)
stitch=mat('Seams | graphite',(.065,.075,.067),0,.68)
red=fabric('Accent | burgundy webbing',(.12,.015,.031),.66)
metal=mat('Hardware | brushed gunmetal',(.21,.24,.215),.72,.32)
sole=mat('Boot | black rubber',(.012,.015,.017),0,.86)
leather=fabric('Boot | graphite coated leather',(.035,.044,.042),.44,185)
tights=fabric('Legwear | dark umber fine knit',(.066,.045,.040),.48,850)
skirtmat=fabric('Skirt | layered charcoal fabric',(.039,.042,.042),.72)
wrapmat=fabric('Waist drape | ash grey mauve',(.22,.205,.215),.85)
accent=mat('Insignia | warm white',(.74,.77,.68),.12,.49)

collection('01 | Body and legs')
loft('Neck',[(1.37,.044,.044,0,0),(1.41,.043,.044,0,0),(1.47,.036,.039,0,0),(1.506,.037,.04,0,0)],skin,48,2)
loft('Hidden fitted torso',[(.895,.133,.09,0,0),(.96,.158,.101,0,0),(1.05,.12,.082,0,0),(1.20,.115,.081,0,0),(1.31,.146,.091,0,0),(1.378,.145,.068,0,0)],black,64,2)
for s,label in [(-1,'R'),(1,'L')]:
    profiles=[(.125,.025,.032,0),(.19,.029,.034,.002),(.245,.033,.038,.004),(.32,.045,.045,.008),(.4,.054,.05,.009),(.455,.047,.045,.007),(.505,.040,.039,0),(.54,.043,.043,-.006),(.575,.048,.047,0),(.66,.057,.053,.007),(.745,.065,.061,.003),(.83,.071,.066,0),(.91,.075,.071,0),(.956,.071,.065,0)]
    loft(label+' | continuous stocking leg',[(z,rx,ry,s*(.087+(.004 if .5<z<.7 else 0)),cy) for z,rx,ry,cy in profiles],tights,64,2)
    loft(label+' | tactical shorts',[(.814,.067,.064,s*.087,0),(.819,.071,.068,s*.087,0),(.853,.074,.071,s*.087,0),(.927,.079,.077,s*.084,0),(.948,.075,.071,s*.080,0)],skirtmat,48,1)
    loft(label+' | shorts lower seam',[(.813,.069,.066,s*.087,0),(.818,.073,.070,s*.087,0),(.832,.074,.071,s*.087,0)],stitch,48,1)
    # thigh webbing with a small rectangular adjuster
    loft(label+' | thigh harness band',[(.803,.069,.065,s*.087,0),(.807,.072,.068,s*.087,0),(.826,.073,.069,s*.087,0),(.830,.070,.066,s*.087,0)],dark,48,1)
    cube(label+' | thigh strap adjuster',(s*.103,-.070,.817),(.03,.009,.028),metal,.003)
    cube(label+' | buckle dark inset',(s*.103,-.076,.817),(.018,.003,.017),dark,.001)

collection('03 | Technical jacket')
shirt_rings=[(.966,.145,.096,0,0),(.972,.158,.104,0,0),(.991,.158,.104,0,0),(1.013,.151,.101,0,0),(1.025,.153,.101,0,0),(1.035,.148,.099,0,0),(1.057,.140,.096,0,0),(1.080,.133,.094,0,0),(1.115,.130,.088,0,0),(1.19,.133,.095,0,-.002),(1.265,.147,.107,0,-.002),(1.315,.156,.11,0,0),(1.350,.164,.099,0,0),(1.379,.150,.079,0,0),(1.397,.085,.065,0,0),(1.404,.055,.049,0,0)]
o=loft('Jacket | shaped main shell',shirt_rings,jacket,96,2)
o.data.materials.append(black)
for face in o.data.polygons:
    if len(face.vertices)==4:
        j=(face.index-1)%96;a=(j+.5)*2*pi/96
        if abs(cos(a))>.942:face.material_index=1
def front_y(z,x=0,offset=.0018):
    for a,b in zip(shirt_rings,shirt_rings[1:]):
        if a[0]<=z<=b[0]:
            t=(z-a[0])/(b[0]-a[0]);rx=a[1]*(1-t)+b[1]*t;ry=a[2]*(1-t)+b[2]*t;cy=a[4]*(1-t)+b[4]*t
            return cy-ry*sqrt(max(.04,1-(x/rx)**2))-offset
    return -.10-offset
for s in [-1,1]:
    curve('Jacket | tailored princess seam',[(s*x,front_y(z,s*x),z) for z,x in [(.982,.12),(1.045,.104),(1.105,.091),(1.19,.088),(1.27,.10),(1.325,.124),(1.36,.130)]],.00145,stitch)
    curve('Jacket | panel top seam',[(s*x,front_y(z,s*x),z) for x,z in [(.013,1.349),(.060,1.357),(.11,1.373),(.14,1.375)]],.0016,stitch)
    for z in [.979,.992]:
        pts=[]
        for j in range(65):
            a=2*pi*j/64;pts.append((.1585*cos(a),.105*sin(a),z))
        curve('Hem | double bound edge',pts,.0015,stitch)
curve('Zip | black center tape',[(0,front_y(z,0,.003),z) for z in [.978,1.035,1.10,1.19,1.27,1.33,1.376]],.0038,dark)
for z in [1.005+i*.008 for i in range(45)]:
    cube('Zip | individual metal tooth',(0,front_y(z,0,.006),z),(.0045,.0014,.0018),metal,.0003)
cube('Zip | slider',(0,front_y(1.31,0,.01),1.31),(.010,.007,.014),metal,.0018)
o=cube('Zip | dark hanging pull',(.005,front_y(1.295,0,.014),1.29),(.009,.004,.027),dark,.0015);o.rotation_euler[1]=-.23
# chest patch and small sewn identification panel
cube('Chest | identity patch',(.073,-.111,1.318),(.051,.005,.024),stitch,.0015)
cube('Chest | embroidered label',(.073,-.1142,1.318),(.046,.001,.019),jacket,.0007)
text_obj('Chest | warning label','A / 07',(.073,-.1155,1.318),.010,red)
for x in [.053,.093]:uv('Chest | patch stitch',(x,-.115,1.318),(.0008,.0007,.008),ivory,12,8)
cube('Hem | ID patch',(-.064,-.103,.999),(.039,.004,.039),ivory,.001)
text_obj('Hem | insignia','07',(-.064,-.106,1.000),.023,dark)

collection('04 | Arms and gloves')
for s,label in [(-1,'R'),(1,'L')]:
    sleeve=[(s*.143,0,1.376),(s*.171,0,1.362),(s*.195,.003,1.324),(s*.216,.005,1.282),(s*.225,.005,1.263),(s*.232,.005,1.249),(s*.238,.005,1.237),(s*.242,.005,1.229),(s*.247,.005,1.219),(s*.250,.005,1.211),(s*.257,.004,1.197),(s*.263,.003,1.185),(s*.273,.002,1.167),(s*.283,0,1.153)]
    sleeve_obj=limb(label+' | black tailored sleeve',sleeve,[.044,.048,.048,.044,.041,.045,.045,.038,.04,.043,.037,.040,.041,.041],black,48,2)
    for v in sleeve_obj.data.vertices:
        z=v.co.z
        if 1.17<z<1.30:
            v.co.y+=.0017*sin((z-1.17)*160+v.co.x*45)
    cuff=[(s*.273,.002,1.174),(s*.278,.001,1.164),(s*.292,-.001,1.140),(s*.297,-.002,1.131)]
    limb(label+' | light turned cuff',cuff,[.043,.047,.047,.041],jacket,48,1)
    for x,z in [(.277,1.167),(.293,1.139)]:
        center=Vector((s*x,0,z));t=Vector((s*.48,0,-.87));basis=t.cross(Vector((0,1,0))).normalized()
        curve(label+' | cuff seam',[center+Vector((0,1,0))*(.047*cos(2*pi*j/48))+basis*(.047*sin(2*pi*j/48)) for j in range(49)],.0013,stitch)
    arm=[(s*.291,0,1.143),(s*.306,-.002,1.117),(s*.332,-.007,1.073),(s*.359,-.012,1.031),(s*.374,-.016,1.008)]
    limb(label+' | bare forearm',arm,[.032,.033,.029,.023,.022],skin,40,2)
    limb(label+' | burgundy wrist wrap',[(s*.365,-.014,1.027),(s*.368,-.015,1.018),(s*.382,-.017,.994)],[.026,.028,.025],red,40,1)
    limb(label+' | wrist black binding',[(s*.380,-.017,1.0),(s*.383,-.018,.995),(s*.386,-.018,.989)],[.026,.027,.026],dark,40,1)
    palm=uv(label+' | hand palm',(s*.394,-.018,.974),(.027,.014,.041),skin,32,20);palm.rotation_euler[1]=-s*.45
    glove=uv(label+' | fingerless glove',(s*.392,-.019,.978),(.029,.019,.033),leather,32,20);glove.rotation_euler[1]=-s*.45
    # Four independent articulated fingers, with exposed fingertips.
    for i in range(4):
        x=s*(.383+i*.011);z=.960+i*.003;length=[.039,.047,.044,.034][i]
        pts=[(x,-.020,z),(x+s*.012,-.021,z-length*.48),(x+s*.017,-.017,z-length)]
        limb(label+' | finger '+str(i+1),pts,[.0057,.0053,.0034],skin,16,1)
        limb(label+' | glove finger '+str(i+1),[pts[0],tuple(Vector(pts[0]).lerp(Vector(pts[1]),.72))],[.0063,.0061],leather,16,1)
        uv(label+' | fingernail '+str(i+1),(pts[-1][0],-.020,pts[-1][2]+.003),(.0026,.0007,.0040),ivory,16,8)
    limb(label+' | thumb',[(s*.376,-.027,.983),(s*.366,-.032,.966),(s*.369,-.031,.952)],[.008,.0067,.0035],skin,20,1)
    cube(label+' | glove knuckle plate',(s*.397,-.040,.979),(.025,.004,.018),dark,.004)
    # sleeve seam, burgundy utility strip and white compact typography
    curve(label+' | sleeve outer red piping',[(s*.181,-.034,1.368),(s*.208,-.038,1.313),(s*.243,-.034,1.242),(s*.269,-.031,1.187)],.0032,red)
    patch=cube(label+' | sleeve ID patch',(s*.224,-.042,1.272),(.028,.004,.080),dark,.002);patch.rotation_euler[1]=-s*.42
    txt=text_obj(label+' | sleeve stencil','FIELD',(s*.225,-.046,1.273),.010,ivory);txt.rotation_euler=(pi/2,s*.42,-s*.42)

for hand_ob in list(COL.objects):
    if any(token in hand_ob.name for token in ['| hand palm','| fingerless glove','| finger ','| glove finger','| fingernail','| thumb','| glove knuckle']):
        hs=-1 if hand_ob.name.startswith('R |') else 1
        hp=Vector((hs*.374,-.016,1.008))
        transform=Matrix.Translation(hp) @ Matrix.Scale(1.18,4) @ Matrix.Translation(-hp)
        hand_ob.matrix_local=transform @ hand_ob.matrix_local

collection('05 | Hood and waist layers')
loft('Collar | high padded neck',[(1.380,.071,.065,0,.007),(1.397,.082,.073,0,.009),(1.443,.075,.066,0,.014),(1.454,.066,.057,0,.014)],lining,64,2)
curve('Collar | light piping',[(-.064,-.025,1.450),(-.048,-.056,1.449),(0,-.066,1.443),(.049,-.056,1.449),(.065,-.021,1.450)],.0013,stitch)
uv('Hood | folded back volume',(0,.071,1.389),(.093,.064,.057),lining,64,32)
curve('Hood | seam',[(-.078,.104,1.411),(-.053,.129,1.374),(0,.137,1.355),(.052,.129,1.374),(.078,.104,1.411)],.002,stitch)
for s in [-1,1]:
    curve('Hood | hanging drawcord',[(s*.053,-.062,1.402),(s*.063,-.103,1.370),(s*.049,-.117,1.317)],.0017,dark)
    rod('Hood | cord aglet',(s*.049,-.117,1.318),(s*.048,-.118,1.305),.0024,metal)
tag=cube('Collar | burgundy clasp',(-.025,-.072,1.412),(.018,.007,.049),red,.002);tag.rotation_euler[1]=-.16
cube('Collar | metallic clasp',(-.025,-.076,1.426),(.012,.003,.01),metal,.001)
curve('Collar | hanging utility tape',[(-.025,-.079,1.401),(-.040,-.120,1.360),(-.045,-.121,1.303)],.0042,red)
# Continuous belt with metal frame buckle.
loft('Belt | encircling tactical webbing',[(1.060,.143,.103,0,0),(1.064,.145,.105,0,0),(1.100,.140,.101,0,0),(1.104,.136,.097,0,0)],dark,80,1)
for x in [-.101,-.056,.058,.108]:
    cube('Belt | keeper',(x,-.106*sqrt(1-(x/.146)**2),1.082),(.013,.008,.047),black,.002)
curve('Belt | angular metal buckle',[(-.023,-.112,1.103),(.018,-.113,1.103),(.027,-.113,1.062),(-.022,-.112,1.062),(-.023,-.112,1.103)],.0031,metal)
curve('Belt | buckle diagonal',[(-.014,-.115,1.098),(.014,-.115,1.066)],.0031,metal)
# Asymmetric wrap forms, thin actual mesh with panel borders.
wrapv=[(-.156,-.075,.978),(-.112,-.111,.965),(0,-.118,.951),(.151,-.082,.953),(.151,-.073,.905),(.05,-.124,.924),(-.06,-.129,.938),(-.155,-.081,.941)]
o=mesh('Waist | ash asymmetrical drape',wrapv,[(0,1,6,7),(1,2,5,6),(2,3,4,5)],wrapmat,True,1);o.modifiers.new('Fabric thickness','SOLIDIFY').thickness=.003
curve('Waist | drape sewn hem',[wrapv[i] for i in [7,6,5,4]],.0015,stitch)
sv=[(-.153,-.087,.949),(-.074,-.129,.939),(.055,-.131,.924),(.154,-.084,.907),(.020,-.146,.842),(-.080,-.136,.803),(-.151,-.091,.855)]
o=mesh('Skirt | diagonal overlapping front panel',sv,[(0,1,6),(1,2,4,5,6),(2,3,4)],skirtmat,False,0);o.modifiers.new('Panel thickness','SOLIDIFY').thickness=.004;b=o.modifiers.new('Edge softness','BEVEL');b.width=.0015;b.segments=2
curve('Skirt | diagonal grey binding',[sv[i] for i in [6,5,4,3]],.003,stitch)
curve('Skirt | diagonal construction seam',[(-.135,-.099,.935),(-.07,-.137,.905),(.006,-.146,.873),(.096,-.115,.904)],.0014,metal)
for i in range(3):
    x=-.087+i*.019;z=.83+i*.01
    curve('Skirt | geometric hem marking',[(x,-.145,z+.031),(x,-.148,z),(x+.014,-.148,z+.008)],.0022,ivory)
rv=[];rf=[];rn=40
for k in range(5):
    t=k/4
    for j in range(rn+1):
        a=pi*j/rn;z=(1-t)*.953+t*(.873+.023*cos(a))
        rv.append(((.159+.004*t)*cos(a),(.112+.004*t)*sin(a)+.003,z))
for k in range(4):
    for j in range(rn):rf.append((k*(rn+1)+j,k*(rn+1)+j+1,(k+1)*(rn+1)+j+1,(k+1)*(rn+1)+j))
rear_wrap=mesh('Skirt | rear unpadded cloth wrap',rv,rf,wrapmat,True,1);rear_wrap.modifiers.new('Thin fabric','SOLIDIFY').thickness=.0025
curve('Skirt | rear diagonal hem',rv[-(rn+1):],.0015,stitch)
# side hanging tags
for s in [-1,1]:
    curve('Waist | loose burgundy strap',[(s*.157,.02,1.071),(s*.180,.023,.984),(s*.178,.021,.884)],.005,red)
    cube('Waist | strap end',(s*.178,.021,.887),(.013,.007,.011),metal,.001)

collection('06 | Boots')
for s,label in [(-1,'R'),(1,'L')]:
    x=s*.087
    # Shaped footprint rings: rounded toe extending forward (-Y).
    shape=[(-.031,.045),(-.041,.018),(-.043,-.028),(-.045,-.077),(-.036,-.105),(-.021,-.116),(.021,-.116),(.037,-.105),(.045,-.077),(.041,-.022),(.033,.044)]
    def foot(name,levels,material):
        vv=[];nf=len(shape)
        for z,factor,dy in levels:
            vv.extend([(x+a*factor,b*factor+dy,z) for a,b in shape])
        ff=[tuple(reversed(range(nf)))]
        for k in range(len(levels)-1):
            for j in range(nf):ff.append((k*nf+j,k*nf+(j+1)%nf,(k+1)*nf+(j+1)%nf,(k+1)*nf+j))
        ff.append(tuple((len(levels)-1)*nf+j for j in range(nf)))
        return mesh(name,vv,ff,material,True,2)
    foot(label+' | burgundy rubber outsole',[(.018,1.01,0),(.021,1.08,0),(.036,1.08,0),(.043,1.02,0)],red)
    foot(label+' | boot midsole',[(.037,1.03,0),(.044,1.05,0),(.057,1.01,0)],sole)
    foot(label+' | molded toe and vamp',[(.051,.97,0),(.065,1.00,0),(.092,.96,.004),(.118,.76,.022),(.135,.57,.024)],leather)
    loft(label+' | fitted ankle boot',[(.072,.039,.046,x,.011),(.095,.04,.05,x,.003),(.128,.037,.041,x,.001),(.175,.039,.038,x,.005),(.196,.041,.039,x,.005),(.205,.036,.034,x,.005)],leather,48,2)
    loft(label+' | pale padded cuff',[(.193,.041,.039,x,.005),(.2,.044,.041,x,.005),(.211,.043,.040,x,.005),(.218,.040,.037,x,.005)],ivory,48,1)
    tongue=cube(label+' | boot tongue',(x,-.038,.163),(.031,.010,.090),dark,.005);tongue.rotation_euler[0]=-.18
    cube(label+' | tongue grey tab',(x,-.044,.205),(.018,.007,.019),ivory,.002)
    for j in range(5):
        z=.093+j*.019;y=-.061+j*.0042;w=.022-j*.0013
        for side in [-1,1]:uv(label+' | lace eyelet',(x+side*w,y,z),(.004,.002,.004),metal,16,8)
        if j<4:
            curve(label+' | cross lace',[(x-w,y-.003,z),(x,y-.012,z+.009),(x+w-.0013,y+.001,z+.019)],.0019,stitch)
            curve(label+' | return lace',[(x+w,y-.003,z),(x,y-.011,z+.009),(x-w+.0013,y+.001,z+.019)],.0019,stitch)
    curve(label+' | toe stitched seam',[(x-.034,-.072,.089),(x-.02,-.089,.099),(x,-.091,.102),(x+.02,-.089,.099),(x+.034,-.072,.089)],.0011,stitch)
    for side in [-1,1]:
        curve(label+' | ankle panel piping',[(x+side*.034,.023,.189),(x+side*.039,-.016,.14),(x+side*.039,-.036,.087)],.0015,stitch)
    for j in range(7):cube(label+' | sole tread',(x,-.10+j*.022,.022),(.073,.008,.012),sole,.002)

# Independently authored detailed head and accessory modules.
for module in ['head_hair.py','gear_wings.py']:
    exec(compile(open(os.path.join(OUT,module),encoding='utf-8').read(),module,'exec'),globals())
for ob in bpy.data.objects:
    if ob.type=='CURVE' and any(w in ob.name for w in ['angular metal buckle','buckle diagonal','geometric hem marking']):
        for sp in ob.data.splines:
            if sp.type=='BEZIER':
                for bp in sp.bezier_points:bp.handle_left_type='VECTOR';bp.handle_right_type='VECTOR'

collection('90 | Reference images')
ref=bpy.data.images.load(os.path.join(OUT,'reference.jpg'));ref.pack()
refob=bpy.data.objects.new('REFERENCE | supplied front side back',None);COL.objects.link(refob);refob.empty_display_type='IMAGE';refob.data=ref;refob.empty_display_size=2.8;refob.location=(0,.75,.94);refob.rotation_euler=(pi/2,0,0);refob.hide_render=True;refob.hide_viewport=True

collection('99 | Studio')
root=None
ground=mat('Studio | neutral warm grey',(.095,.11,.118),.06,.7)
cube('Studio floor',(0,0,-.018),(200,200,.035),ground,.0)
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,color,size,target=(0,0,1)):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);COL.objects.link(o);o.location=loc;aim(o,target)
area('Key | large softbox',(-2.0,-3.0,3.9),165,(1,.89,.83),3.3)
area('Fill | cool softbox',(2.1,-1.7,2.5),85,(.80,.88,1),2.8)
area('Rim | high rear',(0.4,1.5,2.7),155,(1,.80,.73),2.0)
area('Face | eye light',(-.1,-2,1.85),18,(1,.94,.89),1.2)
w=bpy.data.worlds.new('Studio ambience');w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.24,.27,.32,1);w.node_tree.nodes['Background'].inputs[1].default_value=.35;bpy.context.scene.world=w
def camera(name,loc,target,ortho):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);COL.objects.link(o);o.location=loc;d.type='ORTHO';d.ortho_scale=ortho;aim(o,target);return o
hero=camera('CAM | Portrait three quarter',(2.35,-5.5,2.05),(0,0,.92),2.04)
front=camera('CAM | Front orthographic',(0,-5,.92),(0,0,.92),1.99)
side=camera('CAM | Left orthographic',(-5,0,.92),(0,0,.92),1.99)
back=camera('CAM | Back orthographic',(0,5,.92),(0,0,.92),1.99)
close=camera('CAM | Face detail',(.37,-2,1.66),(0,-.01,1.60),.47)
scene=bpy.context.scene;scene.camera=hero;scene.unit_settings.system='METRIC';scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    gpu=False
    for d in prefs.devices:d.use=d.type!='CPU';gpu=gpu or d.use
    if gpu:scene.cycles.device='GPU'
except Exception:pass
scene.render.resolution_x=1100;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.render.film_transparent=False
# Subtle optical glow retains the physical facets of the crystals.
scene.use_nodes=True;n=scene.node_tree.nodes;n.clear();rl=n.new('CompositorNodeRLayers');gl=n.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.quality='HIGH';gl.threshold=1.6;gl.mix=-.92;comp=n.new('CompositorNodeComposite');scene.node_tree.links.new(rl.outputs['Image'],gl.inputs['Image']);scene.node_tree.links.new(gl.outputs['Image'],comp.inputs['Image'])
bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=None
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.region_3d.view_perspective='CAMERA';ar.spaces.active.shading.color_type='MATERIAL';ar.spaces.active.overlay.show_overlays=False
scene['Project']='REFERENCE OPERATOR | local procedural character study'
scene['Reference']='User-supplied three-view image, embedded in hidden reference collection'
scene['Orientation']='Z up, front -Y; scale in meters'
scene['Asset status']='Static editable segmented model. No animation rig or production retopology.'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Endfield_Operator.blend'))
stats={'objects':len(bpy.data.objects),'meshes':sum(o.type=='MESH' for o in bpy.data.objects),'materials':len(bpy.data.materials),'base_vertices':sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH'),'base_polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'blender_version':bpy.app.version_string}
open(os.path.join(OUT,'model_stats.json'),'w',encoding='utf-8').write(json.dumps(stats,indent=2))
print('MODEL_SAVED',stats,flush=True)
scene.cycles.samples=32;scene.render.resolution_x=880;scene.render.resolution_y=1200
scene.render.filepath=os.path.join(OUT,'hero.png');bpy.ops.render.render(write_still=True)
for cam,name in [(front,'front'),(side,'side'),(back,'back')]:
    bpy.data.objects['Studio floor'].hide_render=True
    scene.camera=cam;scene.render.resolution_x=650;scene.render.resolution_y=1100;scene.render.filepath=os.path.join(OUT,name+'.png');bpy.ops.render.render(write_still=True)
scene.camera=close;scene.render.resolution_x=850;scene.render.resolution_y=850;scene.render.filepath=os.path.join(OUT,'face.png');bpy.ops.render.render(write_still=True)
print('ALL_RENDERS_COMPLETE',flush=True)
