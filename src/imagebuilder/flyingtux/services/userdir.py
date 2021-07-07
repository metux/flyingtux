from os_service import Base

"""
Base class for mapping user directories

2DO: make it configurable where exactly to map it from
2DO: honour xdg configuration
"""
class UserDirBase(Base):
    permissions = {
        '__enabled__': { 'default': True },
        'read':   { 'default': True, 'description': 'read all files' },
        'write':  { 'default': True, 'description': '(over)write files' },
        'remove': { 'default': True, 'description': 'remove files' },
        'mkdir':  { 'default': True, 'description': 'create directories' },
        'rmdir':  { 'default': True, 'description': 'remove directories' },
        'create': { 'default': True, 'description': 'create new files' },
    }

    settings = {
        'name':   { 'default': '', 'description': 'container side directory name' },
        'target': { 'default': '', 'description': 'host side directory name' }
    }

    def compute(self):
        """name is the directory name (uneder /home/app) inside the container
           target is the host directory (under $HOME) thats mounted"""
        self.bind_user_dir(self.target, self.name)

    def prepare_conf(self):
        self.settings['name']['default']   = self.name
        self.settings['target']['default'] = self.target

class UserDocuments(UserDirBase):
    name   = 'Documents'
    target = 'Documents'

class UserPictures(UserDirBase):
    name   = 'Pictures'
    target = 'Pictures'

class UserMovies(UserDirBase):
    name   = 'Movies'
    target = 'Movies'

class UserDownloads(UserDirBase):
    name   = 'Downloads'
    target = 'Downloads'
