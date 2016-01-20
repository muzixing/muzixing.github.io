title:如何提升SDN可拓展性
date:2016/1/20
tags:SDN,scalability
category:Tech

Software Defined Networking是一种控制平面和数据平面分离的可编程的网络架构，目前已经有许多商业落地案例。在部署SDN时，往往会因SDN控制器性能不足而限制了SDN的可拓展性。因此SDN网络的规模往往不大。针对此问题，笔者在研究相关文献之后，总结了相关的解决方案，并通过本文来记录和分享。

## 解决方案

SDN分离了网络的控制平面和数据平面，而控制平面是SDN的大脑，其能力极大地影响着SDN网络的可拓展性。所以基本上，解决方案都是围绕如何给控制平面减压或者提升控制平面的能力来实现。根据控制器数目的不同，解决方案可以分为如下两类：

* 单控制器节点的性能拓展
* 部署多控制器系统

## 单控制器节点的性能拓展

单控制器节点的性能拓展是最常见的方式之一，包括控制器采用多线程，负载下放等解决方案。多线程等解决方案属于软件开发范畴，不属于本文讨论范围。通过负载下放（offload）等方式可以降低网络对控制平面的依赖，减少控制平面的负载和压力，从而可以管理更多的交换机，进而提升SDN网络的可拓展性。DIFANE和DoveFlow就是典型的代表。

DIFANE[1]是DIstributed Flow Architecture for Networked Enterprises的缩写。 在DIFANE架构中，其数据平面的所有数据均由数据平面完成，而控制器仅负责策略的计算，而不会直接响应Packet_in。其通过减轻控制平面的负载的方式，从而增强了SDN的可拓展性。

<center>![difane](http://ww4.sinaimg.cn/mw690/7f593341jw1f03rkwo1qsj20r80g6djx.jpg)</center>
<center>图1.DIFANE 架构图</center>

在DIFANE的数据平面，可以分为权威交换机（Authority switch）和包括Ingress switch在内的普通交换机的两类交换机。此外，DIFANE还定义了Cache rules、Authority rules和Partition rules三类流表项。其中Cache rules为从Authority switch上取回来的缓存规则，用于指导数据包的转发；Authority rules是控制器预计算下发的规则，可将其分发给Ingress switch，并作为Cache rules, 其仅存在于Authority switch中。Partition rules用于指导交换机将无法匹配到Cache rules的数据包转向指定的Authority switch，优先级最低。Authority switch具有一定的处理数据的能力，可以运行链路协议等基本协议，可实现DIFANE的数据层面需求。

当网络上线时，控制器通过收集网络的拓扑信息和主机接入位置信息等计算出Authority rules并分发到对应的Authority switch中。此外，控制器还需要完成粗粒度的Partition rules的计算和下发。Partition rules是由网络拓扑的具体情况计算出来的粗粒度规则，其告知Ingress switch将无法匹配Cache rules的数据包应该转发到哪一个Authority switch。当第一个packet到达Ingress switch时，不会选择上报controller，而是会匹配到低优先级的Partition rules，并转发到Authority switch。Authority switch负责将其转发到对应的Egress switch。此外，Authority switch还会将对应的Authority rules推送并安装到Ingress switch中，作为其Cache rules。之后的packet就可以匹配Cache rules，然后直接转发到Egress switch，而不需要转发给Authority switch。在DIFANE架构中，控制器则负责主动预先计算规则并下发，而网络事件的被动响应则由数据平面的Authority switch完成。

DIFANE的设计使得所有的数据平面的数据都由数据平面处理，而不是缓存在交换机队列中，再发送给控制器处理。此举使得络首包的延迟变小，同时也大大降低了控制器的压力，进而可以管理更大的网络。不过这样的解决方案难度较大，需要解决许多问题。比如Cache rules的流表项过期之后如何处理，主机移动带来的策略变化以及拓扑变化带来的策略转变等问题。虽然DIFANE确实降低了控制器的压力，拓展了网络规模，但是其仅在一定程度上提升了可拓展性，无法大规模地扩大网络规模，难以从根本上解决可拓展性的问题。

同样的，为解决OpenFlow处理首包所带来的性能不足的问题，DoveFlow[2]也设计了自己的解决方案。DevoFlow同样主张尽可能将包括流表的安装，统计信息的收集等IO高消耗的业务下放到交换机上，由交换机负责完成。而控制器负责高级的策略计算和下发工作。不过论文仅完成了模型建立和仿真分析，并没有实际部署。

将控制器的部分高IO消耗的业务下放到数据平面来处理，是解决SDN可拓展性问题的主要思路之一。这种方法可以实现不仅可以提升可拓展性，还可以降低网络延迟。不过这样的解决方案难度相对也比较大。

## 多控制器系统

除了通过下放负载来减轻控制器压力来提高可拓展性这种解决思路以外，更普遍的解决思路是通过部署多控制器系统来共同实现网络的管理。而根据控制器系统中控制器的种类异同可以将方案分为分布式控制器和东西向接口协议两种解决方案。

### 分布式控制器

较为出名的分布式控制器，当属HyperFlow[3]系统, Google的Onix[4]以及开源控制器ONOS[5]。

**HyperFlow**

HyperFlow是一个基于事件的OpenFlow分布式控制平台，可以实现多控制器之间协同工作。部署HyperFlow分布式系统的多控制器实例维护一个共同的全局网络视图。在管理本地网络时，控制器无需和其他节点交互而直接进行网络管理，从而实现快速地响应Packet\_in请求。同时HyperFlow并没有改变OpenFlow的协议内容，也不会影响已有的应用运行。与部署DHT不同，HyperFlow不需要改变控制器本身的存储。在数据同步方面也是通过直接推送方式将信息直接推送到其他节点。

每个HyperFlow节点都维护着全局的网络视图，看起来好像管理了全局网络一样，但是只能管理本地的网络。交换机可配置多控制器，从而提供High Availability。一旦某节点的网络视图发生改变，这个事件将会发布给所有订阅它的节点。而其他节点将需要重播(replay)所有已发布的事件来重新构建网络视图，这点将产生大量的同步数据。

**Onix和ONOS**

Onix是google的分布式控制器，其在所有节点之间维护了全局网络视图，实现分布式控制。此外，还定义了一套API，用于定义具体的同步操作。面对不同的场景，比如不同域之间的通信，可制定具体的同步数据细节来保障网络的安全和隐私。Onix支持两种形式的网络拓展：Partition(分区)， Aggregation(聚合)。

当网络规模增长到一定程度时，一个控制器无法应付全部的网络状态和流表状态的存储，内存上出现瓶颈。那么将网络划分为分别由多个控制器管理的子网络可以解决这个问题。所有控制器都共同维持一个网络状态的数据，但是流表状态由本地控制器管理，且本地控制器可以在全局拓扑上计算路径。

当网络继续增大时，一个控制器在全局网络上计算路径就显得有些吃力了，CPU资源成为了新的瓶颈。所以可以把多个子网聚合成一个逻辑节点。而不同逻辑节点之间由另一个管理全局流量的Onix控制器管理，从而实现更大网络的管理。举例如，一个很大的校园网里面，每栋大楼都是由一个Onix管理的子网络。多栋大楼组成的网络可以被抽象成一个逻辑节点，由管理校际的Onix来管理逻辑节点组成的逻辑网络，从而实现大规模网络的管理。

此外Onix也针对数据一致性等方面做了相关的部署。然而由于分布式控制器本身数据同步数据量较大，其需要比较充裕的网络带宽。尽管如此，Onix还是在Google的数据中心中起到了很大的作用。

ONOS是一款开源的分布式控制器。与其他分布式控制器一样，ONOS也构建了全局的拓扑，控制器实例也是独立管理网络。此外,ONOS也可以实现控制器之间的负载均衡。在ONOS的实现过程中，对于不同的数据的分布式存储是不同的。对于分布式集群的master/slaver的关系等信息采用的是Hazelcast来存储，而Device,link等内容则是通过Gossip协议来直接发送。而且发送形式是单播，而非在节点之间组播。

ONOS作为一款新兴的分布式控制器，在可拓展性方面还是相对不错的。但是分布式系统的心跳包等大量数据需要消耗大量带宽，使其可能难以适应链路质量不足的场景。

### 东西向协议

本质上HyperFlow也可以部署在异构的控制器上从而实现多控制协同工作。不过异构控制器部分，解决方案的思路主要是通过协议来消除通信终端的差异性,而HyperFlow并没有强调这一点。目前已有的可用于异构控制器之间的东西向协议有SDNi[6]和West-East[7] Bridge协议。

**SDNi**

SDNi是华为提出的一种用于处理SDN域之间通信的协议。在其提交的草案中，定义了SDN域的概念和SDNi如何帮助域之间通信。目前SDNi已经在开源控制器OpenDaylight[8]上作为应用实现。SDNi需要在控制器之间交互Reachability、Flow setup/tear-down/update请求和包括带宽，QoS和延迟等Capability信息。SDNi的数据交换可以基于SIP或者BGP协议实现，如OpenDaylight中就是基于BGP协议实现的。基于SDNi可以实现异构控制器协同工作，实现大规模网络的管理，实现跨域流量优化等应用。

**West-East Bridge**

West-East Bridge协议也是一种支持异构控制器协同工作的协议。其同样也是通过订阅/发布机制来完成数据的分发。当网络视图发生变化时，该事件将会被发布到所有订阅其数据的节点。为保证数据的一致性，其节点之间为全连接关系。此外，West-East Bridge还设计了虚拟的网络视图，可以满足某些SDN域对于安全和隐私的需求。

### 其他解决方式

除了以上列举的解决方案外，还有许多其他的解决方案，但是笔者无法简单地将其归类为以上两种方案，所以在此部分介绍。

**Kandoo**

第一种解决方案中提到减轻控制器负载可以提升SDN的可拓展性。而第一种方案是通过把相关高IO消耗的业务下放到了数据平面的交换机上。但是这种方式需要对交换机进行修改，其难度较大。所以在控制平面做文章则成为另一种可选的方案。Kandoo就是一种控制平面的解决方案。Kandoo[9]是一种分层式的控制平面，由本地控制器和根控制器组成。其中本地控制器对网络的信息并不了解，仅完成本地的业务。而根控制器负责完成网络范围内的业务请求，如路由等等。本地控制器需要运行APP detect应用来检测大象流等需要上报给根控制器的报文，而根控制器需要运行APP reroute应用来完成网络范围内的业务部署。在根控制器完成计算之后，发送给本地控制器，由本地控制器完成流表项的安装。即本地控制器本质上只是一个代理，完成了大部分的高发频率的本地网络事件，而根控制器完成网络范围内的业务响应。从而将全局网络事件分摊到多个本地控制器上，降低对IO性能的要求，从而提升SDN可拓展性。

<center>![kandoo](http://ww4.sinaimg.cn/mw690/7f593341jw1f041blt59nj20ii0a675w.jpg)</center>
<center>图2.Kandoo架构图</center>

**DISCO**

DISCO[10]本质上可以理解为一种和SDNi类似的东西向协议，但是由于论文中只字不提东西向协议，所以笔者只能将其放在这部分了。DISCO通过AMQP协议实现了控制器之间的数据交换，来实现控制器之间的协同，实现跨域业务的部署，从而增强了SDN的可拓展性。其实现原理和SDNi，West-East Bridge基本一样，不再赘述。

### 总结

目前针对SDN可拓展性的研究已经非常火热，对应的解决方案也已经有不少。从以上的解决方案中我们可以总结出来可以从把负载从控制器上offload到数据平面和拓展控制平面两种大的解决思路。在控制平面能力拓展方面，Google的Onix确实是做得最全面的，包括了是网络的分区和聚合。基本上目前SDN可扩展性方面的研究已经有了一定的基础。随着SDN的发展，相信后续SDN的可拓展性方面或者说东西向方面的内容将会有更多的研究成果出现，从而推动SDN东西向和可拓展性方面的发展进程，进而带来一个更大的SDN网络。

### 参考文献

[1] Curtis A R, Mogul J C, Tourrilhes J, et al. DevoFlow: Scaling flow management for high-performance networks[C]//ACM SIGCOMM Computer Communication Review. ACM, 2011, 41(4): 254-265.

[2] Curtis A R, Mogul J C, Tourrilhes J, et al. DevoFlow: Scaling flow management for high-performance networks[C]//ACM SIGCOMM Computer Communication Review. ACM, 2011, 41(4): 254-265.

[3] Tootoonchian A, Ganjali Y. HyperFlow: A distributed control plane for OpenFlow[C]//Proceedings of the 2010 internet network management conference on Research on enterprise networking. USENIX Association, 2010: 3-3.

[4] Koponen T, Casado M, Gude N, et al. Onix: A Distributed Control Platform for Large-scale Production Networks[C]//OSDI. 2010, 10: 1-6.

[5] Berde P, Gerola M, Hart J, et al. ONOS: towards an open, distributed SDN OS[C]//Proceedings of the third workshop on Hot topics in software defined networking. ACM, 2014: 1-6.

[6] Yin, H., Xie, H., Tsou, T., Lopez, D., Aranda, P.A., Sidi, R.: SDNi: A message exchange protocol for software defined networks (SDNs) across multiple domains. IRTF InternetDraft (2012)

[7] Lin P, Bi J, Chen Z, et al. WE-bridge: West-East Bridge for SDN inter-domain network peering[C]//Computer Communications Workshops (INFOCOM WKSHPS), 2014 IEEE Conference on. IEEE, 2014: 111-112.

[8] https://wiki.opendaylight.org/view/ODL-SDNi_App:Main

[9] Hassas Yeganeh S, Ganjali Y. Kandoo: a framework for efficient and scalable offloading of control applications[C]//Proceedings of the first workshop on Hot topics in software defined networks. ACM, 2012: 19-24.

[10] Phemius K, Bouet M, Leguay J. Disco: Distributed multi-domain sdn controllers[C]//Network Operations and Management Symposium (NOMS), 2014 IEEE. IEEE, 2014: 1-4.

作者简介：
李呈，2014/09-至今，北京邮电大学信息与通信工程学院未来网络理论与应用实验室（FNL实验室）攻读硕士研究生。

个人博客：http://www.muzixing.com




