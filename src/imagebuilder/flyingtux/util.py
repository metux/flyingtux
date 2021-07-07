from os.path import normpath

def clean_path(path):
    return normpath(path).replace('../', '')

class FT_Error(Exception):
    pass

class FT_ConfigError(FT_Error):
    pass

class FT_UnsupportedJail(FT_Error):
    pass

class FT_UnsupportedPkg(FT_Error):
    pass

class FT_UnsupportedTool(FT_Error):
    pass
