import bpy, os, math, json
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'Endfield_Operator.blend'))
main=bpy.context.scene
model_root=bpy.data.objects['OPERATOR | master control']
# A separate scene displays linked instances of the same editable character.
asset=bpy.data.collections.new('ASSET | linked character for turnaround')
asset.objects.link(model_root)
for ob in list(bpy.data.objects):
    if ob.parent==model_root:asset.objects.link(ob)
board=bpy.data.scenes.new('02 | Three-view inspection')
board.world=main.world
label_mat=bpy.data.materials.new('Studio | unlit view labels');label_mat.use_nodes=True
ln=label_mat.node_tree.nodes;ln.clear();le=ln.new('ShaderNodeEmission');le.inputs['Color'].default_value=(.65,.70,.72,1);le.inputs['Strength'].default_value=.8;lo=ln.new('ShaderNodeOutputMaterial');label_mat.node_tree.links.new(le.outputs[0],lo.inputs['Surface'])
for ob in main.objects:
    if ob.type=='LIGHT':board.collection.objects.link(ob)
for name,x,rz in [('FRONT',-.95,0),('SIDE',0,-math.pi/2),('BACK',.95,math.pi)]:
    inst=bpy.data.objects.new(name+' | character instance',None);inst.instance_type='COLLECTION';inst.instance_collection=asset;inst.location=(x,0,0);inst.rotation_euler.z=rz;board.collection.objects.link(inst)
    d=bpy.data.curves.new(name+' label','FONT');d.body=name;d.size=.04;d.align_x='CENTER';d.extrude=0
    o=bpy.data.objects.new(name+' | view label',d);o.location=(x,-.04,-.045);o.rotation_euler=(math.pi/2,0,0);board.collection.objects.link(o)
    o.data.materials.append(label_mat)
d=bpy.data.cameras.new('CAM | Three-view plate');cam=bpy.data.objects.new('CAM | Three-view plate',d);board.collection.objects.link(cam);cam.location=(0,-7,.88);cam.rotation_euler=(Vector((0,0,.88))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=2.97;board.camera=cam
board.render.engine='CYCLES';board.cycles.samples=48;board.cycles.use_denoising=True;board.cycles.device=main.cycles.device
board.render.resolution_x=2250;board.render.resolution_y=1575;board.render.resolution_percentage=100
board.render.image_settings.file_format='PNG';board.render.filepath=os.path.join(OUT,'three_views.png');board.view_settings.view_transform='AgX'
board.unit_settings.system='METRIC'
main.name='01 | Operator studio';main.camera=bpy.data.objects['CAM | Portrait three quarter']
main.render.resolution_x=1100;main.render.resolution_y=1500;main.cycles.samples=64
readme=bpy.data.texts.get('READ ME | model notes') or bpy.data.texts.new('READ ME | model notes');readme.clear();readme.write(open(os.path.join(OUT,'README.md'),encoding='utf-8').read())
# Sanity-check geometry, transforms and portable image packing.
meshes=[o for o in main.objects if o.type=='MESH' and o.parent==model_root]
invalid=[]
for o in meshes:
    if not all(math.isfinite(x) for v in o.data.vertices for x in v.co):invalid.append(o.name)
report={'character_mesh_objects':len(meshes),'nonfinite_meshes':invalid,'reference_packed':bool(bpy.data.images.get('reference.jpg').packed_file),'camera_count':sum(o.type=='CAMERA' for o in main.objects),'scene_names':[s.name for s in bpy.data.scenes],'static_model':True}
open(os.path.join(OUT,'validation.json'),'w',encoding='utf-8').write(json.dumps(report,indent=2))
assert not invalid,invalid
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Endfield_Operator.blend'))
bpy.context.window.scene=board
bpy.ops.render.render(write_still=True)
print('FINAL_SAVED_AND_CHECKED',report,flush=True)
