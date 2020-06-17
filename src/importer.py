import bpy
import bpy_extras
import bmesh
import os
from mathutils import Vector, Matrix, Quaternion
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, CollectionProperty
from .reader import RmfReader
from .rmf import *
from .wad import *
from .config import rmf_icons
from .utils import convert_rmf_face_texture_coordinates_to_uvs


class RMF_LI_WadListItem(bpy.types.PropertyGroup):
    path: StringProperty()
    texture_count: IntProperty()

    @property
    def name(self):
        return self.path

class RMF_UL_WadList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        print(rmf_icons)
        layout.alignment = 'LEFT'
        # layout.prop(item, 'is_selected', icon_only=True)
        layout.label(text=item.path, icon='ACTION')

    def filter_items(self, context, data, property):
        wads = getattr(data, property)
        flt_flags = []
        flt_neworder = []
        if self.filter_name:
            flt_flags = bpy.types.UI_UL_list.filter_items_by_name(self.filter_name, self.bitflag_filter_item, wads, 'name', reverse=self.use_filter_invert)
        return flt_flags, flt_neworder


class RMF_OT_AddWadOperator(bpy.types.Operator):
    bl_idname = "scene.rmf_add_wad_operator"
    bl_label = "Add WADs"

    filepath : bpy.props.StringProperty(name="File Path", description="Filepath used for importing WAD files", maxlen=1024, default="")
    files : bpy.props.CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )
    filename_ext = ".wad"
    filter_glob : bpy.props.StringProperty(default="*.wad", options={'HIDDEN'})

    def execute(self, context):
        root = os.path.dirname(self.filepath)
        for file in self.files:
            wad_list_item = context.scene.rmf_wad_list.add()
            wad_list_item.path = os.path.join(root, file.name)
            wad_list_item.texture_count = 0
        return {'FINISHED'}


    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


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
        maxlen=255,  # Max internal buffer length, longer would be hilighted.
    )

    should_import_textures : BoolProperty(
        default=False
    )

    should_ignore_null_faces : BoolProperty(
        default=True,
    )

    wads = []
    texture_size_cache = dict()  # str: tuple dict

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(self, 'should_import_textures', text='Import Textures')
        if self.should_import_textures:
            box = layout.box()
            box.label(text='Textures', icon='ACTION')
            row = box.row()
            row.template_list('RMF_UL_WadList', 'asd', scene, 'rmf_wad_list', scene, 'rmf_wad_list_index', rows=8)
            layout.operator(RMF_OT_AddWadOperator.bl_idname, icon='ADD')
        layout.prop(self, 'should_ignore_null_faces', text='Ignore NULL faces')

    '''
    Loads all the WADs in the list.
    '''
    def load_wads(self, context):
        self.wads.clear()
        for wad in context.scene.rmf_wad_list:
            print(wad)
            self.wads.append(Wad(wad.path))

    ''''
    Gets the size of a texture, also caches the lookup to a local dictionary.
    '''
    def get_texture_size(self, name: str):
        name = name.upper()
        if name in self.texture_size_cache:
            return self.texture_size_cache[name]
        for wad in self.wads:
            if wad.has_texture(name):
                size = wad.get_texture_size(name)
                self.texture_size_cache[name] = size
                return size
        raise LookupError(f'cannot get texture size for \"{name}\"')


    def add_solid(self, solid):
        mesh_name = 'Solid.000'
        mesh = bpy.data.meshes.new(mesh_name)

        mesh_object = bpy.data.objects.new(mesh_name, mesh)

        '''
        Create or reuse materials 
        '''
        textures = []
        for f in solid.faces:
            if self.should_ignore_null_faces and f.texture_name == 'NULL':
                continue
            if bpy.data.materials.find(f.texture_name) == -1:
                bpy.data.materials.new(f.texture_name)
            material = bpy.data.materials[f.texture_name]
            if f.texture_name not in textures:
                textures.append(f.texture_name)
                mesh.materials.append(material)

        bm = bmesh.new()
        vertex_offset = 0
        for f in solid.faces:
            if self.should_ignore_null_faces and f.texture_name == 'NULL':
                continue
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

        if self.should_import_textures:
            '''
            Assign texture coordinates
            '''
            uv_layer = mesh.uv_layers.new()
            uv_texture = mesh.uv_layers[0]
            j = 0
            for face_index, face in enumerate(solid.faces):
                # NOTE: the UV order has to be reversed to match the reversed vertices due to winding order
                # TODO: come up with a more elegant solution for this
                if self.should_ignore_null_faces and face.texture_name == 'NULL':
                    continue
                texture_size = self.get_texture_size(face.texture_name)
                uvs = convert_rmf_face_texture_coordinates_to_uvs(face, texture_size)
                for uv in reversed(uvs):
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
        self.load_wads(context)
        rmf = RmfReader().from_file(self.filepath)
        self.import_map(rmf)
        return {'FINISHED'}