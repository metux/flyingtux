from basespec import BaseSpec
import yaml
from metux.util import log

class DeploySpec(BaseSpec):
    pass

"""define the representer, responsible for serialization"""
def DeploySpec_representer(dumper, data):
    log.warn("======= representer")
    serializedData = repr(data._my_spec)
    return dumper.represent_dict(data._my_spec)
