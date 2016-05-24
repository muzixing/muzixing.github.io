title:Ryu:如何在LLDP中添加自定义LLDPDU
tags:sdn
date:2016/5/20
category:Tech


---
在许多实验场景中，都需要使用链路发现协议（LLDP）来发现链路，从而构建网络拓扑。然而LLDP协议不仅仅可以用来发现拓扑，也可以用于时延检测等业务。LLDP通过添加对应的TLV格式的LLDPDU（LLDP数据单元）来携带对应的信息，从而为上层业务提供信息支撑。为实现LLDP数据单元的拓展，本文将以Ryu控制器为例，介绍如何添加自定义的LLDPDU，从而满足多种业务的需求。

添加自定义LLDPDU其实只需修改ryu/lib/packet/lldp.py即可，但是由于该文件仅定义了LLDP的相关类，如何使用还需要其他文件去调用，所以还需要其他的修改步骤。具体步骤将在文章后续介绍。

### 修改lldp.py文件

ryu/lib/packet/lldp.py文件是Ryu控制器中关于LLDP协议数据类的描述，其中定义了如LLDPBasicTLV类等重要的报文类。 以添加发送时间戳的TLV为例，我们需要完成TLV类型号的声明，以及TLV类的定义。

在文件开头处有关于LLDP TLV类型的声明，所以首先我们需要添加一个新的类型：LLDP\_TLV\_SEND\_TIME，其类型号为11。

```py
    # LLDP TLV type
    LLDP_TLV_END = 0                        # End of LLDPDU
    LLDP_TLV_CHASSIS_ID = 1                 # Chassis ID
    LLDP_TLV_PORT_ID = 2                    # Port ID
    LLDP_TLV_TTL = 3                        # Time To Live
    LLDP_TLV_PORT_DESCRIPTION = 4           # Port Description
    LLDP_TLV_SYSTEM_NAME = 5                # System Name
    LLDP_TLV_SYSTEM_DESCRIPTION = 6         # System Description
    LLDP_TLV_SYSTEM_CAPABILITIES = 7        # System Capabilities
    LLDP_TLV_MANAGEMENT_ADDRESS = 8         # Management Address
    LLDP_TLV_DOMAIN_ID = 9                  # Domain id for Open Exchange Protocol
    LLDP_TLV_VPORT_ID = 10                  # vport_no for Open Exchange Protocol
    LLDP_TLV_SEND_TIME = 11                 # Time stamp for sending LLDP packet,
                                            # using for delay measurement.
    LLDP_TLV_ORGANIZATIONALLY_SPECIFIC = 127  # organizationally Specific TLVs
```

然后设计此类型的LLDPDU格式，其格式仅包含一个长度为8字节的Double类型的时间戳数据。如何完成类的描述，可以参考TTL类，具体代码如下。

```py
    @lldp.set_tlv_type(LLDP_TLV_SEND_TIME)
    class TimeStamp(LLDPBasicTLV):
        _PACK_STR = '!d'
        _PACK_SIZE = struct.calcsize(_PACK_STR)
        _LEN_MIN = _PACK_SIZE
        _LEN_MAX = _PACK_SIZE
    
        def __init__(self, buf=None, *args, **kwargs):
            super(TimeStamp, self).__init__(buf, *args, **kwargs)
            if buf:
                (self.timestamp, ) = struct.unpack(
                    self._PACK_STR, self.tlv_info[:self._PACK_SIZE])
            else:
                self.timestamp = kwargs['timestamp']
                self.len = self._PACK_SIZE
                assert self._len_valid()
                self.typelen = (self.tlv_type << LLDP_TLV_TYPE_SHIFT) | self.len
    
        def serialize(self):
            return struct.pack('!Hd', self.typelen, self.timestamp)
```

TimeStamp类中定义了该LLDPDU的格式，初始化函数以及序列化函数。

### 修改switches.py

完成LLDPDU的定义之后，还需要在某文件中对其进行初始化构造。如果另外重新编写一个LLDP的构造、发送以及接受解析模块，那么则需要重新写许多代码，所以此处推荐直接修改Ryu/topology/switches.py文件。

switches.py文件中的LLDPPacket类完成了LLDP数据包的初始化和序列化实现。

该类的lldp\_packet方法可以构造LLDP数据包，并返回序列化之后的数据。在此函数中，我们需要添加timestamp的TLV。

在lldp\_parse方法中，需将获取到的字节流的数据解析为对应的LLDP数据包。由于在发送之前，我们加入了一个timestamp的TLV，所以解析时需要完成这个TLV的解析，并将TimeStamp作为返回值返回。

```py
    class LLDPPacket(object):
        # make a LLDP packet for link discovery.
    
        CHASSIS_ID_PREFIX = 'dpid:'
        CHASSIS_ID_PREFIX_LEN = len(CHASSIS_ID_PREFIX)
        CHASSIS_ID_FMT = CHASSIS_ID_PREFIX + '%s'
    
        PORT_ID_STR = '!I'      # uint32_t
        PORT_ID_SIZE = 4
    
        DOMAIN_ID_PREFIX = 'domain_id:'
        DOMAIN_ID_PREFIX_LEN = len(DOMAIN_ID_PREFIX)
        DOMAIN_ID_FMT = DOMAIN_ID_PREFIX + '%s'
    
        VPORT_ID_STR = '!I'      # uint32_t
        VPORT_ID_SIZE = 4
    
        class LLDPUnknownFormat(RyuException):
            message = '%(msg)s'
    
        @staticmethod
        def lldp_packet(dpid, port_no, dl_addr, ttl, timestamp,
                        vport_no=ofproto_v1_0.OFPP_NONE):
            pkt = packet.Packet()
    
            dst = lldp.LLDP_MAC_NEAREST_BRIDGE
            src = dl_addr
            ethertype = ETH_TYPE_LLDP
            eth_pkt = ethernet.ethernet(dst, src, ethertype)
            pkt.add_protocol(eth_pkt)
    
            tlv_chassis_id = lldp.ChassisID(
                subtype=lldp.ChassisID.SUB_LOCALLY_ASSIGNED,
                chassis_id=LLDPPacket.CHASSIS_ID_FMT %
                dpid_to_str(dpid))
    
            tlv_port_id = lldp.PortID(subtype=lldp.PortID.SUB_PORT_COMPONENT,
                                      port_id=struct.pack(
                                          LLDPPacket.PORT_ID_STR,
                                          port_no))
    
            tlv_ttl = lldp.TTL(ttl=ttl)
            tlv_timestamp = lldp.TimeStamp(timestamp=timestamp)
            tlv_end = lldp.End()
    
            tlvs = (tlv_chassis_id, tlv_port_id, tlv_ttl, tlv_timestamp, tlv_end)
            lldp_pkt = lldp.lldp(tlvs)
            pkt.add_protocol(lldp_pkt)
    
            pkt.serialize()
            return pkt.data


        @staticmethod
        def lldp_parse(data):
            pkt = packet.Packet(data)
            i = iter(pkt)
            eth_pkt = i.next()
            assert type(eth_pkt) == ethernet.ethernet
    
            lldp_pkt = i.next()
    
            if type(lldp_pkt) != lldp.lldp:
                raise LLDPPacket.LLDPUnknownFormat()
    
            tlv_chassis_id = lldp_pkt.tlvs[0]
            if tlv_chassis_id.subtype != lldp.ChassisID.SUB_LOCALLY_ASSIGNED:
                raise LLDPPacket.LLDPUnknownFormat(
                    msg='unknown chassis id subtype %d' % tlv_chassis_id.subtype)
            chassis_id = tlv_chassis_id.chassis_id
            if not chassis_id.startswith(LLDPPacket.CHASSIS_ID_PREFIX):
                raise LLDPPacket.LLDPUnknownFormat(
                    msg='unknown chassis id format %s' % chassis_id)
            src_dpid = str_to_dpid(chassis_id[LLDPPacket.CHASSIS_ID_PREFIX_LEN:])
    
            tlv_port_id = lldp_pkt.tlvs[1]
            if tlv_port_id.subtype != lldp.PortID.SUB_PORT_COMPONENT:
                raise LLDPPacket.LLDPUnknownFormat(
                    msg='unknown port id subtype %d' % tlv_port_id.subtype)
            port_id = tlv_port_id.port_id
            if len(port_id) != LLDPPacket.PORT_ID_SIZE:
                raise LLDPPacket.LLDPUnknownFormat(
                    msg='unknown port id %d' % port_id)
            (src_port_no, ) = struct.unpack(LLDPPacket.PORT_ID_STR, port_id)
    
            tlv_timestamp = lldp_pkt.tlvs[3]
            timestamp = tlv_timestamp.timestamp
    
            return src_dpid, src_port_no, timestamp
        
``` 

到此为止，完成了LLDP的构造和解析的定义。但是由于修改了构造函数的参数列表，和解析函数的返回值，所以在构造LLDP数据包和解析LLDP数据包时，均需要做一些改动。示例代码如下：

```py
    def _port_added(self, port):
        _time = time.time()
        lldp_data = LLDPPacket.lldp_packet(port.dpid, port.port_no,
                                           port.hw_addr, self.DEFAULT_TTL, _time)
```
```py
        @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
        def packet_in_handler(self, ev):
            if not self.link_discovery:
                return
    
            msg = ev.msg
            try:
                src_dpid, src_port_no, timestamp = LLDPPacket.lldp_parse(msg.data)
            except LLDPPacket.LLDPUnknownFormat as e:
                # This handler can receive all the packtes which can be
                # not-LLDP packet. Ignore it silently
                return
```

此处需要提醒读者的是，在Ryu的Switches模块中，被发送的LLDP都是一次构造之后保存起来，发送时直接发送的，所以添加的时间戳会固定在第一次构造时的时间。所以如果希望正确地插入发送时间戳，还需要进行额外的逻辑修改。但是这也许就破坏了Ryu设计的完整性，所以如何操作还需要读者自行斟酌。

然而，像VPort\_ID之类的不随时间而改变的TLV，则可以直接使用。添加VPort\_ID的步骤和以上的例子同理，其VPort\_ID类的示例代码如下所示：

```py
    @lldp.set_tlv_type(LLDP_TLV_VPORT_ID)
    class VPortID(LLDPBasicTLV):
        _PACK_STR = '!B'
        _PACK_SIZE = struct.calcsize(_PACK_STR)
    
        # subtype id(1 octet) + port id length(1 - 255 octet)
        _LEN_MIN = 2
        _LEN_MAX = 256
    
        # VPort ID subtype
        SUB_INTERFACE_ALIAS = 1     # ifAlias (IETF RFC 2863)
        SUB_PORT_COMPONENT = 2      # entPhysicalAlias (IETF RFC 4133)
        SUB_MAC_ADDRESS = 3         # MAC address (IEEE Std 802)
        SUB_NETWORK_ADDRESS = 4     # networkAddress
        SUB_INTERFACE_NAME = 5      # ifName (IETF RFC 2863)
        SUB_AGENT_CIRCUIT_ID = 6    # agent circuit ID(IETF RFC 3046)
        SUB_LOCALLY_ASSIGNED = 7    # local
    
        def __init__(self, buf=None, *args, **kwargs):
            super(VPortID, self).__init__(buf, *args, **kwargs)
            if buf:
                (self.subtype, ) = struct.unpack(
                    self._PACK_STR, self.tlv_info[:self._PACK_SIZE])
                self.vport_id = self.tlv_info[self._PACK_SIZE:]
            else:
                self.subtype = kwargs['subtype']
                self.vport_id = kwargs['vport_id']
                self.len = self._PACK_SIZE + len(self.vport_id)
                assert self._len_valid()
                self.typelen = (self.tlv_type << LLDP_TLV_TYPE_SHIFT) | self.len
    
        def serialize(self):
            return struct.pack('!HB', self.typelen, self.subtype) + self.vport_id
```

### 总结

LLDP协议可添加自定义TLV格式的特性，使其可以灵活地被修改，进而应用到不同的业务场景中，十分方便。本文就以Ryu控制器为例，介绍了如何添加自定义LLDPDU的详细流程，希望对读者有一定的帮助。此外，为计算时延，还可以通过switches模块中的PortDatak类的发送时间戳来实现，无需修改LLDP数据包格式。如何在Ryu中完成时延测试的内容将在下一篇文章中详细介绍，敬请关注。

### 作者简介

李呈，2014/09-至今，北京邮电大学信息与通信工程学院未来网络理论与应用实验室（FNL实验室）攻读硕士研究生。

个人博客：http://www.muzixing.com
