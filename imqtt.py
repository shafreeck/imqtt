#coding:utf8

import struct
import socket
import ipshell

"""
IMQTT is a interactive mqtt debug tool to build and send MQTT packets

Notice: The code style here is not pep8(https://www.python.org/dev/peps/pep-0008/). It is too long since I wrote python last time.
"""

class PacketType:
    CONNECT     = 0x01
    CONNACK     = 0x02
    PUBLISH     = 0x03
    PUBACK      = 0x04
    PUBREC      = 0x05
    PUBREL      = 0x06
    PUBCOMP     = 0x07
    SUBSCRIBE   = 0x08
    SUBACK      = 0x09
    UNSUBSCRIBE = 0x0A
    UNSUBACK    = 0x0B
    PINGREQ     = 0x0C
    PINGRESP    = 0x0D
    DISCONNECT  = 0x0E


class TCPClient:
    def __init__(self, host = '127.0.0.1', port = 1883):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        self.buf = bytearray()
        print("connected to", host, port)
        self.s = s
    def Send(self, p):
        self.s.send(p.Marshal())
        return self
    def SendRaw(self, data):
        self.s.send(data)
        return self
    def Recv(self):
        while True:
            buf = self.s.recv(1024)
            if len(buf) == 0:
                self.s.close()
                raise(Exception('Connection closed'))
            self.buf.extend(buf)

            try:
                p, consumed = DecodePacket(self.buf)
                self.buf = self.buf[consumed:]
                return p
            except Exception as e:
                continue

    def Close(self):
        self.s.close()

class TCPServer:
    def __init__(self, host = '127.0.0.1', port = 1883):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        s.listen(128)
        self.s = s
        print('listening on', host, port)

    def Serve(self):
        while True:
            conn, addr = self.s.accept()
            self.conn = conn
            self.buf = bytearray()
            while True:
                buf = self.conn.recv(1024)
                if len(buf) == 0:
                    self.conn.close()
                    raise(Exception('Connection closed'))
                self.buf.extend(buf)

                try:
                    p, consumed = DecodePacket(self.buf)
                    self.buf = self.buf[consumed:]
                    ipshell.enter()
                except Exception as e:
                    continue


    def Send(self, p):
        self.conn.send(p.Marshal())
        return self
    def SendRaw(self, data):
        self.conn.send(data)
        return self
    def Close(self):
        self.s.close()

class FixedHeader:
    ControlPacketType = 0x00
    ControlPacketFlags = 0x00
    RemainingLength = 0
    def Marshal(self):
        hdr = bytearray()
        v = self.ControlPacketType << 4 # upper four bits
        v |= self.ControlPacketFlags & 0x0F # lower four bits
        hdr.append(v)
        hdr.extend(EncodeVarInt(self.RemainingLength))
        return hdr
    def Unmarshal(self, data):
        c = data[0]
        self.ControlPacketType = c >> 4
        self.ControlPacketFlags = c & 0x0F

        rl, consumed = DecodeVarInt(data[1:])
        self.RemainingLength = rl
        return self, consumed + 1
    def __repr__(self):
        fmt = '<FixedHeader ControlPacketType: 0x%x, ControlPacketFlags: %s,' \
         ' RemainingLength: %d>'
        return fmt % (self.ControlPacketType, self.ControlPacketFlags,
        self.RemainingLength)

class ConnectPacket():
     class ConnectFlags:
         UsernameFlag = 0
         PasswordFlag = 0
         WillRetain = 0
         WillQoS = 0
         WillFlag = 0
         CleanSession = 0

     FixedHeader = FixedHeader()
     FixedHeader.ControlPacketType = PacketType.CONNECT
     FixedHeader.ControlPacketFlags = 0x00
     FixedHeader.RemainingLength = 2

     ProtocolName = "MQTT"
     ProtocolLevel = 4
     Flags = ConnectFlags()
     KeepAlive = 300

     Username = ""
     Password = ""
     ClientID = "imqtt"
     WillTopic = ""
     WillMessage = ""
     def __init__(self, ClientID = 'imqtt', Username = '', Password = '', CleanSession = 1, KeepAlive = 300):
         self.ClientID = ClientID
         self.Username = Username
         self.Password = Password
         self.Flags.CleanSession = CleanSession

     def Marshal(self):
         b = bytearray()

         # Protocol name
         b.append(0x00)
         b.append(0x04)
         for c in 'MQTT':
             b.append(ord(c))
         # Protocol level
         b.append(0x04)

         # Connect flags
         flags = 0
         flags |= self.Flags.UsernameFlag << 7
         flags |= self.Flags.PasswordFlag << 6
         flags |= self.Flags.WillRetain << 5
         flags |= self.Flags.WillQoS << 3
         flags |= self.Flags.WillFlag << 2
         flags |= self.Flags.CleanSession << 1
         b.append(flags)

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

         self.FixedHeader.RemainingLength = len(b)
         p = bytearray(self.FixedHeader.Marshal())
         p.extend(b)
         return p
     def Unmarshal(self, data):
         h, n = self.FixedHeader.Unmarshal(data)
         consumed = n

         self.ProtocolName, n = DecodeString(data[consumed:])
         consumed += n

         self.ProtocolLevel = data[consumed]
         consumed += 1

         flags = data[consumed]
         consumed += 1
         self.Flags.UsernameFlag = flags >> 7 & 0x01
         self.Flags.PasswordFlag = flags >> 6 & 0x01
         self.Flags.WillRetain = flags >> 5 & 0x01
         self.Flags.WillQoS = flags >> 3 & 0x03
         self.Flags.WillFlag = flags >> 2 & 0x01
         self.Flags.CleanSession = flags >> 1 & 0x01
         self.Flags.Reserved = flags & 0x01

         self.KeepAlive, = struct.unpack('!H', data[consumed:consumed+2])
         consumed += 2

         self.ClientID, n = DecodeString(data[consumed:])
         consumed += n

         if self.Flags.WillFlag == 1:
             self.WillTopic, n = DecodeString(data[consumed:])
             consumed += n

             self.WillMessage, n = DecodeString(data[consumed:])
             consumed += n

         if self.Flags.UsernameFlag == 1:
             self.Username, n = DecodeString(data[consumed:])
             consumed += n
         if self.Flags.PasswordFlag == 1:
             self.Password, n = DecodeString(data[consumed:])
             consumed += n
         
         return self, consumed 

     def __repr__(self):
         fmt = '<%s %s,  Protocol: %s, ' \
         'Version: %d, <Flags UsernameFlag: %d, PasswordFlag: %d, ' \
         'WillRetain: %d, WillQoS: %d, WillFlag: %d, CleanSession: %d>, ' \
         'KeepAlive: %d, ClientID: %s, Username: %s, Password: %s>'
         return fmt % (self.__class__.__name__, self.FixedHeader,
         self.ProtocolName, self.ProtocolLevel, self.Flags.UsernameFlag,
         self.Flags.PasswordFlag, self.Flags.WillRetain, self.Flags.WillQoS,
         self.Flags.WillFlag, self.Flags.CleanSession, self.KeepAlive,
         self.ClientID, self.Username, self.Password)

class ConnackPacket():
    FixedHeader = FixedHeader()
    FixedHeader.ControlPacketType = PacketType.CONNACK
    FixedHeader.ControlPacketFlags = 0x00
    FixedHeader.RemainingLength = 2

    Flags = 0x00 #Bit 0 is SessionPresent or not, other bits are reserved
    ReturnCode = 0x00 # Counld be 0x00 .. 0x05

    def Marshal(self):
        b = bytearray(self.FixedHeader.Marshal())
        b.append(self.Flags)
        b.append(self.ReturnCode)
        return b
    def Unmarshal(self, data):
        h, i = self.FixedHeader.Unmarshal(data)
        self.Flags = data[i]
        self.ReturnCode = data[i+1]
        return self, i + 2
    def __repr__(self):
        fmt = '<%s %s, Flags: 0x%0x, ReturnCode: 0x%0x>'
        return fmt % (self.__class__.__name__, self.FixedHeader, self.Flags,
        self.ReturnCode)

class PublishPacket():
    FixedHeader = FixedHeader()
    FixedHeader.ControlPacketType = PacketType.PUBLISH
    FixedHeader.ControlPacketFlags = 0x00 #Dup, Qos and Retain
    FixedHeader.RemainingLength = 0 #TODO calc the init length

    Dup = 0
    QoS = 0
    Retain = 0
    Topic = "/imqtt/shell"
    PacketID = 0
    Payload = ""

    def __init__(self, Topic = '/imqtt/shell', Payload = '', 
            PacketID = 0, QoS = 0, Dup = 0, Retain = 0):
        self.Topic = Topic
        self.Payload = Payload
        self.PacketID = PacketID
        self.QoS = QoS
        self.Dup = Dup
        self.Retain = Retain

    def Marshal(self):
        b = bytearray()
        b.extend(EncodeString(self.Topic))
        if self.QoS > 0:
            b.extend(EncodePacketID(self.PacketID))
        b.extend(bytearray(self.Payload, 'utf-8'))

        self.FixedHeader.ControlPacketFlags |= self.Dup << 3
        self.FixedHeader.ControlPacketFlags |= self.QoS << 1
        self.FixedHeader.ControlPacketFlags |= self.Retain
        self.FixedHeader.RemainingLength = len(b)
        p = bytearray(self.FixedHeader.Marshal())
        p.extend(b)
        return p

    def Unmarshal(self, data):
        h, n = self.FixedHeader.Unmarshal(data)
        consumed = n

        self.Dup = self.FixedHeader.ControlPacketFlags >> 3 & 0x01
        self.QoS = self.FixedHeader.ControlPacketFlags >> 1 & 0x03
        self.Retain = self.FixedHeader.ControlPacketFlags & 0x01

        self.Topic, n = DecodeString(data[consumed:])
        consumed += n

        if self.QoS > 0:
            self.PacketID, n = DecodePacketID(data[consumed:])
            consumed += n

        left = self.FixedHeader.RemainingLength - 2
        self.Payload = data[consumed: consumed + left]
        consumed += left
        return self, consumed

    def __repr__(self):
        fmt = '<%s %s, Dup: %d, QoS: %d, Retain: %d, ' \
        'PacketID: %d, Topic: %s, Payload: %s>'
        return fmt%(self.__class__.__name__, self.FixedHeader, self.Dup,
        self.QoS, self.Retain, self.PacketID, self.Topic, self.Payload)

class PubackPacket:
    FixedHeader = FixedHeader()
    FixedHeader.ControlPacketType = PacketType.PUBACK
    FixedHeader.ControlPacketFlags = 0x00
    FixedHeader.RemainingLength = 2

    PacketID = 0

    def __init__(self, PacketID = 0):
        self.PacketID = PacketID

    def Marshal(self):
        b = bytearray(self.FixedHeader.Marshal())
        b.extend(EncodePacketID(self.PacketID))
        return b
    def Unmarshal(self, data):
        h, i = self.FixedHeader.Unmarshal(data)
        self.PacketID, consumed = DecodePacketID(data[i:])
        return self, consumed + i
    def __repr__(self):
        fmt = '<%s %s, PacketID: %d>'
        return fmt%(self.__class__.__name__, self.FixedHeader, self.PacketID)


class PubrecPacket(PubackPacket):
    def __init__(self):
        self.FixedHeader.ControlPacketType = PacketType.PUBREC

class PubrelPacket(PubackPacket):
    def __init__(self):
        self.FixedHeader.ControlPacketType = PacketType.PUBREL

class PubcompPacket(PubackPacket):
    def __init__(self):
        self.FixedHeader.ControlPacketType = PacketType.PUBCOMP

class SubscribePacket():
    FixedHeader = FixedHeader()
    FixedHeader.ControlPacketType = PacketType.SUBSCRIBE
    FixedHeader.ControlPacketFlags = 0x02
    FixedHeader.RemainingLength = 0

    PacketID = 0
    Topics = []
    Qoss = []

    def __init__(self, Topic = '/imqtt/shell', QoS = 0, PacketID = 1):
        self.Topics = []
        self.Qoss = []
        self.Topics.append(Topic)
        self.Qoss.append(QoS)
        self.PacketID = PacketID

    def Marshal(self):
        b = bytearray()
        b.extend(EncodePacketID(self.PacketID))
        for i, t in  enumerate(self.Topics):
            qos = self.Qoss[i]
            b.extend(EncodeString(t))
            b.append(qos)
        self.FixedHeader.RemainingLength = len(b)
        p = bytearray(self.FixedHeader.Marshal())
        p.extend(b)
        return p

    def Unmarshal(self):
        h, n = self.FixedHeader.Unmarshal()
        consumed += n

        self.PacketID, n = DecodePacketID(data[consumed:])
        consumed += n

        left = self.FixedHeader.RemainingLength - 2
        while left > 0:
            topic, n = DecodeString(data[consumed:])
            consumed += n

            qos = data[consumed]
            consumed += 1

            self.Topics.append(topic)
            self.Qoss.append(qos)

            left -= n + 1
        return self, consumed

    def __repr__(self):
        fmt = '<%s %s, PacketID: %d, Topics: %s, Qoss: %s>'
        return fmt%(self.__class__.__name__, self.FixedHeader, self.PacketID,
        self.Topics, self.Qoss)

class SubackPacket():
    FixedHeader = FixedHeader()
    FixedHeader.ControlPacketType = PacketType.SUBACK
    FixedHeader.ControlPacketFlags = 0x00
    FixedHeader.RemainingLength = 0

    PacketID = 0
    ReturnCodes = []

    def __init__(self):
        self.ReturnCodes = []

    def Marshal(self):
        b = bytearray()
        b.extend(EncodePacketID(self.PacketID))
        for code in self.ReturnCodes:
            b.append(code)

        self.FixedHeader.RemainingLength = len(b)
        p = bytearray(self.FixedHeader.Marshal())
        p.extend(b)
        return p
    def Unmarshal(self, data):
        consumed = 0
        h, i = self.FixedHeader.Unmarshal(data)
        consumed += i

        self.PacketID, i = DecodePacketID(data[consumed:])
        consumed += i

        remained = self.FixedHeader.RemainingLength - 2
        for i in range(0, remained):
            self.ReturnCodes.append(data[consumed+i])
        consumed += remained
        return self, consumed
    def __repr__(self):
        fmt = '<%s %s, PacketID: %d, ReturnCodes: %s>'
        return fmt%(self.__class__.__name__, self.FixedHeader, self.PacketID,
        self.ReturnCodes)

class UnsubscribePacket:
    FixedHeader = FixedHeader()
    FixedHeader.ControlPacketType = PacketType.UNSUBSCRIBE
    FixedHeader.ControlPacketFlags = 0x02
    FixedHeader.RemainingLength = 0

    PacketID = 0
    Topics = []

    def __init__(self, Topic = '/imqtt/shell', PacketID = 1):
        self.Topics.append(Topic)
        self.PacketID = PacketID

    def Marshal(self):
        b = bytearray()
        b.extend(EncodePacketID(self.PacketID))
        for t in self.Topics:
            b.extend(EncodeString(t))

        self.FixedHeader.RemainingLength = len(b)
        p = bytearray(self.FixedHeader.Marshal())
        p.extend(b)
        return p
    def __repr__(self):
        fmt = '<%s %s, PacketID: %d, Topics: %s>'
        return fmt%(self.__class__.__name__, self.FixedHeader, self.PacketID,
        self.Topics)

class UnsubackPacket():
    FixedHeader = FixedHeader()
    FixedHeader.ControlPacketType = PacketType.UNSUBACK
    FixedHeader.ControlPacketFlags = 0x00
    FixedHeader.RemainingLength = 2

    PacketID = 0

    def Marshal(self):
        b = bytearray(self.FixedHeader.Marshal())
        b.extend(EncodePacketID(self.PacketID))
        return b
    def Unmarshal(self, data):
        h, i = self.FixedHeader.Unmarshal(data)
        id, consumed = DecodePacketID(data[i:])
        return id, consumed + i
    def __repr__(self):
        fmt = '<%s %s, PacketID: %d, Topics: %s, Qoss: %s>'
        return fmt%(self.__class__.__name__, self.FixedHeader, self.PacketID,
        self.Topics, self.Qoss)

class PingReqPacket():
    FixedHeader = FixedHeader()
    FixedHeader.ControlPacketType = PacketType.PINGREQ
    FixedHeader.ControlPacketFlags = 0x00
    FixedHeader.RemainingLength = 0

    def Marshal(self):
        return bytearray(self.FixedHeader.Marshal())
    def Unmarshal(self, data):
        h, i = self.FixedHeader.Unmarshal(data)
        return self, i
    def __repr__(self):
        fmt = '<%s %s>'
        return fmt%(self.__class__.__name__, self.FixedHeader)

class PingRespPacket():
    FixedHeader = FixedHeader()
    FixedHeader.ControlPacketType = PacketType.PINGRESP
    FixedHeader.ControlPacketFlags = 0x00
    FixedHeader.RemainingLength = 0

    def Marshal(self):
        return bytearray(self.FixedHeader.Marshal())
    def Unmarshal(self, data):
        h, i = self.FixedHeader.Unmarshal(data)
        return self, i
    def __repr__(self):
        fmt = '<%s %s>'
        return fmt%(self.__class__.__name__, self.FixedHeader)

class DisconnectPacket():
    FixedHeader = FixedHeader()
    FixedHeader.ControlPacketType = PacketType.DISCONNECT
    FixedHeader.ControlPacketFlags = 0x00
    FixedHeader.RemainingLength = 0

    def Marshal(self):
        return bytearray(self.FixedHeader.Marshal())
    def Unmarshal(self, data):
        h, i = self.FixedHeader.Unmarshal(data)
        return self, i
    def __repr__(self):
        fmt = '<%s %s>'
        return fmt%(self.__class__.__name__, self.FixedHeader)

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

def DecodeVarInt(data):
    '''
    return decoded value and length consumed
    '''
    m = 1
    v = 0
    i = 0
    # We do not care about the length of data now
    # It will raise excepiton if the length is not enough
    while True:
        b = data[i]
        v += (b & 127) * m
        m *= 128
        i += 1
        if (m > 128**3):
            raise Exception('Malformed Remaining Length')
        if b & 128 == 0:
            break
    return v, i

def EncodeString(s):
    b = bytearray()
    b.extend(struct.pack('!H', len(s)))
    b.extend(bytearray(s, 'utf-8'))
    return b
def DecodeString(data):
    length, = struct.unpack('!H', data[0:2])
    return data[2:length+2], length+2

def EncodePacketID(id):
    return bytearray(struct.pack('!H', id))
def DecodePacketID(data):
    id, = struct.unpack('!H', data[0:2])
    return id, 2

def DecodePacket(data):
    p = None
    consumed = 0

    c = data[0]
    t = c >> 4
    if t == PacketType.CONNECT:
        p = ConnectPacket()
    elif t == PacketType.CONNACK:
        p = ConnackPacket()
    elif t == PacketType.PUBLISH:
        p = PublishPacket()
    elif t == PacketType.PUBACK:
        p = PubackPacket()
    elif t == PacketType.PUBREC:
        p = PubrecPacket()
    elif t == PacketType.PUBREL:
        p = PubrelPacket()
    elif t == PacketType.PUBCOMP:
        p = PubcompPacket()
    elif t == PacketType.SUBSCRIBE:
        p = SubscribePacket()
    elif t == PacketType.SUBACK:
        p = SubackPacket()
    elif t == PacketType.UNSUBSCRIBE:
        p = UnsubscribePacket()
    elif t == PacketType.UNSUBACK:
        p = UnsubackPacket()
    elif t == PacketType.PINGREQ:
        p = PingReqPacket()
    elif t == PacketType.PINGRESP:
        p = PingRespPacket()
    elif t == PacketType.DISCONNECT:
        p = DisconnectPacket()
    else:
        raise(Exception('Unknown packet type'))

    return p.Unmarshal(data)

