"""
helper functions for naming conventions. the whole purpose of
them is moving them all to a central place for better clarity.
"""

def app_container_name(appname, version):
    return 'flyingtux-app-%s_%s' % (appname, version)
