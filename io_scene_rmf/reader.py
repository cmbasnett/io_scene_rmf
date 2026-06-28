import io
import struct
from typing import BinaryIO
import numpy
from .rmf import *   # TODO: remove wildcard import


def _unpack(f, fmt):
    return struct.unpack(fmt, f.read(struct.calcsize(fmt)))


def _read_fixed_length_null_terminated_string(fp: BinaryIO, length: int) -> str:
    s = _unpack(fp, '{}s'.format(length))[0]
    length = next(i for i, v in enumerate(s) if v == 0)
    s = s[:length]
    return s.decode('utf-8')


def _read_length_prefixed_null_terminated_string(fp: BinaryIO) -> str:
    length = fp.read(1)[0]
    s = fp.read(length)[:-1]
    return s.decode('utf-8')


# https://developer.valvesoftware.com/wiki/Rich_Map_Format
class RmfReader:
    def __init__(self):
        pass

    @staticmethod
    def _read_vector2(f: BinaryIO, v: NDArray[float]):
        v[0], v[1] = _unpack(f, '2f')

    @staticmethod
    def _read_vector3(f: BinaryIO, v: NDArray[float]):
        v[0], v[1], v[2] = _unpack(f, '3f')

    @staticmethod
    def _read_color(f: BinaryIO):
        color = Color()
        color.r, color.g, color.b = _unpack(f, '3B')
        return color

    @staticmethod
    def _read_visgroup(fp: BinaryIO):
        visgroup = Rmf.VisGroup()
        visgroup.name = _read_fixed_length_null_terminated_string(fp, 128)
        visgroup.color = RmfReader._read_color(fp)
        fp.seek(1, io.SEEK_CUR) # Skip unknown byte
        visgroup.index = _unpack(fp, 'i')[0]
        visgroup.visible = _unpack(fp, 'b')[0] != 0
        fp.seek(3, io.SEEK_CUR) # Skip unknown bytes
        return visgroup

    @staticmethod
    def _read_face(f: BinaryIO):
        face = Rmf.Face()
        face.texture_name = _read_fixed_length_null_terminated_string(f, 256)
        f.seek(4, io.SEEK_CUR)  # Skip unknown bytes
        RmfReader._read_vector3(f, face.texture_u_axis)
        face.texture_u_shift = _unpack(f, 'f')[0]
        RmfReader._read_vector3(f, face.texture_v_axis)
        face.texture_v_shift = _unpack(f, 'f')[0]
        face.texture_rotation = _unpack(f, 'f')[0]
        RmfReader._read_vector2(f, face.texture_scale)
        _unpack(f, '16b')
        vertex_count = _unpack(f, 'i')[0]
        for i in range(vertex_count):
            vertex = numpy.array([0.0, 0.0, 0.0])
            RmfReader._read_vector3(f, vertex)
            face.vertices.append(vertex)
        for i in range(3):
            face.plane.append(numpy.array([0.0, 0.0, 0.0]))
            RmfReader._read_vector3(f, face.plane[i])
        return face

    @staticmethod
    def _read_solid(f: BinaryIO):
        solid = Rmf.Solid()
        solid.visgroup_index = _unpack(f, 'i')[0]
        solid.color = RmfReader._read_color(f)
        _ = _unpack(f, '4b')
        face_count = _unpack(f, 'i')[0]
        solid.faces = [RmfReader._read_face(f) for _ in range(face_count)]
        return solid

    @staticmethod
    def _read_world(f: BinaryIO):
        world = Rmf.World()
        f.read(7)  # ? (probably visgroup and Color fields but not used by VHE)
        object_count = _unpack(f, 'i')[0]
        world.objects = [RmfReader._read_object(f) for _ in range(object_count)]
        world.classname = _read_length_prefixed_null_terminated_string(f)
        _unpack(f, '4b')
        world.flags = _unpack(f, 'i')[0]
        world.properties = RmfReader._read_properties(f)
        _unpack(f, '12b')
        from pprint import pprint
        pprint(world.properties)
        path_count = _unpack(f, 'i')[0]
        world.paths = [RmfReader._read_path(f) for _ in range(path_count)]
        docinfo_header = f.read(8)
        if docinfo_header != b'DOCINFO\x00':
            raise RuntimeError(f'Expected DOCINFO string, got: {docinfo_header}')
        camera_version = _unpack(f, 'f')[0]
        print(f'Camera version: {camera_version}')
        world.active_camera_index = _unpack(f, 'i')[0]
        camera_count = _unpack(f, 'i')[0]
        print(f'Camera count: {camera_count}')
        world.cameras = [RmfReader._read_camera(f) for _ in range(camera_count)]
        return world

    @staticmethod
    def _read_camera(f):
        camera = Rmf.Camera()
        RmfReader._read_vector3(f, camera.eye_position)
        RmfReader._read_vector3(f, camera.look_position)
        return camera   

    @staticmethod
    def _read_entity(f):
        entity = Rmf.Entity()
        entity.visgroup_index = _unpack(f, 'i')[0]
        entity.color = RmfReader._read_color(f)
        brush_count = _unpack(f, 'i')[0]
        entity.brushes = [RmfReader._read_object(f) for _ in range(brush_count)]
        entity.classname = _read_length_prefixed_null_terminated_string(f)
        _unpack(f, '4b')
        entity.flags = _unpack(f, 'i')[0]
        entity.properties = RmfReader._read_properties(f)
        _unpack(f, '14b')
        RmfReader._read_vector3(f, entity.location)
        _unpack(f, '4b')
        return entity

    @staticmethod
    def _read_group(f):
        group = Rmf.Group()
        group.visgroup_index = _unpack(f, 'i')[0]
        group.color = RmfReader._read_color(f)
        object_count = _unpack(f, 'i')[0]
        group.objects = [RmfReader._read_object(f) for _ in range(object_count)]
        return group

    @staticmethod
    def _read_corner(f):
        corner = Rmf.Corner()
        RmfReader._read_vector3(f, corner.location)
        corner.index = _unpack(f, 'i')[0]
        corner.name = _read_fixed_length_null_terminated_string(f, 128)
        corner.properties = RmfReader._read_properties(f)
        return corner

    @staticmethod
    def _read_path(f):
        path = Rmf.Path()
        path.name = _read_fixed_length_null_terminated_string(f, 128)
        path.class_name = _read_fixed_length_null_terminated_string(f, 128)
        path.type = _unpack(f, 'i')[0]
        corner_count = _unpack(f, 'i')[0]
        path.corners = [RmfReader._read_corner(f) for _ in range(corner_count)]
        return path

    @staticmethod
    def _read_object(f):
        object_read_function_map = {
            'CMapWorld': RmfReader._read_world,
            'CMapEntity': RmfReader._read_entity,
            'CMapGroup': RmfReader._read_group,
            'CMapSolid': RmfReader._read_solid,
        }
        object_type_string = _read_length_prefixed_null_terminated_string(f)
        object_read_function = object_read_function_map[object_type_string]
        return object_read_function(f)

    @staticmethod
    def _read_properties(f: BinaryIO) -> dict[str, str]:
        properties: dict[str, str] = dict()
        property_count = _unpack(f, 'i')[0]
        for _ in range(property_count):
            key = _read_length_prefixed_null_terminated_string(f)
            value = _read_length_prefixed_null_terminated_string(f)
            properties[key] = value
        return properties

    @staticmethod
    def from_file(path):
        with open(path, 'rb') as f:
            _version, _magic = _unpack(f, 'i3s')
            print(f'RMF version: {_version}, magic: {_magic}')
            if _version != 1074580685:
                raise RuntimeError(f'Unsupported RMF version: {_version}')
            if _magic != b'RMF':
                raise RuntimeError(f'Invalid RMF file: {_magic}')
            visgroup_count = _unpack(f, 'i')[0]
            for i in range(visgroup_count):
                visgroup = RmfReader._read_visgroup(f)
            rmf = RmfReader._read_object(f)
            return rmf
