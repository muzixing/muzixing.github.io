date:2013-12-12
title:【原创】OpenFlow通信流程解读
category:Tech
tags:SDN,OpenFlow

##前言

接触了这么久的SDN，OpenFlow协议前前后后也读过好多遍，但是一直没有时间总结一下自己的一些见解。现在有时间了，就写一写自己对OpenFlow协议通信流程的一些理解。

##SDN中Switch和controller

在SDN中很重要的两个实体是Switch跟Controller。Controller在网络中相当于上帝，可以知道网络中所有的消息，可以给交换机下发指令。Switch就是一个实现Controller指令的实体，只不过这个交换机跟传统的交换机不一样，他的转发规则由流表指定，而流表由控制器发送。

###switch组成与传统交换机的差异

####switch组成

switch由一个Secure Channel和一个flow table组成，of1.3之后table变成多级流表，有256级。而of1.0中table只在table0中。

* Secure Channel是与控制器通信的模块，switch和controller之间的连接时通过socket连接实现。
* Flow table里面存放这数据的转发规则，是switch的交换转发模块。数据进入switch之后，在table中寻找对应的flow进行匹配，并执行相应的action，若无匹配的flow则产生packet_in（后面有讲）

####of中sw与传统交换机的差异

* 匹配层次高达4层，可以匹配到端口，而传统交换机只是2层的设备。
* 运行of协议，实现许多路由器的功能，比如组播。
* 求补充！！（如果你知道，请告诉我，非常感谢！）

####OpenFlow的switch可以从以下方式获得

* 实体of交换机，目前市场上有一些厂商已经制造出of交换机，但是普遍反映价格较贵！性能最好。
* 在实体机上安装OVS，OVS可以使计算机变成一个OpenFlow交换机。性能相对稳定。
* 使用mininet模拟环境。可以搭建许多交换机，任意拓扑，搭建拓扑具体教程本博客有一篇。性能依赖虚拟机的性能。

###controller组成

控制器有许多种，不同的语言，如python写的pox,ryu，如java写的floodlight等等。从功能层面controller分为以下几个模块：

* 底层通信模块：OpenFlow中目前controller与switch之间使用的是socket连接，所以控制器底层的通信是socket。
* OpenFlow协议。socket收到的数据的处理规则需按照OpenFlow协议去处理。
* 上层应用：根据OpenFlow协议处理后的数据，开发上层应用，比如pox中就l2\_learning,l3\_learning等应用。更多的应用需要用户自己去开发。


##OpenFlow通信流程

以下教程环境为：mininet+自编简单控制器+scapy封装

###建立连接

首先启动mininet，mininet会自行启动一个default拓扑，你也可以自己建立你的拓扑。sw建立完成之后，会像controllerIP:controllerport发送数据。

controller启动之后，监听指定端口，默认6633，但是好像以后的都改了，因为该端口被其他协议占用。

3次握手之后，建立连接，这个是底层的通信，是整一套系统的基础设施。

###OFPT_HELLO

创建socket之后，sw跟controller会彼此发送hello数据包。

+ 目的：协议协商。
+ 内容：本方支持的最高版本的协议
+ 成果：使用双方都支持的最低版本协议。
+ 成功：建立连接
+ 失败：OFPT\_ERROR  (TYPE:OFPT\_HELLO\_FAILED,CODE =0),终止连接。

###OFPT_ERROR

说到OFPT_ERROR,我们不妨先了解一下。

	ofp_error_type = { 0: "OFPET_HELLO_FAILED",
    	               1: "OFPET_BAD_REQUEST",
    	               2: "OFPET_BAD_ACTION",
    	               3: "OFPET_FLOW_MOD_FAILED",
    	               4: "OFPET_PORT_MOD_FAILED",
    	               5: "OFPET_QUEUE_OP_FAILED"}

错误类型如上所示。对应的type还会有对应的code.所以报错的格式为：

	OFPT_ERROR
	TYPE: 
	CODE:
	[PAYLOAD]具体的错误信息。

如 TYPE:0 CODE:0为：**OFPHFC_INCOMPATIBLE**

具体对应的关系，请自行查看OF协议。

###OFPT_ECHO

* 分类：对称信息 OFPT\_ECHO\_REQUEST, OFPT\_ECHO\_REPLY
* 作用：查询连接状态，确保通信通畅。

当没有其他的数据包进行交换时，controller会定期循环给sw发送OFPT\_ECHO\_REQUEST。

###OFPT_FEATURES

当sw跟controller完成连接之后，控制器会向交换机下发OFPT\_FEATYRES\_REQUEST的数据包，目的是请求交换机的信息。

+ 发送时间：连接建立完成之后
+ 发送数据：OFPT\_FEATURES\_REQUEST
+ 对称数据：OFPT\_FEATURES\_REPLY
+ 目的：获取交换机的信息

#### OFPT\_FEATURES\_REQUEST

+ TYPE=5
+ Without data

#### OFPT\_FEATURES\_REPLY

+ TYPE =6
+ [0:8]为header
+ [8:32]长度24byte为sw的features
+ [32:]长度与端口数成正比，存放port的信息。每一个port信息长度为48byte。

		class ofp_features_reply(Packet):
		    name = "OpenFlow Switch Features Reply"
		    fields_desc=[ BitFieldLenField('datapath_id', None, 64, length_of='varfield'),
		                  BitFieldLenField('n_buffers', None, 32, length_of='varfield'),
		                  XByteField("n_tables", 0),
		                  X3BytesField("pad", 0),
		                  #features
		                  BitField("NOT DEFINED", 0, 24),
		                  BitField("OFPC_ARP_MATCH_IP", 0, 1),  #1<<7 Match IP address in ARP packets
		                  BitField("OFPC_QUEUE_STATS", 0, 1),   #1<<6 Queue statistics
		                  BitField("OFPC_IP_STREAM", 0, 1),     #1<<5 Can reassemble IP fragments
		                  BitField("OFPC_RESERVED", 0, 1),      #1<<4 Reserved, must be zero
		                  BitField("OFPC_STP", 0, 1),           #1<<3 802.1d spanning tree
		                  BitField("OFPC_PORT_STATS", 0, 1),    #1<<2 Port statistics
		                  BitField("OFPC_TABLE_STATS", 0, 1),   #1<<1 Table statistics
		                  BitField("OFPC_FLOW_STATS", 0, 1),    #1<<0 Flow statistics
		                  BitFieldLenField('actions', None, 32, length_of='varfield'),
		                ]
		bind_layers( ofp_header, ofp_features_reply, type=6 )


以上的结构是交换机的features,紧跟在后面的是端口的结构：

	class ofp_phy_port(Packet):
	    name = "OpenFlow Port"
	    fields_desc=[ ShortEnumField("port_no", 0, ofp_port),
	                  MACField("hw_addr", "00:00:00:00:00:00"),
	                  StrFixedLenField("port_name", None, length=16),
	                  BitField("not_defined", 0, 25),
	                  BitField("OFPPC_NO_PACKET_IN", 0, 1),
	                  BitField("OFPPC_NO_FWD", 0, 1),
	                  BitField("OFPPC_NO_FLOOD", 0, 1),
	                  BitField("OFPPC_NO_RECV_STP",0, 1),
	                  BitField("OFPPC_NO_RECV", 0, 1),
	                  BitField("OFPPC_NO_STP", 0, 1),
	                  BitField("OFPPC_PORT_DOWN", 0, 1),

	                  #uint32_t for state
	                  BitField("else", 0, 31),
	                  BitField("OFPPS_LINK_DOWN", 0, 1),
	
	                  #uint32_t for Current features
	                  BitField("not_defined", 0, 20),
	                  BitField("OFPPF_PAUSE_ASYM", 0, 1),
	                  BitField("OFPPF_PAUSE", 0, 1),
	                  BitField("OFPPF_AUTONEG", 0, 1),
	                  BitField("OFPPF_FIBER", 0, 1),
	                  BitField("OFPPF_COPPER", 0, 1),
	                  BitField("OFPPF_10GB_FD", 0, 1),
	                  BitField("OFPPF_1GB_FD", 0, 1),
	                  BitField("OFPPF_1GB_HD", 0, 1),
	                  BitField("OFPPF_100MB_FD", 0, 1),
	                  BitField("OFPPF_100MB_HD", 0, 1),
	                  BitField("OFPPF_10MB_FD", 0, 1),
	                  BitField("OFPPF_10MB_HD", 0, 1),
	                  
	                  #uint32_t for features being advised by the port
	                  BitField("advertised", 0, 32),
	
	                  #uint32_t for features supported by the port
	                  BitField("supported", 0, 32),
	
	                  #uint32_t for features advertised by peer
	                  BitField("peer", 0, 32)]

交换机和端口的配置信息在整一个通信过程起着至关的作用，因为所有关于的操作都需要从features里面提取相关的信息，如**dpid,port\_no**，等在整个通信过程中多次被用到的重要数据。所以，对这两个数据结构了然于心，对于研究OpenFlow来说，至关重要。每一次交换机连到控制器，都会收到控制器的features\_request,当sw将自己的features回复给控制器之后，控制器就对交换机有了一个全面的了解，从而为后面的控制提供的控制信息。



###OFPT\_PACKET\_IN

在控制器获取完交换机的特性之后，交换机开始处理数据。

对于进入交换机而没有匹配流表，不知道如何操作的数据包，交换机会将其封装在packet\_in中发给controller。包含在packet\_in中的数据可能是很多种类型，arp和icmp是最常见的类型。

当然产生packet\_in的原因不止一种，产生packet\_in的原因主要有一下两种：

* **OFPR\_NO\_MATCH**
* **OFPR\_ACTION**

无法匹配的数据包会产生packet\_in,action也可以指定将数据包发给packet\_in,也就是说我们可以利用这一点，将需要的数据包发给控制器。

packet\_in事件之后，一般会触发两类事件：

* **packet\_out**
* **flow\_mod**

如果是广播包，如arp，控制器一般会将其包装起来，封装成packet_out数据包，将其发给交换机，让其flood,flood操作是将数据包往除去in\_port以外的所有端口发送数据包。

###OFPT\_PACKET\_OUT

很多人不是特别了解packet\_out的作用。

* 作用：通过控制器发送交换机希望发送的数据
* 例子：当一个没有匹配上流表项的数据上报控制器时，控制器可以下发packet\_out，指定交换机对该数据包做泛洪或丢弃动作。

当packet\_out中的buffer\_id=-1时，指明该数据并不在交换机的buffer中，而在packet\_out的data。当buffer\_id不为-1时，指明要操作的数据包是交换机中该buffer\_id的数据。

###OFPT\_FLOW\_MOD

OFPT\_FLOW\_MOD是整一个OpenFlow协议中最重要的数据结构。

OFPT\_FLOW\_MOD由**header+match+flow_mod+action[]**组成。为了操作简单，以下的结构是将wildcards和match分开的形式，形成两个结构，在编程的时候能更方便一些。由于这个数据包很重要，所以，我将把这个数据包仔细拆分解读。

    flow_mod = of.ofp_header(type=14,length=72)/of.ofp_flow_wildcards(OFPFW_NW_TOS=1,
                                      OFPFW_DL_VLAN_PCP=1,
                                      OFPFW_NW_DST_MASK=0,
                                      OFPFW_NW_SRC_MASK=0,
                                      OFPFW_TP_DST=1,
                                      OFPFW_TP_SRC=1,
                                      OFPFW_NW_PROTO=1,
                                      OFPFW_DL_TYPE=1,
                                      OFPFW_DL_VLAN=1,
                                      OFPFW_IN_PORT=1,
                                      OFPFW_DL_DST=1,
                                      OFPFW_DL_SRC=1)\
               /of.ofp_match(in_port=msg.payload.payload.payload.in_port,
                             dl_src=pkt_parsed.src,
                             dl_dst=pkt_parsed.dst,
                             dl_type=pkt_parsed.type,
                             dl_vlan=pkt_parsed.payload.vlan,
                             nw_tos=pkt_parsed.payload.tos,
                             nw_proto=pkt_parsed.payload.proto,
                             nw_src=pkt_parsed.payload.src,
                             nw_dst=pkt_parsed.payload.dst,
                             tp_src = 0,
                             tp_dst = 0)\
               /of.ofp_flow_mod(cookie=0,
                                command=0,
                                idle_timeout=10,
                                hard_timeout=30,
                                out_port=msg.payload.payload.payload.payload.port,
                                buffer_id=buffer_id,
                                flags=1)
####**OFP\_HEADER**

header是所有数据包的报头，有三个参数：

* type:类型
* length:整个数据包的长度
* xid：数据包的编号

比如ofp\_flow\_mod的type就是14，具体的哪一种数据的类型将在文章最后给出。length最基本长度为72，每一个action长度为8。所以长度必定为8的倍数才是一个正确的数据长度。

####WILDCARDS

这是从match域提取出来的前32bit。

**在of1.0中这里的0，1意义跟我们平时接触的如子网掩码等意义相反**，如OFPFW_NW_DST_MASK=0则表示全匹配目标IP。如果为63，则表示不匹配IP。为什么拿这个举例？原因就在于，他的长度是6bit，最大是63，需要将数值转变成对应2进制数值才是我们想要的匹配规则，且注意，1是忽略，0是匹配。如果wildcards全0，则表示由match精确指定，即所有12元组都匹配。

当然高兴的是，在1.3的时候，这个逻辑改成了正常的与逻辑。即1为使能匹配，0为默认不匹配。

####MATCH

这个数据结构会出现在机会所有重要的数据包中，因为他存的就是控制信息。

如有packet\_in引发的下发流表，则match部分应对应填上对应的数据，这样下发的流表才是正确的。

但是在下发的时候还需要注意许多细节，比如：

* **并不是所有的数据包都有vlan\_tag**。如0x0800就是纯IP，并没有携带vlan_tag，所以填充式应根据packet\_in的具体情况填充。
* **并不是所有的数据都有四层端口**，所以四层的源端口，目的端口都不是任何时候都能由packet\_in去填充的。不去管就好了，默认的会填充一个默认值，匹配的时候不去匹配4层端口就没有问题。

####FLOW_MOD

这里面的信息也是至关重要的。

	class ofp_flow_mod(Packet):
	    name = "OpenFlow Flow Modify"
	    fields_desc=[ BitField("cookie", 0, 64), #Opaque controller-issued identifier
	                  ShortEnumField("command", 0, ofp_flow_mod_command),
	                  ShortField("idle_timeout", 60),
	                  ShortField("hard_timeout", 0),
	                  ShortField("priority", 0),
	                  IntField("buffer_id", 0),
	                  ShortField("out_port", 0),
	                  #flags are important, the 1<<0 bit is OFPFF_SEND_FLOW_REM, send OFPT_FLOW_REMOVED
	                  #1<<1 bit is OFPFF_CHECK_OVERLAP, checking if the entries' field overlaps(among same priority)  
	                  #1<<2 bit is OFPFF_EMERG, used only switch disconnected with controller) 
	                  ShortField("flags", 0)]

**command里面的类型决定了flow_mod的操作是添加，修改还是删除等。类型如下**

	ofp_flow_mod_command = { 0: "OFPFC_ADD",            # New flow
	                         1: "OFPFC_MODIFY",         # Modify all matching flows
	                         2: "OFPFC_MODIFY_STRICT",  # Modify entry strictly matching wildcards
	                         3: "OFPFC_DELETE",         # Delete all matching flows
	                         4: "OFPFC_DELETE_STRICT"}  # Strictly match wildcards and priority

**例如：如果要添加一条新流，command=0。**

**两个时间参数idle\_timeout & idle\_timeout：**

* **idle\_timeout:如值为10，则某条流在10秒之内没有被匹配，则删除，可以称之为活跃时间吧。**
* **hard\_timeout:如值为30，则30秒到达的时候，一定删除这条流，即使他还活跃，即被匹配。**

####priority

priority是流的优先级的字段，**字数越大则优先级越高，存放在号数越小的table中**。

####buffer\_id

由交换机指定的buffei_id,准确的说是由dpid指定的。如果是手动下发的流，**buffer\_id应填-1**，即0xffff,告诉交换机这个数据包并没有缓存在队列中。

####out_port

指定流的出口，但是这个出口并不是直接指导流转发的，至少我是这么觉得，指导流转发的出口会在action里面添加，这个端口是为了在flow_removed的时候查询，并返回控制器的作用。（求纠正！）

有一些端口是很特殊的，如flood，local等。具体分类如下：

	ofp_port = { 0xff00: "OFPP_MAX",
	             0xfff8: "OFPP_IN_PORT",
	             0xfff9: "OFPP_TABLE",
	             0xfffa: "OFPP_NORMAL",
	             0xfffb: "OFPP_FLOOD",
	             0xfffc: "OFPP_ALL",
	             0xfffd: "OFPP_CONTROLLER",
	             0xfffe: "OFPP_LOCAL",
	             0xffff: "OFPP_NONE"}
如果你不知道端口是多少，最好填flood,也就是0xfffb。

####flags

在上面的注释中也说得比较清楚了。如果没有特殊用处，**请将他置1**，因为这样能让交换机在删除一条流的时候给交换机上报flow_removed信息。

###ACTION

action是OpenFlow里面最重要的结构。对，他也是最重要的。每一条流都必须指定必要的action,不然匹配上之后，**没有指定action，交换机会默认执行drop操作。**

action有2种类型：

* **必备行动: Forward  and Drop**

* **选择行动:FLOOD,NALMAL 等**

如添加output就是一个必须要添加的action.每一个action最好有一个action_header(),然后再接一个实体。如：

	ofp_action_header(type=0)/ofp_action_output(type =0, port =oxfffb,len =8)

具体的action类型如下：

	ofp_action_type = { 0: "OFPAT_OUTPUT",
	                    1: "OFPAT_SET_VLAN_VID",
	                    2: "OFPAT_SET_VLAN_PCP",
	                    3: "OFPAT_STRIP_VLAN",
	                    4: "OFPAT_SET_DL_SRC",
	                    5: "OFPAT_SET_DL_DST",
	                    6: "OFPAT_SET_NW_SRC",
	                    7: "OFPAT_SET_NW_DST",
	                    8: "OFPAT_SET_NW_TOS",
	                    9: "OFPAT_SET_TP_SRC",
	                    10: "OFPAT_SET_TP_DST",
	                    11: "OFPAT_ENQUEUE"
	               		}


action不仅仅会出现在flow\_mod中，也会出现在如stats\_reply中。

###OFPT\_BARRIER\_REQUEST  && REPLY

这个数据包可以的作用很简单，交换机在收到OFPT_BARRIER_REQUEST的时候，会回复控制器一个OFPT\_BARRIER\_REPLY。我们默认数据下发的顺序不会在传输中发生变化，在进入消息队列之后处理也是按照FIFO进行的，那么只要在flow\_mod之后发送这个数据，当收到reply之后，交换机默认flow已经写成功。也许你会问他只是保证了flow\_mod命令执行了，写入的结果如何并没有保证，如何确定确实写入流表了呢？

* 如果非逻辑错误，那么交换机在处理flow\_mod的时候会报错。所以我们会知道写入结果。
* 如果是逻辑错误，那么会写进去，但是逻辑错误应该是人的问题，所以barrier还是有他的功能的。

###OFPT\_FLOW\_REMOVED

如果flow\_mod的flags填成1，则该流在失效之后会回复控制器一条OFPT\_FLOW\_REMOVED信息。

* 结构：header()/wildcards()/match()/flow_removed()
* 作用：在流失效的时候回复控制器，并携带若干统计数据。


		class ofp_flow_removed(Packet):
		  name = "OpenFlow flow removed"
		  fields_desc = [ BitField("cookie", 0, 64),
		                  BitField("priority", 0,16),
		                  BitField("reason", 0, 8),
		                  ByteField("pad", None),
		                  BitField("duration_sec", 0, 32),
		                  BitField("duration_nsec", 0, 32),
		                  BitField("idle_timeout", 0, 16),
		                  ByteField("pad", 0),
		                  ByteField("pad", 0),
		                  BitField("packet_count", 0, 64),
		                  BitField("byte_count", 0, 64)
		                ]


其实的duration\_sec是流存在的时间，单位为秒，duration\_nsec单位为纳秒。

###OFPT\_STATS\_REQUEST && REPLY

以上的数据都是通信过程中必须的部分。还有一些数据包是为了某些目的而设计的，如OFPT\_STATS\_REQUEST && REPLY可以获得统计信息，我们可以利用统计信息做的事情就太多了。如：**负载平衡**， 流量监控等基于流量的操作。

####OFPT\_STATS\_REQUEST

OFPT\_STATS\_REQUEST类型有很多，回复的类型也很多。
	
	class ofp_stats_request(Packet):
	    name = "OpenFlow Stats Request"
	    fields_desc=[ ShortEnumField("type", 0, ofp_stats_types),
	                  ShortField("flag", 0)]     

####Type

* 0:请求交换机版本信息，制造商家等信息。
* 1:单流请求信息
* 2:多流请求信息
* 3:流表请求信息
* 4:端口信息请求
* 5:队列请求信息
* 6:vendor请求信息，有时候没有定义。


		   msg = { 0: of.ofp_header(type = 16, length = 12)/of.ofp_stats_request(type = 0),                            #Type of  OFPST_DESC (0) 
		            1: of.ofp_header(type = 16, length = 56)/of.ofp_stats_request(type =1)/ofp_flow_wildcards/ofp_match/of.ofp_flow_stats_request(out_port = ofp_flow_mod.out_port),                  #flow stats
		            2: of.ofp_header(type = 16, length =56)/of.ofp_stats_request(type = 2)/ofp_flow_wildcards/of.ofp_match/of.ofp_aggregate_stats_request(),                                  # aggregate stats request
		            3: of.ofp_header(type = 16, length = 12)/of.ofp_stats_request(type = 3),                            #Type of  OFPST_TABLE (0) 
		            4: of.ofp_header(type = 16, length =20)/of.ofp_stats_request(type = 4)/of.ofp_port_stats_request(port_no = port),   # port stats request    
		            5: of.ofp_header(type = 16, length =20)/of.ofp_stats_request(type =5)/of.ofp_queue_stats_request(), #queue request
		            6: of.ofp_header(type = 16, length = 12)/of.ofp_stats_request(type = 0xffff)                        #vendor request
		        } 


####OFPT\_STATS\_REPLY

每一种请求信息都会对应一种回复信息。我们只介绍最重要的**flow\_stats\_reply**。

* 结构：**header(type=17)/reply\_header()/flow\_stats/wildcards/match/
flow\_stats\_data**
* 作用：携带流的统计信息，如通过的数据包个数，字节数。
 
**ofp\_flow\_stats(body[4:8])**里面会有的**table\_id**字段表明该流存放在哪一个流表里。
		          
**flow\_stats\_data里面有packet\_count和byte\_count是最有价值的字段，流量统计就是由这两个字段提供的信息。**

如想统计某条流的速率：**前后两个reply的字节数相减除以duration\_time只差就可以求得速率**

由速率我们可以做很多基于流量的app，如**流量监控，负载均衡**等等。

值得注意的是，在这些数据之后，其实还有一些**action**,但是目前我还没有查看这些action到底是干什么用的。


##后续

写到这里，我使用到的数据包都写了一遍，其他的报文其实道理也是一样的。如**OFPT\_GET\_CONFIG\_REQUEST和REPLY**，道理应该和stats一样，只是数据结构不一样罢了。不再多说。


最后把我们用的一些比较多的信息帖出来让大家更好的学习。

###ERROR

在调试的过程中遇到错误是再所难免的，前面也提到了error的结构。这里就贴一下type跟code吧。

####Type
	ofp_error_type = { 0: "OFPET_HELLO_FAILED",
	                   1: "OFPET_BAD_REQUEST",
	                   2: "OFPET_BAD_ACTION",
	                   3: "OFPET_FLOW_MOD_FAILED",
	                   4: "OFPET_PORT_MOD_FAILED",
	                   5: "OFPET_QUEUE_OP_FAILED"}

####相关的code：

	ofp_hello_failed_code = { 0: "OFPHFC_INCOMPATIBLE",
	                          1: "OFPHFC_EPERM"}
	
	ofp_bad_request_code = { 0: "OFPBRC_BAD_VERSION",
	                         1: "OFPBRC_BAD_TYPE",
	                         2: "OFPBRC_BAD_STAT",
	                         3: "OFPBRC_BAD_VENDOR",
	                         4: "OFPBRC_BAD_SUBTYPE",
	                         5: "OFPBRC_EPERM",
	                         6: "OFPBRC_BAD_LEN",
	                         7: "OFPBRC_BUFFER_EMPTY",
	                         8: "OFPBRC_BUFFER_UNKNOWN"}
	
	ofp_bad_action_code = { 0: "OFPBAC_BAD_TYPE",
	                        1: "OFPBAC_BAD_LEN",
	                        2: "OFPBAC_BAD_VENDOR",
	                        3: "OFPBAC_BAD_VENDOR_TYPE",
	                        4: "OFPBAC_BAD_OUT_PORT",
	                        6: "OFPBAC_BAD_ARGUMENT",
	                        7: "OFPBAC_EPERM",          #permissions error
	                        8: "OFPBAC_TOOMANY",
	                        9: "OFPBAC_BAD_QUEUE"}
	
	ofp_flow_mod_failed_code = { 0: "OFPFMFC_ALL_TABLES_FULL",
	                             1: "OFPFMFC_OVERLAP",
	                             2: "OFPFMFC_EPERM",
	                             3: "OFPFMFC_BAD_EMERG_TIMEOUT",
	                             4: "OFPFMFC_BAD_COMMAND",
	                             5: "OFPFMFC_UNSUPPORT"}
	
	ofp_port_mod_failed_code = { 0: "OFPPMFC_BAD_PORT",
	                             1: "OFPPFMC_BAD_HW_ADDR"}
	
	ofp_queue_op_failed_code = { 0: "OFPQOFC_BAD_PORT",
	                             1: "OFPQOFC_BAD_QUEUE"}


谢谢我的两个师傅richardzhao,kimi带我走进OpenFlow的世界。

####整篇文档均为牧紫星原创，转载请声明告知。希望能给你带来一些帮助。
