from .rmf import Rmf
import numpy
import bmesh


def convert_rmf_face_texture_coordinates_to_uvs(face: Rmf.Face, texture_size: tuple):
    """
    if (width <= 0 || height <= 0 || Texture.XScale == 0 || Texture.YScale == 0)
    {
        return Vertices.Select(x => Tuple.Create(x, 0f, 0f));
    }

    var udiv = width * Texture.XScale;
    var uadd = Texture.XShift / width;
    var vdiv = height * Texture.YScale;
    var vadd = Texture.YShift / height;

    return Vertices.Select(x => Tuple.Create(x, x.Dot(Texture.UAxis) / udiv + uadd, x.Dot(Texture.VAxis) / vdiv + vadd));
    """
    if texture_size[0] <= 0 or texture_size[1] <= 0 or face.texture_scale[0] == 0 or face.texture_scale[1] == 0:
        return [numpy.array([0., 0., 0]) for _ in face.vertices]

    width, height = texture_size
    udiv = width * face.texture_scale[0]
    uadd = face.texture_u_shift / width
    vdiv = height * face.texture_scale[1]
    vadd = face.texture_v_shift / height

    uvs = []
    for vertex in face.vertices:
        u = numpy.dot(vertex, face.texture_u_axis) / udiv + uadd
        v = numpy.dot(vertex, face.texture_v_axis) / vdiv + vadd
        uvs.append(numpy.array([u, v]))
    return uvs


# TODO: INVERSE of the above! take UVs and convert them to RMF texcoords
# We may have to make some simplifying assumptions (affine transforms!) (just take one triangle from the polygon?)
# per face:
# set of UVs (a shape, in 2d space) [scale by size of texture]
# face shape ~> uv shape
def convert_uvs_to_rmf_face_coordinates(uvs, texture_size):
    pass
