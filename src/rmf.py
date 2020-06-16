import numpy


class Color(object):
    def __init__(self):
        self.r = 0
        self.g = 0
        self.b = 0

    def __repr__(self):
        return ','.join(map(lambda x: str(x), [self.r, self.g, self.b]))


class Rmf:
    class VisGroup(object):
        def __init__(self):
            self.name = ''
            self.color = Color()
            self.index = 0
            self.visible = False

        def __repr__(self):
            return self.name

    class Face(object):
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

    class Solid(object):
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


    class World(object):
        def __init__(self):
            self.objects = []
            self.classname = ''
            self.paths = []
            self.properties = []

    class Entity(object):  # TODO: one of these has to be the rotation
        def __init__(self):
            self.visgroup_index = 0
            self.color = Color()
            self.brushes = []
            self.classname = ''
            self.flags = ''
            self.properties = {}
            self.location = numpy.array([0.0, 0.0, 0.0])

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
            self.properties = dict()

    class Path(object):
        def __init__(self):
            self.name = ''
            self.path = ''
            self.type = 0
            self.corners = []

    class Group(object):
        def __init__(self):
            self.visgroup_index = 0
            self.color = Color()
            self.objects = []
