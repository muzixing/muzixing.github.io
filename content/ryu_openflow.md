title:Ryu:OpenFlow协议源码分析
date:2015/7/24
tags:ryu, openflow
category:Tech

Ryu支持OpenFlow所有的版本，是所有SDN控制器中对OpenFlow支持最好的控制器之一。这得益于Ryu的代码设计，Ryu中关于OpenFlow协议的代码量不多。阅读Ryu源码，不仅让我了解到了Ryu的运行细节，也学会了许多的编码知识。这为我当前开发的协议提供了很大的帮助。

本篇将从交换机与控制器建立连接开始，介绍OpenFlow报文的解析的相关代码实现。关于如何注册handler和发送报文，可查看之前的[RYU核心源码解读：OFPHandler,Controller,RyuApp和AppManager](http://www.muzixing.com/pages/2014/12/27/ryuhe-xin-yuan-ma-jie-du-ofphandlercontrollerryuapphe-appmanager.html)。该篇侧重点为Ryu整体架构的运作，重点在RyuApp和AppManager;本篇重点在与详细介绍OpenFlow的解析和封装实现。希望对读者提供帮助。

###**Ofp_handler**

负责底层数据通信的模块是ofp\_handler模块。ofp\_handler启动之后，start函数实例化了一个controller.OpenFlowController实例。OpenFlowController实例化之后，立即调用\__call\__()函数，call函数启动了server\_loop去创建server socket，其handler为domain\_connection\_factory函数。每当收到一个switch连接，domain\_connection\_factory就会实例化一个datapath对象。这个对象用于描述交换机的所有行为。其中定义了接收循环和发送循环。

###**Datapath**

datapath.serve函数是socket通信收发逻辑的入口。该函数启动了一个绿色线程去处理发送循环，然后本线程负责接收循环的处理。self.\_send\_loop是发送主循环。其主要逻辑为：不断获取发送队列是否有数据，若有，则发送；底层调用的是socket.send\_all（）函数, 逻辑比较简单，不加赘述。

```python
    def serve(self):
        send_thr = hub.spawn(self._send_loop)

        # send hello message immediately
        hello = self.ofproto_parser.OFPHello(self)
        self.send_msg(hello)

        try:
            self._recv_loop()
        finally:
            hub.kill(send_thr)
            hub.joinall([send_thr])
```

接收函数\_reck\_loop中实现了数据的接收和解析。 重点较多，解释作为代码注释，注释如下：

```python    
        @_deactivate
        def _recv_loop(self):
            buf = bytearray()   #初始化一个字节数组
            required_len = ofproto_common.OFP_HEADER_SIZE   # ofproto_common模块定义了OpenFlow常用的公共属性         
                                                            # 如报头长度=8
            count = 0
            while self.is_active:
                ret = self.socket.recv(required_len)
                if len(ret) == 0:
                    self.is_active = False
                    break
                buf += ret
                while len(buf) >= required_len:
                    # ofproto_parser是在Datapath实例的父类ProtocolDesc的属性。
                    # 用于寻找对应协议版本的解析文件,如ofproto_v1_0_parser.py
                    # header函数是解析报头的函数。定义在ofproto_parser.py。
                    (version, msg_type, msg_len, xid) = ofproto_parser.header(buf)
                    required_len = msg_len
                    if len(buf) < required_len:
                        break
                    # ofproto_parser.msg的定义并没有在对应的ofproto_parser中
                    # msg函数的位置和header函数位置一样，都在ofproto_parser.py中。
                    # msg返回的是解析完成的消息。
                    # msg函数返回了msg_parser函数的返回值
                    # ofproto_parser.py中的_MSG_PARSERS记录了不同版本对应的msg_parser。其注册手法是通过@ofproto_parser.register_msg_parser(ofproto.OFP_VERSION)装饰器。
                    # 在对应版本的ofproto_parser,如ofproto_v1_0_parser.py中，都有定义一个同名的_MSG_PARSERS字典，这个字典用于记录报文类型和解析函数的关系。此处命名不恰当，引入混淆。
                    # parser函数通过@register_parser来将函数注册/记录到_MSG_PARSERS字典中。
                    
                    msg = ofproto_parser.msg(self,
                                             version, msg_type, msg_len, xid, buf)
                    # LOG.debug('queue msg %s cls %s', msg, msg.__class__)
                    if msg:
                        # Ryu定义的Event system很简单，在报文名前加上前缀“Event”,即是事件的名称。
                        # 同时此类系带msg信息。
                        # 使用send_event_to_obserevrs()函数将事件分发给监听事件的handler，完成事件的分发。
                        ev = ofp_event.ofp_msg_to_ev(msg)
                        self.ofp_brick.send_event_to_observers(ev, self.state)
    
                        dispatchers = lambda x: x.callers[ev.__class__].dispatchers
                        # handler的注册是通过使用controller.handler.py文件下定义的set_ev_handler作为装饰器去注册。                
                        # self.ofp_brick在初始化时，由注册在服务列表中查找名为"ofp_event"的模块赋值。
                        # ofp_handler模块的名字为"ofp_event"，所以对应的模块是ofp_handler
                        handlers = [handler for handler in
                                    self.ofp_brick.get_handlers(ev) if
                                    self.state in dispatchers(handler)]
                        for handler in handlers:
                            handler(ev)
    
                    buf = buf[required_len:]
                    required_len = ofproto_common.OFP_HEADER_SIZE
    
                    # We need to schedule other greenlets. Otherwise, ryu
                    # can't accept new switches or handle the existing
                    # switches. The limit is arbitrary. We need the better
                    # approach in the future.
                    count += 1
                    if count > 2048:
                        count = 0
                        hub.sleep(0)
```

###**OpenFlow协议实现**

OpenFlow协议解析部分代码大部分在ofproto目录下，少部分在controller目录下。以下内容将首先介绍ofproto目录下的源码内容，再介绍controller目录下的ofp_event文件。

####**__init__**

首先，\_\_init\_\_.py并不为空。该文件定义了两个功能类似的函数get\_ofp\_module()和get\_ofp\_modules()，前者用于取得协议版本对应的协议定义文件和协议解析模块，后者则取出整个字典。对应的字典在ofproto\_protocol模块中定义。

####**ofproto\_protocol**

在ofproto\_protocol定义了\_versions字典，具体如下：

```python
    _versions = {
        ofproto_v1_0.OFP_VERSION: (ofproto_v1_0, ofproto_v1_0_parser),
        ofproto_v1_2.OFP_VERSION: (ofproto_v1_2, ofproto_v1_2_parser),
        ofproto_v1_3.OFP_VERSION: (ofproto_v1_3, ofproto_v1_3_parser),
        ofproto_v1_4.OFP_VERSION: (ofproto_v1_4, ofproto_v1_4_parser),
    }
```

除此之外，该文件还定义了Datapath的父类ProtocolDesc，此类基本上只完成了与协议版本相关的内容。该类最重要的两个成员是self.ofproto和self.ofproto\_parser，其值指明所本次通信所使用的OpenFlow协议的版本以及对应的解析模块。

####**ofproto\_common**

ofproto\_common文件比较简单，主要定义了OpenFlow需要使用的公共属性，如监听端口，报头长度，报头封装格式等内容。

####**ofproto\_parser**

ofproto\_parser文件定义了所有版本都需要的解析相关的公共属性。如定义了最重要的基类MsgBase(StringifyMixin)。
StringifyMixin类的定义在lib.stringify文件，有兴趣的读者可自行查看。MsgBase基类定义了最基础的属性信息，具体如下所示：

```python
    @create_list_of_base_attributes
    def __init__(self, datapath):
        super(MsgBase, self).__init__()
        self.datapath = datapath
        self.version = None
        self.msg_type = None
        self.msg_len = None
        self.xid = None
        self.buf = None
```

此外，该类还定义了基础的parser函数和serialize函数。基础的parser函数基本什么都没有做，仅返回一个赋值后的消息体。

```python
    @classmethod
    def parser(cls, datapath, version, msg_type, msg_len, xid, buf):
        msg_ = cls(datapath)
        msg_.set_headers(version, msg_type, msg_len, xid)
        msg_.set_buf(buf)
        return msg_
```

serialize函数分为3部分，self.\_serialize\_pre(), self.\_serialize\_body()和self.\_serialize\_header()。本质上完成了header的序列化。关于body的序列化，将在对应的派生类中得到重写。

####**ofproto_v1_0**

以1.0版本为例介绍ofproto\_v1\_x.py文件的作用。由于Ryu支持多版本的OpenFlow，所以在ofproto目录下，定义了从1.0到1.5版本的所有代码实现。所以其文件命名为ofproto\_v1_x.py，x从[1,2,3,4,5]中获得，分别对应相应的协议版本。

此类文件最重要的一个目的是定义了所有需要的静态内容，包括某字段的所有选项以及消息封装的格式以及长度。与OpenFlow消息内容相关的有协议的类型，动作的类型，port的类型等。此外对应每一个报文，都需要定义其封装的格式，以及封装的长度。Ryu采用了Python的Struct库去完成数据的解封装工作，关于Struct的介绍将在后续内容介绍。具体定义内容举例如下：

```python

    # enum ofp_port
    OFPP_MAX = 0xff00
    OFPP_IN_PORT = 0xfff8   # Send the packet out the input port. This
                            # virtual port must be explicitly used
                            # in order to send back out of the input
                            # port.
    OFPP_TABLE = 0xfff9     # Perform actions in flow table.
                            # NB: This can only be the destination
                            # port for packet-out messages.
    OFPP_NORMAL = 0xfffa    # Process with normal L2/L3 switching.
    OFPP_FLOOD = 0xfffb     # All physical ports except input port and
                            # those disabled by STP.
    OFPP_ALL = 0xfffc       # All physical ports except input port.
    OFPP_CONTROLLER = 0xfffd        # Send to controller.
    OFPP_LOCAL = 0xfffe     # Local openflow "port".
    OFPP_NONE = 0xffff      # Not associated with a physical port.


    # enum ofp_type
    OFPT_HELLO = 0  # Symmetric message
    OFPT_ERROR = 1  # Symmetric message
    OFPT_ECHO_REQUEST = 2   # Symmetric message
    OFPT_ECHO_REPLY = 3     # Symmetric message
    OFPT_VENDOR = 4         # Symmetric message
    OFPT_FEATURES_REQUEST = 5       # Controller/switch message
    OFPT_FEATURES_REPLY = 6         # Controller/switch message
    OFPT_GET_CONFIG_REQUEST = 7     # Controller/switch message
    OFPT_GET_CONFIG_REPLY = 8       # Controller/switch message
    OFPT_SET_CONFIG = 9      # Controller/switch message
    OFPT_PACKET_IN = 10      # Async message
    OFPT_FLOW_REMOVED = 11   # Async message
    OFPT_PORT_STATUS = 12    # Async message
    OFPT_PACKET_OUT = 13     # Controller/switch message
    OFPT_FLOW_MOD = 14       # Controller/switch message
    OFPT_PORT_MOD = 15       # Controller/switch message
    OFPT_STATS_REQUEST = 16  # Controller/switch message
    OFPT_STATS_REPLY = 17    # Controller/switch message
    OFPT_BARRIER_REQUEST = 18       # Controller/switch message
    OFPT_BARRIER_REPLY = 19  # Controller/switch message
    OFPT_QUEUE_GET_CONFIG_REQUEST = 20      # Controller/switch message
    OFPT_QUEUE_GET_CONFIG_REPLY = 21        # Controller/switch message

    OFP_HEADER_PACK_STR = '!BBHI'
    OFP_HEADER_SIZE = 8
    OFP_MSG_SIZE_MAX = 65535
    assert calcsize(OFP_HEADER_PACK_STR) == OFP_HEADER_SIZE

```


OFP\_HEADER\_PACK\_STR = '!BBHI'的意思是将header按照8|8|16|32的长度封装成对应的数值。在Python中分别对应的是1个字节的integer|一个字节的integer|2个字节的integer|4个字节的integer。

calcsize函数用于计算对应的format的长度。

其他内容均为静态的定义，无需赘述。

####**ofproto_v1_0_parser**

本模块用于定义报文的解析等动态内容。模块中定义了与OpenFlow协议对应的Common\_struct及message type对应的类。每一个message对应的类都是有MsgBase派生的，其继承了父类的parser函数和serialize函数。若报文无消息体，如Hello报文，则无需重写parser和serialize函数。

本模块定义了几个重要的全局函数：\_set\_msg\_type，\_register\_parser，msg\_parser和\_set\_msg\_reply。其作用介绍如下：

* \_set\_msg\_type: 完成类与ofproto模块中定义的报文名字的映射，原因在于ofproto模块定义的名字并不是类名，而解析时需要使用ofproto中的名字。
* \_register\_parser：完成对应的类与类中的parser函数的映射，当解析函数从ofproto模块的名字映射到类之后，若需要解析，则需从类对应到对应的解析函数。parser函数是一个类函数，所以在使用时必须传入对应的类的对象作为参数。
* msg\_parser：从\_MSG\_PARSERS中获取对msg\_type的parser，并返回解析之后的内容。
* \_set\_msg\_reply：完成该类与对应的回应报文的映射。

源码如下：

```python
    def _set_msg_type(msg_type):
        '''Annotate corresponding OFP message type'''
        def _set_cls_msg_type(cls):
            cls.cls_msg_type = msg_type
            return cls
        return _set_cls_msg_type
    
    
    def _register_parser(cls):
        '''class decorator to register msg parser'''
        assert cls.cls_msg_type is not None
        assert cls.cls_msg_type not in _MSG_PARSERS
        _MSG_PARSERS[cls.cls_msg_type] = cls.parser
        return cls
    
    
    @ofproto_parser.register_msg_parser(ofproto.OFP_VERSION)
    def msg_parser(datapath, version, msg_type, msg_len, xid, buf):
        parser = _MSG_PARSERS.get(msg_type)
        return parser(datapath, version, msg_type, msg_len, xid, buf)
    
    
    def _set_msg_reply(msg_reply):
        '''Annotate OFP reply message class'''
        def _set_cls_msg_reply(cls):
            cls.cls_msg_reply = msg_reply
            return cls
        return _set_cls_msg_reply
```

报文如果有消息体，则需要重写parser函数或者serialize函数，具体根据报文内容而不一样。此处，分别以Packet\_in和Flow\_mod作为parser的案例和serialize的案例，示例如下：

```python
    @_register_parser
    @_set_msg_type(ofproto.OFPT_PACKET_IN)
    class OFPPacketIn(MsgBase):
        def __init__(self, datapath, buffer_id=None, total_len=None, in_port=None,
                     reason=None, data=None):
            super(OFPPacketIn, self).__init__(datapath)
            self.buffer_id = buffer_id
            self.total_len = total_len
            self.in_port = in_port
            self.reason = reason
            self.data = data
    
        @classmethod
        def parser(cls, datapath, version, msg_type, msg_len, xid, buf):
            # 解析头部，获取msg
            msg = super(OFPPacketIn, cls).parser(datapath, version, msg_type,
                                                 msg_len, xid, buf)
            # 解析body,获取packet_in相关字段。
            (msg.buffer_id,
             msg.total_len,
             msg.in_port,
             msg.reason) = struct.unpack_from(
                ofproto.OFP_PACKET_IN_PACK_STR,
                msg.buf, ofproto.OFP_HEADER_SIZE)
            # 将ofproto.OFP_PACKET_IN_SIZE长度之外的buf内容，赋值给data
            msg.data = msg.buf[ofproto.OFP_PACKET_IN_SIZE:]
            if msg.total_len < len(msg.data):
                # discard padding for 8-byte alignment of OFP packet
                msg.data = msg.data[:msg.total_len]
            return msg


    @_set_msg_type(ofproto.OFPT_FLOW_MOD)
    class OFPFlowMod(MsgBase):
        def __init__(self, datapath, match, cookie, command,
                     idle_timeout=0, hard_timeout=0,
                     priority=ofproto.OFP_DEFAULT_PRIORITY,
                     buffer_id=0xffffffff, out_port=ofproto.OFPP_NONE,
                     flags=0, actions=None):
            if actions is None:
                actions = []
            super(OFPFlowMod, self).__init__(datapath)
            self.match = match
            self.cookie = cookie
            self.command = command
            self.idle_timeout = idle_timeout
            self.hard_timeout = hard_timeout
            self.priority = priority
            self.buffer_id = buffer_id
            self.out_port = out_port
            self.flags = flags
            self.actions = actions
    
        def _serialize_body(self):
            offset = ofproto.OFP_HEADER_SIZE
            self.match.serialize(self.buf, offset)
            # 封装的起点是offset
            offset += ofproto.OFP_MATCH_SIZE
            # 按照ofproto.OFP_FLOW_MOD_PACK_STR0的格式，将对应的字段封装到self.buf中
            msg_pack_into(ofproto.OFP_FLOW_MOD_PACK_STR0, self.buf, offset,
                          self.cookie, self.command,
                          self.idle_timeout, self.hard_timeout,
                          self.priority, self.buffer_id, self.out_port,
                          self.flags)
    
            offset = ofproto.OFP_FLOW_MOD_SIZE
            if self.actions is not None:
                for a in self.actions:
                    # 序列化action
                    a.serialize(self.buf, offset)
                    offset += a.len
```

此模块代码量大，包括OpenFlow协议对应版本内容的完全描述。分类上可分为解析和序列化封装两个重点内容。读者在阅读源码时可根据需求阅读片段即可。

####**Inet & ether**

这两个模块非常简单，ether定义了常用的以太网的协议类型及其对应的代码；inet定义了IP协议族中不同协议的端口号，如TCP=6。

####**oxm_field**

在1.3等高版本OpenFlow中，使用到了oxm\_field的概念。oxm全称为OpenFlow Extensible Match。当OpenFlow逐渐发展成熟，flow的match域越来越多。然而很多通信场景下使用到的匹配字段很少，甚至只有一个。OXM是一种TLV格式，使用OXM可以在下发流表时仅携带使用到的match域内容，而放弃剩余的大量的match域。当使用的match域较少时，统计概率上会减少报文传输的字节数。

####**nx_match**

该文件定义了nicira extensible match的相关内容。

###**ofp_event**

这个模块的位置并不再ofproto，而位于controller目录下。controller模块下的event定义了基础的事件基类。ofp\_event模块完成了OpenFlow报文到event的生成过程。模块中定义了EventOFPMsgBase(event.EventBase)类和\_ofp\_msg\_name\_to\_ev\_name(msg\_name)等函数的定义。相关函数都非常的简单，可从函数名了解到其功能，不再赘述。示例代码如下：

```python
    def _ofp_msg_name_to_ev_name(msg_name):
        return 'Event' + msg_name

```

文件中最后一句代码很重要，最后一句完成了服务的注册，告知app_manager,本模块需要以来于服务：ofp\_handler,即需要启动ofp\_handler才能完成本模块的工作。

```python
    handler.register_service('ryu.controller.ofp_handler')
```

###**Struct lib**

Python的[struct](https://docs.python.org/2/library/struct.html)库是一个简单的，高效的数据封装\解封装的库。该库主要包含5个函数，介绍如下：

* struct.pack(fmt, v1, v2, ...)： 将V1,V2等值按照对应的fmt(format)进行封装。
* struct.pack_into(fmt, buffer, offset, v1, v2, ...)：将V1,V2等值按照对应的fmt(format)封装到buffer中，从初始位置offset开始。
* struct.unpack(fmt, string): 将string按照fmt的格式解封
* struct.unpack_from(fmt, buffer[offset=0，])： 按照fmt的格式，从offset开始将buffer解封。
* struct.calcsize(fmt)： 计算对应的fmt的长度。

更家详细的封装语法，请查看struct对应的链接。此处仅对常用语法进行介绍：

* ！：大端存储
* c: char
* B： 一个字节长度，unsigned char.
* H：两个字节，16位
* I： 4个字节，int型
* Q: 64bits
* x: padding
* 3x：3个字节的padding
* 5s: 5字节的字符串


###**总结**

Ryu对OpenFlow协议的支持非常好，入门也比较容易，网上的资源也比较多，是一个非常值得推荐的SDN控制器。本篇对Ryu中从底层的数据收发到OpenFlow报文的解析的代码进行简要的分析，希望对读者有一定的帮助。

