import bpy
from bpy_extras.io_utils import ImportHelper
import bmesh
import os
from typing import cast as typing_cast
from bpy.types import Collection, Context, ShaderNodeTexImage, Operator, PropertyGroup, UIList, UI_UL_list, OperatorFileListElement
from bpy.props import StringProperty, BoolProperty, IntProperty, CollectionProperty
from .reader import RmfReader
from .rmf import *
from .wad import *
from .utils import convert_rmf_face_texture_coordinates_to_uvs
from mathutils import Matrix, Vector
from math import radians


class RMF_LI_wad_list_item(PropertyGroup):
    path: StringProperty()
    texture_count: IntProperty()

    @property
    def name(self):
        return self.path


class RMF_UL_wad_list(UIList):
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


class RMF_OT_wad_add(Operator):
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

    wads = []
    texture_size_cache = dict()  # str: tuple dict
    vis_group_names: list[str] = []

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
            layout.operator(RMF_OT_wad_add.bl_idname, icon='ADD')

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

    def add_camera(self, camera: Rmf.Camera) -> bpy.types.Object:
        print('Adding camera')
        camera_data = bpy.data.cameras.new(name='Camera')
        camera_object = bpy.data.objects.new('Camera', camera_data)
        camera_object.location = tuple(camera.eye_position)
        camera_direction = Vector(camera.look_position) - Vector(camera.eye_position)
        camera_direction.normalize()

        # Calculate forward and left vectors
        forward = camera_direction
        up = Vector((0, 0, 1))  # Assuming Z is up
        left = up.cross(forward)
        assert isinstance(left, Vector)

        # Calculate the rotation matrix
        rotation_matrix = Matrix((forward, left, up)).transposed()
        camera_object.rotation_euler = rotation_matrix.to_euler()
        # Swap X and Z in euler angles.
        camera_object.rotation_euler.x, camera_object.rotation_euler.z = camera_object.rotation_euler.z, camera_object.rotation_euler.x
        # Then swap Y and Z in euler angles.
        camera_object.rotation_euler.y, camera_object.rotation_euler.z = camera_object.rotation_euler.z, camera_object.rotation_euler.y

        # Set this to the same FOV that J.A.C.K. uses by default.
        camera_data.lens_unit = 'FOV'
        camera_data.angle = radians(90.0)

        # Add the camera to the scene
        bpy.context.scene.collection.objects.link(camera_object)

        return camera_object

    def add_solid(self, solid: Rmf.Solid) -> bpy.types.Object:
        '''
        Prune faces based on material names.
        '''
        mesh_name = 'Solid.000'
        mesh = bpy.data.meshes.new(mesh_name)

        mesh_object = bpy.data.objects.new(mesh_name, mesh)
        mesh_object.color = solid.color.rgba_float

        '''
        Create or reuse materials 
        '''
        textures = []
        for f in solid.faces:
            material = self.load_material(f.texture_name)
            if f.texture_name not in textures:
                textures.append(f.texture_name)
                mesh.materials.append(material)


        # For all the faces, add their unique vertices.
        face_vertex_index_count = sum(map(lambda face: len(face.vertices), solid.faces))
        face_vertex_indices = numpy.zeros(face_vertex_index_count, dtype=int)
        vertices: list[NDArray[float]] = []
        j = 0
        for face in solid.faces:
            for vertex in face.vertices:
                index: int | None = None
                for i, v in enumerate(vertices):
                    if (vertex == v).all():
                        index = i
                        break
                if index is None:
                    index = len(vertices)
                    vertices.append(vertex)
                face_vertex_indices[j] = index
                j += 1
        
        bm = bmesh.new()

        # Add the vertices.
        for vertex in vertices:
            bm.verts.new(tuple(vertex))
        bm.verts.ensure_lookup_table()

        # Now add the faces.
        j = 0
        for f in solid.faces:
            # The face order is reversed because of differences in winding order
            face = list(reversed([bm.verts[x] for x in face_vertex_indices[j:j+len(f.vertices)]]))
            bmface = bm.faces.new(face)
            bmface.material_index = textures.index(f.texture_name)
            j += len(f.vertices)

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
            for face_index, face in enumerate(solid.faces):
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

    def get_collection_for_solid(self, solid: Rmf.Solid) -> bpy.types.Collection:
        if solid.has_clip:
            return bpy.data.collections['Clip']
        elif solid.has_sky:
            return bpy.data.collections['Sky']
        elif solid.has_trigger:
            return bpy.data.collections['Trigger']
        else:
            return bpy.context.scene.collection


    def add_object(self, rmf_object: Rmf.Object):
        vis_group_collection: Collection | None = bpy.data.collections[self.vis_group_names[rmf_object.visgroup_index - 1]] if rmf_object.visgroup_index > 0 else None
        if type(rmf_object) == Rmf.Solid:
            solid_object = self.add_solid(rmf_object)
            if vis_group_collection is not None:
                vis_group_collection.objects.link(solid_object)
            yield solid_object
        elif type(rmf_object) == Rmf.Entity:
            # TODO: abstract this out somehow
            entity = rmf_object

            entity_object = bpy.data.objects.new(entity.classname, None)
            entity_object['classname'] = entity.classname
            for key, value in entity.properties.items():
                entity_object[key] = value
            entity_object.location = Vector(tuple(entity.location))

            if vis_group_collection is not None:
                vis_group_collection.objects.link(entity_object)

            yield entity_object
                
            if entity.is_point_entity:
                # Point Entity
                point_entities_collection = bpy.data.collections['Point Entities']
                point_entities_collection.objects.link(entity_object)
            else:
                # Brush Entity
                group_collection = bpy.data.collections['Brush Entities']
                group_collection.objects.link(entity_object)

                # Add the solids and parent them to the root entity.
                for solid_object in rmf_object.brushes:
                    solid_object = self.add_solid(solid_object)
                    if solid_object is not None:
                        group_collection.objects.link(solid_object)
                    solid_object.parent = entity_object
                    solid_object.location = -Vector(tuple(entity.location))

                    yield solid_object
        elif type(rmf_object) == Rmf.Group:
            objects: list[bpy.types.Object] = []
            for x in rmf_object.objects:
                objects.extend(self.add_object(x))
            for obj in objects:
                if vis_group_collection is not None:
                    if obj.name not in vis_group_collection.objects:
                        vis_group_collection.objects.link(obj)
            yield from objects

    def create_collections(self):
        collections_names = 'Trigger', 'Sky', 'Clip', 'Brush Entities', 'Point Entities'
        for name in collections_names:
            if name not in bpy.data.collections:
                collection = bpy.data.collections.new(name)
                bpy.context.scene.collection.children.link(collection)
                
    
    # TODO: not verified to be working. need some test data.
    def add_path(self, path: Rmf.Path) -> bpy.types.Object:
        path_curve_data = bpy.data.curves.new(name=path.name, type='CURVE')
        path_curve_data.dimensions = '3D'
        path_curve_data.resolution_u = 2

        path_curve_object = bpy.data.objects.new(path.name, path_curve_data)

        polyline = path_curve_data.splines.new('POLY')
        polyline.points.add(len(path.corners) - 1)
        for i, corner in enumerate(path.corners):
            x, y, z = corner.location
            polyline.points[i].co = (x, y, z, 1)

        # Add the curve object to the scene
        bpy.context.scene.collection.objects.link(path_curve_object)

        return path_curve_object

    def import_rmf(self, rmf: Rmf):
        print('import rmf')
        for vis_group in rmf.vis_groups:
            print(vis_group.name)
            if vis_group.name not in bpy.data.collections:
                bpy.data.collections.new(vis_group.name)
            vis_group_collection = bpy.data.collections[vis_group.name]
            vis_group_collection.hide_viewport = not vis_group.visible
            self.vis_group_names.append(vis_group.name)
            bpy.context.scene.collection.children.link(vis_group_collection)
        print(rmf.world)
        self.import_world(rmf.world)

    def import_world(self, world: Rmf.World):
        # Collections
        self.create_collections()
        for obj in world.objects:
            # NOTE: This needs to be forcibly evaluated otherwise it never runs the generator.
            list(self.add_object(obj))
        # Paths
        for path in world.paths:
            self.add_path(path)
        # Cameras
        for camera in world.cameras:
            self.add_camera(camera)

    def execute(self, context: Context):
        #self.load_wads(context)
        rmf = RmfReader().from_file(self.filepath)
        self.import_rmf(rmf)
        return {'FINISHED'}


__classes__ = [
    RMF_OT_wad_add,
    RMF_OT_import,
    RMF_UL_wad_list,
    RMF_LI_wad_list_item,
]