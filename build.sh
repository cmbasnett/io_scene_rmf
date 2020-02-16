GIT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
GIT_TAG="$(git tag | sort -V | tail -l)"
mkdir -p build
ZIP_PATH="io_scene_rmf-"$GIT_BRANCH"-"$GIT_TAG".zip"
zip -rvq build/"$ZIP_PATH" src/*.py
echo $ZIP_PATH "created"