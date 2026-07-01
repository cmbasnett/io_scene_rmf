from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, StringProperty


class RMF_PG_fgd(PropertyGroup):
    path: StringProperty(name='Path', subtype='FILE_PATH')


class RMF_PG_wad(PropertyGroup):
    path: StringProperty(name='Path', subtype='FILE_PATH')


class RMF_PG_game_profile(PropertyGroup):
    id: StringProperty(name='ID')

    name: StringProperty(name='Name')
    fgds: CollectionProperty(type=RMF_PG_fgd)
    
    # Directories
    game_executable_path: StringProperty(name='Game Executable', subtype='FILE_PATH')
    base_game_directory: StringProperty(name='Base Game Directory', subtype='DIR_PATH')
    mod_directory: StringProperty(name='Mod Directory', subtype='DIR_PATH')

    # Build Programs
    csg_path: StringProperty(name='CSG Executable', subtype='FILE_PATH')
    bsp_path: StringProperty(name='BSP Executable', subtype='FILE_PATH')
    vis_path: StringProperty(name='VIS Executable', subtype='FILE_PATH')
    rad_path: StringProperty(name='RAD Executable', subtype='FILE_PATH')


__classes__ = [
    RMF_PG_fgd,
    RMF_PG_wad,
    RMF_PG_game_profile,
]
