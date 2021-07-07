from basespec import BaseSpec
from ..util import clean_path
from os.path import basename

class ImageSpec(BaseSpec):
    def get_repos(self):
        r = self['OSBASE'].get_repos()
        k = self['DATADIR']+'/keys/'
        return {
            'keys': r['keys'] + [k+clean_path(x) for x in self.get_cf_list('rootfs::repos::keys')],
            'urls': r['urls'] + self.get_cf_list('rootfs::repos::urls'),
        }

    def __mergelist(self, name):
        return (self.get_cf_list('OSBASE::'+name)
               +self.get_cf_list('rootfs::'+name))

    ## fixme: filter out those we wanna keep
    def get_purged_locales(self):
        locale_dirs    = self.__mergelist('post-clean::locale-dirs')
        remove_locales = self.__mergelist('post-clean::remove-locales')

        r = []
        for ld in locale_dirs:
            r.extend([ld+"/"+rl for rl in remove_locales])
        return r

    def get_purged_files(self):
        return (self.get_purged_locales()
               +self.__mergelist('post-clean::remove'))

    def get_empty_dirs(self):
        return self.__mergelist('post-clean::empty-dirs')

    def post_init(self):
        self.default_set('user', 'app')
