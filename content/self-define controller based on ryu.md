title:基于Ryu打造自定义控制器
date:2015/11/20
tags:Ryu
category:Tech

控制器是SDN网络中最重要的组成部分。在开发SDN应用时，需要基于某一个控制器开发，而大部分开源控制器都是一个框架或者平台，更多个性化的设置和应用需要开发者自己完成。对于开发者而言，一个自定义的控制器可以让控制器更加适配开发场景，发挥控制器最大的作用，提高开发效率。本篇文章将以Ryu为例，介绍如何修改Ryu源码，打造属于自己风格的自定义控制器。其内容包括自定义参数，事件，启动顺序，报文，协议和底层服务。

### 自定义参数

很多应用都会涉及相关参数的输入才能运行， 如OpenFlow协议的启动需要配置监听端口。在编写新应用时，需要获取相关参数的值来运行应用，所以需要开发应用时注册参数。目前已有的参数可以通过ryu-manager -h查看。而不同的应用注册的参数很可能名字一样，这就有可能发生冲突。为解决这个问题，Ryu采用了OpenStack的Oslo库，支持全局的命令注册和解析。Oslo支持全局的命令注册和解析，成功解除了命令冲突的难题，也大大降低了参数注册和解析的难度。注册新参数的方法很简单，只需要新建一个文件，然后按照如下案例完成注册，最后再在cmd/manager.py中import即可。

```py
from ryu import cfg

CONF = cfg.CONF
CONF.register_cli_opts([
    cfg.StrOpt(
        'milestone-argument', default='', help='my test argument'),
    cfg.IntOpt('milestone-server-port', default=6666,
               help='milestone server port')])
    

```
```py
from ryu import flags
from ryu import version
from ryu.app import wsgi
from ryu.base.app_manager import AppManager
from ryu.controller import controller
from ryu.milestone import milestone
from ryu.topology import switches
```

通过python setup.py install重新安装Ryu之后即可通过ryu-manager -h来查看到新注册的命令。

### 自定义事件

Ryu的应用之间通信通过事件机制来完成。比如底层的协议解析模块解析报文之后，生成对应的报文事件，然后分发到各个监听该事件的监听函数。不过，目前为止事件类型还不够丰富，很多需要的信息还无法通过事件传递。比如网络流量监控服务监控到流量发生变化的事件之后，需要生成对应的事件。又比如OFPPacket\_in事件包含了所有报文类型的数据，还可以根据触发Packet\_in的数据的协议类型来定义细粒度的事件去分流，从而使得处理ARP报文的函数只接收ARP报文的Packet\_in, 而不是全部接收到然后再去判断是否是不是ARP报文。以网络流量变化事件EventOXPTrafficStateChange为例，定义事件，生成事件和处理事件的流程如下：

(1) 在controller/ofp\_event.py中添加相关类描述：

```py
class EventOXPTrafficStateChange(event.EventBase):
    def __init__(self, traffic=None):
        super(EventOXPTrafficStateChange, self).__init__()
        self.traffic = traffic
```
(2) 在相关应用中实例化事件，并通过OFPHandler模块的send\_event\_to\_observers函数分发到指定函数。

```py
    event = oxp_event.EventOXPTrafficStateChange(traffic=self.free_band_width)
    self.oxp_brick = app_manager.lookup_service_brick('oxp_event')
    self.oxp_brick.send_event_to_observers(event, MAIN_DISPATCHER)
```

(3) 注册handler处理事件， 使用@set\_ev\_cls来注册handler监听该事件。

```py
@set_ev_cls(oxp_event.EventOXPTrafficStateChange, MAIN_DISPATCHER)
def reflesh_bw_best_path(self, ev):
    self.free_band_width = ev.traffic
    do_some_thing(self.free_band_width)

```

像Packet\_in分流的定义可以参考以上的做法，将事件作为新事件的属性。也可以参考ofp\_event模块中的修改类名的方式将类名修改，从而生成新的事件。

###自定义启动顺序

Ryu关于Application的启动源码在cmd/manager.py文件中。main函数中完成了app\_lists的赋值，即启动应用的顺序。若在Ryu开发了一个很重要的底层应用，需要在启动那个时启动，则可以将其加入app\_lists中. 比如当milestone参数为1时，启动多个应用，否则仅启动基础应用的示例如下：

```py
if not app_lists:
    app_lists = ['ryu.controller.ofp_handler']

if CONF.milestone == '1':
    my_app_list = ["muzixing", "milestone"]
    app_lists.extend(my_app_list)
```
这个自定义启动顺序一般情况下不需要修改，但是当开发的应用是非常重要的底层服务时，可能需要初始化就启动，所以也是非常关键的自定义内容之一。

###自定义报文

在某些特定的场景中，需要对OpenFlow协议等协议进行报文拓展，从而完成新报文，新字段的测试工作。在Ryu中自定义OpenFlow报文的操作步骤如下：

(1) 在对应版本的ofproto\_v1\_x.py中定义所有需要使用到的字段值，如最重要的报文类型，以定义一个名为milestone的报文为例，报文类型为25, 字段只有一个字符串类型的data, 可以用来放任何信息，长度为64bits。所以在文件中定义/声明 报文名字和类型的对应，报文的格式和长度，以便序列化和解析。Ryu使用struct对数据进行序列化和解析。

```py
OFPT_MILESTONE = 25
OFP_MILESTONE_PACK_STR = '!8s'  #定义报文格式
OFP_MILESTONE_SIZE = 16    # 定义报文长度
assert (calcsize(OFP_MILESTONE_PACK_STR) + OFP_HEADER_SIZE ==OFP_MILESTONE_SIZE）  # 检查长度是否正确

```

(2) 在对应版本的ofproto\_v1\_x\_parser.py中添加对应报文类的定义，包括其解析方法和序列化方法。其中解析方法是一个类方法，在MsgBase中定义，派生类调用时需要使用类型来区分。序列化方法分为self.\_serialize\_pre(), self.\_serialize\_body()和self.\_serialize\_header()三部分。派生类仅需完成self.\_serialize\_body()的内容即可。值得注意的是，如果需要对报文进行除报头以外的解析，则必须在完成parser函数之后使用@\_register\_parser装饰符将对应函数和类名的映射关系加入到关系字典中，以便使用时查找，否则会报错。

```py
@_register_parser
@_set_msg_type(ofproto.OFPT_MILESTONE)
class OFPMILESTONE(MsgBase):
    """
    MILESTONE message

    It is a test msg:www.muzixing.com
    ========== =========================================================
    Attribute  Description
    ========== =========================================================
    data       just some data.
    ========== =========================================================
    """
    def __init__(self, datapath, data=None):
        super(OFPMILESTONE, self).__init__(datapath)
        self.data = data

    @classmethod
    def parser(cls, datapath, version, msg_type, msg_len, xid, buf):
        msg = super(OFPMILESTONE, cls).parser(datapath, version, msg_type,
                                          msg_len, xid, buf)

        offset = ofproto.OFP_HELLO_HEADER_SIZE
        data = struct.unpack_from(ofproto.OFP_MILESTONE_PACK_STR, msg.buf, offset)

        msg.data = data
        return msg
        
    def _serialize_body(self):
        msg_pack_into(ofproto.OFP_MILESTONE_PACK_STR, self.buf,
                      ofproto.OFP_HEADER_SIZE, self.data)
```

至此，自定义报文完成。关于struct模块的使用，以及OpenFlow协议代码的介绍可以参考另一篇文章[《Ryu:OpenFlow协议源码分析》](http://www.muzixing.com/pages/2015/07/24/ryuopenflowxie-yi-yuan-ma-fen-xi.html)。重新安装Ryu即可将该报文写入到Ryu运行代码中，Ryu的事件机制会自动将这个报文生成对应的事件，进一步测试需要读者自行开发。

###自定义协议

既然讲到自定义报文，那么继续提一下自定义协议。读者可以根据[《Ryu:OpenFlow协议源码分析》](http://www.muzixing.com/pages/2015/07/24/ryuopenflowxie-yi-yuan-ma-fen-xi.html)提到的思路去模仿编写一个新的协议。底层的数据收发可以学习controller/controller.py, 协议定义可以学习ofproto目录下的一系列内容。各种需要自定义的细节，如自定义参数，自定义事件等都已经在上文提到。后续将会专门书写如何在Ryu中开发新协议，本文不再展开。

### 自定义服务

为了更好的开发应用，开发者应该开发一套底层的服务，为自己的进一步开发提供帮助。如ARP代理，DHCP服务，基础的网络资源感知服务等等。SDN集中式的优点很大在于拥有全局的视角，可以掌握全局的资源，从而进行全局最优的业务部署。所有业务的基础都基于对网络资源的感知，所以此处以网络资源感知为例。首先需要完成网络拓扑的最优路径的计算，此外处于某些场景的需求，需要收集网络流量状况的数据，从而完成基于流量的最优化决策。在此基础之上，完成基础的
最短路径转发应用，实现最基础的网络应用，为其他更高层次的应用开发和算法验证提供基本的服务支撑。由于篇幅限制，本文不加展开，详情可查看[《SDN网络感知服务与最短路径应用》](http://www.muzixing.com/pages/2015/07/08/sdnwang-luo-gan-zhi-fu-wu-yu-zui-duan-lu-jing-ying-yong.html)。如果读者希望自己搭建一套底层服务，或者在笔者的基础之上加工，推荐使用networkx进行拓扑信息的存储。networkx提供了大量高效有用的函数，可以最大程度降低开发者在算法问题上的工作量。

完成以上应用之后，可将其作为启动服务的一种，并通过参数来确定是否启动Ryu时启动这些业务。这些业务中涉及到的自定义事件，可用于与上层应用之间的通信，实现定制化的SDN控制器。

### 总结

本篇文章介绍了基于Ryu打造自定义控制器的内容，包括自定义参数，事件，启动顺序，报文，协议和服务。相信读者如果能根据应用场景进行深度自定义，可以很大程度上提升开发效率。关于自定义协议部分，后续会有更多文章介绍，敬请期待。


















