"""Reference-inspired equipment, crystal wings and halo.

Executed by the character assembly script after its geometry helpers are defined.
Coordinates are metres; the character looks toward negative Y.
"""
import math
import bpy
from mathutils import Vector


collection('06 • Prismatic crystal wings')
gw_crystal_colours = [
    ('Rose quartz', (0.78, 0.17, 0.40, 1)),
    ('Blush glass', (0.88, 0.36, 0.55, 1)),
    ('Pearl peach', (0.79, 0.44, 0.30, 1)),
    ('Opal violet', (0.37, 0.23, 0.73, 1)),
    ('Iridescent mint', (0.24, 0.61, 0.51, 1)),
    ('Pale gold', (0.71, 0.57, 0.29, 1)),
    ('Frost lavender', (0.58, 0.42, 0.78, 1)),
]
gw_glass = []
for gw_name, gw_col in gw_crystal_colours:
    gw_m = mat('Crystal / ' + gw_name, gw_col, metallic=0.05, rough=0.14)
    gw_bs = gw_m.node_tree.nodes.get('Principled BSDF')
    if gw_bs:
        gw_bs.inputs['IOR'].default_value = 1.46
        if 'Transmission Weight' in gw_bs.inputs:
            gw_bs.inputs['Transmission Weight'].default_value = 0.62
        elif 'Transmission' in gw_bs.inputs:
            gw_bs.inputs['Transmission'].default_value = 0.62
        if 'Coat Weight' in gw_bs.inputs:
            gw_bs.inputs['Coat Weight'].default_value = 0.30
        if 'Coat Roughness' in gw_bs.inputs:
            gw_bs.inputs['Coat Roughness'].default_value = 0.10
        if 'Emission Color' in gw_bs.inputs:
            gw_bs.inputs['Emission Color'].default_value = gw_col
        elif 'Emission' in gw_bs.inputs:
            gw_bs.inputs['Emission'].default_value = gw_col
        if 'Emission Strength' in gw_bs.inputs:
            gw_bs.inputs['Emission Strength'].default_value = 0.06
    gw_glass.append(gw_m)


def gw_shard(name, start, tip, width, thickness, palette_offset=0):
    """A clean elongated asymmetrical gemstone with a tapered root and apex."""
    a, b = Vector(start), Vector(tip)
    length_dir = (b - a).normalized()
    across = Vector((-length_dir.z, 0, length_dir.x)).normalized()
    depth = length_dir.cross(across).normalized()
    # Long longitudinal facets produce a shard, rather than a feather silhouette.
    shoulder = a.lerp(b, 0.43)
    upper = a.lerp(b, 0.66)
    vs = [a,
          shoulder + across * width * 0.50,
          shoulder + depth * thickness * 0.50,
          shoulder - across * width * 0.50,
          shoulder - depth * thickness * 0.50,
          upper + across * width * 0.29,
          upper + depth * thickness * 0.31,
          upper - across * width * 0.29,
          upper - depth * thickness * 0.31,
          b]
    fs = [(0, 2, 1), (0, 3, 2), (0, 4, 3), (0, 1, 4),
          (1, 2, 6, 5), (2, 3, 7, 6), (3, 4, 8, 7), (4, 1, 5, 8),
          (5, 6, 9), (6, 7, 9), (7, 8, 9), (8, 5, 9)]
    ob = mesh(name, [tuple(v) for v in vs], fs, gw_glass[0], smooth=False)
    for m in gw_glass[1:]:
        ob.data.materials.append(m)
    # Keep pink and violet dominant even as each shard varies; reserve warm and
    # mint facets for the shorter roots so strong studio lights do not wash the
    # broad blade faces into white or yellow.
    body_palette = [0, 1, 3, 6]
    main_colour = body_palette[palette_offset % len(body_palette)]
    second_colour = body_palette[(palette_offset + 1) % len(body_palette)]
    tip_colour = body_palette[(palette_offset + 2) % len(body_palette)]
    face_indices = [2, 5, 4, 6,
                    main_colour, second_colour, 3, 0,
                    tip_colour, main_colour, 0, 3]
    for f, idx in zip(ob.data.polygons, face_indices):
        f.material_index = idx
    return ob


# Each side originates behind the shoulder blades. Different heights, blade lengths
# and out-of-plane angles make the back and side silhouette read like the reference.
gw_wing_layout = [
    # root x, root z, tip x, tip z, tip y, width, thickness, colour offset
    (0.084, 1.326, 0.353, 1.698, 0.172, 0.044, 0.020, 0),
    (0.102, 1.337, 0.310, 1.568, 0.241, 0.049, 0.018, 1),
    (0.093, 1.322, 0.379, 1.479, 0.194, 0.041, 0.018, 0),
    (0.083, 1.312, 0.308, 1.394, 0.248, 0.041, 0.017, 2),
    (0.090, 1.295, 0.300, 1.324, 0.180, 0.034, 0.017, 1),
    (0.080, 1.291, 0.280, 1.245, 0.224, 0.038, 0.017, 3),
    (0.069, 1.285, 0.215, 1.205, 0.173, 0.039, 0.018, 0),
    (0.070, 1.309, 0.230, 1.477, 0.294, 0.037, 0.019, 4),
]
for gw_side, gw_label in [(-1, 'R'), (1, 'L')]:
    for gw_i, (rx, rz, tx, tz, ty, ww, tt, cc) in enumerate(gw_wing_layout):
        gw_shard('Crystal wing ' + gw_label + ' / shard %02d' % (gw_i + 1),
                 (gw_side * rx, 0.154 + 0.008 * (gw_i % 3), rz),
                 (gw_side * tx, ty, tz), ww, tt, cc)
    # Small concealed opal socket behind the shoulder, with no visible branches.
    uv('Wing opal socket ' + gw_label, (gw_side * .078, .15, 1.307),
       (.022, .014, .025), gw_glass[6], segments=24, rings=16)


collection('07 • Luminous halo')
gw_halo_mat = mat('Halo / warm champagne light', (1.0, .82, .60, 1), metallic=.05, rough=.25)
gw_bs = gw_halo_mat.node_tree.nodes.get('Principled BSDF')
if gw_bs:
    if 'Emission Color' in gw_bs.inputs:
        gw_bs.inputs['Emission Color'].default_value = (1.0, .74, .46, 1)
    elif 'Emission' in gw_bs.inputs:
        gw_bs.inputs['Emission'].default_value = (1.0, .74, .46, 1)
    if 'Emission Strength' in gw_bs.inputs:
        gw_bs.inputs['Emission Strength'].default_value = 3.5
gw_halo_verts = []
gw_halo_faces = []
gw_halo_n, gw_halo_t = 128, 12
for gw_i in range(gw_halo_n):
    gw_a = math.tau * gw_i / gw_halo_n
    for gw_j in range(gw_halo_t):
        gw_b = math.tau * gw_j / gw_halo_t
        gw_halo_verts.append(((.084 + .00245 * math.cos(gw_b)) * math.cos(gw_a),
                              (.070 + .00245 * math.cos(gw_b)) * math.sin(gw_a),
                              1.805 + .00245 * math.sin(gw_b)))
for gw_i in range(gw_halo_n):
    for gw_j in range(gw_halo_t):
        gw_halo_faces.append((gw_i * gw_halo_t + gw_j,
                              ((gw_i + 1) % gw_halo_n) * gw_halo_t + gw_j,
                              ((gw_i + 1) % gw_halo_n) * gw_halo_t + (gw_j + 1) % gw_halo_t,
                              gw_i * gw_halo_t + (gw_j + 1) % gw_halo_t))
mesh('Floating luminous halo', gw_halo_verts, gw_halo_faces, gw_halo_mat, smooth=True)


collection('08 • Tactical harness and belt equipment')
gw_black = mat('Gear / charcoal polymer', (.023, .025, .026, 1), metallic=.12, rough=.48)
gw_edge = mat('Gear / graphite edge', (.051, .054, .052, 1), metallic=.42, rough=.36)
gw_webbing = mat('Gear / woven graphite webbing', (.032, .035, .035, 1), rough=.83)
gw_stitch = mat('Gear / webbing stitches', (.19, .19, .175, 1), rough=.80)
gw_olive = mat('Gear / olive nylon', (.075, .082, .069, 1), rough=.72)
gw_olive_light = mat('Gear / olive lid facing', (.113, .118, .101, 1), rough=.68)
gw_steel = mat('Gear / satin steel fittings', (.30, .31, .285, 1), metallic=.78, rough=.32)
gw_burgundy = mat('Gear / oxblood webbing', (.30, .052, .100, 1), rough=.62)
gw_pale = mat('Gear / faded bone markings', (.61, .60, .53, 1), rough=.69)


def gw_ribbon(name, points, width, material):
    pts = [Vector(p) for p in points]
    vv = []
    for i, p in enumerate(pts):
        tangent = pts[min(i + 1, len(pts)-1)] - pts[max(i - 1, 0)]
        across = Vector((-tangent.z, 0, tangent.x)).normalized() * width * .5
        vv.extend([tuple(p - across), tuple(p + across)])
    ff = [(i * 2, i * 2 + 1, i * 2 + 3, i * 2 + 2) for i in range(len(pts)-1)]
    ob = mesh(name, vv, ff, material, smooth=True)
    mod = ob.modifiers.new('Webbing thickness', 'SOLIDIFY')
    mod.thickness = .0022
    mod = ob.modifiers.new('Soft strap edges', 'BEVEL')
    mod.width = .0010
    mod.segments = 2
    return ob


for gw_s, gw_l in [(-1, 'R'), (1, 'L')]:
    gw_points = [(gw_s * .117, .085, 1.391),
                 (gw_s * .111, .126, 1.362),
                 (gw_s * .074, .149, 1.291),
                 (gw_s * .009, .148, 1.214),
                 (-gw_s * .071, .137, 1.123),
                 (-gw_s * .107, .124, 1.080)]
    gw_ribbon('Back crossing harness ' + gw_l, gw_points, .023, gw_webbing)
    # Parallel stitching emphasizes textile construction in close back views.
    for gw_dx in [-.0075, .0075]:
        curve('Harness seam ' + gw_l, [(x + gw_dx, y + .0018, z) for x, y, z in gw_points],
              .00065, gw_stitch)
    gw_hardware = cube('Harness adjuster ' + gw_l, (gw_s * .068, .155, 1.281),
                       (.032, .007, .020), gw_edge, bevel=.002)
    gw_hardware.rotation_euler.y = gw_s * -.54
    cube('Rear belt anchor ' + gw_l, (gw_s * .107, .132, 1.095),
         (.031, .011, .033), gw_black, bevel=.003)

# Rear compact utility pouch: separate gussets, flap, piping and two strap buckles.
cube('Rear utility pouch / padded body', (0, .166, 1.025), (.190, .077, .121), gw_olive, bevel=.015)
cube('Rear utility pouch / rear gusset', (0, .126, 1.029), (.165, .025, .099), gw_black, bevel=.009)
cube('Rear utility pouch / flap', (0, .207, 1.050), (.180, .012, .068), gw_olive_light, bevel=.008)
cube('Rear utility pouch / lower panel', (0, .206, .998), (.155, .009, .026), gw_olive, bevel=.004)
for gw_s in [-1, 1]:
    cube('Rear pouch / side gusset', (gw_s * .091, .168, 1.025), (.015, .063, .089), gw_edge, bevel=.005)
    cube('Rear pouch / closure webbing', (gw_s * .057, .217, 1.027), (.017, .005, .099), gw_webbing, bevel=.0015)
    cube('Rear pouch / closure buckle', (gw_s * .057, .222, 1.013), (.024, .009, .022), gw_edge, bevel=.002)
    cube('Rear pouch / buckle face inset', (gw_s * .057, .2275, 1.013), (.012, .002, .010), gw_olive_light, bevel=.0007)
    curve('Rear pouch / flap stitching', [(gw_s * .080, .215, 1.076),
                                         (gw_s * .080, .215, 1.029),
                                         (gw_s * .013, .215, 1.024)], .00065, gw_stitch)
cube('Rear pouch / small maker tab', (.013, .216, 1.072), (.019, .003, .010), gw_webbing, bevel=.001)
cube('Rear pouch / tab stripe', (.013, .218, 1.072), (.010, .001, .002), gw_pale, bevel=.0002)

# Left hip double pocket, visible from front and profile.
for gw_i in range(2):
    gw_py = -.013 + gw_i * .047
    cube('Left belt pocket %d' % (gw_i + 1), (.164, gw_py, 1.056),
         (.047, .049, .087), gw_black, bevel=.008)
    cube('Left belt pocket / flap %d' % (gw_i + 1), (.190, gw_py, 1.077),
         (.009, .042, .040), gw_edge, bevel=.003)
    cube('Left belt pocket / keeper %d' % (gw_i + 1), (.196, gw_py, 1.050),
         (.004, .012, .038), gw_webbing, bevel=.001)
    cube('Left belt pocket / snap %d' % (gw_i + 1), (.199, gw_py, 1.050),
         (.002, .012, .012), gw_steel, bevel=.003)
gw_ribbon('Oxblood hanging belt strap', [(.177, .023, 1.042), (.187, .024, .966),
                                       (.191, .019, .870), (.188, .018, .837)], .012, gw_burgundy)
cube('Hanging strap / metal tip', (.188, .018, .840), (.014, .006, .014), gw_edge, bevel=.001)

# Compact holstered side utility piece, mounted outside the left thigh.
cube('Left thigh / utility sheath', (.160, -.003, .811), (.040, .043, .141), gw_black, bevel=.006)
cube('Left thigh / sheath inlay', (.183, -.003, .805), (.006, .027, .085), gw_olive_light, bevel=.002)
cube('Left thigh / upper retention band', (.163, -.003, .842), (.048, .049, .016), gw_webbing, bevel=.002)
cube('Left thigh / lower retention band', (.163, -.003, .774), (.048, .049, .013), gw_webbing, bevel=.002)
cube('Left thigh / utility grip', (.161, -.003, .895), (.030, .030, .042), gw_edge, bevel=.003)
for gw_i in range(4):
    cube('Left thigh / grip groove', (.178, -.003, .881 + gw_i * .008),
         (.003, .026, .0024), gw_black, bevel=.0005)


collection('09 • Carbine visual prop')
# This is a nonfunctional external design prop, assembled as solid display geometry.
gw_prop_origin = Vector((-.199, .028, .908))
gw_prop_tilt = .215


def gw_prop_pt(x, y, z):
    return tuple(gw_prop_origin + Vector((x * math.cos(gw_prop_tilt) + z * math.sin(gw_prop_tilt),
                                         y,
                                         -x * math.sin(gw_prop_tilt) + z * math.cos(gw_prop_tilt))))


def gw_prop_box(name, offset, size, material, bevel=.002):
    ob = cube(name, gw_prop_pt(*offset), size, material, bevel=bevel)
    ob.rotation_euler.y = gw_prop_tilt
    return ob


gw_prop_box('Carbine / central receiver', (0, 0, .014), (.043, .041, .145), gw_black, .004)
gw_prop_box('Carbine / receiver faceplate', (0, -.023, .038), (.035, .007, .105), gw_edge, .002)
gw_prop_box('Carbine / stock spine', (0, .002, .131), (.024, .028, .074), gw_edge, .002)
gw_prop_box('Carbine / stock cheek pad', (.005, -.002, .170), (.052, .038, .045), gw_black, .003)
gw_prop_box('Carbine / butt cap', (.006, -.002, .195), (.061, .040, .012), gw_edge, .002)
gw_prop_box('Carbine / foregrip shell', (0, -.001, -.095), (.037, .042, .095), gw_black, .003)
gw_prop_box('Carbine / foregrip left inset', (-.020, -.002, -.095), (.005, .029, .067), gw_olive, .001)
gw_prop_box('Carbine / forward barrel shroud', (0, 0, -.155), (.019, .023, .056), gw_edge, .0015)
gw_prop_box('Carbine / muzzle cap', (0, 0, -.188), (.025, .028, .017), gw_black, .001)
gw_prop_box('Carbine / solid muzzle face', (0, -.015, -.188), (.013, .003, .008), gw_edge, .001)
gw_prop_box('Carbine / side grip', (.038, .001, .018), (.050, .034, .025), gw_black, .002)
gw_prop_box('Carbine / magazine exterior', (.037, .001, -.027), (.026, .031, .058), gw_olive, .002)
gw_prop_box('Carbine / magazine floor plate', (.037, .001, -.059), (.031, .035, .010), gw_edge, .001)
gw_prop_box('Carbine / top rail', (-.022, -.001, .011), (.010, .030, .197), gw_edge, .001)
for gw_i in range(12):
    gw_prop_box('Carbine / rail notch %02d' % gw_i, (-.028, -.001, -.080 + gw_i * .016),
                (.004, .034, .006), gw_black, .0005)
for gw_i in range(6):
    gw_prop_box('Carbine / handguard vent %02d' % gw_i, (0, -.023, -.126 + gw_i * .012),
                (.022, .003, .0045), gw_edge, .0007)
gw_prop_box('Carbine / receiver accent', (0, -.028, .068), (.018, .002, .021), gw_olive_light, .001)
gw_prop_box('Carbine / oxblood identification', (0, -.029, .052), (.022, .001, .005), gw_burgundy, .0005)
for gw_z in [-.012, .027, .081]:
    uv('Carbine / recessed screw', gw_prop_pt(.012, -.028, gw_z), (.002, .001, .002),
       gw_steel, segments=12, rings=8)
gw_prop_box('Carbine / upper sling lug', (.015, .019, .100), (.025, .012, .016), gw_edge, .002)
gw_ribbon('Carbine / shoulder sling', [(-.120, .089, 1.384), (-.148, .099, 1.307),
                                     (-.159, .094, 1.206), (-.167, .066, 1.101),
                                     gw_prop_pt(.015, .025, .106)], .016, gw_webbing)
gw_ribbon('Carbine / lower retention strap', [(-.155, .059, 1.069), (-.205, .070, .968),
                                            gw_prop_pt(-.016, .026, -.074)], .013, gw_webbing)
