from os.path import normpath

def clean_path(path):
    return normpath(path).replace('../', '')
