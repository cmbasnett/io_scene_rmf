import struct
import io
from .rmf import Rmf, Color


def pack(fmt, *values):
    return struct.pack(fmt, *values)


def write_fixed_length_null_terminated_string(f: io.FileIO, length: int, string: str):
    buffer = bytearray(length)
    string_bytes = string.encode()
    buffer[:len(string_bytes)] = string_bytes
    f.write(buffer)


def write_length_prefixed_null_terminated_string(f, string: str):
    string_bytes = bytearray(string.encode())
    string_bytes.append(0)
    f.write(pack('B', len(string_bytes)))
    f.write(string_bytes)


class RmfWriter(object):

    def __init__(self):
        pass

    @staticmethod
    def write_color(f, color: Color):
        f.write(pack('3B', color.r, color.g, color.b))

    @staticmethod
    def write_visgroup(f, visgroup):
        write_fixed_length_null_terminated_string(f, 128, visgroup.name)
        RmfWriter.write_color(f, visgroup.color)
        f.write(pack('b', visgroup.unk1))
        f.write(pack('i', visgroup.index))
        f.write(pack('b', visgroup.is_visible))
        f.write(bytes(3))

    @staticmethod
    def write_docinfo(f, docinfo):
        f.write('DOCINFO\0'.encode())
        f.write(pack('f', 0.2))
        f.write(pack('i', docinfo.camera_index))
        f.write(pack('i', len(docinfo.cameras)))
        for camera in docinfo.cameras:
            RmfWriter.write_vector3(f, camera.eye)
            RmfWriter.write_vector3(f, camera.lookat)

    @staticmethod
    def get_object_type_string(obj):
        object_type_string_map = {
            Rmf.World: 'CMapWorld',
            Rmf.Entity: 'CMapEntity',
            Rmf.Group: 'CMapGroup',
            Rmf.Solid: 'CMapSolid',
        }
        return object_type_string_map[type(obj)]

    @staticmethod
    def write_corner(f, corner: Rmf.Corner):
        RmfWriter.write_vector3(f, corner.location)
        f.write(pack('i', corner.index))
        write_fixed_length_null_terminated_string(f, 128, corner.name)
        RmfWriter.write_properties(f, corner.properties)
        return corner

    @staticmethod
    def write_path(f, path: Rmf.Path):
        write_fixed_length_null_terminated_string(f, 128, path.name)
        write_fixed_length_null_terminated_string(f, 128, path.classname)
        f.write(pack('i', path.type))
        f.write(pack('i', len(path.corners)))
        for corner in path.corners:
            RmfWriter.write_corner(f, corner)

    @staticmethod
    def write_world(f, world: Rmf.World):
        f.write(world.unk1)  # ? (probably vis group and Color fields but not used by VHE)
        f.write(pack('i', len(world.objects)))
        for obj in world.objects:
            RmfWriter.write_object(f, obj)
        write_length_prefixed_null_terminated_string(f, world.classname)
        f.write(bytearray(4))  # unknown1
        f.write(pack('i', world.flags))
        RmfWriter.write_properties(f, world.properties)
        f.write(bytearray(12))  # unknown2
        f.write(pack('i', len(world.paths)))
        for path in world.paths:
            RmfWriter.write_path(f, path)

    @staticmethod
    def write_vector2(f, v: tuple):
        f.write(pack('2f', v[0], v[1]))

    @staticmethod
    def write_vector3(f, v: tuple):
        f.write(pack('3f', v[0], v[1], v[2]))

    @staticmethod
    def write_properties(f, properties: dict):
        f.write(pack('i', len(properties)))
        for key, value in properties.items():
            write_length_prefixed_null_terminated_string(f, key)
            write_length_prefixed_null_terminated_string(f, value)

    @staticmethod
    def write_entity(f, entity):
        f.write(pack('i', entity.visgroup_index))
        RmfWriter.write_color(f, entity.color)
        f.write(pack('i', len(entity.brushes)))
        for brush in entity.brushes:
            RmfWriter.write_object(f, brush)
        write_length_prefixed_null_terminated_string(f, entity.classname)
        f.write(entity.unk1)
        f.write(pack('i', entity.flags))
        RmfWriter.write_properties(f, entity.properties)
        f.write(entity.unk2)
        RmfWriter.write_vector3(f, entity.location)
        f.write(entity.unk3)

    @staticmethod
    def write_group(f, group: Rmf.Group):
        f.write(pack('i', group.visgroup_index))
        RmfWriter.write_color(f, group.color)
        f.write(pack('i', len(group.objects)))
        for obj in group.objects:
            RmfWriter.write_object(f, obj)

    @staticmethod
    def write_face(f, face: Rmf.Face):
        write_fixed_length_null_terminated_string(f, 256, face.texture_name)
        f.write(pack('f', face.unk1))
        RmfWriter.write_vector3(f, face.texture_u_axis)
        f.write(pack('f', face.texture_u_shift))
        RmfWriter.write_vector3(f, face.texture_v_axis)
        f.write(pack('f', face.texture_v_shift))
        f.write(pack('f', face.texture_rotation))
        RmfWriter.write_vector2(f, face.texture_scale)
        f.write(face.unk2)
        f.write(pack('i', len(face.vertices)))
        for vertex in face.vertices:
            RmfWriter.write_vector3(f, vertex)
        for i in range(3):
            RmfWriter.write_vector3(f, face.plane[i])

    @staticmethod
    def write_solid(f, solid: Rmf.Solid):
        f.write(pack('i', solid.visgroup_index))
        RmfWriter.write_color(f, solid.color)
        f.write(solid.unk1)
        f.write(pack('i', len(solid.faces)))
        for face in solid.faces:
            RmfWriter.write_face(f, face)

    @staticmethod
    def write_object(f, obj):
        object_read_function_map = {
            Rmf.World: RmfWriter.write_world,
            Rmf.Entity: RmfWriter.write_entity,
            Rmf.Group: RmfWriter.write_group,
            Rmf.Solid: RmfWriter.write_solid,
        }
        write_length_prefixed_null_terminated_string(f, type(obj).type_string)
        object_write_function = object_read_function_map[type(obj)]
        object_write_function(f, obj)

    def to_file(self, rmf: Rmf, path: str):
        with open(path, 'wb') as f:
            f.write(pack('i', 1074580685))   # version
            f.write(pack('3s', 'RMF'.encode()))       # magic
            f.write(pack('i', len(rmf.visgroups)))
            for visgroup in rmf.visgroups:
                RmfWriter.write_visgroup(f, visgroup)
            RmfWriter.write_object(f, rmf.root_object)
            RmfWriter.write_docinfo(f, rmf.docinfo)
