Iteractive MQTT packet manipulation shell based on IPython

You would love it if your are an expert of MQTT and Python

## Enter IMQTT shell

```
./imqtt.py
```

## Build a TCP Client and connect to mqtt server
```
In [1]: c = TCPClient(host = '127.0.0.1', port = 1883)
('connected to', '127.0.0.1', 1883)
```

## Send a MQTT Connect Packet

```
In [2]: p = ConnectPacket()

In [3]: c.Send(p)
Out[3]: <__main__.TCPClient instance at 0x215c518>
```

## Recv the Connack Packet

```
In [4]: ack = c.Recv()

In [5]: ack
Out[5]: <ConnackPacket <FixedHeader ControlPacketType: 0x2, ControlPacketFlags: 0, RemainingLength: 2>, Flags: 0x1, ReturnCode: 0x0>
```

## Publish a message
```
In [6]: pp = PublishPacket(Topic = '/imqtt/test', Payload = 'Hello world', QoS = 1, PacketID = 1)

In [7]: pp
Out[7]: <PublishPacket <FixedHeader ControlPacketType: 0x3, ControlPacketFlags: 0, RemainingLength: 0>, Dup: 0, QoS: 1, Retain: 0, PacketID: 1, Topic: /imqtt/test, Payload: Hello world>

In [8]: c.Send(pp).Recv()
Out[8]: <PubackPacket <FixedHeader ControlPacketType: 0x4, ControlPacketFlags: 0, RemainingLength: 2>, PacketID: 1>
```
