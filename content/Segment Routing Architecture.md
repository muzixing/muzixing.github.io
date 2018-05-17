title: Segment Routing架构介绍
date: 2018/8/15
tags: SR, Segment Routing, SR-MPLS, SRv6
category: Tech


### 前言

从第一次接触到Segment Routing（SR），到现在专注与Segment Routing的研究和标准化，了解越来越深入，也越来越清楚SR将成为网络的发展趋势。在SR架构文稿成为[RFC8402](https://tools.ietf.org/html/rfc8402)的这一刻，没有什么比写一篇介绍SR架构的文章更好的选择了。

### Segment Routing Architecture
   
Segment Routing (SR)是一种源路由机制。SR支持在源节点往数据报文中插入一组有序的操作指令来显示地指定数据包的转发路径和处理流程。这个操作指令称之为“Segment”。一个Segment可以是具有拓扑意义的，比如代表一个节点或者一条链路，也可以是基于服务的，比如描述一个service。 

一个segment可以是本地意义的，也可以是全局意义的。比如描述一个指向一个邻接的链路，或者描述一个全局的节点或者网段。 

基于SR，可以实现数据流的显示路径转发，而且只需在Ingress节点维持per-flow的状态而无需在中间节点或尾节点来维持per-flow的状态。相比RSVP-TE MPLS需要在所有节点维持per-flow的状态，SR大大节省了网络的状态维护难度，从而简化了网络，也提升了网络的可扩展性。

当下的SR架构可以部署在两种数据平面上：

**MPLS**：

部署在MPLS数据平面上的SR，标准上习惯称之为SR-MPLS，当然也有人喜欢叫MPLS-SR。其可以直接基于现有的MPLS数据平面部署，无需对数据平面进行任何改动。这意味着，从RSVP-TE MPLS到SR-MPLS的改动只需对控制平面进行升级，使得网络可以更平滑地存量演进。在SR-MPLS中，一个Segment表现为一个MPLS label（标签）。

一组有序的Segment，称之为Segment list呈现为一个MPLS标签栈。需要被处理的标签为栈顶的标签。被处理完的标签，将会被弹出。所以随着数据包在MPLS网络中转发，标签栈中的标签会不断弹出，直到最后弹完。数据包的转发动作，则有标签指定，其转发行为同RSVP-TE MPLS网络。

**SRv6**

SR架构也可以应用在IPv6网络中，只是还需要扩展一个IPv6 Routing Header: Segment Routing Header(SRH). 一个Segment表现为一个128 bit的IPv6地址。一个Segment list就表现为插入在SRH中的一组有序的IPv6列表。Active Segment就是IPv6地址中的目的地址对应的值（上一个被更新到DA的SID）。


Segment Routing的诞生背景和SDN紧密相关。在SDN出现早起，SDN几乎和OpenFlow密不可分。但在商业上，OpenFlow这样极具革命性创新的新协议很难被传统设备商所接受，也影响了巨头们的利益。在技术上，OpenFlow网络中每个节点都要维持网络状态，当网络规模变大，业务变多，网络管理和运维就变得复杂，网络的可扩展性就受到了限制。为了面对OpenFlow的挑战，Cisco提出了Segment Routing(SR),一种可以在ingress节点指明数据包转发路径的源路有机制。

SR典型图（TBD）

总体来看，SR主要有如下的特征（包括但不限于）

* 支持源路由，支持在源节点显示指定转发路径
* SR只在Ingress节点保持Per-flow的状态，中间网络节点无需维护Per-flow的网络状态，只需无状态转发即可，因此SR具有很好的可扩展性。
* SR无需在节点之间采用任何信令协议，不要求增加任何新的网络协议，减少网络信令协议的使用。
* SR可以部署在MPLS和IPv6两种数据平面。


### Link-State IGP Segments 

描述Segment的ID称为Segment ID，缩写为SID。在不同的数据平面，SID的表现形式不同。在MPLS数据平面，SID表现为一个MPLS标签，而在IPv6数据平面里，SID表现为一个128bit的值，其可以是节点的一个接口地址，也可以不是。

SR的控制平面在Ingress节点根据SR policy给数据包插入Segment list，显示指定数据包的转发路径(松散路径或者严格路径，后面介绍)，以及在指定节点的操作。节点需要根据数据包中的指令来处理和转发数据包。

SR控制平面可以是分布式的，也可以是集中式的。在分布式的情况下，需要通过扩展IGP（IS-IS／OSPF）来支持SR，

### IGP 
#### node-SID
TBD
#### Prefix-SID
TBD
#### Adjacency-SID
TBD
#### Binding-SID
TBD

### SR-MPLS
####四种sid的对应，mpls的介绍

SR-MPLS的文稿结构

### SRv6
#### SRv6的介绍
SRH

#### SRv6 NP
SID，functions


#### SRv6的流程
Locator 路由，SID发布，

### an

### SR的潜力

SR TE SR BE
SRv6，端到端解决方案，未来的网络架构

### SR use case

SFC，SR TE，网络编程。






###总结

PS：本文章为个人学习总结，不涉及任何商业信息。


