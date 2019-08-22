import bpy
import bpy_extras
import bmesh
from mathutils import Vector, Matrix, Quaternion
from bpy.props import StringProperty, BoolProperty, FloatProperty
from .reader import RmfReader
from .rmf import *


class RMF_OT_ImportOperator(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = 'io_scene_rmf.rmf_import'  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = 'Import Rich Map Format'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    # ImportHelper mixin class uses this
    filename_ext = ".rmf"

    filter_glob : StringProperty(
        default="*.rmf",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clighted.
    )

    def add_solid(self, solid):
        mesh_name = 'Solid.000'
        mesh = bpy.data.meshes.new(mesh_name)
        mesh_object = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.scene.collection.objects.link(mesh_object)
        bm = bmesh.new()
        vertex_offset = 0
        for f in solid.faces:
            for vertex in f.vertices:
                bm.verts.new(tuple(vertex))
            bm.verts.ensure_lookup_table()
            # The face order is reversed because of differences in winding order
            face = reversed([bm.verts[vertex_offset + x] for x in range(len(f.vertices))])
            bmface = bm.faces.new(face)
            vertex_offset += len(f.vertices)
        bm.to_mesh(mesh)
        return mesh_object

    def add_object(self, object):
        if type(object) == Rmf.Solid:
            self.add_solid(object)
        elif type(object) == Rmf.Entity:
            # TODO: abstract this out somehow
            entity = object
            if entity.is_point_entity:
                if entity.classname == 'light_environment':
                    # TODO: create new light
                    light_data = bpy.data.lights.new(name='light_environment', type='SUN')
                    light_object = bpy.data.objects.new('light_environment', light_data)
                    light_object.location = tuple(entity.location)
                    # TODO: put the light somewhere
                    bpy.context.scene.collection.objects.link(light_object)
                    pitch, yaw, roll = map(lambda x: float(x), entity['angles'].split())
                    print(pitch, yaw, roll)
            else:
                for solid in object.brushes:
                    self.add_solid(solid)
        elif type(object) == Rmf.Group:
            objects = [self.add_object(x) for x in object.objects]
            # bpy.ops.object.select_all(action='DESELECT')
            # for object in objects:
            #    object.select = True
            # bpy.oops.group.create()

    def import_map(self, map):
        for i, object in enumerate(map.objects):
            self.add_object(object)

    def execute(self, context):
        # Now add it all in baybee
        rmf = RmfReader().from_file(self.filepath)
        self.import_map(rmf)
        return {'FINISHED'}