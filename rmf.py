import struct
import bpy
import bmesh


# https://developer.valvesoftware.com/wiki/Rich_Map_Format


def unpack(f, fmt):
    return struct.unpack(fmt, f.read(struct.calcsize(fmt)))


def read_fixed_length_null_terminated_string(f, len):
    s = unpack(f, '{}s'.format(len))[0]
    len = next(i for i, v in enumerate(s) if v == 0)
    s = s[:len]
    return s.decode()


def read_length_prefixed_null_terminated_string(f):
    len = f.read(1)[0]
    s = f.read(len)[:-1]
    return s.decode()


class Vector2(object):
    def __init__(self):
        self.x = 0
        self.y = 0

    @staticmethod
    def from_buffer(f):
        vector = Vector2()
        vector.x, vector.y = unpack(f, '2f')
        return vector


class Vector3(object):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    @staticmethod
    def from_buffer(f):
        vector = Vector3()
        vector.x, vector.y, vector.z = unpack(f, '3f')
        return vector

    def __repr__(self):
        return '(' + ','.join([str(x) for x in [self.x, self.y, self.z]]) + ')'


class Color(object):
    def __init__(self):
        self.r = 0
        self.g = 0
        self.b = 0

    @staticmethod
    def from_buffer(f):
        color = Color()
        color.r, color.g, color.b = unpack(f, '3B')
        return color

    def __repr__(self):
        return ','.join(map(lambda x: str(x), [self.r, self.g, self.b]))


class VisGroup(object):
    def __init__(self):
        self.name = ''
        self.color = Color()
        self.index = 0
        self.visible = False

    def __repr__(self):
        return self.name

    @staticmethod
    def from_buffer(f):
        visgroup = VisGroup()
        visgroup.name = read_fixed_length_null_terminated_string(f, 128)
        visgroup.color = Color.from_buffer(f)
        visgroup.unk1, \
        visgroup.index, \
        visgroup.is_visible = unpack(f, 'bib')
        return visgroup


class Face(object):
    def __init__(self):
        self.texture_name = ''
        self.texture_u_axis = Vector3()
        self.texture_u_shift = 0.0
        self.texture_v_axis = Vector3()
        self.texture_v_shift = 0.0
        self.texture_rotation = 0.0
        self.texture_scale = Vector2()
        self.vertices = []
        self.plane = []

    @staticmethod
    def from_buffer(f):
        face = Face()
        face.texture_name = read_fixed_length_null_terminated_string(f, 256)
        unpack(f, 'f')
        face.texture_u_axis = Vector3.from_buffer(f)
        face.texture_u_shift = unpack(f, 'f')
        face.texture_v_axis = Vector3.from_buffer(f)
        face.texture_u_shift = unpack(f, 'f')
        face.texture_rotation = unpack(f, 'f')
        face.texture_scale = Vector2.from_buffer(f)
        unpack(f, '16b')
        vertex_count = unpack(f, 'i')[0]
        face.vertices = [Vector3.from_buffer(f) for i in range(vertex_count)]
        face.plane = [Vector3.from_buffer(f) for i in range(3)]
        return face


class Solid(object):
    def __init__(self):
        self.visgroup_index = 0
        self.color = Color()
        self.faces = []

    @staticmethod
    def from_buffer(f):
        solid = Solid()
        solid.visgroup_index = unpack(f, 'i')
        solid.color = Color.from_buffer(f)
        unk1 = unpack(f, '4b')
        face_count = unpack(f, 'i')[0]
        solid.faces = [Face.from_buffer(f) for i in range(face_count)]
        return solid


class World(object):
    def __init__(self):
        self.objects = []
        self.classname = ''
        self.paths = []
        self.properties = []
        pass

    @staticmethod
    def from_buffer(f):
        world = World()
        f.read(7)  # ? (probably visgroup and Color fields but not used by VHE)
        object_count = unpack(f, 'i')[0]
        world.objects = [read_object(f) for _ in range(object_count)]
        world.classname = read_length_prefixed_null_terminated_string(f)
        unpack(f, '4b')
        world.flags = unpack(f, 'i')[0]
        world.properties = read_properties(f)
        unpack(f, '12b')
        path_count = unpack(f, 'i')[0]
        world.paths = [Path.from_buffer(f) for _ in range(path_count)]
        return world


class Entity(object):  # TODO: one of these has to be the rotation
    def __init__(self):
        self.visgroup_index = 0
        self.color = Color()
        self.brushes = []
        self.classname = ''
        self.flags = ''
        self.properties = {}
        self.location = Vector3()
        pass

    @staticmethod
    def from_buffer(f):
        entity = Entity()
        entity.visgroup_index = unpack(f, 'i')[0]
        entity.color = Color.from_buffer(f)
        brush_count = unpack(f, 'i')[0]
        entity.brushes = [read_object(f) for i in range(brush_count)]
        entity.classname = read_length_prefixed_null_terminated_string(f)
        unpack(f, '4b')
        entity.flags = unpack(f, 'i')
        entity.properties = read_properties(f)
        unpack(f, '14b')
        entity.location = Vector3.from_buffer(f)
        unpack(f, '4b')
        return entity

    def __getitem__(self, key):
        return self.properties[key]

    @property
    def is_point_entity(self):
        return len(self.brushes) == 0


class Group(object):
    def __init__(self):
        self.visgroup_index = 0
        self.color = Color()
        self.objects = []

    @staticmethod
    def from_buffer(f):
        group = Group()
        group.visgroup_index = unpack(f, 'i')
        group.color = Color.from_buffer(f)
        object_count = unpack(f, 'i')[0]
        group.objects = [read_object(f) for i in range(object_count)]
        return group


class Corner(object):
    def __init__(self):
        self.location = Vector3()
        self.index = 0
        self.name = ''
        self.properties = dict()

    @staticmethod
    def from_buffer(f):
        corner = Corner()
        corner.location = Vector3.from_buffer(f)
        corner.index = unpack(f, 'i')
        corner.name = read_fixed_length_null_terminated_string(128)
        corner.properties = read_properties(f)
        return corner


class Path(object):
    def __init__(self):
        self.name = ''
        self.path = ''
        self.type = 0
        self.corners = []

    @staticmethod
    def from_buffer(f):
        path = Path()
        path.name = read_fixed_length_null_terminated_string(f, 128)
        path.classname = read_fixed_length_null_terminated_string(f, 128)
        path.type = unpack(f, 'i')
        corner_count = unpack(f, 'i')
        path.corners = [Corner.from_buffer(x) for x in range(corner_count)]
        return path


_object_type_map_ = {
    'CMapWorld': World,
    'CMapEntity': Entity,
    'CMapGroup': Group,
    'CMapSolid': Solid,
}


def read_object(f):
    object_type_string = read_length_prefixed_null_terminated_string(f)
    object_type = _object_type_map_[object_type_string]
    return object_type.from_buffer(f)


def read_properties(f):
    properties = dict()
    property_count = unpack(f, 'i')[0]
    for _ in range(property_count):
        key = read_length_prefixed_null_terminated_string(f)
        value = read_length_prefixed_null_terminated_string(f)
        properties[key] = value
    return properties


def add_solid(solid):
    mesh_name = 'Solid.000'
    mesh = bpy.data.meshes.new(mesh_name)
    mesh_object = bpy.data.objects.new(mesh_name, mesh)
    bpy.context.scene.objects.link(mesh_object)
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


def add_object(object):
    if type(object) == Solid:
        add_solid(object)
    elif type(object) == Entity:
        # TODO: abstract this out somehow
        entity = object
        if entity.is_point_entity:
            if entity.classname == 'light_environment':
                # TODO: create new lamp
                lamp_data = bpy.data.lamps.new(name='light_environment', type='SUN')
                lamp_object = bpy.data.objects.new('light_environment', lamp_data)
                lamp_object.location = tuple(entity.location)
                # TODO: put the lamp somewhere
                bpy.context.scene.objects.link(lamp_object)
                pitch, yaw, roll = map(lambda x: float(x), entity['angles'].split())
                print(pitch, yaw, roll)
        else:
            for solid in object.brushes:
                add_solid(solid)
    elif type(object) == Group:
        objects = [add_object(x) for x in object.objects]
        # bpy.ops.object.select_all(action='DESELECT')
        # for object in objects:
        #    object.select = True
        # bpy.oops.group.create()


# TODO: find the sky and make an equivalent lamp somewhere?

fp = r'C:/Users/Colin/Desktop/Leveling/Day of Defeat/dod_kaust/dod_kaust.rmf'
with open(fp, 'rb') as f:
    version, magic = unpack(f, 'i3s')
    visgroup_count = unpack(f, 'i')[0]
    for i in range(visgroup_count):
        visgroup = VisGroup.from_buffer(f)
    world = read_object(f)
    # Now add it all in baybee
    for i, object in enumerate(world.objects):
        add_object(object)
