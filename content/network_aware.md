title:SDN网络感知服务与最短路径应用
tags:SDN,ryu, network_aware
date:2015/7/8
category:Tech

本文将介绍RYU中的网络感知服务，与基于网络服务的最短路径应用，主要内容包括网络资源感知模块，网络监控模块和基于网络信息的最短路由模块介绍。在一个真实的网络环境下，需掌握网络的实时动态，包括网络的资源以及网络流量状况，其中网络的信息包括交换机，端口，主机的信息，以及基于流的流量统计信息和基于端口的流量统计信息。在掌握这些关键的网络信息后，控制器就可以根据这些信息作出当下最正确的路由决策，完成网络的通信。

###网络资源感知

网络资源感知模块用于感知网络资源的实时变化，包括拓扑信息以及主机信息的变化。任何网络应用，可达性都是最基本的要求。SDN网络的集中控制，使得控制器可以根据全局的信息作出最佳决策而无需在交换节点上采用分布式的路由算法。所以感知网络资源是SDN应用最基础的一项服务。网络资源感知模块源码链接：[network_aware](https://github.com/muzixing/ryu/blob/master/ryu/app/network_aware/network_aware.py).

实现该模块的类为Network\_Aware类，该类描述如下：

```python
    class Network_Aware(app_manager.RyuApp):
        OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
        _NAME = 'network_aware'
    
        def __init__(self, *args, **kwargs):
            super(Network_Aware, self).__init__(*args, **kwargs)
            self.name = "Network_Aware"
            self.topology_api_app = self
    
            # links   :(src_dpid,dst_dpid)->(src_port,dst_port)
            self.link_to_port = {}
    
            # {(sw,port) :[host1_ip,host2_ip,host3_ip,host4_ip]}
            self.access_table = {}
    
            # ports
            self.switch_port_table = {}  # dpid->port_num
    
            # dpid->port_num (outer ports)
            self.access_ports = {}
    
            # dpid->port_num(interior ports)
            self.interior_ports = {}
            self.graph = {}
    
            self.pre_link_to_port = {}
            self.pre_graph = {}
            self.pre_access_table = {}
    
            self.discover_thread = hub.spawn(self._discover)
```

其中数据结构与其作用关系如下：

* link\_to\_port字典存储交换机之间链路与端口的映射关系；
* access\_table字典存储主机的接入信息；
* switch\_port\_table存储交换机端口列表；
* access_ports存储外向端口（与终端连接的接口）；
* interior\_ports存储内部端口;
* grap存储网络拓扑图；
* pre\_link\_to\_port等带有pre前缀的数据结构用于保存上一次获取的信息，用于和当前获取信息做比较。
* \_discover函数是主循环函数

在\_discover函数中，周期执行get\_topology和是show\_topology函数。在get\_topology函数中，控制器可以获取到网络中的交换机和端口信息、链路信息、主机接入信息等。此外，控制器通过实时检测网络变化的异步事件来更新网络资源信息。show\_topology函数则是将网络信息格式化地展示在终端中。由于前端开发能力有限，目前仅仅简单将后台数据展现在终端。

Note that:可以通过置位IS_UPDATE来控制是否输出信息。此外，若拓扑信息不发生变化，将不打印，即仅打印拓扑一次，直至拓扑更新。可以将判断中的and 修改为or,即可每次都打印。

<center>![network info](http://ww2.sinaimg.cn/mw690/7f593341jw1etvgswsahwj20k30ddtcl.jpg)</center>
<center>图1.网络资源信息</center>

###网络流量监控

网络的信息除了物理资源信息以外，还包括逻辑链路等信息；获取流表信息可获得对应的逻辑连接信息。此外，获取网络的数据流量的统计情况对防止网络故障，合理优化网络等方面起到了重要的作用。网络流量监控模块实现了对端口流量和流表项流量的监控。应用可周期获取到流量信息，并在终端中输出展示。源码链接：[Network_Monitor](https://github.com/muzixing/ryu/blob/master/ryu/app/network_aware/network_aware.py)

实现网络流量监控的类为：Network_Monitor,具体描述如下：

```python
    class Network_Monitor(app_manager.RyuApp):
        OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
        _NAME = 'Network_Monitor'
    
        def __init__(self, *args, **kwargs):
            super(Network_Monitor, self).__init__(*args, **kwargs)
    
            self.datapaths = {}
            self.port_stats = {}
            self.port_speed = {}
            self.flow_stats = {}
            self.flow_speed = {}
            # {"port":{dpid:{port:body,..},..},"flow":{dpid:body,..}
            self.stats = {}
            self.port_link = {}  # {dpid:{port_no:(config,state,cur),..},..}
            self.monitor_thread = hub.spawn(self._monitor)
```

其中数据结构的作用如下：

* datapaths记录与控制器连接的datapath;
* port_stats保存端口的统计信息；
* port_speed保存端口的速率信息；
* flow_stats保存流的统计信息；
* flow_speed保存流的速率信息；
* stats保存所有的统计信息；
* port\_link保存link的特性信息；
* \_monitor函数为主循环函数；

在主循环函数中，周期调用了self.\_request\_stats和self.show\_stat函数，前者用于下发统计信息请求报文，后者用于展现统计信息。统计信息回复报文处理函数为：\_flow\_stats\_reply\_handler和\_port\_stats\_reply\_handler，两者分别使用的@set\_ev\_cls装饰符，注册监听了对应的事件。至此流量统计模块已经完成了闭环，可以作为底层的服务为上层的应用提供实时的流量统计信息。

<center>![port stats](http://ww1.sinaimg.cn/mw690/7f593341jw1etvgsxtlpfj21040f5thy.jpg)</center>
<center>图2. 端口流量统计信息</center>


<center>![flow stats](http://ww2.sinaimg.cn/mw690/7f593341jw1etvgsx513ij20mt0ctgs9.jpg)</center>
<center>图3. 流表项流量统计信息</center>

###基于网络资源的最短路径

基于以上的网络资源感知模块与网络流量监控模块提供的数据，我们可以做很多事情，比如负载均衡等流量调度应用，有比如安全接入等安全应用。本小节介绍基于网络资源的最短路径应用。衡量最短路径的参考系是跳数，稍加修改可以变为剩余带宽，延时或者多参考系加权的方案。源代码链接：[shortest_route](https://github.com/muzixing/ryu/blob/master/ryu/app/network_aware/shortest_route.py)

最短路径应用流程图如下：
<center>![shortest path](http://ww3.sinaimg.cn/mw690/7f593341jw1etvhwx97yjj20870dxq31.jpg)</center>
<center>图4, 最短路由流程图</center>

首先，查询主机表，若查找成功，则查询主机位置表，之后直接由控制器将ARP数据包发送给对应的端口，此时控制器并不做ARP的代理。当目标主机回复ARP时，将数据包直接发送到源主机的接入端口。从而完成了ARP的学习过程。由于此时已经掌握了主机的接入信息以及网络信息，当ICMP或其他数据包出发packet\_in事件时，则可根据源目两个IP查询到接入交换机，再依据拓扑信息，计算最短路径，从而完成最短路由。若希望使用其他的参考标准来计算最短路径，只需修改计算最短路径的算法即可。

在网络初始化时，控制器并没有办法发现沉默的主机，原因在于我们没有进行DHCP分配，导致控制器没有掌握主机的IP/MAC信息。所以第一步我们需要处理的数据包是ARP。处理流程具体如下所示：

<center>![arp_handler](http://ww4.sinaimg.cn/mw690/7f593341jw1etvhwx229pj209y0aujri.jpg)</center>
<center>图5. ARP处理流程图</center>



**Note that**:本应用假设主机发起通信时需先发起ARP，不可通过其他途径获取到ARP的信息，否则控制器无法获得目的端主机接入信息，则无法完成路由。对于域外的主机，只需在找不到目的端时，将其送给出口网关即可。此时需使用到子网掩码，网段，路由等概念。本应用仅针对简单局域网计算路径。

<center>![shortest path](http://ww3.sinaimg.cn/mw690/7f593341jw1etvgsxenqtj20gy0cradi.jpg)</center>
<center>图6. 流表项流量统计信息</center>

###总结

网络感知服务对于SDN网络而言非常重要，是一切网络应用的基础。充分利用网络资源的信息，可以对网络进行优化，提高网络的安全性。以上的Network\_aware和monitor模块均可以直接做为APP的service app（在RYU中需在\_CONTEXTS添加）提供数据服务，希望可以给有需要的读者提供一些帮助。











