from .rmf import Rmf
import numpy

'''
Converts a face's texture coordinates to a list of UVs corresponding to the vertices of the face.
In order to do this properly, the size of the texture used on the face is needed, so this must be passed in as well.
'''
def convert_rmf_face_texture_coordinates_to_uvs(face: Rmf.Face, texture_size: tuple):
    u = face.texture_u_axis
    v = face.texture_v_axis
    w = numpy.cross(u, v)
    rotation = numpy.array([
        [u[0], v[0], w[0], 0.0],
        [u[1], v[1], w[1], 0.0],
        [u[2], v[2], w[2], 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])
    scale = numpy.array([
        [1.0 / face.texture_scale[0], 0.0, 0.0, 0.0],
        [0.0, 1.0 / face.texture_scale[1], 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])
    translation = numpy.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [face.texture_u_shift,face.texture_v_shift, 0.0, 1.0]
    ])
    transform = rotation.dot(scale).dot(translation)
    uvs = []
    for v in face.vertices:
       uv = numpy.array([v[0], v[1], v[2], 1.0]).dot(transform)
       uv = numpy.resize(uv, 2)
       uvs.append(numpy.divide(uv, texture_size))
    return uvs
