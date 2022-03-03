bl_info = {
    'name': 'Rich Map Format',
    'description': 'Import Rich Map Format (rmf) files used in Valve Hammer Editor',
    'author': 'Colin Basnett',
    'version': (1, 0, 0),
    'blender': (2, 80, 0),
    'location': 'File > Import-Export',
    'warning': 'This add-on is under development.',
    'wiki_url': 'https://github.com/cmbasnett/io_scene_rmf/wiki',
    'tracker_url': 'https://github.com/cmbasnett/io_scene_rmf/issues',
    'support': 'COMMUNITY',
    'category': 'Import-Export'
}

if 'bpy' in locals():
    import importlib
    # TODO: does this also conflict with other shit?
    if 'config'     in locals(): importlib.reload(config)
    if 'utils'      in locals(): importlib.reload(utils)
    if 'wad'        in locals(): importlib.reload(wad)
    if 'rmf'        in locals(): importlib.reload(rmf)
    if 'reader'     in locals(): importlib.reload(reader)
    if 'writer'     in locals(): importlib.reload(writer)
    if 'importer'   in locals(): importlib.reload(importer)
    if 'exporter'   in locals(): importlib.reload(exporter)
    if 'builder'    in locals(): importlib.reload(builder)

import bpy
import bpy.utils.previews
from bpy.props import IntProperty, CollectionProperty, StringProperty
import os
from . import config
from . import utils
from . import wad
from . import rmf
from . import reader
from . import writer
from . import importer
from . import exporter
from . import builder

icons = [
    # 'lambda',
]

classes = (
    importer.RMF_OT_ImportOperator,
    exporter.RMF_OT_ExportOperator
)


def menu_func_import(self, context):
    self.layout.operator(importer.RMF_OT_ImportOperator.bl_idname, text='Rich Map Format (.rmf)')


def menu_func_export(self, context):
    self.layout.operator(exporter.RMF_OT_ExportOperator.bl_idname, text='Rich Map Format (.rmf)')


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
    config.rmf_icons = bpy.utils.previews.new()
    for icon in icons:
        config.rmf_icons.load(icon, os.path.join(icons_dir, icon + '.png'), 'IMAGE')

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    bpy.utils.previews.remove(config.rmf_icons)

    for cls in classes:
        bpy.utils.unregister_class(cls)
