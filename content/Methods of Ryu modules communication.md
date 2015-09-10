title:Ryu:模块间通信机制分析
date:2015/9/8
tags:ryu
category:Tech

Ryu是一款非常轻便的SDN控制器，在科研方面得到了广泛的应用。相比其他控制器，受益于Python语言，在Ryu上开发SDN应用的效率要远高于其他控制器。为了解决复杂的业务，有时需要在Ryu上开发多模块来协同工作，从而共同完成复杂的业务。本文将介绍Ryu模块之间通信的包括Context等方式的多种通信方式。

###\_CONTEXTS

在RyuApp类中有一个属性是\_CONTEXTS。\_CONTEXTS中的内容将作为当前模块的服务在模块初始化时得到加载。示例如下：

```python
    _CONTEXTS = {
        "Network_Aware": network_aware.Network_Aware,
        "Network_Monitor": network_monitor.Network_Monitor,
    }
    
    def __init__(self, *args, **kwargs):
        super(Shortest_forwarding, self).__init__(*args, **kwargs)
        self.name = 'shortest_forwarding'
        self.network_aware = kwargs["Network_Aware"]
        self.network_monitor = kwargs["Network_Monitor"]
```

在模块启动时，首先会将\_CONTEXTS中的模块先启动，在模块的初始化函数中可以通过self.network_aware = kwargs["Network_Aware"]的形式获得该服务模块的实例，从而获取到该模块的数据，并具有完全的读写能力。这种模式很清晰地体现了模块之间的关系。然而在Ryu的实现中，这个机制并不完美，或者有所限制。首先，当某个模块作为别的模块的服务启动时，就无法在启动Ryu时手动启动。这种做法应该是出于保证模块启动顺序，从而顺利完成多模块启动而设计。另一方面，Ryu不支持多级的服务关系， 如A是B的服务，那么B就不能作为其他模块的服务，也即这种服务关系只有两层。所以在设计模块时，若完全使用\_CONTEXTS方式来传递信息则需将架构设计成两层以内。若希望不受此限制，开发者可以自己修改其源码解除这个限制。

###app\_manager.lookup\_service\_brick()


在某些业务场景，我们需要使用其他模块的数据，但是又不希望将对方作为自己的服务来加载，则可以通过app\_manager.lookup\_service\_brick('module name')来获取运行中的某个模块的实例，从而获取其数据。典型案例可以参考controller/controller.py中的Datapath类。示例如下：

```python
        self.ofp_brick = ryu.base.app_manager.lookup_service_brick('ofp_event')
        
        def set_state(self, state):
            self.state = state
            ev = ofp_event.EventOFPStateChange(self)
            ev.state = state
            self.ofp_brick.send_event_to_observers(ev, state)
```

这种做法区别于import, import引入的是静态的数据，如某个类的函数的定义，静态数据的定义。当涉及到动态的数据，import则无法获取到对应的数据。如名为app的模块中有一个属性self.domain = Domain(）,那么import可以获得其类的定义，而实际上，我们需要的是运行状态时Domain的实例，而import无法做到这一点。通过app = app\_manager.lookup\_service\_brick(‘app’)可以获得当前的app实例，进而通过app.domain来获取当前的domain实例的数据。

###Event

通过事件系统来通信是模块之间通信的最普通的形式。每当交换机和Ryu建立连接，都会实例化一个Datapath对象来处理这个连接。在Datapath对象中，会将接收到的数据解析成对应的报文，进而转化成对应的事件，然后发布。注册了对应事件的模块将收到事件，然后调用对应的handler处理事件。示例如下：

```python
    [module: controller]

    if msg:
        ev = ofp_event.ofp_msg_to_ev(msg)
        self.ofp_brick.send_event_to_observers(ev, self.state)

        dispatchers = lambda x: x.callers[ev.__class__].dispatchers
        handlers = [handler for handler in
                    self.ofp_brick.get_handlers(ev) if
                    self.state in dispatchers(handler)]
        for handler in handlers:
            handler(ev)

    [module:simple_switch_13.py]
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
```

编译运行之后，simple\_switch\_13模块的\_packet\_in\_handler函数注册了事件ofp\_event.EventOFPPacketIn, 当Controller模块中的Datapath分发ofp\_event.EventOFPPacketIn事件时， 将会分发到\_packet\_in\_handler函数，在Datapath中调用handler(ev)来处理事件，从而完成了信息在模块之间的通信。

###公共文件读写

除了以上的形式以外，某些数据的通信则通过读写公共文件完成。最典型的案例是oslo.config的使用。[oslo](https://wiki.openstack.org/wiki/Oslo)是OpenStack的开源库。oslo.config提供一个全局的配置文件，同时也完成命令行的解析。通过读写公共文件的内容，可以完成信息的传递，如模块A将config中CONF对象的某个参数arg的i值修改为1, B再读取对应的参数arg，则可以获得数值1, 从而完成通信。面对配置信息等全局信息时，公共文件的使用可以避免不同模块之间的冲突，从而实现全局数据的统一。但是这种做法会频繁地读写文件，效率不高。且此类数据仅适合静态数据的传递，不适合存在于实例中的动态数据。

###总结

在使用Ryu开发SDN网络应用的过程中，多模块协同工作是非常常见的场景。使用\_CONTEXTS形式可以更清晰地体现模块之间的关系，代码架构可读性更高；采用app\_manager.lookup\_service\_brick()形式可以得到运行的实例，可以达到\_CONTEXTS的效果，适用与仅需使用某模块某小部分功能集合，模块之间没有明显的服务关系的场景；Event是最普通的模块见通信，可以实现订阅发布模式的多模块协同工作场景，实现模块之间解偶；采用公共文件作为信息的中转站是最后的选择，效率比较低，适用于全局信息的传递。以上的几种方式是笔者在实验过程中总结的通信方式，若有错误指出，敬请指出，万分感谢。



