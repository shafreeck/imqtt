#!coding:utf8

import struct
import socket

"""
IMQTT is a interactive mqtt debug tool to build and send MQTT packets

Notice: The code style here is not pep8(https://www.python.org/dev/peps/pep-0008/). It is too long since I wrote python last time.
"""

class TCPClient:
    def __init__(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        print("connected to", address)
        self.s = s
    def Send(self, p):
        s.send(p.Marshal())
    def Recv(self):
        resp = s.recv(1024)


class FixedHeader:
    ControlPacketType = 0x00
    ControlPacketFlags = 0x00
    RemainingLength = 0
    def Marshal(self):
        hdr = bytearray()
        hdr.append(self.ControlPacketType & 0xF0) # upper four bits
        hdr.append(self.ControlPacketFlags & 0x0F)# lower four bits
        hdr.extend(EncodeVarInt(self.RemainingLength))
        return hdr

class Packet:
    FixedHeader = FixedHeader()

class ConnectPacket(Packet):
     class ConnectFlags:
         UsernameFlag = 0
         PasswordFlag = 0
         WillRetain = 0
         WillQoS = 0
         WillFlag = 0
         CleanSession = 0

     FixedHeader.ControlPacketType = 0x01
     FixedHeader.ControlPacketFlags = 0x00
     FixedHeader.RemainingLength = 2

     ProtocolName = "MQTT"
     ProtocolLevel = 4
     Flags = ConnectFlags()
     KeepAlive = 300

     CleanSession = 1
     Username = ""
     Password = ""
     ClientID = ""
     WillTopic = ""
     WillMessage = ""

     def Marshal(self):
         b = bytearray()
         b.extend(self.FixedHeader.Marshal())

         # Protocol name
         b.append(0x00)
         b.append(0x04)
         for c in 'MQTT':
             b.append(ord(c))
         # Protocol level
         b.append(0x04)

         # Connect flags
         flags = 0
         flags |= self.Flags.UsernameFlag < 7
         flags |= self.Flags.PasswordFlag < 6
         flags |= self.Flags.WillRetain < 5
         flags |= self.Flags.WillQoS < 3
         flags |= self.Flags.WillFlag < 2
         flags |= self.Flags.CleanSession < 1
         b.append(flags & 0xFF)

         # KeepAlive
         b.extend(struct.pack('!H', self.KeepAlive))

         # Payload
         b.extend(EncodeString(self.ClientID))
         if self.Flags.WillFlag == 1:
             b.extend(EncodeString(self.WillTopic))
             b.extend(EncodeString(self.WillMessage))
         if self.Flags.UsernameFlag == 1:
             b.extend(EncodeString(self.Username))
         if self.Flags.PasswordFlag == 1:
             b.extend(EncodeString(self.Password))
         return b
     def Unmarshal(self, data):
         return ""

class ConnackPacket(Packet):
    FixedHeader.ControlPacketType = 0x02
    FixedHeader.ControlPacketFlags = 0x00
    FixedHeader.RemainingLength = 0

    Flags = 0x00 #Bit 0 is SessionPresent or not, other bits are reserved
    ReturnCode = 0x00 # Counld be 0x00 .. 0x05

class PublishPacket(Packet):
    FixedHeader.ControlPacketType = 0x03
    FixedHeader.ControlPacketFlags = 0x00 #Dup, Qos and Retain
    FixedHeader.RemainingLength = 0 #TODO calc the init length

    Topic = "imqtt"
    PacketID = 0
    Payload = ""

class PubackPacket(Packet):
    FixedHeader.ControlPacketType = 0x04
    FixedHeader.ControlPacketFlags = 0x00
    FixedHeader.RemainingLength = 2

    PacketID = 0

class PubrecPacket(PubackPacket):
    FixedHeader.ControlPacketType = 0x05

class PubrelPacket(PubackPacket):
    FixedHeader.ControlPacketType = 0x06

class PubcompPacket(PubackPacket):
    FixedHeader.ControlPacketType = 0x07

class SubscribePacket(Packet):
    FixedHeader.ControlPacketType = 0x08
    FixedHeader.ControlPacketFlags = 0x02
    FixedHeader.RemainingLength = 0

    PacketID = 0
    Topics = []
    Qoss = []

class SubackPacket(Packet):
    FixedHeader.ControlPacketType = 0x09
    FixedHeader.ControlPacketFlags = 0x00
    FixedHeader.RemainingLength = 2

    PacketID = 0
    ReturnCodes = []

class UnsubscribePacket:
    FixedHeader.ControlPacketType = 0x0A
    FixedHeader.ControlPacketFlags = 0x00
    FixedHeader.RemainingLength = 0

    PacketID = 0
    Topics = []

class UnsubackPacket(Packet):
    FixedHeader.ControlPacketType = 0x0B
    FixedHeader.ControlPacketFlags = 0x00
    FixedHeader.RemainingLength = 2

    PacketID = 0

class PingReqPacket(Packet):
    FixedHeader.ControlPacketType = 0x0C
    FixedHeader.ControlPacketFlags = 0x00
    FixedHeader.RemainingLength = 0

class PingRespPacket(Packet):
    FixedHeader.ControlPacketType = 0x0D
    FixedHeader.ControlPacketFlags = 0x00
    FixedHeader.RemainingLength = 0

class DisconnectPacket(Packet):
    FixedHeader.ControlPacketType = 0x0E
    FixedHeader.ControlPacketFlags = 0x00
    FixedHeader.RemainingLength = 0

def EncodeVarInt(n):
    b = bytearray()
    v = 0
    while True:
        v = n & 127 # equals to n % 128, but should be faster
        n = n >> 7  # n / 128
        if n > 0:
            b.append(v | 128)
        else:
            b.append(v)
            break
    return b
def EncodeString(s):
    b = bytearray()
    b.extend(struct.pack('!H', len(s)))
    b.extend(s)
    return b

c = ConnectPacket()
print(dir(c))
