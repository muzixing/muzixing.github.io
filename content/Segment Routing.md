title: Segment Routing系列文章：To Write List
date: 2018/8/9
tags: SR, Segment Routing, SR-MPLS, SRv6
category: Tech

### 前言


----------
人啊，总是懒惰的。

一懒惰，就是两年。

总是有太多理由，总是有太多借口。

但终究，还是无法再骗过自己了。

问过了领导，领导答复：“写互联网公开的，开源的内容没有问题”。那就从我平时研究的Segment Routing开始写吧。为避免踩信息安全红线，还是要很郑重地声明：

**所有文章内容均为互联网公开资料和个人技术理解，不涉及任何商业机密。**


### 什么是SR

Segment Routing， 中文翻译为段路由，是一种源路由架构，其支持在Ingress node(源节点)指定数据包的转发路径。

Segment Routing的诞生背景和SDN紧密相关。在SDN出现早期，SDN几乎和OpenFlow密不可分。但现在OpenFlow却并没有像前两年那样如火如荼，已经开始慢慢冷却，慢慢退出人们的视野。

OpenFlow冷却的原因很多。从商业上，极具革命性的OpenFlow可能会打破网络行业的格局，影响了行业巨头的利益，所以很难被传统设备商所接受。在技术上，OpenFlow网络中的每个节点都要维持per-flow的网络状态，当网络规模变大，业务变复杂，网络管理和运维就变得复杂，网络的可扩展性就成了问题。就在此时，一个更容易平滑演进，又具有足够的网络编程能力的网络架构Segment Routing被提了出来。Segment Routing (SR) 是一种可以在源节点指明数据包转发路径的源路由网络架构。

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




