title:OpenVirteX：Operation and Subsystems
date:2014/10/28
tags:network virtualization
category:Tech

##前言

继上篇[《OpenVirteX文档概述（一）：Overview and Components》](http://www.muzixing.com/pages/2014/10/23/openvirtexwen-dang-xiang-jie-overview-and-components.html)之后，本篇将继续介绍OVX的Operation and Subsystems部分。主要讲述OVX内部的运作原理，本文属于个人简介，有误之处敬请指出，希望对读者有所帮助。本篇的顺序依然是按照官网文档的顺序介绍。

##简介

本部分将介绍OVX内部的工作原理，如哪些内部子系统实现了哪一些功能，从而使得OVX能支持OpenFlow网络的虚拟化。以下的内容将分为如下的小点介绍：

* System Overview
* Startup and Shutdown
* The Event Loops
* Network Discovery and Presentation
* Virtualization and De-virtualization
* State Synchronization
* Reslience
* persistence
* The JSONRPC API

##System Overveiw

OVX分为以下几个主要的部分：

* 一半是面向南向物理基础设施的部分 ，管理了datapath到OVX之间的OpenFlow通道，并建立和维持了一系列数据结构，用于描述物理基础网络。
* 另一半是面向北向租户控制器的部分，向租户控制器提供由OVXSwicth等组成的虚拟网络，并维护好OVX到各个租户控制器的OpenFlow通道。
* Global maps则保存了物理设施到OVXNetwork的component之间的映射关系，完成PhysicalNetwork到OVXNetwork之间的桥接路由（其实就是映射）。
* JSON的API用于配置和获取系统的信息。

Global mapping是在OVXNetwork被创建的时候完成的，两段channel的管理也在不同的IO Loop中完成配置，使得从datapath到tenant controller的两段OpenFlow channel 能够正确对接成一条完整的controller channel。每一个需要被路由到OVXNetwork，或者需要横跨南北两部分的数据包都要在loop中调用virtualize()或者devirtualize()函数以完成消息的转换。由于global map的存在，使得底层物理网络和租户的虚拟网络之间的状态可以解耦，从而使得OVXNetwork可以在运行状态下动态地改变网络，也让OVX可以在没有任何租户网络的情况下控制底层网络。

##Startup and Shutdown

这部分将要介绍的是OVX启动和关闭时OVX内部的程序运作流程。分为以下4个小节：

* Main process startup
* PhysicalNetwork / Southbound channel initialization
* Tenant Network (OVXNetwork) / Northbound channel initialization
* System shutdown

###Main process startup

OVX的入口方法在**OpenVirteX.java[package net.onrc.openvirtex.core]**文件,通过解析命令行的输入参数来启动OpenVirteXController,OpenVirteXController完成了OVX核心的启动，也完成了环境变量，OVX参数等系统配置和初始化。启动的内容包括：

* 初始化单一的PhysicalNetwork实例，用于描述底层物理网络。
* 尝试连接数据库，恢复数据库中先前存在虚网。
* 启动API服务，接受API调用。
* 初始化南向的通道处理函数，监听网络事件。

第三步的时候，OVX监听API调用，第四步时，监听来自datapaths的连接。

###PhysicalNetwork population / Southbound channel initialization

交换机连接到OVX以及链路发现的数据都记录到了PhysicalNetwork中。OVX为每一个交换机创建了一个PhysicalSwitch和SwitchDiscoveryManger的对象，用户描述交换机。此时OVX对于交换机而言，就是一个控制器。以下的图形象地描述了OVX在处理datapath连接时的状态变化。

![](http://ovx.onlab.us/wp-content/uploads/2014/04/ClientFSM.png)

Fig.1:OVX的南向与datapath握手的状态机示意图

如果对这个经典的OpenFlow协议的状态机不熟悉，可以参考[《OpenFlow通信流程解读》](http://www.muzixing.com/pages/2013/12/12/yuan-chuang-openflowtong-xin-liu-cheng-jie-du.html)

**SwitchChannelHandler [net.onrc.openvirtex.core.io]**将这个状态机设置成枚举类型的ChannelState,每一个状态都有对应的方法去处理当前状态下的事件和消息。

当datapath达到WAIT\_DESCRIPTION\_STAT\_REPLY之后，OVX才能将datapath映射成一个PhysicalSwitch。利用datapath提供的信息，OVX可以对datapath对应的PhysicaiSwitch进行配置，并将其加入到PhysicalNetwork中。当SwitchDiscoveryManager找到datapath的PhysicalNetwork，并且PhysicalSwitch的statisticsManager开启之后，datapath进入ACTIVE状态。当datapath进入ACTIVE状态时，datapath将参与到网络发现和OVX的事件循环当中，此时的datapath是一个正常运行状态的交换网桥。

###Tenant network (OVXNetwork) / Northbound channel initialization

一个租户的网络的创建、配置和初始化都通过API的调用，其中步骤包括：

* Declare an OVXNetwork, the Address block used, and tenant controller(s) to  

* connect the OVXNetwork to

* Create OVXSwitches from available PhysicalSwitches

* Add OVXPorts to the OVXSwitches

* Add OVXLinks, Hosts, and for BVSes, SwitchRoutes

* If manual, specify paths for OVXLinks and SwitchRoutes

* Optionally, add backup paths for OVXLinks and SwitchRoutes

* Initialize the OVXNetwork

以上的步骤完成之后，OVX需要将其components初始化，并将virtual components映射到PhysicalNetwork components，并记录在global map中。然后将虚拟的components状态置为ACTIVE,在这种非常具有强制依赖性的顺序之下，最终完成OVXNetwork的初始化。具体的API都写在了**API server [net.onrc.openvirtex.api.server]**中，他们在**tenant handlers [api.server.handlers.tenant]**中被调用。具体的接口函数此处不加赘述，读者可到官网查看，也可以直接查看源码。下图描述了OVX中tenant Network的创建过程：
![](http://ovx.onlab.us/wp-content/uploads/2014/04/VnetInit.jpg)

每一个Component都包含有register()和boot()的接口函数用于注册和初始化component。容易意识到的一点是，这些Component的启动肯定是有顺序的，或者说他们之间的以来关系肯定是固定的。如端口必然以来于交换机，没有交换机类，就不会有端口类。下图介绍了Components之间的包含和映射关系。其中实线为包含关系，虚线为映射关系。

![](http://ovx.onlab.us/wp-content/uploads/2014/04/dependencies.png)


**ControllerChannelHandler [net.onrc.openvirtex.core.io]**	负责OVXSwitch实例到tenant controller的连接，并维持一个状态机如下图所示。当且仅当一个OVXNetwork完成了所有OVXSwitch和控制器的连接时，才能进入ACTIVE状态。此时的OVX对于tenant Controller而言是一个datapath。

![](http://ovx.onlab.us/wp-content/uploads/2014/04/ServerFSM.png)


###System shutdown

**OpenVirtexShutdownHook [net.onrc.openvirtex.core.io]**调用 OpenVirteXController.terminate()方法完成系统的关闭。这个方法关闭了面向租户和面向datapath两端的channel，也注销了PhysicalNetwork。

##The Event Loops

这部分将介绍OVX的I/O loop。

###Overview

OVX event loop主要用于处理OpenFlow messages。主要完成如下三个功能：

* 负责OVX与datapath、OVX和tenant controller的OpenFlow协议通信。
* 完成OpenFlow messages的virtualize()和devirtualize():主要是将来自datapath的OpenFlow消息重写，路由到对应的租户控制器以及反向的消息转换。
* 保持OVX和datapath、OVX和tenant controller的连接。

###Message handling and (de)virtualization

OVXMessages部署了以下的两个接口中任意一个或者全部：

**Virtualizable**: virtualize(PhysicalSwitch sw) : controller-bound messages

**Devirtualizable** : devirtualize(OVXSwitch sw) : network-bound messages

这两个接口函数的参数都是switch类的子类。对于那些没有必要跨越virtual-physical gap的消息，就没有这些方法，如keep alive的消息（echo-request and echo-reply）。而那些需要从datapath一直交付到tenan controller的消息就必须要这写方法了，如flow_mod。

这些方法在handleIO()调用。handleIO()是PhysicalSwitch和OVXSwitch类中abstract method。

	@Override
	public void handleIO(OFMessage msg, Channel channel) {
	    this.state.handleIO(this, msg, channel);
	}


当交换机处于ACTIVE状态时，才会被调用。

PhysicalPhysicalSwitch.Switchstate.ACTIVE满足时，handleIO允许被调用。函数代码如下：

	public void handleIO(PhysicalSwitch psw, final OFMessage msg, Channel ch) {
	    try {
	        ((Virtualizable) msg).virtualize(psw);
	    } catch (final ClassCastException e) {
	    psw.log.error("Received illegal message : " + msg);
	    }
	}

OVXSwitch.Switchstate.ACTIVE满足时，函数代码如下：

	public void handleIO(OVXSwitch vsw, final OFMessage msg, Channel ch) {
	    /*
	     * Save the channel the msg came in on
	     */
	    msg.setXid(vsw.channelMux.translate(msg.getXid(), ch));
	    try {
	        /*
	         * Check whether this channel (ie. controller) is permitted
	         * to send this msg to the dataplane
	         */
	
	        if (vsw.roleMan.canSend(ch, msg) )
	            ((Devirtualizable) msg).devirtualize(vsw);
	        else
	            vsw.denyAccess(ch, msg, vsw.roleMan.getRole(ch));
	    } catch (final ClassCastException e) {
	        OVXSwitch.log.error("Received illegal message : " + msg);
	    }
	}



其整个event loop（事件循环）示意图如下：

![](http://ovx.onlab.us/wp-content/uploads/2014/07/io_main-622x1024.png)

从上图中我们可以看到一些细节部分，比如来自租户的LLDP数据包是不会发送到datapath的。直接在OVX查询topology的数据结构就可以模拟出LLDP的效果了。同样OVX不断的在发送LLDP数据包，而packet_in数据类型而LLDP时，不会交给租户的控制器，而是由OVX的拓扑发现模块去处理，事实上，OVX就是一个控制器！只不过，它比控制器多出来虚拟化的功能，从而将网络的管理权，交给了各个租户的控制器而已。蓝色部分是面向租户的，橙色部分是面向datapath的，而中间的淡绿色部分是global部分。通过调用virtualize()和devirtualize()函数和使用global map数据完成消息的转换。

###Network Discovery and Presentation

为了保证虚拟化的准确性，OVX必须保证获取到实时的网络试图，这就需要做以下的事情：

* 探测拓扑和流表的变化
* 将拓扑变化对应地修改到PhysicalNetwork和PhysicalSwitch数据结构中。
* 检测拓扑变化是否对租户的虚网有影响，有则更新租户虚网拓扑信息。

这一部分需要注意的一个重点是，OVX对网络拓扑，特别是对虚网拓扑的处理。按常规思路，直接下发转发tenan controller的LLDP数据包，和上传LLDP的packet_in是最简单的。但是代价就是会增加OVX的IO压力，给网络增加过多的流量。优化方法就是由OVX代理获取物理拓扑，而对于租户的拓扑探测请求则直接通过查询OVX的拓扑信息返回，这样就可以使得来自租户控制器的大量LLDP数据包在OVX上就得到回复，从而模拟了拓扑发现过程。

####Topology discovery/LLDP handling

**Physical LLDP handling**

每一个PhysicalNetwork的SwitchDiscoveryManager负责处理LLDP消息。其处理流程如下图：

![](http://ovx.onlab.us/wp-content/uploads/2014/04/SDMgr-loop-1024x807.png)

根据每一个端口的探测计数器结果（默认为3），可以将端口分为fast和slow端口。其中fast端口为内部端口，即端口对端也是一个交换机端口，能回复LLDP数据包。否则就是slow端口，理论上slow端口为连接主机的端口。每一次发送一个探测包，探测计数器就加1，收到回复则减1，当计数器大于3时，可将端口定义为slow port，这些数据都存储在Map<Short, AtomicInteger> portProbeCount。

####PhysicalSwitch Statistics Collection

在OVX中统计信息存储在如下的数据结构中：

	AtomicReference<Map<Short, OVXPortStatisticsReply>> portStats;
	AtomicReference<Map<Integer, List>> flowStats;

OVX通过**StatisticsManager[net.onrc.openvirtex.elements.datapath.statistics]**来获取统计信息。

**Physical flow table synchronization**

OVX通过周期地发送statisticsRequest来收集网络的统计信息，并存储在PhysicalSwitch.flowStats之中。具体的实现可以查看**StatisticsManager[net.onrc.openvirtex.elements.datapath.statistics]**等模块。

###OVXNetwork Presentation

**Virtual topology presentation**OVX通过查找OVX拓扑数据，来回复租户的拓扑发现请求，从而显著减少了LLDP消息在物理网络中的传播。其中步骤为：

* 查找neighborPortMap表中destination port的数据
* 将结果封装成LLDP报文的packet_in并发送给租户控制器。

下图介绍了这个处理流程。

![](http://ovx.onlab.us/wp-content/uploads/2014/04/topology-resolution-1024x616.png)

OVX目前还没有做关于租户多控制器的实现。

##Network Virtualization

本部分将介绍OVX的核心模块，网络虚拟化模块，主要完成virtual<--->physical之间的映射转换。主要完成源目地址的修改，接入端口的翻译，OF消息的翻译等内容。具体的实现将分为以下几部分介绍。

* Switch Representation Translation
* OpenFlow field translation – Cookies, Buffer IDs, XIDs
* Address virtualization
* Link and Route virtualization

###Switch Representation Translation

* **OVXSwitch -> PhysicalSwitch (Southbound)**
	
	通过拦截从tenant controller发向datapath的消息，以in_port为键值查找对应的PhysicalPort,从而找到对应的物理交换机，也可以通过tenant ID的方式查找OVXMap。具体实现，读者需要自行查看源码。
	
* **PhysicalSwitch -> OVXSwitch (Northbound)**

	上行数据的查找可以直接通过MAC地址来查找，因为主机的MAC地址是唯一属于一个虚网的，所以可以作为key，用于查找tenantID，从而实现转换。也可以通过OpenFlow协议的消息字段，如xid，来找到某一个controller channel，而一个controller channel将对应一个租户的控制器。

###OpenFlow field translation – Cookies, Buffer IDs, XIDs

那些需要从datapath到租户控制器的OpenFlow消息都需要就行翻译。需要翻译的OpenFlow消息的字段包括cookies,buffer_id,xid等。

**XIDTranslator.XID**需要在datapath上唯一，这个是OpenFlow协议的规定。而OVX在翻译消息的构成中，需要将来自datapath的xid以及生成的xid的键值对存储下来，以便在反向通信时，还原成原来的数据，保证通信的正确性。这个工作由XidTranslator.translate()完成，其中包括以下几个步骤：

* generates a new XID
* creates an XidPair to store the original XID and source OVXSwitch
* stores the XidPair in xidMap, using the new XID as the key
* returns the new XID value to the caller

反向的处理则由XidTranslator.untranslate()负责。

**OVXFlowTable**是以cookie为键值存储在OVX上的。而这个cookie的产生由generateCookie() 函数负责。每一个cookie的编码都有tenantID参与，保证在OVX上cookie的唯一性以及导向性。

	private long generateCookie() {
	    ...
	        final int cookie = this.cookieCounter.getAndIncrement();
	        return (long) this.vswitch.getTenantId() &lt;&lt; 32 | cookie;
	    }
	}

**bufferMap**在packet\_in/packet\_out数据中，他们共用一个buffer_id。在消息的转换过程中，需要将来自packet\_in的buffer\_id和生成的buffer\_id存起来，当packet\_out数据下发时，则需要查找，并转换。

###Address virtualization

**地址虚拟化是OVX中非常关键的部分**。为了允许用户使用任意的IP，OVX定义了OVXIPAddress用于描述用户定义的IP，这个IP地址在虚网内是唯一的。OVX还定义了PhysicalIPAddress,用于描述底层物理的IP地址，这个地址在物理网络中是唯一的。在数据层面的通信中，OVX需要将边源端口的入口流量重写IP地址成PhysicalIPAddress,还需要重写边源端口的出流量数据的IP，转换成OVXIPAddress,从而向租户展现一个使用了租户定义地址的通信流程。而中间的转发过程，也即在core datapath的转发过程中，一直都是使用PhysicalIPAddress的，且其转发等行为也由OVX直接完成了。

为了完成这个工作，OVX将datapath分为两种：

* core datapath:仅和datapath相连的内部datapath,没有host挂载。
* edge datapath:连接有host的datapath。

对于edge datapath而言，OVX需要作如下两件事情：

* 对于来自网络侧的流量，查询映射表，将PhysicalIPAddress重写成OVXIPAddress.
* 对于来自主机测的流量，查询映射表，将OVXIPAddress重写成PhysicalIPAddress.

下图举例介绍了一个简单的通信流程：

![](http://ovx.onlab.us/wp-content/uploads/2014/07/addr_virt.png)

图中蓝色部分为使用OVXIPAddress通信的部分，橙色部分为使用PhysicalIPAddress通信的部分。其中:

* a为packet\_in过程，直接发送给tenant controller;
* b是packet\_out过程，b过程需要将OVXIPAddress重写成PhysicalIPAddress;
* c过程是core datapath的控制过程，直接由OVX完成，不需要上传给tenant controller，如果在虚妄中并没有这个交换机的存在的话。
* d过程是对端edge datapath的packet\_in过程，上传到OVX上时，需要转换成OVXIPAddress,进行虚拟化转换，才能转发给tenant controller。
* e过程为packet\_out过程，OVX需要将PhysicalIPAddress重写成OVXIPAddress。

####Implementations

以下介绍哪一些消息需要转换。

**PhysicalIPAddress -> OVXIPAddress:**
	
* OVXPacketIn

**OVXIPAddress -> PhysicalIPAddress:**

* OVXPacketOut
* OVXFlowMod
* OVXActionNetworkLayerSource/Destination

以下图片举例介绍了virtualize和devirtualize的流程：

![](http://ovx.onlab.us/wp-content/uploads/2014/04/PacketIn.png)

**PacketIn virtualization**


![](http://ovx.onlab.us/wp-content/uploads/2014/04/PacketOut-1024x682.png)

**PacketOut devirtualization**

![](http://ovx.onlab.us/wp-content/uploads/2014/04/FlowMod-1024x863.png)
**FlowMod devirtualization**



###Link and Route virtualization

TODO

##State Synchronization

###Error Escalation

OVX通过获取到网络的错误来同步PhysicalNetwork，如某一个port Down掉了，那么在PhysicalNetwork就应该更新其状态，并把与之对应的link down掉。这些状态变化依赖于PortStatus消息，这些消息的处理由**OVXPortStatus [net.onrc.openvirtex.messages]**负责。

OVX拥有错误消除的能力，能在一定范围内，隐藏底层网络中发生的错误事件，及时调整策略，保障租户的虚网正常运行。如一个BVS（Big Virtual Switch）中有一条链路发生故障，OVX可以重新映射一条没有人使用的备用链路，从而向租户隐藏错误。而对于普通的链路，OVX也可以将故障的OVXLink重新映射到冗余的链路上，保障网络的连通性。以下举例说明：

![](http://ovx.onlab.us/wp-content/uploads/2014/04/err_ignore.png)

* 左边的图中，b,c两点并没有映射到租户的虚网中，所以OVX完全向租户控制器隐藏了这些错误，当然租户的控制器才不关心这些不属于他的交换机到底什么状态。
* 中间的图，a,d两点之间有多条path,当且仅当，所有的path都down掉，OVX才会通知租户控制器这一事件。
* 右边的图中，当a到b的SwitchRoute都down掉时，才会向租户上报错误。

###Flow Table State Synchronization

**OVXFlowTable Synchronization**

 来自tenant controller的flow\_mod在进行devirtualize()转换之前，需要存储在OVX上。tenant controller查看流表信息时，直接查看的就是存储在OVX上的流表信息。OVX始终为通过**OVXFlowMods [net.onrc.openvirtex.messages]**来为OVXSwitch保存着一个实时更新的flow table。

	/* Within class OVXFlowMod */
	public void devirtualize(final OVXSwitch sw) {
	    ...
	    FlowTable ft = this.sw.getFlowTable();
	    ...
	    long cookie = ((OVXFlowTable) ft).getCookie();
	    //Store the virtual flowMod and obtain the physical cookie
	    ovxMatch.setCookie(cookie);
	    /* update sw's OVXFlowTable */
	    boolean pflag = ft.handleFlowMods(this, cookie);

**OVXFlowTable.handleFlowMods()**根据flow\_mod的command类型来修改对应的流表项。

在虚拟的流表被更新之后，OVX将把这个更新下发到datapath，实时修改datapath的流表。

**Physical flow table synchronization** 
datapath的flow table信息被记录在PhysicalSwitch.flowStats数据结构中。每一个PhysicalSwitch实例中的**StatisticsManager [net.onrc.openvirtex.elements.datapath.statistics]**负责周期地发送 OFFlowStatisticsRequests来获取统计数据，普遍的可以设置为30秒为刷新周期。

**Synchronization between flow tables**

physical flow table和virtual flow table的同步通过virtualize()函数和devirtualize()函数实现。具体代码实现如下：

	public void virtualize(final PhysicalSwitch sw) {
	    /* determine tenant from cookie */
	    int tid = (int) (this.cookie &gt;&gt; 32);
	    ...
	    try {
	        /* find which OVXSwitch's flowtable is affected */
	        OVXSwitch vsw = sw.getMap().getVirtualSwitch(sw, tid);
	        if (vsw.getFlowTable().hasFlowMod(this.cookie)) {
	            OVXFlowMod fm = vsw.getFlowMod(this.cookie);
	            vsw.deleteFlowMod(this.cookie);
	            /* send north ONLY if tenant controller wanted a FlowRemoved for the FlowMod*/
	            if (fm.hasFlag(OFFlowMod.OFPFF_SEND_FLOW_REM)) {
	            writeFields(fm);
	            vsw.sendMsg(this, sw);
	        }
	    }
	    ...
	}

##Resilience

网络中的网元肯定是会有down掉的时候的。为了减少这些底层设施的failures影响到租户的网络，OVX采用了冗余映射的方式，解决这一问题，主要包括以下的方面：

* OVXLinks : multiple paths

* SwitchRoute : multiple paths

* OVXBigSwitch : multiple SwitchRoutes, sets of PhysicalSwitches, or SwitchRoutes with multiple paths

当某一个冗余映射的component发生故障时，他就可以通过调用**Resilient[net.onrc.openvirtex.elements]**接口完成故障恢复。这个接口提供了以下连个方法：

* public boolean tryRecovery(Component c) : Given the failure of c, attempt to switch over to any backup mappings, if possible

* public boolean tryRevert(Component c) : Given the resumed function of c, attempt to switch back to the original (favored) mapping

以下将两个过程介绍了link故障和linkh恢复的过程。

![](http://ovx.onlab.us/wp-content/uploads/2014/04/tryRecovery.png)

从上图可以看出，当physical link failed时,OVX将在查找他的备份链路，试图重新映射，并把以前的流表导入到新的link相关的switch中，同时还需要将failed的link加入到broken set，将重新映射的link从backup list中删除。

![](http://ovx.onlab.us/wp-content/uploads/2014/04/tryRevert.png)

上图介绍了链路恢复的过程。当之前failed的link重新恢复之后，OVX将自动尝试将映射恢复到原来的链路上，这包括流表的倒换等操作。这时需要注意的是链路的优先级问题，假设原先的链路具有最高优先级，这能让问题变得简单一些。

##Persistence

本部分将介绍OVX中关于配置持续性的描述。OVX使用数据库存储用户的配置信息，并实时更新信息。当OVX重启时，能通过读取用户信息，迅速恢复租户的虚网。不仅仅包括虚网的拓扑，还包括所有的ID(tenantID, DPID等等)

###Configuration Parameters

<table class="table-bordered table-striped table-condensed">
<tr>
	<td><b>Option</b></td>
	<td><b>Argument</b></td>
	<td><b>Comments</b></td>
</tr>
<tr>
	<td>-dh or –db-host</td>
	<td>hostname</td>
	<td>default: "127.0.0.1"</td>
</tr>
<tr>
	<td>-dp or –db-port</td>
	<td>port</td>
	<td>default:27017</td>
</tr>
</table>

值得注意的是，当虚网没有提前进行配置时，会出现以下的问题：

* If OVX can’t connect to the database: Currently, this generates error messages in the log. These messages won’t interfere with the regular operation of OVX.

* Using the option “–db-clear”: All persistence data is deleted from storage.

###Related Packages and Classes

由于笔者对数据库不了解，所以这部分不做详细介绍，详情读者可以到官网查看文档。

####class DBManager

**Fields**

	// Database collection names
	public static final String DB_CONFIG = "CONFIG";
	public static final String DB_USER = "USER";
	public static final String DB_VNET = "VNET";
	
	// Database object
	private DBConnection dbConnection;
	
	// Map of collection names and collection objects
	private Map<String, DBCollection> collections;
	
	// Mapping between physical dpids and a list of vnet managers
	private Map<Long, List<OVXNetworkManager>> dpidToMngr;
	// Mapping between physical links and a list of vnet managers
	private Map<DPIDandPortPair, List<OVXNetworkManager>> linkToMngr;
	// Mapping between physical ports and a list of vnet managers
	private Map<DPIDandPort, List<OVXNetworkManager>> portToMngr;

**Methods**
	
	// Initialize database connection
	public void init(String host, Integer port, boolean clear)
	
	// Create a document in database from persistable object obj
	public void createDoc(Persistable obj)
	// Remove a document
	public void removeDoc(Persistable obj)
	
	// Save an element to the list of specified key in document
	public void save(Persistable obj
	// Remove an element from the list of specified key in document
	public void remove(Persistable obj)
	
	// Reads all virtual networks from database and spawn an OVXNetworkManager
	// for each.
	private void readOVXNetworks()
	
	// Reads virtual components from a list of maps in db format and registers the
	// physical components in their manager.
	private void readOVXSwitches(List<Map<String, Object>> switches,
	                        OVXNetworkManager mngr)
	private void readOVXLinks(List<Map<String, Object>> links,
	                        OVXNetworkManager mngr)
	private void readOVXPorts(List<Map<String, Object>> ports,
	                        OVXNetworkManager mngr)
	private void readOVXRoutes(List<Map<String, Object>> routes,
	                        OVXNetworkManager mngr)

####class OVXNetworkManager

OVXNetworkManager负责从数据库中恢复租户的虚网。

**Field**

	// Document of virtual network
	private Map<String, Object> vnet;
	
	private Integer tenantId;
	
	// Set of offline and online physical switches
	private Set<Long> offlineSwitches;
	private Set<Long> onlineSwitches;
	
	// Set of offline and online physical links identified as (dpid, port number)-pair
	private Set<DPIDandPortPair> offlineLinks;
	private Set<DPIDandPortPair> onlineLinks;
	
	// Set of offline and online physical ports
	private Set<DPIDandPort> offlinePorts;
	private Set<DPIDandPort> onlinePorts;
	
	private boolean bootState;

**Methods**

	// Register a physical component to offline list
	public void registerSwitch(final Long dpid)
	public void registerLink(final DPIDandPortPair dpp)
	public void registerPort(final DPIDandPort port)
	
	// Delete a physical component from offline list,
	// add it to online list,
	// and then, if all physical components are online,
	// create a virtual network.
	public synchronized void setSwitch(final Long dpid)
	public synchronized void unsetSwitch(final Long dpid)
	public synchronized void setLink(final DPIDandPortPair dpp)

####Storing Configurations

当虚网的component初始化之后，他们的信息将以文档的形式存入数据库。目前需要存在数据库中的component的如下所示：

* OVXNetwork
* OVXSingleSwitch
* OVXBigSwitch
* OVXPort
* OVXLink
* SwitchRoute
* Host

####Mechanism

当component初始化时，需要调用register()方法。在这个方法中，会调用DBManager.save()方法，用于将信息存储到数据库，其中包括：

* Gets target collection by getDBName() e.g. “VNET”
* Gets query index by getDBIndex() e.g. { “tenantId”:1 }
* Gets key by getDBKey() and value by getDBObject() e.g. key is “switches”, value is { “dpids”:[4], “vdpid”:400 }
* Adds (updates) this value into the list of this key by using MongoDB’s $addToSet operator. If the initial set is {“switches”:[{“dpids”:[1], “vdpid”:100}]}, this becomes {“switches”:[{“dpids”:[1], “vdpid”:100}, {“dpids”:[4], “vdpid”:400}]}

####Persistible Components

 OVXSwitch subclasses (OVXSingleSwitch, OVXBigSwitch), OVXLink, SwitchRoute, OVXPort and Host等class都具有persistible属性，都会将信息存储在数据库中。


####Updating (Deleting) Configurations

当component发生更新时，OVX会创建新对象去描述这个新的component，同时也要把这些新数据存到数据库中。但是这个过程对于全部的component来说并不是统一的，分为以下两种情况：

* **OVXNetworks** : DBManager.removeDoc() deletes a document of the specified virtual network. This method is called by OVXNetwork.unregister().

* **Other Elements** : DBManager.remove() deletes an element in the list of the value for specified key by the $pull operation of MongoDB. This method is called by component inactivation methods:

	* unregisterDP() – OVXSwitch
	* unregister() – OVXPort, OVXLink, SwitchRoute, OVXHost

####Restoring Configurations

当boot完成的时候，physical component是处于在offline状态的。OVX将去查询在offline list中的component是否还是offline，当OVX发现某一个physical element(物理网元)处于活跃状态时，将为其创建对应的physical component。当全部的physical element都处于active时，OVX将试图从数据库中恢复OVXNetwork

##后语

原本我想写的是OVX的文档详解，但是目前看来好像写成了文档翻译。因为确实我对于OVX只是通过文档了解到了一些皮毛，没有更深的理解，写出来的文章缺乏主观的观点。这种问题在很久以前我已经意识到。我自己目前陷入一种非常尴尬的状态，对新知识渴望，但是却了解甚少。所以以后的时间可能需要专心读书，沉下心来好好学术。博客已经开了快一年了，但是一直以来写的都是偏工程的教程和代码详解等文章，其学术意义不大。现在也成为一个研究生了，还没有找到一个合适的节奏，希望在以下的学习生活中，能脚踏实地，加强点核心竞争力吧。谢谢浏览本博客的所有人！





















