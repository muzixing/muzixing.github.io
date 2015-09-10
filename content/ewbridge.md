title:The study notes of East-west Bridge for SDN Network Peering
date:2014/4/10
tags:sdn Ewbridge
category:Tech
###前言

这是一篇学习笔记，是在阅读了林萍萍女士的论文"East-West Bridge for SDN Network Peering  "之后的总结与思考。

东西向接口通信中交换的数据是一个域中的数据。

###控制器之间的发现

最简单的方式就是直接指定,但是这明显不是一个合理的方法。比较好的做法是让所有的控制器在开启的时候向一个注册服务器注册自己的信息，然后再获取所有控制器的信息，如IP,PORT,用于建立控制器之间的连接。另有更智能的方法是通过lldp去发现邻居。即LLDP报文中携带本域中控制器的信息。
即有如下三种方式：

* 	通过配置信息设置
* 	访问注册服务器获取
* 	通过LLDP去发现邻居	

我认为，第一种方法最简单，但是需要手动配置。第二种方法最易于设计。第三种方法最智能。我觉得使用LLDP去发现邻居是一种不错的方式。每一次接入网络都需要探测自己的邻居，然后发送自己的拓扑信息给邻居，同时当拓扑发生变化时也需要给邻居同步，此处的拓扑发生变化可以包含如下两点：

* 域内拓扑发生变化，如link down
* 邻居C拓扑变化传送过来导致本地存储拓扑变化，从而需要更新拓扑，并通知其他邻居。

###网络信息的存储

* 	分布式存储在每一个控制器，每一个控制器只保存自己的视图，需要全局数据时再发送请求从别的控制器获取。此方式为主动请求方式，能减少拓扑信息传递的数量。但是耗时大。
* 	分布式存储在每一个控制器，每一个控制器都有全网视图。时刻保持tcp连接，实时更新全网拓扑。
* 	集中式存储，全网视图在某一指定服务器上。当全网视图发生改变，则分发给订阅的控制器。

以上3种方法都需要在控制器启动的时候，将自己的拓扑信息提交给集中式存储的服务器或者发布给订阅的控制器。

个人以为第三种集中式存储会比较好。控制器连接的时候也不需要去建立多个连接，只需订阅这一服务即可。（如何分析？）

###网络视图

每一个网络都有一个视图，这个视图包含了如下的信息：（此表摘自参考文献）

<table class="table-bordered table-striped table-condensed">
   <tr>
      <td>Name</td>
      <td>Type</td>
      <td>Columns</td>
   </tr>
   <tr>
      <td>Node_id</td>
      <td>Virtual/physical</td>
      <td>IP/MAC, OF_version, port_numbers，is_edge_node, Vendor_name,MTU，Device_type，Deveice_function</td>
   </tr>
   <tr>
      <td>Link_id</td>
      <td>Virtual/physical</td>
      <td>Node_ID_src, Port_ID_src, Node_ID_dst,
      Port_ID_dst,
      Bandwidth,is_interdomain_link</td>
   </tr>
   <tr>
      <td>Port_id</td>
      <td>Virtual/physical</td>
      <td>Node_ID,
      Port_MAC,is_active, is_edge_port,
      VLAN_ID,
      throughput</td>
   </tr>
   <tr>
      <td>Node_capbility</td>
      <td>NULL</td>
      <td>protocol_name, version, port</td>
   </tr>
   <tr>
      <td>Reachability</td>
      <td>NULL</td>
      <td>IP_prefixes,length</td>
   </tr>
   <tr>
      <td>Node_table_ID(Flow entity)</td>
      <td>NULL</td>
      <td>Columns names are the same as the fields defined in the flowtable in OpenFlow specification</td>
   </tr>
   <tr>
      <td>Link_Utilities</td>
      <td>NULL</td>
      <td>Link_ID， Link utilities</td>
   </tr>
   <tr>
      <td>Flow_path(Node_ID_src  Node_ID_dst)</td>
      <td>NULL</td>
      <td>Port_ID (in), Node_ID_src, Port_ID (out),Port_ID (in), Node_ID_dst, Port_ID (out)</td>
   </tr>
   <tr>
      <td></td>
   </tr>
</table>


在上表之外，东西向接口还应该交换主机数据。如：

	IP/MAC :DPID(edge)+port

用于回复ARP信息。



###网络视图学习

网络试图的基础信息可以通过LLDP报文获取，若更多高级的信息，我们需要通过对LLDP的数据段进行拓展，以携带相关的信息。本处所提到的学习是指从底层网络获取相关信息。

###交换数据格式

* 	Json，xml均可。

对于这些我表示不太懂。一般的我使用scapy封装数据包，转换成stream之后，使用socket传输。

###网络虚拟化

为了私有原因或者安全原因，我们有时候并不希望别的控制器全部知道我们的拓扑，所以网络虚拟化是很有必要的。**我们可以将拓扑简化为几个边源端口组成的大交换机** 从而隐藏内部拓扑的细节。

这一点非常必要，而网络虚拟化可以完美解决。网络虚拟化产品有很多，有flowvisor，也有北京邮电大学开发的CNVP

###交换事件

当网络信息（拓扑信息）发生变化时，我们需要实时地通知其他控制器这一变化。模拟BGP协议，我们可以设置5种类型的消息结构。

*	Open
*	Update
*	Notification
*	Keep-alive
*	View-refresh

当启动控制器时，控制器与其他控制器连接，发送open消息。然后发送update消息，将自己的网络信息传递给对方，同时获取对方传递过来的网络信息，以获得更新的全网拓扑。在无数据传输的时候，需要传递Keep-alive消息保持TCP连接。View-refresh消息用于主动获取网络信息。

###后语

这是昨天拜读林萍萍女士论文的总结与思考。虽然东西向接口大家都能想到，但是早在一年前就做出来，并做了implementation 和evaluation，这是非常厉害的！向前辈们学习！更多详细信息可以直接阅读参考文献。

###参考文献：
Pingping Lin, Jun Bi, and Yangyang Wang

East-West Bridge for SDN Network Peering

Institute for Network Sciences and Cyberspace, Department of Computer Science,
Tsinghua University

Tsinghua National Laboratory for Information Science and Technology (TNList)
