import numpy


class Color:
    def __init__(self):
        self.r: int = 0
        self.g: int = 0
        self.b: int = 0

    def __repr__(self):
        return ','.join(map(lambda x: str(x), [self.r, self.g, self.b]))


class Rmf:
    class VisGroup:
        def __init__(self):
            self.name = ''
            self.color = Color()
            self.index = 0
            self.visible = False

        def __repr__(self):
            return self.name

    class Face:
        def __init__(self):
            self.texture_name = ''
            self.texture_u_axis = numpy.array([0.0, 0.0, 0.0])
            self.texture_u_shift = 0.0
            self.texture_v_axis = numpy.array([0.0, 0.0, 0.0])
            self.texture_v_shift = 0.0
            self.texture_rotation = 0.0
            self.texture_scale = numpy.array([0.0, 0.0])
            self.vertices = []
            self.plane = []

        @property
        def is_clip(self):
            return self.texture_name == 'CLIP'

        @property
        def is_sky(self):
            return self.texture_name == 'SKY'

        @property
        def is_trigger(self):
            return self.texture_name == 'AAATRIGGER'

    class Solid:
        def __init__(self):
            self.visgroup_index = 0
            self.color = Color()
            self.faces = []

        @property
        def has_clip(self):
            return any(map(lambda x: x.is_clip, self.faces))

        @property
        def has_sky(self):
            return any(map(lambda x: x.is_sky, self.faces))

        @property
        def has_trigger(self):
            return any(map(lambda x: x.is_trigger, self.faces))


    class World:
        def __init__(self):
            self.objects = []
            self.classname = ''
            self.paths = []
            self.properties = []

    class Entity:  # TODO: one of these has to be the rotation
        def __init__(self):
            self.visgroup_index: int = 0
            self.color = Color()
            self.brushes: list[Rmf.Solid] = []
            self.classname: str = ''
            self.flags = ''
            self.properties = {}
            self.location = numpy.array([0.0, 0.0, 0.0])

        def __getitem__(self, key):
            return self.properties[key]

        @property
        def is_point_entity(self):
            return len(self.brushes) == 0

    class Corner:
        def __init__(self):
            self.location = numpy.array([0.0, 0.0, 0.0])
            self.index: int = 0
            self.name: str = ''
            self.properties = dict()

    class Path:
        def __init__(self):
            self.name: str = ''
            self.path: str = ''
            self.type: int = 0
            self.corners: list[Rmf.Corner] = []

    class Group:
        def __init__(self):
            self.visgroup_index: int = 0
            self.color = Color()
            self.objects = []
