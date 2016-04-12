title:RYU入门教程
tag:SDN,RYU
CATEGORY:Tech
date:2014/9/20

###前言

辗转了POX,NOX,OpenDaylight等多个控制器之后，我终于意识到我只喜欢python语言的控制器。但是我依然记得OpenDaylight的Nullpointer的Exception,还记得YANG文件的深奥，但是OpenDaylight让我对控制器开发的兴趣减少了，这不是我想要的事情。最后，我下决定转向RYU。我突然发现，生活突然变得很美好。我用着我熟悉的，喜欢的，优美的python，写着充满美感的语句，犹如写诗一般的惬意。

本篇主要介绍如何安装RYU，和如何在RYU上开发APP。

###RYU的安装

安装RYU，需要安装一些python的套件,具体的安装方法可以谷歌，但推荐通过pip install安装，详情查看源码安装部分。

* python-eventlet
* python-routes
* python-webob
* python-paramiko

安装RYU主要有两种方式：
	
* pip安装
	
		pip install ryu

* 下载源文件安装
	
	 	git clone git://github.com/osrg/ryu.git
		cd ryu
		sudo pip install -r tools/pip-requires
		sudo python setup.py install

依赖软件已经在源码的tools/pip-requires文件中，通过pip install来批量安装依赖文件。这种安装方式相比逐个安装依赖要方便，且所需的所有的依赖由官方提供，全面而准确，所以推荐读者通过这种方式安装依赖。

安装之后，如果遇到lxml的问题，可以通过安装lxml来解决。

	apt-get install libxml2-dev libxslt1-dev python-dev
	apt-get install python-lxml

若遇到six版本不够的问题，则：

	pip uninstall six 
	pip install six

来安装高版本的six.

若还有更多问题，可参考[@linton小伙伴的博客](http://linton.tw/2014/02/15/note-install-ryu-36-sdn-framework/)

###RYU使用

安装RYU之后，进入ryu目录，输入：

	 ryu-manager yourapp.py

运行对应的APP，如

	ryu-manager simple_switch.py

###	RYU源码分析

当我安装好了RYU之后，第一件事就是迫不及待地去看它的源码，其可读性之高，超出我的想象。

下面介绍ryu/ryu目录下的主要目录内容。

* **base**
		
	base中有一个非常重要的文件：app_manager.py.其作用是RYU 应用的管理中心。用于加载RYU应用程序，接受从APP发送过来的信息，同时也完成消息的路由。
	
	其主要的函数有app注册、注销、查找、并定义了RYUAPP基类，定义了RYUAPP的基本属性。包含name,threads,events、event\_handlers和observers等成员，以及对应的许多基本函数。如：start(),stop()等。
	
	这个文件中还定义了AppManager基类,用于管理APP。定义了加载APP等函数。不过如果仅仅是开发APP的话，这个类可以不必关心。
	
* **controller**

	controller文件夹中许多非常重要的文件，如events.py,ofp_handler.py,controller.py等。其中controller.py中定义了OpenFlowController基类。用于定义OpenFlow的控制器，用于处理交换机和控制器的连接等事件，同时还可以产生事件和路由事件。其事件系统的定义，可以查看events.py和ofp\_events.py。

	在ofp\_handler.py中定义了基本的handler(应该怎么称呼呢？句柄？处理函数？)，完成了基本的如：握手，错误信息处理和keep alive 等功能。更多的如packet\_in\_handler应该在app中定义。

	在dpset.py文件中，定义了交换机端的一些消息，如端口状态信息等，用于描述和操作交换机。如添加端口，删除端口等操作。

	其他的文件不再赘述。

* **lib**

	lib中定义了我们需要使用到的基本的数据结构，如dpid,mac和ip等数据结构。在lib/packet目录下，还定义了许多网络协议，如ICMP,DHCP，MPLS和IGMP等协议内容。而每一个数据包的类中都有parser和serialize两个函数。用于解析和序列化数据包。

	lib目录下，还有ovs,netconf目录，对应的目录下有一些定义好的数据类型，不再赘述。

* **ofproto**

	在这个目录下，基本分为两类文件，一类是协议的数据结构定义，另一类是协议解析，也即数据包处理函数文件。如ofproto\_v1\_0.py是1.0版本的OpenFlow协议数据结构的定义，而ofproto\_v1\_0_parser.py则定义了1.0版本的协议编码和解码。具体内容不赘述，实现功能与协议相同。

* **topology**

	包含了switches.py等文件，基本定义了一套交换机的数据结构。event.py定义了交换上的事件。dumper.py定义了获取网络拓扑的内容。最后api.py向上提供了一套调用topology目录中定义函数的接口。

* **contrib**

	这个文件夹主要存放的是开源社区贡献者的代码。我没看过。

* **cmd**

	定义了RYU的命令系统，具体不赘述。

* **services**	

	完成了BGP和vrrp的实现。具体我还没有使用这个模块。

* **tests**

	tests目录下存放了单元测试以及整合测试的代码，有兴趣的读者可以自行研究。

###开发你自己的RYU应用程序

大概浏览了一下RYU的源代码，相信看过OpenDaylight的同学会发现，太轻松了！哈哈，我想我真的不喜欢maven,osgi,xml，yang以及java，但是不能不承认OpenDaylight还是很牛逼的，在学习的读者要坚持啊！

开发RYU的APP，真的再简单不过了。

先来最简单的：

	from ryu.base import app_manager

	class L2Switch(app_manager.RyuApp):
    	def __init__(self, *args, **kwargs):
        	super(L2Switch, self).__init__(*args, **kwargs)

如果你觉得非常熟悉，不要怀疑，我确实是在拿官网的例子再讲。

首先，我们从ryu.base import app_manager，在前面我们也提到过这个文件中定义了RyuApp基类。我们在开发APP的时候只需要继承这个基类，就获得你想要的一个APP的一切了。于是，我们就不用去注册了？！是的，不需要了！

保存文件，可以取一个名字为L2Switch.py。

现在你可以运行你的APP了。快得有点不敢相信吧！但是目前什么都没有，运行之后，马上就会结束，但起码我们的代码没有报错。

运行:
	
	ryu-manager L2Switch.py


继续往里面添加内容：

	from ryu.base import app_manager
	from ryu.controller import ofp_event
	from ryu.controller.handler import MAIN_DISPATCHER
	from ryu.controller.handler import set_ev_cls
	
	class L2Switch(app_manager.RyuApp):
	    def __init__(self, *args, **kwargs):
	        super(L2Switch, self).__init__(*args, **kwargs)
	
	    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	    def packet_in_handler(self, ev):
	        msg = ev.msg
	        datapath = msg.datapath
	        ofp = datapath.ofproto
	        ofp_parser = datapath.ofproto_parser
	
	        actions = [ofp_parser.OFPActionOutput(ofp.OFPP_FLOOD)]
	        out = ofp_parser.OFPPacketOut(
	            datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
	            actions=actions)
	        datapath.send_msg(out)

其中ofp_event完成了事件的定义，从而我们可以在函数中注册handler，监听事件，并作出回应。

packet\_in\_handler方法用于处理packet\_in事件。@set\_ev\_cls修饰符用于告知RYU，被修饰的函数应该被调用。（翻译得有点烂这句）

set\_ev\_cls第一个参数表示事件发生时应该调用的函数，第二个参数告诉交换机只有在交换机握手完成之后，才可以被调用。

下面分析具体的数据操作：

* ev.msg：每一个事件类ev中都有msg成员，用于携带触发事件的数据包。
* msg.datapath:已经格式化的msg其实就是一个packet\_in报文，msg.datapath直接可以获得packet\_in报文的datapath结构。datapath用于描述一个交换网桥。也是和控制器通信的实体单元。datapath.send\_msg()函数用于发送数据到指定datapath。通过datapath.id可获得dpid数据，在后续的教程中会有使用。
* datapath.ofproto对象是一个OpenFlow协议数据结构的对象，成员包含OpenFlow协议的数据结构，如动作类型OFPP_FLOOD。
* datapath.ofp\_parser则是一个按照OpenFlow解析的数据结构。
* actions是一个列表，用于存放action list，可在其中添加动作。
* 通过ofp\_parser类，可以构造构造packet\_out数据结构。括弧中填写对应字段的赋值即可。

如果datapath.send\_msg()函数发送的是一个OpenFlow的数据结构，RYU将把这个数据发送到对应的datapath。

至此，一个简单的HUB已经完成。

###RYU进阶——二层交换机

在以上的基础之上，继续修改就可以完成二层交换机的功能。具体代码如下：


	import struct
	import logging

	from ryu.base import app_manager
	from ryu.controller import mac_to_port
	from ryu.controller import ofp_event
	from ryu.controller.handler import MAIN_DISPATCHER
	from ryu.controller.handler import set_ev_cls
	from ryu.ofproto import ofproto_v1_0
	from ryu.lib.mac import haddr_to_bin
	from ryu.lib.packet import packet
	from ryu.lib.packet import ethernet
	
	class L2Switch(app_manager.RyuApp):
	
		OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]#define the version of OpenFlow
	
		def __init__(self, *args, **kwargs):
			super(L2Switch, self).__init__(*args, **kwargs)
			self.mac_to_port = {} 
	
		def add_flow(self, datapath, in_port, dst, actions):
			ofproto = datapath.ofproto
	
			match = datapath.ofproto_parser.OFPMatch(
				in_port = in_port, dl_dst = haddr_to_bin(dst))
	
			mod = datapath.ofproto_parser.OFPFlowMod(
				datapath = datapath, match = match, cookie = 0,
				command = ofproto.OFPFC_ADD, idle_timeout = 10,hard_timeout = 30,
				priority = ofproto.OFP_DEFAULT_PRIORITY,
				flags =ofproto.OFPFF_SEND_FLOW_REM, actions = actions)
	
			datapath.send_msg(mod)
	
		@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
		def packet_in_handler(self, ev):
			msg = ev.msg
			datapath = msg.datapath
			ofproto = datapath.ofproto
	
			pkt = packet.Packet(msg.data)
			eth = pkt.get_protocol(ethernet.ethernet)
	
			dst = eth.dst
			src = eth.src
	
			dpid = datapath.id    #get the dpid
			self.mac_to_port.setdefault(dpid, {})
	
			self.logger.info("packet in %s %s %s %s", dpid, src, dst , msg.in_port)
			#To learn a mac address to avoid FLOOD next time.
	
			self.mac_to_port[dpid][src] = msg.in_port
	
	
			out_port = ofproto.OFPP_FLOOD
			
			#Look up the out_port 
			if dst in self.mac_to_port[dpid]:
				out_port = self.mac_to_port[dpid][dst]
	
			ofp_parser = datapath.ofproto_parser
	
			actions = [ofp_parser.OFPActionOutput(out_port)]
	
			if out_port != ofproto.OFPP_FLOOD:
				self.add_flow(datapath, msg.in_port, dst, actions)
			

			#We always send the packet_out to handle the first packet.
			packet_out = ofp_parser.OFPPacketOut(datapath = datapath, buffer_id = msg.buffer_id,
				in_port = msg.in_port, actions = actions)
			datapath.send_msg(packet_out)
		#To show the message of ports' status.
		@set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
		def _port_status_handler(self, ev):
			msg = ev.msg
			reason = msg.reason
			port_no = msg.desc.port_no
	
			ofproto = msg.datapath.ofproto
	
			if reason == ofproto.OFPPR_ADD:
				self.logger.info("port added %s", port_no)
			elif reason == ofproto.OFPPR_DELETE:
				self.logger.info("port deleted %s", port_no)
			elif reason == ofproto.OFPPR_MODIFY:
				self.logger.info("port modified %s", port_no)
			else:
				self.logger.info("Illeagal port state %s %s", port_no, reason)

相信代码中的注释已经足以让读者理解这个程序。完成之后，运行:

	ryu-manager L2Switch.py

然后可以使用mininet进行pingall测试，成功！

###后语

习惯性还是写一写总结。RYU的方便简洁大大超出我的预料，比我使用过的任何一个控制器都要易于使用和开发。 这些是我学RYU一两天的收获，希望在后续的学习中还能有所收获，写出更好的博文。如果你有什么意见或建议可以评论，相互学习，共同进步。

最后提供一些有用的链接：

* http://osrg.github.io/ryu/resources.html
	
	我比较喜欢里里面的	http://ryu.readthedocs.org/en/latest/
	
	当然里面的电子书也是相当好的：http://osrg.github.io/ryu-book/en/html/

* 推荐一个小伙伴的博客：linton.tw 

	他在RYU上有更多的学习和研究。欢迎访问！


 

 

