date:2013-12-7
title:【原创】SDN下的分布式广播风暴解决方案
category:Tech
tags:SDN,Openflow

###前言

这是很久以前的成果了，那时候我才大三上。为了学习sdn,openflow等知识，北邮科研楼628的一群哥们儿，想着各种新奇的东西去解决已有的问题。

有一天，我们遇到了网络风暴，但是我们觉得STP有点复杂，而且，确实也不愿意去学。那么，就自己写一个解决方案吧。于是，下面的小代码产生了。

###核心思想

其实特别简单，一句话：**不让同一个数据包从第二个端口进入，即仅允许数据包从第一个进来的端口进入。**

也就是说，我确保了，同一个数据包，不会从别的交换机从非第一次的in_port进入本交换机，那就不会有环路，也就解决了风暴，而且，同一个端口允许进入，不影响主机继续发送广播包。

###具体实现

这个就需要我们建立一个macToport的表，在python里面数据结构字典来实现。使用src_mac作为key，记录值为[dstip,port,time]

	self.macToPort = {srcMAC:[dst_ip,in_port,time]}

这个字典记录了用数据包的mac地址记录了数据包的目标ip,入口端口，到达时间三个信息，其实如果为了更好的对应，我们应该使用上xid,让**（src_mac,xid）**去唯一确定一个数据包。

相应的处理逻辑如下，我们可以把他写成一个函数去调用，调用位置应处于packet_in的处理逻辑里面。

	def anti_brocast(packet):
    	if packet.dst.isMulticast()://如果是广播性质，则处理
    	  if isinstance(packet.next,arp) and (packet.next.opcode == arp.REQUEST)://假设所有的通信之前都有arp，即广播风暴只能由ARP引起，已经arp之后是不会出现storm的。
    	    if (packet.next.hwsrc in self.packetToPort) and (packet.next.protodst 	==self.packetToPort[packet.src][0])://如果src_mac在表内，且dst_ip相同,我们默认这是会产生风暴的同一个流的广播包。
	        #如果如端口不是原先的记录中端口，即第一次端口，则丢弃，否则flood.
	          if(inport != self.packetToPort[packet.src][1]):
	            drop()#if not the specially inport,then drop it.
	            return
	          else:
	            flood("Another Arp_Request from %s -- flooding,we set limit_time to drop it" % (packet.src))
	            print("Another muticast packet form %s at %i port in %i "%(packet.src,inport,dpid))
	            return
	        else:#如果没有在字典中，那么记住它！
	          self.packetToPort[packet.src]=[packet.next.protodst,inport,TimeToArrive]#record and lock the port
	          self.macToPort[packet.src]=[inport,TimeToArrive]#update the L2 table.
	          print("update the table entry of %s at %i in %i ,"%(packet.src,inport,dpid))
	          flood()
	      return

这是一个极其简单的逻辑，但是可以解决ARP的风暴，也就是说解决了很大程度上的广播风暴。相比于STP，这个小逻辑是不是更清爽呢？


###后续

SDN也许还没有明确的定义，明确的方向，但是不可否认的是，SDN的诞生，openflow的诞生，给解决某些问题提供了新的方案，我想这也是一种创新吧。希望读完这篇博文能给你一些小启发。
