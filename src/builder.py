import bpy
from .rmf import Rmf
import numpy
import bmesh


class RmfBuilder(object):
    def __init__(self):
        pass

    def create_solid_from_mesh(self, mesh_object) -> Rmf.Solid:
        solid = Rmf.Solid()
        bm = bmesh.new()
        bm.from_mesh(mesh_object.data)
        for face in bm.faces:
            rmf_face = Rmf.Face()
            for loop in reversed(face.loops):
                v = mesh_object.matrix_world @ loop.vert.co
                rmf_face.vertices.append(v)
            solid.faces.append(rmf_face)
        del bm
        return solid

    def from_context(self, context):
        rmf = Rmf()
        world = Rmf.World()
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                solid = self.create_solid_from_mesh(obj)
                world.objects.append(solid)
        rmf.root_object = world
        return rmf
