import bpy
from bpy_extras.io_utils import ImportHelper
import bmesh
import os
from typing import cast as typing_cast
from bpy.types import Context, ShaderNodeTexImage, Operator, PropertyGroup, UIList, UI_UL_list, OperatorFileListElement
from bpy.props import StringProperty, BoolProperty, IntProperty, CollectionProperty
from .reader import RmfReader
from .rmf import *
from .wad import *
from .utils import convert_rmf_face_texture_coordinates_to_uvs


class RMF_LI_WadListItem(PropertyGroup):
    path: StringProperty()
    texture_count: IntProperty()

    @property
    def name(self):
        return self.path


class RMF_UL_WadList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.alignment = 'LEFT'
        # layout.prop(item, 'is_selected', icon_only=True)
        layout.label(text=item.path, icon='ACTION')

    def filter_items(self, context, data, property):
        wads = getattr(data, property)
        flt_flags = []
        flt_neworder = []
        if self.filter_name:
            flt_flags = UI_UL_list.filter_items_by_name(self.filter_name, self.bitflag_filter_item, wads, 'name', reverse=self.use_filter_invert)
        return flt_flags, flt_neworder


class RMF_OT_AddWadOperator(Operator):
    bl_idname = "scene.rmf_add_wad_operator"
    bl_label = "Add WADs"

    filepath : StringProperty(name="File Path", description="Filepath used for importing WAD files", maxlen=1024, default="")
    files : CollectionProperty(
        name="File Path",
        type=OperatorFileListElement,
    )
    filename_ext = ".wad"
    filter_glob : StringProperty(default="*.wad", options={'HIDDEN'})

    def execute(self, context):
        root = os.path.dirname(self.filepath)
        for file in self.files:
            wad_list_item = context.scene.rmf_wad_list.add()
            wad_list_item.path = os.path.join(root, file.name)
            wad_list_item.texture_count = 0
        return {'FINISHED'}


    def invoke(self, context, event):
        assert context.window_manager
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class RMF_OT_import(Operator, ImportHelper):
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
        default=False,
    )

    wads = []
    texture_size_cache = dict()  # str: tuple dict

    def draw(self, context: Context):
        layout = self.layout
        assert layout is not None
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
            self.wads.append(Wad(wad.path))

    def has_wad_for_texture(self, name: str):
        try:
            self.get_wad_for_texture(name)
            return True
        except LookupError:
            return False

    def get_wad_for_texture(self, name: str):
        name = name.upper()
        for wad in self.wads:
            if wad.has_texture(name):
                return wad
        raise LookupError(f'no wad with texture "{name}"')

    ''''
    Gets the size of a texture, also caches the lookup to a local dictionary.
    '''
    def get_texture_size(self, name: str):
        name = name.upper()
        if name in self.texture_size_cache:
            return self.texture_size_cache[name]
        wad = self.get_wad_for_texture(name)
        size = wad.get_texture_size(name)
        self.texture_size_cache[name] = size
        return size

    def get_texture_pixels(self, name: str):
        wad = self.get_wad_for_texture(name)
        return wad.get_texture_pixels(name)

    def load_image(self, texture_name: str):
        if texture_name in bpy.data.images:
            return bpy.data.images[texture_name]
        if not self.has_wad_for_texture(texture_name):
            return None
        width, height = self.get_texture_size(texture_name)
        pixels = self.get_texture_pixels(texture_name)
        image = bpy.data.images.new(texture_name.upper(), width=width, height=height)
        image.pixels = pixels
        return image

    def load_material(self, texture_name: str):
        if bpy.data.materials.find(texture_name) != -1:
            return bpy.data.materials[texture_name]
        material = bpy.data.materials.new(texture_name)
        if material.node_tree is None:
            return None
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # TODO: make this better, set up node positions etc.
        diffuse_bsdf_node = nodes.new('ShaderNodeBsdfDiffuse')

        image_texture_node = typing_cast(ShaderNodeTexImage, nodes.new('ShaderNodeTexImage'))
        image_texture_node.image = self.load_image(texture_name)

        material_output_node = nodes['Material Output']

        links.new(diffuse_bsdf_node.inputs['Color'], image_texture_node.outputs['Color'])
        links.new(material_output_node.inputs['Surface'], diffuse_bsdf_node.outputs['BSDF'])

        return material

    def add_solid(self, solid: Rmf.Solid):
        '''
        Prune faces based on material names.
        '''
        # TODO: have this list be part of the settings!
        textures_to_ignore = {'NULL', 'AAATRIGGER', 'CLIP', 'SKY', '{BLUE'}
        faces = list(filter(lambda f: f.texture_name not in textures_to_ignore, solid.faces))

        if len(faces) == 0:
            return None

        mesh_name = 'Solid.000'
        mesh = bpy.data.meshes.new(mesh_name)

        mesh_object = bpy.data.objects.new(mesh_name, mesh)

        '''
        Create or reuse materials 
        '''
        textures = []
        for f in faces:
            material = self.load_material(f.texture_name)
            if f.texture_name not in textures:
                textures.append(f.texture_name)
                mesh.materials.append(material)

        bm = bmesh.new()
        vertex_offset = 0
        for f in faces:
            for vertex in f.vertices:
                bm.verts.new(tuple(vertex))
            bm.verts.ensure_lookup_table()

            # The face order is reversed because of differences in winding order
            face = list(reversed([bm.verts[vertex_offset + x] for x in range(len(f.vertices))]))
            bmface = bm.faces.new(face)
            bmface.material_index = textures.index(f.texture_name)
            vertex_offset += len(f.vertices)

        bm.to_mesh(mesh)

        collection = self.get_collection_for_solid(solid)
        collection.objects.link(mesh_object)

        default_texture_size = 256, 256
        if self.should_import_textures:
            '''
            Assign texture coordinates
            '''
            uv_layer = mesh.uv_layers.new()
            j = 0
            for face_index, face in enumerate(faces):
                try:
                    texture_size = self.get_texture_size(face.texture_name)
                except LookupError:
                    # If we don't have the texture, just assume a texture size of 256x256
                    texture_size = default_texture_size
                uvs = convert_rmf_face_texture_coordinates_to_uvs(face, texture_size)
                # NOTE: the UV order has to be reversed to match the reversed vertices due to winding order
                for uv in reversed(uvs):
                    uv[1] = -uv[1]
                    uv_layer.data[j].uv = uv.tolist()
                    j += 1

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


    def add_object(self, rmf_object: Rmf.Object):
        if type(rmf_object) == Rmf.Solid:
            solid = self.add_solid(rmf_object)
        elif type(rmf_object) == Rmf.Entity:
            # TODO: abstract this out somehow
            entity = rmf_object
            if entity.is_point_entity:
                if entity.classname == 'light_environment':
                    # TODO: create new light
                    light_data = bpy.data.lights.new(name='light_environment', type='SUN')
                    light_object = bpy.data.objects.new('light_environment', light_data)
                    light_object.location = tuple(entity.location)
                    # TODO: put the light somewhere
                    bpy.context.scene.collection.objects.link(light_object)
                    pitch, yaw, roll = map(lambda x: float(x), entity['angles'].split())
            else:
                # TODO: create a collection
                brush_entities_collection = bpy.data.collections['Brush Entities']
                entity_collection = bpy.data.collections.new(entity.classname)
                brush_entities_collection.children.link(entity_collection)
                # TODO: make a new EMPTY
                for solid in rmf_object.brushes:
                    solid_object = self.add_solid(solid)
                    if solid_object is not None:
                        entity_collection.objects.link(solid_object)
        elif type(rmf_object) == Rmf.Group:
            objects = [self.add_object(x) for x in rmf_object.objects]
            # bpy.ops.object.select_all(action='DESELECT')
            # for object in objects:
            #    object.select = True
            # bpy.oops.group.create()

    def create_collections(self):
        collections_names = 'Trigger', 'Sky', 'Clip', 'Brush Entities'
        for name in collections_names:
            if name not in bpy.data.collections:
                collection = bpy.data.collections.new(name)
                bpy.context.scene.collection.children.link(collection)

    def import_world(self, map: Rmf.World):
        self.create_collections()
        for _i, object in enumerate(map.objects):
            self.add_object(object)

    def execute(self, context: Context):
        self.load_wads(context)
        rmf = RmfReader().from_file(self.filepath)
        self.import_world(rmf)
        return {'FINISHED'}