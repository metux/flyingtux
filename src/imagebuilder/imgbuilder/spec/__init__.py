
from image import ImageSpec
from osbase import OSBaseSpec
from platform import PlatformSpec

obj_types = {
    'image': ImageSpec,
    'osbase': OSBaseSpec,
    'platform': PlatformSpec
}

def loadobj(cfdir, type, name, param = None):
    obj = obj_types[type](param)
    obj.load_spec('%s/%s/%s.yml' % (cfdir, type, name))
    obj.default_set('NAME', name)
    return obj
