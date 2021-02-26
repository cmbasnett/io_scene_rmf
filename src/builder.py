import bpy
from .rmf import Rmf
import numpy


class RmfBuilder(object):
    def __init__(self):
        pass

    def mesh_to_solid(self, mesh_object) -> Rmf.Solid:
        mesh_data = mesh_object.data
        solid = Rmf.Solid()
        for polygon in mesh_data.polygons:
            rmf_face = Rmf.Face()
            for loop_index in reversed(polygon.loop_indices):
                v = numpy.array(mesh_data.vertices[mesh_data.loops[loop_index].vertex_index].co)
                rmf_face.vertices.append(v)
            solid.faces.append(rmf_face)
        return solid

    def from_context(self, context):
        rmf = Rmf()
        world = Rmf.World()
        for object in context.selected_objects:
            if object.type == 'MESH':
                solid = self.mesh_to_solid(object)
                world.objects.append(solid)
        rmf.root_object = world
        return rmf
        # TODO: loop through cameras and set up docinfo
