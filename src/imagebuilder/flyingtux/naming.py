# SPDX-License-Identifier: AGPL-3.0-or-later
"""
helper functions for naming conventions. the whole purpose of
them is moving them all to a central place for better clarity.
"""

def app_container_name(appname, version):
    return 'flyingtux-app-%s_%s' % (appname, version)
