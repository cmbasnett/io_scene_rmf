from enum import Enum, IntEnum, IntEnum

import numpy
from numpy.typing import NDArray


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
            self.name: str = ''
            self.color: Color = Color()
            self.index: int = 0
            self.visible: bool = False

        def __repr__(self):
            return self.name

    class Face:
        def __init__(self):
            self.texture_name: str = ''
            self.texture_u_axis: NDArray[float] = numpy.array([0.0, 0.0, 0.0])
            self.texture_u_shift: float = 0.0
            self.texture_v_axis: NDArray[float] = numpy.array([0.0, 0.0, 0.0])
            self.texture_v_shift: float = 0.0
            self.texture_rotation: float = 0.0
            self.texture_scale: NDArray[float] = numpy.array([0.0, 0.0])
            self.vertices: list = []
            self.plane: list = []

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
            self.visgroup_index: int = 0
            self.color: Color = Color()
            self.faces: list[Rmf.Face] = []

        @property
        def has_clip(self):
            return any(map(lambda x: x.is_clip, self.faces))

        @property
        def has_sky(self):
            return any(map(lambda x: x.is_sky, self.faces))

        @property
        def has_trigger(self):
            return any(map(lambda x: x.is_trigger, self.faces))

    class Entity:  # TODO: one of these has to be the rotation
        def __init__(self):
            self.visgroup_index: int = 0
            self.color: Color = Color()
            self.brushes: list[Rmf.Solid] = []
            self.classname: str = ''
            self.flags: int = 0
            self.properties = {}
            self.location: NDArray[float] = numpy.array([0.0, 0.0, 0.0])

        def __getitem__(self, key):
            return self.properties[key]

        @property
        def is_point_entity(self):
            return len(self.brushes) == 0

    type Object = Solid | Entity | Group

    class Corner:
        def __init__(self):
            self.location: NDArray[float] = numpy.array([0.0, 0.0, 0.0])
            self.index: int = 0
            self.name: str = ''
            self.properties = dict()

    class Path:
        class Type(IntEnum):
            ONE_WAY = 0
            CIRCULAR = 1
            PING_PONG = 2

        def __init__(self):
            self.name: str = ''
            self.class_name: str = ''
            self.type: Rmf.Path.Type = Rmf.Path.Type.ONE_WAY
            self.corners: list[Rmf.Corner] = []

    class Group:
        def __init__(self):
            self.visgroup_index: int = 0
            self.color: Color = Color()
            self.objects: list[Rmf.Object] = []
    
    class Camera:
        def __init__(self):
            self.eye_position: NDArray[float] = numpy.array([0.0, 0.0, 0.0])
            self.look_position: NDArray[float] = numpy.array([0.0, 0.0, 0.0])

    class World:
        def __init__(self):
            self.objects: list[Rmf.Object] = []
            self.classname: str = ''
            self.flags: int = 0
            self.properties: dict[str, str] = {}
            self.paths: list[Rmf.Path] = []
            self.active_camera_index: int = 0
            self.cameras: list[Rmf.Camera] = []

