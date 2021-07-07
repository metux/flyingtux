from os.path import normpath
from image import ImageSpec
from osbase import OSBaseSpec
from platform import PlatformSpec
from ..util import clean_path

obj_types = {
    'image': ImageSpec,
    'osbase': OSBaseSpec,
    'platform': PlatformSpec
}
