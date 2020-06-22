# io_scene_rmf
Blender 2.8x addon for importing Rich Map Format (RMF) map files used in the GoldSrc engine.

This addon was created to aid artists in modeling assets around a level's geometry.

## Features
* Imports all brushes from RMF file.
* Imports all texturing information and loads textures from provided WADs.
* Organizes brushes into collections (eg. sky, clip, trigger, brush entities).

## Future Plans
* Importing model geometry from `.mdl` files referenced in `env_model` entities.
* Automatically weld brush vertices to avoid duplication and improve performance.
* The ability to export meshes to an RMF file, allowing for more complex brush geometry and texturing precision than would be feasible to do in a map editor alone.

## Note
The steps for importing textures are still a work in progress. Once the feature set is complete I will create a guide for how to use the plugin from start to finish.
