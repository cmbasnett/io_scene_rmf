import os
import struct
from .rmf import *


def is_eof(f):
    s = f.read(1)
    if s != b'':
        f.seek(-1, os.SEEK_CUR)
    return s == b''


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

    @staticmethod
    def read_vector2(f, v):
        v[0], v[1] = unpack(f, '2f')

    @staticmethod
    def read_vector3(f, v):
        v[0], v[1], v[2] = map(lambda x: float(int(x)), unpack(f, '3f'))

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
        visgroup.unk1 = unpack(f, 'b')[0]
        visgroup.index = unpack(f, 'i')[0]
        visgroup.is_visible = unpack(f, 'b')[0]
        visgroup.unk2 = f.read(3)  # this is just padding
        return visgroup

    @staticmethod
    def read_face(f):
        face = Rmf.Face()
        face.texture_name = read_fixed_length_null_terminated_string(f, 256)
        face.unk1 = unpack(f, 'f')[0]
        RmfReader.read_vector3(f, face.texture_u_axis)
        face.texture_u_shift = unpack(f, 'f')[0]
        RmfReader.read_vector3(f, face.texture_v_axis)
        face.texture_v_shift = unpack(f, 'f')[0]
        face.texture_rotation = unpack(f, 'f')[0]
        RmfReader.read_vector2(f, face.texture_scale)
        face.unk2 = f.read(16)
        vertex_count = unpack(f, 'i')[0]
        for i in range(vertex_count):
            vertex = numpy.array([0.0, 0.0, 0.0])
            RmfReader.read_vector3(f, vertex)
            face.vertices.append(vertex)
        for i in range(3):
            plane_vertex = numpy.array([0.0, 0.0, 0.0])
            RmfReader.read_vector3(f, plane_vertex)
            face.plane[i] = plane_vertex
        return face

    @staticmethod
    def read_solid(f):
        solid = Rmf.Solid()
        solid.visgroup_index = unpack(f, 'i')[0]
        solid.color = RmfReader.read_color(f)
        solid.unk1 = f.read(4)
        face_count = unpack(f, 'i')[0]
        solid.faces = [RmfReader.read_face(f) for _ in range(face_count)]
        return solid

    @staticmethod
    def read_camera(f):
        camera = Rmf.Camera()
        RmfReader.read_vector3(f, camera.eye)
        RmfReader.read_vector3(f, camera.lookat)
        return camera

    @staticmethod
    def read_docinfo(f):
        r = unpack(f, '8s')
        docinfo = Rmf.DocumentInfo()
        docinfo.version = unpack(f, 'f')[0]
        docinfo.camera_index = unpack(f, 'i')[0]
        camera_count = unpack(f, 'i')[0]
        docinfo.cameras = [RmfReader.read_camera(f) for _ in range(camera_count)]
        return docinfo

    @staticmethod
    def read_world(f):
        world = Rmf.World()
        world.unk1 = f.read(7)  # (probably visgroup and Color fields but not used by VHE)
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
        entity.unk1 = f.read(4)
        entity.flags = unpack(f, 'i')[0]
        entity.properties = RmfReader.read_properties(f)
        entity.unk2 = f.read(14)
        RmfReader.read_vector3(f, entity.location)
        entity.unk3 = f.read(4)
        return entity

    @staticmethod
    def read_group(f):
        group = Rmf.Group()
        group.visgroup_index = unpack(f, 'i')[0]
        group.color = RmfReader.read_color(f)
        object_count = unpack(f, 'i')[0]
        group.objects = [RmfReader.read_object(f) for _ in range(object_count)]
        return group

    @staticmethod
    def read_corner(f):
        corner = Rmf.Corner()
        RmfReader.read_vector3(f, corner.location)
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
        properties = OrderedDict()
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
            rmf = Rmf()
            for i in range(visgroup_count):
                visgroup = RmfReader.read_visgroup(f)
                rmf.visgroups.append(visgroup)
            rmf.root_object = RmfReader.read_object(f)
            if not is_eof(f):
                rmf.docinfo = RmfReader.read_docinfo(f)
            return rmf
