from .rmf import Rmf
import numpy

def convert_rmf_to_uv(face: Rmf.Face):
    u = face.texture_u_axis
    v = face.texture_v_axis
    w = numpy.cross(face.texture_u_axis, face.texture_v_axis)
    rotation_matrix = numpy.array([
        [u[0], v[0], w[0], 0.0],
        [u[1], v[1], w[1], 0.0],
        [u[2], v[2], w[2], 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])
    scale_matrix = numpy.array([
        [face.texture_scale[0], 0.0, 0.0, 0.0],
        [0.0, face.texture_scale[1], 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])
    scale_matrix = numpy.linalg.inv(scale_matrix)
    translation_matrix = numpy.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [face.texture_u_shift,face.texture_v_shift, 0.0, 1.0]
    ])
    b = numpy.dot(numpy.dot(rotation_matrix, scale_matrix), translation_matrix)
    uvs = []
    for vertex in face.vertices:
        uv = numpy.array([vertex[0], vertex[1], vertex[2], 1.0])
        uv = numpy.resize(numpy.dot(uv, b), 2)
        uv = numpy.divide(uv, (256, 128))
        uvs.append(uv)
    return uvs
