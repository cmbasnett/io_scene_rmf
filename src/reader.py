import struct
from .rmf import *


def unpack(f, fmt):
    return struct.unpack(fmt, f.read(struct.calcsize(fmt)))


def read_fixed_length_null_terminated_string(f, length):
    s = unpack(f, '{}s'.format(length))[0]
    length = next(i for i, v in enumerate(s) if v == 0)
    s = s[:length]
    return s.decode()


def read_length_prefixed_null_terminated_string(f):
    length = f.read(1)[0]
    s = f.read(length)[:-1]
    return s.decode()


# https://developer.valvesoftware.com/wiki/Rich_Map_Format
class RmfReader:
    def __init__(self):
        pass

    @staticmethod
    def read_vector2(f):
        vector = Vector2()
        vector.x, vector.y = unpack(f, '2f')
        return vector

    @staticmethod
    def read_vector3(f):
        vector = Vector3()
        vector.x, vector.y, vector.z = unpack(f, '3f')
        return vector

    @staticmethod
    def read_color(f):
        color = Color()
        color.r, color.g, color.b = unpack(f, '3B')
        return color

    @staticmethod
    def read_visgroup(f):
        visgroup = Rmf.VisGroup()
        visgroup.name = read_fixed_length_null_terminated_string(f, 128)
        visgroup.color = RmfReader.read_color(f)
        visgroup.unk1, \
        visgroup.index, \
        visgroup.is_visible = unpack(f, 'bib')
        return visgroup

    @staticmethod
    def read_face(f):
        face = Rmf.Face()
        face.texture_name = read_fixed_length_null_terminated_string(f, 256)
        unpack(f, 'f')
        face.texture_u_axis = RmfReader.read_vector3(f)
        face.texture_u_shift = unpack(f, 'f')
        face.texture_v_axis = RmfReader.read_vector3(f)
        face.texture_u_shift = unpack(f, 'f')
        face.texture_rotation = unpack(f, 'f')
        face.texture_scale = RmfReader.read_vector2(f)
        unpack(f, '16b')
        vertex_count = unpack(f, 'i')[0]
        face.vertices = [RmfReader.read_vector3(f) for _ in range(vertex_count)]
        face.plane = [RmfReader.read_vector3(f) for _ in range(3)]
        return face

    @staticmethod
    def read_solid(f):
        solid = Rmf.Solid()
        solid.visgroup_index = unpack(f, 'i')
        solid.color = RmfReader.read_color(f)
        _ = unpack(f, '4b')
        face_count = unpack(f, 'i')[0]
        solid.faces = [RmfReader.read_face(f) for _ in range(face_count)]
        return solid

    @staticmethod
    def read_world(f):
        world = Rmf.World()
        f.read(7)  # ? (probably visgroup and Color fields but not used by VHE)
        object_count = unpack(f, 'i')[0]
        world.objects = [RmfReader.read_object(f) for _ in range(object_count)]
        world.classname = read_length_prefixed_null_terminated_string(f)
        unpack(f, '4b')
        world.flags = unpack(f, 'i')[0]
        world.properties = RmfReader.read_properties(f)
        unpack(f, '12b')
        path_count = unpack(f, 'i')[0]
        world.paths = [RmfReader.read_path(f) for _ in range(path_count)]
        return world

    @staticmethod
    def read_entity(f):
        entity = Rmf.Entity()
        entity.visgroup_index = unpack(f, 'i')[0]
        entity.color = RmfReader.read_color(f)
        brush_count = unpack(f, 'i')[0]
        entity.brushes = [RmfReader.read_object(f) for _ in range(brush_count)]
        entity.classname = read_length_prefixed_null_terminated_string(f)
        unpack(f, '4b')
        entity.flags = unpack(f, 'i')
        entity.properties = RmfReader.read_properties(f)
        unpack(f, '14b')
        entity.location = RmfReader.read_vector3(f)
        unpack(f, '4b')
        return entity

    @staticmethod
    def read_group(f):
        group = Rmf.Group()
        group.visgroup_index = unpack(f, 'i')
        group.color = RmfReader.read_color(f)
        object_count = unpack(f, 'i')[0]
        group.objects = [RmfReader.read_object(f) for _ in range(object_count)]
        return group

    @staticmethod
    def read_corner(f):
        corner = Rmf.Corner()
        corner.location = RmfReader.read_vector3(f)
        corner.index = unpack(f, 'i')
        corner.name = read_fixed_length_null_terminated_string(f, 128)
        corner.properties = RmfReader.read_properties(f)
        return corner

    @staticmethod
    def read_path(f):
        path = Rmf.Path()
        path.name = read_fixed_length_null_terminated_string(f, 128)
        path.classname = read_fixed_length_null_terminated_string(f, 128)
        path.type = unpack(f, 'i')
        corner_count = unpack(f, 'i')[0]
        path.corners = [RmfReader.read_corner(f) for _ in range(corner_count)]
        return path

    @staticmethod
    def read_object(f):
        object_read_function_map = {
            'CMapWorld': RmfReader.read_world,
            'CMapEntity': RmfReader.read_entity,
            'CMapGroup': RmfReader.read_group,
            'CMapSolid': RmfReader.read_solid,
        }
        object_type_string = read_length_prefixed_null_terminated_string(f)
        object_read_function = object_read_function_map[object_type_string]
        return object_read_function(f)

    @staticmethod
    def read_properties(f):
        properties = dict()
        property_count = unpack(f, 'i')[0]
        for _ in range(property_count):
            key = read_length_prefixed_null_terminated_string(f)
            value = read_length_prefixed_null_terminated_string(f)
            properties[key] = value
        return properties

    @staticmethod
    def from_file(path):
        with open(path, 'rb') as f:
            version, magic = unpack(f, 'i3s')
            visgroup_count = unpack(f, 'i')[0]
            for i in range(visgroup_count):
                visgroup = RmfReader.read_visgroup(f)
            rmf = RmfReader.read_object(f)
            return rmf
