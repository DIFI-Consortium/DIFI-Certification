####################
# Error Types
####################

from utils.nonCompliantClass import DifiInfo

class InvalidDataReceived(Exception):
    pass

class InvalidPacketType(Exception):
    pass

class NoncompliantDifiPacket(Exception):
    def __init__(self, message, difi_info: DifiInfo=None):
        super().__init__()
        self.message = message
        self.difi_info = difi_info

    def __str__(self):
        return str(self.message)

class InvalidArgs(Exception): #command-line args error type
    pass