from os_service import Base

class KernelDevice(Base):
    def compute(self):
        self.add_device(self.name)

class DriDevice(KernelDevice):
    name = '/dev/dri/card0'
