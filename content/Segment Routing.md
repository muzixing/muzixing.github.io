title: Segment Routing系列文章：To Write List
date: 2018/8/9
tags: SR, Segment Routing, SR-MPLS, SRv6
category: Tech

### 前言

人啊，总是懒惰的。

一懒惰，就是两年。

总是有太多理由，总是有太多借口。

但终究，还是无法再骗过自己了。

问过了领导，答复写互联网公开的，开源的内容没有问题。那就从我平时研究的Segment Routing开始写吧。为避免踩信息安全红线，还是要很郑重地声明：

**所有文章内容均为互联网公开资料和个人技术理解，不涉及任何商业机密。**


### 什么是SR

Segment Routing， 中文翻译为段路由，是一种源路由架构，其支持在Ingress node(源节点)制定数据包的转发路径。

Segment Routing的诞生背景和SDN紧密相关。在SDN出现早期，SDN几乎和OpenFlow密不可分。但最近OpenFlow却并没有如前两年那样如火如荼，已经开始慢慢冷却，推出人们的视线。

原因很多。从商业上，极具革命性的OpenFlow容易打破网络行业的布局，影响了行业巨头的利益，所以很难被传统设备商所接受。在技术上，OpenFlow网络中每个节点都要维持网络状态，当网络规模变大，业务变多，网络管理和运维就变得复杂，网络的可扩展性就受到了限制。而此时，一个更容易演进，又提供了足够的网络变成能力的网络架构Segment Routing被提了出来。Segment Routing(SR)是一种可以在ingress节点指明数据包转发路径的源路有机制。

### 后续文章计划
更多的内容将会在如下的文章中被介绍，主要包括SR的原理，协议扩展等内容：

* 《Segment Routing架构基础：SR-MPLS和SRv6》—— 待完成
* 《SR-MPLS：RSVP-TE的退场与SR-MPLS的崛起》—— 待完成
* 《SRv6：SDN的未来？》—— 待完成
    * 《SRH简介》—— 待完成
    * 《SRv6 Network Programming》—— 待完成
    * 《IS-IS extensions for SRv6》—— 待完成
* 《SR for SFC》—— 待完成
    * 《SFC：PBR vs NSH vs SR》—— 待完成


计划都放出来了，难道要反悔？不可能的!

成长的速度太慢了，要追不上梦想了，要努力哦。




