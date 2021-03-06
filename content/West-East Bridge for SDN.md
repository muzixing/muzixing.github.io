title:SDN东西向现状简介
tags:SDN,west-east
date:2015/10/29
category:Tech

###What is SDN West-East Interface

在SDN架构中，控制平面掌控全局网络的资源，控制数据平面的转发等功能，尤其重要，所以控制平面的性能对整体网络的性能有直接的影响。以前控制平面多以单例控制器为主，控制平面能力欠缺成为SDN网络规模受限的最大原因之一。 后来OpenDayLight，ONOS等控制器的出现，使用了集群技术，使得SDN控制平面性能得到了提升，是当下解决SDN控制平面性能不足的主要解决方案之一。

然而，这样的解决方案只能用于同一控制器之间的性能扩展，无法完成异构控制器之间的协同工作。此外，某些场景对于安全，隐私方面的考虑，需要隐藏网络内部的细节，所以还需要有SDN域的概念。如何完成跨域之间的流量处理，实现多异构控制器之间的协同工作是未来研究的方向之一，笔者将其归类为SDN控制平面的东西向接口。SDN控制平面的南向接口面对数据平面，北向接口面向应用，容易理解，控制器之间的接口称之为东西向接口，用于完成控制器之间的通信。

<center>![West-East](http://ww2.sinaimg.cn/mw690/7f593341jw1exixzvkpi6j20og0d2gml.jpg)</center>
<center>Figure1. West-East Interface of SDN</center>

###Why SDN need West-East Interface

SDN东西向接口是定义控制器之间通信的接口。由于单控制器能力有限，为满足大规模和可拓展性要求，东西向接口的研究成为下一个SDN研究领域。目前对于SDN东西向接口的研究还处于初级阶段，还缺少行业标准。标准的SDN东西向接口应与SDN控制器解耦，能实现不同厂家控制器之间通信。

在很多场景中都需要控制器之间的协同工作，如在运营商网络场景中，接入网，回传网，核心网三者功能差异很大，需要制定不同的控制器去运行不同的应用，而这三者又需要协同合作，实现全网的最优化。此时就需要东西向接口来完成控制器之间的通信。跨数据中心的网络中，多数据中心的控制器也有相互通信的需求。

<center>![West-East interface for mobiel network](http://ww4.sinaimg.cn/mw690/7f593341jw1exixzu4513j20wq0cm76v.jpg)</center>
<center>Figure2. Federation of SDN Controllers</center>

目前南向的标准还为统一，OpenFlow成为SDN南向接口的通用标准之一，其他还有许多可以实现SDN架构的南向接口协议。总的来说，目前南向接口是百花齐放的状态。北向接口方面，目前ONF已经有相关部门在进行这项工作。统一的北向接口标准可以降低在不同控制器上开发应用的成本。关于东西向接口的标准，目前在业界中还未的到重视，仅ONF一个项目组在关注这个方向。

###Approach for West-East Interface

SDN控制平面性能拓展方案中，目前的设计方案有两种，一种是垂直架构的，另一种是水平架构的[1]。垂直架构的实现方案是在多个控制器之上再叠加一层高级控制层，用于协调多个异构控制器之间的通信，从而完成跨控制器的通信请求。水平架构中，所有的节点都在同一层级，身份也相同，没有级别之分。目前比较常见的架构为水平架构，比如华为的SDNi[2]，Pingping Lin博士提出的West-East Bridge for SDN inter-domain network peering[3]。垂直架构目前在中国移动提出的SPTN架构中有涉及，笔者正在研究的内容也正是这部分内容。

<center>![](http://ww4.sinaimg.cn/mw690/7f593341jw1exixzuopf7j20jj0a4gm1.jpg)</center>
<center>Figure3. Vertical Approach for Inter-SDN Controller Communication </center>

<center>![](http://ww3.sinaimg.cn/mw690/7f593341jw1exixzud6drj20ky07b74i.jpg)</center>
<center>Figure4. Horizontal Approach for Inter-SDN Controller Communication </center>

###Previous Research

东西向接口其实并不是一个新鲜事，在很多架构中都会被提到。2013年， 清华的博士pingping lin的论文“East-West Bridge for SDN Network Peering”中提出了West-East Bridge的概念。论文中介绍了他们设计的东西向接口的功能，并完成了部署和测试。

SDNi是华为提出的一种SDN东西向的实现，目前已经在OpenDayLight中部署实现。其架构为水平架构，可实现多OpenDayLight实例之间的通信，完成跨域通信。目前支持传输Topology Data, QoS Data和其他一些拓展内容。

中国移动发布的关于SPTN的白皮书中也有设计多控制器协同工作的内容，然而目前仅仅处于白皮书阶段，并没有实际部署和测试。SPTN白皮书中提到了层级式的SDN控制平面架构，分别为Super层和Domain层。Super层的Super Controller负责跨域通信的业务，Domain层的Domain Controller负责域内的通信。分级的架构能使得SDN控制平面能力得到大大的提升。

TATA在很久以前发布了关于跨域通信的报告。报告中介绍了实现SDN跨域通信的两种架构：垂直架构和水平架构。此外还提出了基于BGP或者SIP协议去完成SDN东西向接口的想法，不过报告内容仅限于次，并没有提及任何实际部署的内容。目前为止，依然没有搜集到相关的实践部署。

其他相关论文也有若干，但影响力不够，暂不介绍。

目前笔者正在研究SDN东西向的内容，期待后续能有所产出。

###Conclusion

随着SDN的发展，部署SDN的网络规模将越来越大，对SDN控制平面的性能要求也越来越高。虽然当下业界对SDN控制层面东西向并不够重视，但相信随着技术的发展，东西向方向的解决方案，技术标准将逐渐完善。期待未来自己的成果能顺利发表，产生一定的影响。

###References
[1]：http://www.tcs.com/SiteCollectionDocuments/White%20Papers/Inter-SDN-Controller-Communication-Border-Gateway-Protocol-0314-1.pdf 

[2]：https://tools.ietf.org/html/draft-yin-sdn-sdni-00

[3]：Lin P, Bi J, Chen Z, et al. WE-bridge: West-East Bridge for SDN inter-domain network peering[C]//Computer Communications Workshops (INFOCOM WKSHPS), 2014 IEEE Conference on. IEEE, 2014: 111-112.
