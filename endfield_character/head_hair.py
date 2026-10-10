"""Reference-derived stylised face and layered wine-red short hair.

Executed inside the main character builder. Coordinates are metres; front is -Y.
All facial features are modelled geometry, and the hair locks are closed meshes.
"""
import math
import random
from mathutils import Vector

collection('02 | Head and face')
hf_skin = mat('Face | warm porcelain', (0.79, 0.595, 0.486, 1), rough=0.66)
hf_ear = mat('Ear and lip | warm blush', (0.55, 0.245, 0.225, 1), rough=0.65)
hf_lips = mat('Mouth | muted rose', (0.36, 0.13, 0.145, 1), rough=0.58)
hf_dark = mat('Lashes | aubergine ink', (0.065, 0.028, 0.036, 1), rough=0.60)
hf_white = mat('Eyes | ivory sclera', (0.70, 0.68, 0.61, 1), rough=0.45)
hf_iris = mat('Eyes | honey amber', (0.48, 0.27, 0.055, 1), rough=0.27)
hf_iris_light = mat('Eyes | golden iris filaments', (0.80, 0.57, 0.17, 1), rough=0.32)
hf_iris_rim = mat('Eyes | olive brown limbal ring', (0.16, 0.12, 0.045, 1), rough=0.4)
hf_pupil = mat('Eyes | deep pupil', (0.018, 0.01, 0.013, 1), rough=0.25)
hf_glint = mat('Eyes | catchlight', (1.0, 0.98, 0.91, 1), rough=0.18)
hf_brows = mat('Brows | muted wine', (0.17, 0.065, 0.070, 1), rough=0.8)
for hf_m in (hf_skin, hf_ear):
    if hf_m.use_nodes:
        hf_bsdf = hf_m.node_tree.nodes.get('Principled BSDF')
        if hf_bsdf and 'Subsurface Weight' in hf_bsdf.inputs:
            hf_bsdf.inputs['Subsurface Weight'].default_value = 0.045
            hf_bsdf.inputs['Subsurface Radius'].default_value = (0.8, 0.36, 0.2)

# A single continuous facial surface. Each row stores Z, half-width,
# anterior depth, and posterior depth. The nose is displaced into this mesh.
hf_profile = [
    (1.483, 0.009, 0.039, 0.009),
    (1.491, 0.026, 0.052, 0.022),
    (1.507, 0.047, 0.067, 0.040),
    (1.526, 0.069, 0.080, 0.056),
    (1.551, 0.087, 0.091, 0.067),
    (1.577, 0.099, 0.096, 0.078),
    (1.610, 0.103, 0.092, 0.085),
    (1.648, 0.105, 0.091, 0.086),
    (1.679, 0.098, 0.083, 0.081),
    (1.706, 0.080, 0.066, 0.068),
    (1.731, 0.046, 0.038, 0.039),
    (1.742, 0.003, 0.003, 0.003),
]

def hf_profile_at(z):
    if z <= hf_profile[0][0]:
        return hf_profile[0][1:]
    if z >= hf_profile[-1][0]:
        return hf_profile[-1][1:]
    for i in range(len(hf_profile) - 1):
        a, b = hf_profile[i], hf_profile[i + 1]
        if a[0] <= z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            # Hermite interpolation preserves soft cheeks without flat bands.
            out = []
            for j in (1, 2, 3):
                p = hf_profile[max(0, i - 1)]
                q = hf_profile[min(len(hf_profile) - 1, i + 2)]
                ma = (b[j] - p[j]) / (b[0] - p[0])
                mb = (q[j] - a[j]) / (q[0] - a[0])
                dz = b[0] - a[0]
                out.append((2*t**3-3*t*t+1)*a[j] + (t**3-2*t*t+t)*ma*dz
                           + (-2*t**3+3*t*t)*b[j] + (t**3-t*t)*mb*dz)
            return out

def hf_front(x, z):
    rx, front, back = hf_profile_at(z)
    u = min(0.99999, abs(x) / max(0.001, rx))
    y = -front * max(0.0, 1.0 - u**3.1)**0.52
    nose = 0.0115 * math.exp(-(x/0.011)**2 - ((z-1.568)/0.0115)**2)
    bridge = 0.0045 * math.exp(-(x/0.009)**2 - ((z-1.585)/0.020)**2)
    muzzle = 0.0025 * math.exp(-(x/0.024)**2 - ((z-1.539)/0.012)**2)
    # Very mild eye socket recession, applied to skin only.
    socket = 0.0013 * sum(math.exp(-((x-s*0.044)/0.029)**2 - ((z-1.603)/0.019)**2)
                             for s in (-1, 1))
    return y - nose - bridge - muzzle + socket

hf_v, hf_f = [], []
hf_rows, hf_sides = 100, 128
for j in range(hf_rows + 1):
    z = 1.483 + (1.742 - 1.483) * j / hf_rows
    rx, fd, bd = hf_profile_at(z)
    for k in range(hf_sides):
        a = 2.0 * math.pi * k / hf_sides
        x = rx * math.sin(a)
        if math.cos(a) >= 0:
            y = hf_front(x, z)
        else:
            y = -bd * math.cos(a)
        hf_v.append((x, y, z))
for j in range(hf_rows):
    for k in range(hf_sides):
        a = j*hf_sides + k
        b = j*hf_sides + (k+1)%hf_sides
        hf_f.append((a, b, b+hf_sides, a+hf_sides))
hf_f.append(tuple(reversed(range(hf_sides))))
hf_f.append(tuple(hf_rows*hf_sides+k for k in range(hf_sides)))
hf_head = mesh('Head | continuous sculpted anime face', hf_v, hf_f, hf_skin, sub=1)

# Ears remain anatomically attached and visible in the side views.
for hf_s, hf_label in ((-1, 'L'), (1, 'R')):
    hf_o = uv('Ear ' + hf_label + ' | auricle', (hf_s*0.1015, 0.001, 1.577),
              (0.0125, 0.016, 0.027), hf_skin, segments=40, rings=24)
    hf_o.rotation_euler[1] = hf_s * -0.12
    uv('Ear ' + hf_label + ' | inner concha', (hf_s*0.1120, -0.0035, 1.578),
       (0.0032, 0.0090, 0.014), hf_ear, segments=32, rings=20)
    pts = [(hf_s*(0.111+0.001*math.cos(t)), -0.004+0.009*math.sin(t),
            1.578+0.019*math.cos(t)) for t in [i*math.pi*2/32 for i in range(33)]]
    curve('Ear ' + hf_label + ' | folded helix', pts, 0.0027, hf_skin)

def hf_face_line(name, xzs, material, radius, offset=0.0018):
    return curve(name, [(x, hf_front(x,z)-offset, z) for x,z in xzs], radius, material)

# Almond eyes are conformal surfaces, not floating eyeballs.
for hf_s, hf_label in ((-1, 'L'), (1, 'R')):
    hf_cx, hf_cz = hf_s * 0.0435, 1.605
    def hf_eye_xz(t, r=1.0):
        dx = 0.0275 * math.cos(t) * r
        sn = math.sin(t)
        dz = (0.0110 if sn>=0 else -0.0072) * abs(sn)**1.4 * r
        return hf_cx + dx, hf_cz + dz + hf_s*dx*0.08
    eyeverts = [(hf_cx, hf_front(hf_cx,hf_cz)-0.0014, hf_cz)]
    eyefaces = []
    n, nr = 64, 6
    for ir in range(1, nr+1):
        rr=ir/nr
        for k in range(n):
            x,z=hf_eye_xz(2*math.pi*k/n, rr)
            eyeverts.append((x,hf_front(x,z)-0.00065-0.00075*(1-rr*rr),z))
    for k in range(n):
        eyefaces.append((0,1+k,1+(k+1)%n))
    for ir in range(nr-1):
        base=1+ir*n
        for k in range(n):
            kn=(k+1)%n
            eyefaces.append((base+k,base+n+k,base+n+kn,base+kn))
    mesh('Eye '+hf_label+' | almond sclera',eyeverts,eyefaces,hf_white)

    # Iris and pupil are clipped by the eyelids, giving a calm half-lidded gaze.
    def hf_clip_eye(x,z):
        q=min(1.0,abs(x-hf_cx)/0.0275)
        shape=max(0.0,1-q*q)**0.70
        mid=hf_cz+hf_s*(x-hf_cx)*0.08
        return max(mid-0.0072*shape+0.00020,min(mid+0.0110*shape-0.00020,z))
    def hf_disk(name, radius_x, radius_z, material, offset, cx=hf_cx, cz=hf_cz):
        vv=[(cx,hf_front(cx,cz)-offset,cz)]
        for k in range(64):
            t=2*math.pi*k/64
            x,z=cx+radius_x*math.cos(t),cz+radius_z*math.sin(t)
            z=hf_clip_eye(x,z)
            vv.append((x,hf_front(x,z)-offset+0.00015,z))
        ff=[(0,k+1,(k+1)%64+1) for k in range(64)]
        return mesh(name,vv,ff,material)
    hf_disk('Eye '+hf_label+' | limbal outline',0.0112,0.0123,hf_iris_rim,0.00175,cz=hf_cz+0.0020)
    hf_disk('Eye '+hf_label+' | amber iris',0.0102,0.0112,hf_iris,0.00195,cz=hf_cz+0.0020)
    for k in range(28):
        t=2*math.pi*k/28
        pp=[]
        for r in (0.51,0.66,0.87):
            x=hf_cx+0.0102*r*math.cos(t)
            z=hf_clip_eye(x,hf_cz+0.0020+0.0111*r*math.sin(t))
            pp.append((x,hf_front(x,z)-0.00210,z))
        curve('Eye '+hf_label+' | iris fiber %02d'%k,pp,0.00015,hf_iris_light)
    hf_disk('Eye '+hf_label+' | oval pupil',0.0050,0.0072,hf_pupil,0.00225,cz=hf_cz+0.0020)
    hf_disk('Eye '+hf_label+' | main catchlight',0.0016,0.0019,hf_glint,0.00250,
            cx=hf_cx-0.0034,cz=hf_cz+0.0050)
    hf_disk('Eye '+hf_label+' | secondary catchlight',0.00065,0.00075,hf_glint,0.00250,
            cx=hf_cx+0.0037,cz=hf_cz-0.0035)

    upper=[]
    lower=[]
    for k in range(41):
        t=math.pi*k/40
        upper.append(hf_eye_xz(t))
        lower.append(hf_eye_xz(math.pi+t))
    # Flat tapered upper lash ribbon, with no encircling lower black frame.
    lashv,lashf=[],[]
    for k,(x,z) in enumerate(upper):
        t=k/(len(upper)-1)
        taper=max(0.0,math.sin(math.pi*t))**0.60
        thick=0.0015*taper
        lashv.extend([(x,hf_front(x,z)-0.00240,z),
                      (x,hf_front(x,z+thick)-0.00130,z+thick)])
        if k:
            lashf.append((2*k-2,2*k-1,2*k+1,2*k))
    mesh('Eye '+hf_label+' | tapered upper lash',lashv,lashf,hf_dark)
    ox=hf_cx+hf_s*0.0270
    oz=hf_cz+0.0022
    wing=[(ox-hf_s*0.0025,oz+0.001),(ox+hf_s*0.0030,oz+0.0030),
          (ox+hf_s*0.0002,oz-0.0004)]
    mesh('Eye '+hf_label+' | outer lash wing',
         [(x,hf_front(x,z)-0.0018,z) for x,z in wing],[(0,1,2)],hf_dark)
    # A soft partial lower waterline in a skin shade prevents a goggle effect.
    hf_face_line('Eye '+hf_label+' | lower waterline',lower[9:32],hf_ear,0.00025,0.0008)
    brow=[(hf_s*x,z) for x,z in [(0.021,1.630),(0.031,1.6325),
                                 (0.044,1.6335),(0.058,1.6325),(0.069,1.629)]]
    hf_face_line('Brow '+hf_label+' | soft wine arc',brow,hf_brows,0.00065,0.0008)

# Integrated nose shape receives only tiny nostril accents; mouth is a slim
# curved seam and two lip planes in the surface, deliberately understated.
for hf_s in (-1,1):
    hf_face_line('Nose | nostril accent '+str(hf_s),
                 [(hf_s*0.005,1.559),(hf_s*0.0074,1.5595),(hf_s*0.0087,1.561)],
                 hf_ear,0.00055,0.0010)
hf_face_line('Mouth | gentle closed seam',
             [(-0.014,1.539),(-0.008,1.5398),(-0.003,1.5394),(0,1.539),
              (0.004,1.5395),(0.010,1.5396),(0.014,1.539)],hf_lips,0.00070,0.0013)
hf_face_line('Mouth | lower lip reflected light',
             [(-0.007,1.5365),(0,1.5358),(0.007,1.5365)],hf_ear,0.0006,0.0010)

collection('03 | Layered burgundy hair')
hf_hair_base = mat('Hair | deep wine root', (0.015,0.0022,0.0045,1), rough=0.46)
hf_hair_mats = [
    mat('Hair | burgundy satin', (0.048,0.0065,0.011,1), rough=0.43),
    mat('Hair | garnet midtone', (0.060,0.0090,0.014,1), rough=0.44),
    mat('Hair | wine shadow', (0.027,0.0035,0.006,1), rough=0.46),
    mat('Hair | rose sheen', (0.068,0.011,0.017,1), rough=0.43),
]
hf_hair_gloss = mat('Hair | fine muted rose glints', (0.080,0.018,0.025,1), rough=0.46)
hf_hair_groove = mat('Hair | strand grooves', (0.012,0.002,0.004,1), rough=0.46)
for hf_m in [hf_hair_base,hf_hair_gloss,hf_hair_groove]+hf_hair_mats:
    if hf_m.use_nodes:
        hf_bsdf=hf_m.node_tree.nodes.get('Principled BSDF')
        if hf_bsdf:
            if 'Specular IOR Level' in hf_bsdf.inputs:
                hf_bsdf.inputs['Specular IOR Level'].default_value=0.18
            if 'Coat Weight' in hf_bsdf.inputs:
                hf_bsdf.inputs['Coat Weight'].default_value=0.0

# Fine longitudinal fibres use strand UVs, leaving the silhouette and hue intact.
for hf_m in hf_hair_mats:
    hf_nt=hf_m.node_tree
    hf_bsdf=hf_nt.nodes.get('Principled BSDF')
    if not hf_bsdf:
        continue
    hf_color=tuple(hf_bsdf.inputs['Base Color'].default_value)
    hf_uvnode=hf_nt.nodes.new('ShaderNodeUVMap')
    hf_uvnode.name='Hair | regular strand UV'
    hf_uvnode.uv_map='StrandUV'
    hf_uvnode.location=(-720,100)
    hf_scale=hf_nt.nodes.new('ShaderNodeVectorMath')
    hf_scale.name='Hair | longitudinal fibre frequency'
    hf_scale.operation='MULTIPLY'
    hf_scale.inputs[1].default_value=(40.0,2.0,1.0)
    hf_scale.location=(-530,100)
    hf_noise=hf_nt.nodes.new('ShaderNodeTexNoise')
    hf_noise.name='Hair | subtle fine silk texture'
    hf_noise.noise_dimensions='3D'
    hf_noise.inputs['Scale'].default_value=1.0
    hf_noise.inputs['Detail'].default_value=2.0
    hf_noise.inputs['Roughness'].default_value=0.65
    hf_noise.location=(-330,100)
    hf_ramp=hf_nt.nodes.new('ShaderNodeValToRGB')
    hf_ramp.name='Hair | restrained tone variation'
    hf_ramp.color_ramp.elements[0].color=tuple(c*0.75 for c in hf_color[:3])+(1.0,)
    hf_ramp.color_ramp.elements[1].color=tuple(c*1.12 for c in hf_color[:3])+(1.0,)
    hf_ramp.location=(-90,160)
    hf_bump=hf_nt.nodes.new('ShaderNodeBump')
    hf_bump.name='Hair | microscopic fibre relief'
    hf_bump.inputs['Strength'].default_value=0.12
    hf_bump.inputs['Distance'].default_value=0.0001
    hf_bump.location=(-80,-100)
    hf_nt.links.new(hf_uvnode.outputs['UV'],hf_scale.inputs[0])
    hf_nt.links.new(hf_scale.outputs['Vector'],hf_noise.inputs['Vector'])
    hf_nt.links.new(hf_noise.outputs['Fac'],hf_ramp.inputs['Fac'])
    hf_nt.links.new(hf_ramp.outputs['Color'],hf_bsdf.inputs['Base Color'])
    hf_nt.links.new(hf_noise.outputs['Fac'],hf_bump.inputs['Height'])
    hf_nt.links.new(hf_bump.outputs['Normal'],hf_bsdf.inputs['Normal'])

def hf_cap_point(theta, phi, extra=0.0):
    return Vector(((0.117+extra)*math.sin(phi)*math.sin(theta),
                   0.009-(0.107+extra)*math.sin(phi)*math.cos(theta),
                   1.631+(0.134+extra)*math.cos(phi)))

# Scalloped closed hair foundation hidden beneath individual tapered locks.
vv,ff=[],[]
hs,hr=112,36
for j in range(hr+1):
    for k in range(hs):
        a=2*math.pi*k/hs
        backness=(1-math.cos(a))/2
        phimax=1.21+1.31*min(1.0,backness*2.3)**0.52
        phi=0.014+(phimax-0.014)*j/hr
        vv.append(tuple(hf_cap_point(a,phi)))
for j in range(hr):
    for k in range(hs):
        kn=(k+1)%hs
        ff.append((j*hs+k,j*hs+kn,(j+1)*hs+kn,(j+1)*hs+k))
ff.append(tuple(reversed(range(hs))))
ff.append(tuple(hr*hs+k for k in range(hs)))
mesh('Hair | shaped short bob foundation',vv,ff,hf_hair_base,sub=1)

def hf_catmull(points,t):
    nn=len(points)-1
    u=min(nn-0.000001,max(0,t*nn))
    i=int(u)
    f=u-i
    a=Vector(points[max(0,i-1)])
    b=Vector(points[i])
    c=Vector(points[min(nn,i+1)])
    d=Vector(points[min(nn,i+2)])
    return 0.5*((2*b)+(-a+c)*f+(2*a-5*b+4*c-d)*f*f+(-a+3*b-3*c+d)*f*f*f)

def hf_lock(name,points,width,material,thickness=0.0045,highlight=True):
    """Closed lens-section lock: curved ridged face, flat underside, fine tip."""
    rows=28
    us=(-1,-0.80,-0.47,0,0.47,0.80,1)
    vv,ff=[],[]
    frames=[]
    for j in range(rows+1):
        t=j/rows
        p=hf_catmull(points,t)
        tangent=(hf_catmull(points,min(1,t+0.006))-hf_catmull(points,max(0,t-0.006))).normalized()
        normal=Vector((p.x/0.117,(p.y-0.009)/0.107,(p.z-1.631)/0.134)).normalized()
        across=tangent.cross(normal).normalized()
        if across.length<0.5:
            across=Vector((1,0,0))
        normal=across.cross(tangent).normalized()
        # Root tapers to enable layering, broad mid section, long pointed tip.
        profile=(0.49+0.62*math.sin(math.pi*t*0.90))*max(0.0,1-t)**0.47
        profile=max(0.014,profile)
        w=width*1.14*profile
        th=thickness*0.32*max(0.09,math.sin(math.pi*(0.10+0.88*t))**0.55)
        frames.append((p,across,normal,w,th))
        for u in us:
            arch=max(0,1-abs(u)**4)**0.65
            vv.append(tuple(p+across*(u*w)+normal*(th*arch+0.00025*(1-abs(u)))))
        for u in reversed(us):
            vv.append(tuple(p+across*(u*w)-normal*0.00055))
    n=len(us)*2
    for j in range(rows):
        for k in range(n):
            ff.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
    ff.append(tuple(reversed(range(n))))
    ff.append(tuple(rows*n+k for k in range(n)))
    obj=mesh(name,vv,ff,material,sub=1)
    strand_uv=obj.data.uv_layers.new(name='StrandUV')
    cross_us=list(us)+list(reversed(us))
    for poly in obj.data.polygons:
        for loop_index in poly.loop_indices:
            vertex_index=obj.data.loops[loop_index].vertex_index
            row,cross_index=divmod(vertex_index,n)
            strand_uv.data[loop_index].uv=((cross_us[cross_index]+1.0)*0.5,row/rows)
    if highlight:
        for ii,u in enumerate((-0.25,)):
            pp=[]
            start=4+(ii*2)
            end=rows-4-(ii*2)
            for j in range(start,end):
                p,across,normal,w,th=frames[j]
                pp.append(tuple(p+across*(u*w)+normal*(th*max(0,1-abs(u)**4)**0.65+0.00032)))
            curve(name+' | fine sheen '+str(ii+1),pp,0.00016,hf_hair_gloss)
    return obj

# Back and side underlayers follow the skull, then flick away from the nape.
hf_rng=random.Random(7718)
for layer in range(3):
    count=(15,18,19)[layer]
    for k in range(count):
        a=0.98+(2*math.pi-1.96)*(k+0.35*(layer%2))/(count-1)
        a+=hf_rng.uniform(-0.03,0.03)
        start=(0.38,0.65,0.94)[layer]
        end=(2.06,2.24,2.46)[layer]+hf_rng.uniform(-0.12,0.10)
        pts=[]
        for j in range(5):
            t=j/4
            ph=start+(end-start)*t
            sweep=0.10*math.sin(t*math.pi)+(0.07 if k%2 else -0.06)*t
            p=hf_cap_point(a+sweep,ph,0.004+0.0035*layer)
            if j==4:
                radial=Vector((math.sin(a),-math.cos(a),0))
                p+=radial*(0.012+(0.006 if k%3==0 else 0))
                p.z-=0.009
            pts.append(tuple(p))
        hf_lock('Hair | layer %d lock %02d'%(layer+1,k+1),pts,
                (0.021,0.020,0.018)[layer],hf_hair_mats[(k+layer)%4],
                thickness=0.0044,highlight=k%3!=1)

# Fringe has a displaced part and overlapping S-shaped locks. Eye centres stay
# visible; the long outer pieces frame the jaw and reproduce the reference bob.
hf_bangs=[
    ([(-0.026,0.010,1.765),(-0.071,-0.040,1.736),(-0.094,-0.080,1.688),
      (-0.103,-0.078,1.639),(-0.113,-0.056,1.591)],0.021,2),
    ([(-0.023,0.000,1.772),(-0.060,-0.071,1.735),(-0.067,-0.107,1.691),
      (-0.074,-0.111,1.655),(-0.089,-0.091,1.627)],0.021,1),
    ([(-0.012,-0.007,1.772),(-0.041,-0.080,1.735),(-0.041,-0.119,1.698),
      (-0.048,-0.120,1.670),(-0.058,-0.116,1.647)],0.021,0),
    ([(0.000,-0.004,1.771),(-0.016,-0.087,1.734),(-0.012,-0.120,1.696),
      (-0.019,-0.126,1.666),(-0.032,-0.120,1.644)],0.020,1),
    ([(0.010,0.001,1.770),(0.019,-0.075,1.741),(0.025,-0.115,1.702),
      (0.012,-0.127,1.666),(0.018,-0.118,1.637)],0.022,0),
    ([(0.014,0.010,1.767),(0.043,-0.064,1.739),(0.050,-0.112,1.695),
      (0.043,-0.123,1.659),(0.035,-0.114,1.633)],0.022,3),
    ([(0.018,0.016,1.765),(0.067,-0.049,1.735),(0.077,-0.098,1.690),
      (0.073,-0.115,1.652),(0.061,-0.111,1.630)],0.022,0),
    ([(0.022,0.022,1.764),(0.082,-0.032,1.728),(0.101,-0.080,1.679),
      (0.099,-0.086,1.631),(0.087,-0.081,1.587)],0.021,1),
]
for k,(pts,w,mi) in enumerate(hf_bangs):
    hf_lock('Hair | sculpted fringe %02d'%(k+1),pts,w,hf_hair_mats[mi],0.0052)

# Short temple wisps terminate in sharp, staggered silhouettes.
for s,label in ((-1,'L'),(1,'R')):
    for k in range(4):
        yy=-0.036+k*0.019
        pts=[(s*0.092,yy+0.013,1.686-k*0.004),
             (s*0.119,yy-0.015,1.641-k*0.007),
             (s*0.115,yy-0.025,1.587-k*0.011),
             (s*(0.127-k*0.007),yy-0.019,1.556-k*0.014)]
        hf_lock('Hair | '+label+' temple flick %02d'%(k+1),pts,0.0135,
                hf_hair_mats[(k+1)%4],0.0036,highlight=k%2==0)

# The crown stays close to the skull; no vertical flyaway antenna.
