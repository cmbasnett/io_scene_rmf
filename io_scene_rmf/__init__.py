import bpy
from bpy.props import IntProperty, CollectionProperty
from . import utils
from . import wad
from . import rmf
from . import reader
from . import importer

_needs_reload = 'bpy' in locals()

if _needs_reload:
    import importlib
    importlib.reload(utils)
    importlib.reload(wad)
    importlib.reload(rmf)
    importlib.reload(reader)
    importlib.reload(importer)

icons = [
    # 'lambda',
]

classes = (
    importer.RMF_OT_AddWadOperator,
    importer.RMF_OT_import,
    importer.RMF_UL_WadList,
    importer.RMF_LI_WadListItem,
)


def menu_func_import(self, context):
    self.layout.operator(importer.RMF_OT_import.bl_idname, text='Rich Map Format (.rmf)')


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    setattr(bpy.types.Scene, 'rmf_wad_list', CollectionProperty(type=importer.RMF_LI_WadListItem))
    setattr(bpy.types.Scene, 'rmf_wad_list_index', IntProperty(default=0))

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    delattr(bpy.types.Scene, 'rmf_wad_list')
    delattr(bpy.types.Scene, 'rmf_wad_list_index')

    for cls in classes:
        bpy.utils.unregister_class(cls)
