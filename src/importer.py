import bpy
import bpy_extras
import bmesh
from mathutils import Vector, Matrix, Quaternion
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
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
    filter_glob: StringProperty(
        default="*.rmf",
        options={'HIDDEN'},
        maxlen=255,
    )
    should_skip_null_faces: BoolProperty(
        default=True,
        name='Skip NULL Faces'
    )

    units_items = (
        ('NATIVE', 'Native', 'Native scale (1 unit = 1/16 ft)'),
        ('METRIC', 'Metric', 'Metric scale (1 unit = 1m)')
    )
    units_default = 'METRIC'
    units_scales = {
        'NATIVE': 1.0,
        'METRIC': 0.01904999939
    }
    scale = units_scales[units_default]

    def update_units(self, context):
        self.scale = self.units_scales[self.units]

    units: EnumProperty(
        items=units_items,
        name='Units',
        default=units_default,
        options={'ANIMATABLE'},
        update=update_units
    )

    def add_solid(self, solid: Rmf.Solid):
        mesh_name = 'Solid.000'
        mesh = bpy.data.meshes.new(mesh_name)
        mesh_object = bpy.data.objects.new(mesh_name, mesh)
        mesh_object.scale = (self.scale, self.scale, self.scale)

        bm = bmesh.new()
        vertex_offset = 0
        for f in solid.faces:
            if self.should_skip_null_faces and f.texture_name == 'NULL':
                continue
            for vertex in f.vertices:
                bm.verts.new(tuple(vertex))
            bm.verts.ensure_lookup_table()
            # The face order is reversed because of differences in winding order
            face = reversed([bm.verts[vertex_offset + x] for x in range(len(f.vertices))])
            bm.faces.new(face)
            vertex_offset += len(f.vertices)
        bm.to_mesh(mesh)

        collection = self.get_collection_for_solid(solid)
        collection.objects.link(mesh_object)

        return mesh_object

    def get_collection_for_solid(self, solid: Rmf.Solid):
        if solid.has_clip:
            return bpy.data.collections['Clip']
        elif solid.has_sky:
            return bpy.data.collections['Sky']
        elif solid.has_trigger:
            return bpy.data.collections['Trigger']
        else:
            return bpy.context.scene.collection

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
                elif entity.classname == 'env_model':
                    entity['model']
                    pass
            else:
                # TODO: create a collection
                brush_entities_collection = bpy.data.collections['Brush Entities']
                entity_collection = bpy.data.collections.new(entity.classname)
                brush_entities_collection.children.link(entity_collection)
                # TODO: make a new EMPTY
                for solid in object.brushes:
                    object = self.add_solid(solid)
                    entity_collection.objects.link(object)
        elif type(object) == Rmf.Group:
            # TODO: we could add grouped objects to a collection
            objects = [self.add_object(x) for x in object.objects]
            # bpy.ops.object.select_all(action='DESELECT')
            # for object in objects:
            #    object.select = True
            # bpy.oops.group.create()

    def import_map(self, map: Rmf.World):
        collections_names = 'Trigger', 'Sky', 'Clip', 'Brush Entities'
        for name in collections_names:
            collection = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(collection)
        for i, object in enumerate(map.objects):
            self.add_object(object)

    def execute(self, context):
        rmf = RmfReader().from_file(self.filepath)
        self.import_map(rmf)
        return {'FINISHED'}
