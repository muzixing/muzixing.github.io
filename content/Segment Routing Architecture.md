title: Segment Routing架构介绍
date: 2018/10/26
tags: SR, Segment Routing, SR-MPLS, SRv6
category: Tech

### 前言

从第一次接触到Segment Routing（SR），到现在专注与Segment Routing的研究和标准化，了解越来越深入，也越来越清楚SR将成为网络的发展趋势。在SR架构文稿成为[RFC8402](https://tools.ietf.org/html/rfc8402)的这一刻，没有什么比写一篇介绍SR架构的文章更好的选择了。

### 背景 
Segment Routing的诞生背景和SDN紧密相关。在SDN出现早起，SDN几乎和OpenFlow密不可分。但在商业上，OpenFlow这样极具革命性创新的新协议很难被传统设备商所接受，也影响了巨头们的利益。在技术上，OpenFlow网络中每个节点都要维持网络状态，当网络规模变大，业务变多，网络管理和运维就变得复杂，网络的可扩展性就受到了限制。为了面对OpenFlow的挑战，Cisco提出了Segment Routing(SR)，一种可以在Ingress节点指明数据包转发路径的源路由机制。

总体来看，SR主要有如下的特征（包括但不限于）

* 支持源路由，支持在源节点显示指定转发路径
* SR只在Ingress节点保持Per-flow的状态，中间网络节点无需维护Per-flow的网络状态，只需无状态转发即可，因此SR具有很好的可扩展性。
* SR无需在节点之间采用任何信令协议，不要求增加任何新的网络协议，减少网络信令协议的使用。
* SR可以部署在MPLS和IPv6两种数据平面。

### Segment Routing Architecture

Segment Routing (SR)是一种源路由机制。SR支持在源节点往数据报文中插入一组有序的操作指令来显示地指定数据包的转发路径和处理流程。这个操作指令称之为“Segment”。一个Segment可以是具有拓扑意义的，比如代表一个节点或者一条链路，也可以是基于服务的，比如描述一个service。 

一个Segment可以是本地意义的，也可以是全局意义的。比如描述一个指向一个邻接的链路，或者描述一个全局的节点或者网段。 

基于SR，可以实现数据流的显示路径转发，而且只需在Ingress节点维持Per-flow的状态而无需在中间节点或尾节点来维持per-flow的状态。相比RSVP-TE MPLS需要在所有节点维持Per-flow的状态，SR大大节省了网络的状态维护难度，从而简化了网络，也提升了网络的可扩展性。

当下的SR架构可以部署在两种数据平面上：

**MPLS**：

部署在MPLS数据平面上的SR，标准上习惯称之为SR-MPLS，当然也有人喜欢叫MPLS-SR。其可以直接基于现有的MPLS数据平面部署，无需对数据平面进行任何改动。这意味着，从RSVP-TE MPLS到SR-MPLS的改动只需对控制平面进行升级，使得网络可以更平滑地存量演进。在SR-MPLS中，一个Segment表现为一个MPLS Label（标签）。

![SR-MPLS](http://wx3.sinaimg.cn/mw690/7f593341ly1fwlyjl3qa1j21kw0ttdnf.jpg)

[Ref:Huawei Document:IPv4 Segment Routing](http://support.huawei.com/enterprise/zh/doc/DOC1000173014?section=j004)

Segment／Label可能是具有全局意义的，也可能是具有本地意义的。在SR-MPLS中，每一个节点会配置对应本地标签块SRLB（Segment Routing Local Block）和SRGB（Segment Routing Global Block)。从SRLB中的标签值具有本地意义，从SRGB中的标签值具有全局意义。

为了满足MPLS标签资源本地化，同时又要满足SR全局标签的需求，SRGB是节点的配置信息，不强制全网统一，但在实际部署时，为方便起见，一般是统一的。

比如节点A的SRGB为1000-2000，节点B的SRGB为3000-4000。节点A的Node-SID为1，B的Node-SID为2，那么节点A在发布自己的节点SID时，可以选择发布绝对值1001，也可以发布index为1。其他节点会依据节点A发布的SRGB（1000-2000）来计算转发到该节点时，应该使用标签1001。而一个全网路由的Node-SID 1在转发到B节点时，标签值就是其SRGB下限3000+1=3001。从而保证了标签均为本地意义，但同时又提供了全局路由的能力。

当SRGB均一样时，就容易理解地多。比如SRGB均为1000-2000。那么无论转发到A节点还是B节点，标签值均为1001。

一组有序的Segment，称之为Segment list，在SR-MPLS网络呈现为一个MPLS标签栈。需要被处理的标签为栈顶的标签。被处理完的标签，将会被弹出。所以随着数据包在MPLS网络中转发，标签栈中的标签会不断弹出，直到最后弹完。数据包的转发动作，则有标签指定，其转发行为同RSVP-TE MPLS网络。

更多标签操作，如PUSH，NEXT，CONTINUE等基础知识可以参考[draft-ietf-spring-segment-routing-mpls-15](https://tools.ietf.org/html/draft-ietf-spring-segment-routing-mpls-15)。



**SRv6**

SR架构也可以应用在IPv6网络中，称为SRv6(Segment Roouting over IPv6)[draft-ietf-6man-segment-routing-header-15](https://tools.ietf.org/html/draft-ietf-6man-segment-routing-header-15)。

在SRv6中，一个Segment表现为一个128 bit的IPv6地址。一个Segment list就表现为插入在SRH中的一组有序的IPv6地址列表。但并不是所有的IPv6地址都是SID，其需要被声明为SID。此外，SID可以是节点的地址或者接口的地址，但大部分情况下是独立声明的SID。

为了支持SRv6，需要扩展一种新的IPv6 Routing Header: Segment Routing Header(SRH)，格式如下图：

![SRH](http://wx2.sinaimg.cn/mw690/7f593341ly1fwlyfgeo1oj20vk0nswgi.jpg)

关于SRH的内容后续文章会继续介绍。

### Link-State IGP Segments 

描述Segment的ID称为Segment ID，缩写为SID。在不同的数据平面，SID的表现形式不同。在MPLS数据平面，SID表现为一个MPLS标签，而在IPv6数据平面里，SID表现为一个128bit的值，其可以是节点的一个接口地址，也可以不是。

SR的控制平面在Ingress节点根据[SR Policy](https://tools.ietf.org/html/draft-ietf-spring-segment-routing-policy-02)给数据包插入Segment List，显示指定数据包的转发路径(松散路径或者严格路径，后面介绍)，以及在指定节点的操作。节点需要根据数据包中的指令来处理和转发数据包。

SR控制平面可以是分布式的，也可以是集中式的。在分布式的情况下，需要通过扩展IGP（IS-IS／OSPF）或BGP等路由协议来支持SR。

### IGP SID

本小节将简要介绍SR中重要的几类SID。

#### Node-SID

节点SID, 用于表示一个SR节点。
SR-MPLS：FEC 10.8.8.3对应的／绑定的SID可以是一个MPLS标签，值为1003。
SRv6: IPv6地址A::1/128本身就可以发布成SID。

#### Prefix-SID
用于描述网段的SID。
SR-MPLS：网段10.8/16的SID可以是标签1001。
SRv6：网段A::/48的SID就是A::/48。

#### Adjacency-SID

用于描述邻接的SID，描述指向邻接的某条链路或集合。用于指定数据包发向指定链路，可用于严格路径的SR-TE。

SR-MPLS: 从SRLB中取出的某本地标签值，比如9001。
SRv6: 可以是某一个节点的接口的IPv6地址。比如A::C6。

#### Binding-SID

绑定SID。可用于映射SID List。比如SID值100为一个Binding-SID，其映射的SID list为[2001,2003,2005]。那么为了缩短SID list，可以采用插入Binding SID的方式来取代[2001,2003,2005]。一般可用于标签粘连和和[SR Policy](https://tools.ietf.org/html/draft-ietf-spring-segment-routing-policy-02)场景。

SR-MPLS: 从SRLB中取出的某本地标签值，比如9002。
SRv6: 发布成SID的某一个IPv6地址，比如A::C6。

#### Path SID

[Path SID](https://tools.ietf.org/html/draft-cheng-spring-mpls-path-segment-03)用于标识SR网络中的路径。其出现的原因主要是因为在SR-MPLS中，标签会不断被弹出，当数据包到达Egress节点时，节点无法识别数据包来自哪一条路径，所以需要一个Path SID来标识。

而在SRv6网络中，使用SID List来描述一条路径过于复杂，所以[SRv6 Path Segment](https://tools.ietf.org/html/draft-li-spring-srv6-path-segment-00)也被提出来了。


### SR-MPLS
后续文章会介绍SR-MPLS。可参考[draft-ietf-spring-segment-routing-mpls-15](https://tools.ietf.org/html/draft-ietf-spring-segment-routing-mpls-15)。

### SRv6
后续文章会介绍SRv6。可参考[draft-ietf-6man-segment-routing-header-15](https://tools.ietf.org/html/draft-ietf-6man-segment-routing-header-15)。

#### SRv6 NP

后续文章会介绍SRv6 Network Programming。可参考[draft-filsfils-spring-srv6-network-programming-06](https://tools.ietf.org/html/draft-filsfils-spring-srv6-network-programming-06)。

### SR Use Cases

更多Use cases后续可能会有文稿介绍，建议读者直接阅读ietf标准草案。

* SFC
* SR TE
* 网络编程
* E2E SRv6

###总结

关于Segment Routing的更多学习，后续会有更多文章介绍。读者可前往[SPRING WG](https://tools.ietf.org/wg/spring)阅读进一步内容。也可以下载[华为的技术文档](http://support.huawei.com/enterprise/zh/doc/DOC1000173014?section=j004)或者[搜索华为技术文档](http://e.huawei.com/enterprisesearch/?lang=zh#keyword=segment+routing&lang=zh&site=1&type=ALL)。

PS：本文章为个人学习总结，不涉及任何商业信息。


