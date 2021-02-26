import numpy
from collections import OrderedDict


class Color(object):
    def __init__(self):
        self.r = 0
        self.g = 0
        self.b = 0

    def __repr__(self):
        return ','.join(map(lambda x: str(x), [self.r, self.g, self.b]))


class Rmf:

    def __init__(self):
        self.visgroups = []
        self.root_object = None
        self.docinfo = Rmf.DocumentInfo()

    class VisGroup(object):
        def __init__(self):
            self.name = ''
            self.color = Color()
            self.index = 0
            self.visible = False
            self.unk1 = 0
            self.unk2 = 0

        def __repr__(self):
            return self.name

    class Face(object):
        def __init__(self):
            self.texture_name = ''
            self.texture_u_axis = numpy.array([1.0, 0.0, 0.0])
            self.texture_u_shift = 0.0
            self.texture_v_axis = numpy.array([0.0, 0.0, 1.0])
            self.texture_v_shift = 0.0
            self.texture_rotation = 0.0
            self.texture_scale = numpy.array([1.0, 1.0])
            self.vertices = []
            self.plane = [numpy.array([0.0, 0.0, 0.0])] * 3
            self.unk1 = 0.0
            self.unk2 = bytes(16)

        @property
        def is_clip(self):
            return self.texture_name == 'CLIP'

        @property
        def is_sky(self):
            return self.texture_name == 'SKY'

        @property
        def is_trigger(self):
            return self.texture_name == 'AAATRIGGER'

    class Solid(object):

        type_string = 'CMapSolid'

        def __init__(self):
            self.visgroup_index = 0
            self.color = Color()
            self.faces = []
            self.unk1 = bytes(4)

        @property
        def has_clip(self):
            return any(map(lambda x: x.is_clip, self.faces))

        @property
        def has_sky(self):
            return any(map(lambda x: x.is_sky, self.faces))

        @property
        def has_trigger(self):
            return any(map(lambda x: x.is_trigger, self.faces))

    class World(object):

        type_string = 'CMapWorld'

        def __init__(self):
            self.objects = []
            self.classname = 'worldspawn'
            self.paths = []
            self.properties = OrderedDict()
            self.properties['newunit'] = '0'
            self.properties['MaxRange'] = '4096'
            self.flags = 0
            self.unk1 = bytes(7)

    class Entity(object):  # TODO: one of these has to be the rotation

        type_string = 'CMapEntity'

        def __init__(self):
            self.visgroup_index = 0
            self.color = Color()
            self.brushes = []
            self.classname = ''
            self.flags = ''
            self.properties = OrderedDict()
            self.location = numpy.array([0.0, 0.0, 0.0])
            self.unk1 = bytes(4)
            self.unk2 = bytes(14)
            self.unk3 = bytes(4)

        def __getitem__(self, key):
            return self.properties[key]

        @property
        def is_point_entity(self):
            return len(self.brushes) == 0

    class Corner(object):
        def __init__(self):
            self.location = numpy.array([0.0, 0.0, 0.0])
            self.index = 0
            self.name = ''
            self.properties = OrderedDict()

    class Path(object):
        def __init__(self):
            self.name = ''
            self.path = ''
            self.type = 0
            self.corners = []

    class Group(object):

        type_string = 'CMapGroup'

        def __init__(self):
            self.visgroup_index = 0
            self.color = Color()
            self.objects = []

    class DocumentInfo(object):
        def __init__(self):
            self.version = 0.0
            self.camera_index = 0
            self.cameras = []

    class Camera(object):

        def __init__(self):
            self.eye = numpy.array([0.0, 0.0, 0.0])
            self.lookat = numpy.array([0.0, 0.0, 0.0])
