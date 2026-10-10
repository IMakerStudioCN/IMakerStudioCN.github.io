import bpy,os
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'Endfield_Operator.blend'))
m=bpy.data.materials.new('Studio | unlit view labels');m.use_nodes=True
n=m.node_tree.nodes;n.clear();e=n.new('ShaderNodeEmission');e.inputs['Color'].default_value=(.65,.70,.72,1);e.inputs['Strength'].default_value=.8;o=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(e.outputs[0],o.inputs['Surface'])
for ob in bpy.data.scenes['02 | Three-view inspection'].objects:
    if ob.type=='FONT':ob.data.materials.clear();ob.data.materials.append(m)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Endfield_Operator.blend'))
bpy.context.window.scene=bpy.data.scenes['02 | Three-view inspection']
bpy.ops.render.render(write_still=True)
