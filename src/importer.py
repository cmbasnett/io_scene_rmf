import bpy
import bpy_extras
import bmesh
from mathutils import Vector, Matrix, Quaternion
from bpy.props import StringProperty, BoolProperty, FloatProperty
from .reader import RmfReader
from .rmf import *
from .utils import convert_rmf_to_uv


class RMF_OT_ImportOperator(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = 'io_scene_rmf.rmf_import'  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = 'Import Rich Map Format'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    # ImportHelper mixin class uses this
    filename_ext = '.rmf'

    filter_glob : StringProperty(
        default="*.rmf",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clighted.
    )

    def add_solid(self, solid):
        mesh_name = 'Solid.000'
        mesh = bpy.data.meshes.new(mesh_name)

        mesh_object = bpy.data.objects.new(mesh_name, mesh)

        textures = []
        for f in solid.faces:
            if bpy.data.materials.find(f.texture_name) == -1:
                bpy.data.materials.new(f.texture_name)
            material = bpy.data.materials[f.texture_name]
            if f.texture_name not in textures:
                textures.append(f.texture_name)
                mesh.materials.append(material)

        bm = bmesh.new()
        vertex_offset = 0
        for f in solid.faces:
            for vertex in f.vertices:
                bm.verts.new(tuple(vertex))
            bm.verts.ensure_lookup_table()

            # The face order is reversed because of differences in winding order
            face = reversed([bm.verts[vertex_offset + x] for x in range(len(f.vertices))])
            bmface = bm.faces.new(face)
            bmface.material_index = textures.index(f.texture_name)
            vertex_offset += len(f.vertices)

        bm.to_mesh(mesh)

        collection = self.get_collection_for_solid(solid)
        collection.objects.link(mesh_object)

        '''
        Assign texture coordinates
        '''
        uv_layer = mesh.uv_layers.new()
        uv_texture = mesh.uv_layers[0]
        j = 0
        for face_index, face in enumerate(solid.faces):
            # NOTE: the UV order has to be reversed to match the reversed vertices due to winding order
            # TODO: come up with a more elegant solution for this
            uv = reversed(convert_rmf_to_uv(face))
            for i, uv in enumerate(uv):
                uv[1] = -uv[1]
                uv_texture.data[j].uv = uv.tolist()
                j += 1

        return mesh_object

    def get_collection_for_solid(self, solid):
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
            solid = self.add_solid(object)
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
                # TODO: create a collection
                brush_entities_collection = bpy.data.collections['Brush Entities']
                entity_collection = bpy.data.collections.new(entity.classname)
                brush_entities_collection.children.link(entity_collection)
                # TODO: make a new EMPTY
                for solid in object.brushes:
                    object = self.add_solid(solid)
                    entity_collection.objects.link(object)
        elif type(object) == Rmf.Group:
            objects = [self.add_object(x) for x in object.objects]
            # bpy.ops.object.select_all(action='DESELECT')
            # for object in objects:
            #    object.select = True
            # bpy.oops.group.create()

    def import_map(self, map):
        # TODO: create collections!
        collections_names = 'Trigger', 'Sky', 'Clip', 'Brush Entities'
        for name in collections_names:
            collection = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(collection)
        for i, object in enumerate(map.objects):
            self.add_object(object)

    def execute(self, context):
        # Now add it all in baybee
        rmf = RmfReader().from_file(self.filepath)
        self.import_map(rmf)
        return {'FINISHED'}