from ctypes import *
import struct
import numpy

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

    # http://hlbsp.sourceforge.net/index.php?content=waddef

    def get_texture_pixels(self, name):
        lump = self.lumps[name.upper()]
        self.fp.seek(lump.offset)
        self.fp.read(16)  # skip the name
        width, height = struct.unpack('II', self.fp.read(8))
        mip_offsets = struct.unpack('4I', self.fp.read(16))
        pixels_indices = []
        # TODO: precaculate the offset of the palette so we don't have to run through all the mipmaps
        for i, mip_offset in enumerate(mip_offsets):
            self.fp.seek(lump.offset + mip_offset)
            length = (width >> i) * (height >> i)
            if i == 0:
                pixels_indices = numpy.array(list(self.fp.read(length)), dtype=numpy.uint8)
            else:
                # dumb skip
                self.fp.read(length)
        self.fp.read(2)
        palette = numpy.array(list(self.fp.read(3 * 256)))
        palette.resize((256, 3))
        pixels = numpy.ones((width * height, 4))
        is_alpha_texture = name.startswith('{')
        for i, pixel_index in enumerate(pixels_indices):
            pixels[i][:3] = [x / 255.0 for x in palette[pixel_index]]
            if is_alpha_texture and pixel_index == 255:
                pixels[i][3] = 0.0
        pixels.resize((height, width, 4))
        pixels = numpy.flip(pixels, 0)
        return pixels.flatten()

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
