import bpy, os
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'Ironclad_07.blend'))
gun=bpy.data.objects['GUN | elevation pivot']
children=[(o,o.matrix_world.copy()) for o in gun.children]
gun.location=(-1.65,0,2.68)
bpy.context.view_layer.update()
for o,m in children:o.matrix_world=m
scene=bpy.context.scene
scene.cycles.samples=96
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Ironclad_07.blend'))
scene.camera=bpy.data.objects['CAMERA | rear detail']
scene.render.resolution_x=1200;scene.render.resolution_y=900
scene.render.filepath=os.path.join(OUT,'tank_rear.png')
bpy.ops.render.render(write_still=True)
print('VERIFIED',len(bpy.data.objects),'objects',len([o for o in bpy.data.objects if o.name.startswith('Track ') and 'shoe' in o.name]),'track links',flush=True)
