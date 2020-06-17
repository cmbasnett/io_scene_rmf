from ctypes import *

# https://yuraj.ucoz.com/half-life-formats.pdf

class Wad(object):
    def __init__(self, path: str):
        self.fp = None
        self.lumps = dict()
        self._read_(path)

    def _read_(self, path: str):
        self.fp = open(path, 'rb')
        header = Header.from_buffer_copy(self.fp.read(sizeof(Header)))
        if header.magic != b'WAD3':
            raise RuntimeError('invalid file format')
        self.fp.seek(header.lumps_offset)
        for i in range(header.texture_count):
            lump = Lump.from_buffer_copy(self.fp.read((sizeof(Lump))))
            self.lumps[lump.name.decode().upper()] = lump

    def release(self):
        self.fp.close()

    def has_texture(self, name: str):
        return name.upper() in self.lumps

    def get_texture_size(self, name: str):
        lump = self.lumps[name.upper()]
        self.fp.seek(lump.offset)
        data_class = get_data_class_for_lump_type(lump.type)
        data = data_class.from_buffer_copy(self.fp.read(sizeof(data_class)))
        return data.width, data.height

    def get_texture_pixels(self, name):
        raise NotImplementedError()

class Header(Structure):
    _fields_ = [
        ('magic', c_char * 4),
        ('texture_count', c_uint32),
        ('lumps_offset', c_uint32)
    ]

WAD_LUMP_TYPE_QPIC = 0x42
WAD_LUMP_TYPE_MIPTEX = 0x43
WAD_LUMP_TYPE_FONT = 0x46

class Lump(Structure):
    _fields_ = [
        ('offset', c_uint32),
        ('compressed_length', c_uint32),
        ('length', c_uint32),
        ('type', c_uint8),
        ('compression', c_uint8),
        ('padding', c_char * 2),
        ('name', c_char * 16)
    ]

class Qpic(Structure):
    _fields_ = [
        ('width', c_int32),
        ('height', c_int32),
    ]

class MipTex(Structure):
    _fields_ = [
        ('name', c_char * 16),
        ('width', c_int32),
        ('height', c_int32),
    ]

class FontCharacter(Structure):
    _fields_ = [
        ('start_offset', c_uint32),
        ('char_width', c_uint32)
    ]

class Font(Structure):
    _fields_ = [
        ('width', c_int32),
        ('height', c_int32),
        ('row_coount', c_uint32),
        ('row_height', c_uint),
        ('characters', FontCharacter * 256)
    ]

__wad_lump_type_map__ = {
    WAD_LUMP_TYPE_QPIC: Qpic,
    WAD_LUMP_TYPE_FONT: Font,
    WAD_LUMP_TYPE_MIPTEX: MipTex
}

def get_data_class_for_lump_type(type: int):
    return __wad_lump_type_map__[type]
