date:2013-12-6
title:【原创】mininet搭建自定义网络拓扑 by muzi
category:Tech
tags:mininet


###你知道的mininet

相信很多研究SDN的朋友都知道mininet，也是用过mininet。但是恐怕大多数人都只是局限于workthough的水平.链接：http://mininet.org/walkthrough/

搭建更多的，灵活的拓扑还是有一定的难度。

上一次实验的时候，看了一下spirent testceter的一套测试拓扑，从中受益，学了一点。现在写出来分享一下。

如果你想快速建立拓扑，请直接拉到最后一个标题

###教你搭建你自己的任意拓扑

首先把需要用到的相关模块import进来。

	/#!/usr/bin/python

	import re
	from mininet.cli import CLI
	from mininet.log import setLogLevel, info,error
	from mininet.net import Mininet
	from mininet.link import Intf
	from mininet.topolib import TreeTopo
	from mininet.util import quietRun
	from mininet.node import RemoteController, OVSKernelSwitch

re模块提供python正则表达式的支持，我们会看到我们定义的checkIntf()函数会使用到正则表达式。

接着要从mininet中import进来很多文件，

* __CLI是命令行服务的文件。__

* __log是一些记录__

* __net里面包含了最重要的类，Mininet类，这是定义一个网络的类__

		class Mininet( object ):
	    "Network emulation with hosts spawned in network 	namespaces."
	
	    	def __init__( self, topo=None, switch=OVSKernelSwitch, host=Host,
                  controller=Controller, link=Link, intf=Intf,
                  build=True, xterms=False, cleanup=False, ipBase='10.0.0.0/8',
                  inNamespace=False,
                  autoSetMacs=False, autoStaticArp=False, autoPinCpus=False,
                  listenPort=None ):
	    
	以上的参数是基本的参数，也是最重要的参数。除了这些数据成员，Mininet类还有一些重要函数如：

		def addHost( self, name, cls=None, **params ):
	
		def addSwitch( self, name, cls=None, **params ):

		def addController( self, name='c0', controller=None, **params ):

		def ping( self, hosts=None, timeout=None ):
		
		def addLink( self, node1, node2, port1=None, port2=None,
                 cls=None, **params ):
	以上的函数已经足够你构建一个足够复杂的，足够灵活的网络了。

* __link里面的Intf是一个接口函数__
	
		class Intf( object ):

    		"Basic interface object that can configure itself."

    		def __init__( self, name, node=None, port=None, link=None, **params ):
	这个类可以用于定义一个网络接口，如：定义虚拟机某个网卡与mininet中某交换机的某网卡相连，这样我们就可以使用一些打流工具，如**spirent的testcenter**给虚拟机的网卡打流，从而引导到mininet构建的网络中，达到打流的目的。
	
	默认情况下，port可以不填，mininet会自动分配。

* __TreeTopo是支持快速生成一个网络树的函数__
	
		class TreeTopo( Topo ):
    		"Topology for a tree network with a given depth and fanout."	
    		def __init__( self, depth=1, fanout=2 ):
	depth 定义的是树的深度，fanout是每一层的分支数。
	mininet中便捷使用是， --tree(n,m),可以生成n层的m叉树。

* __node里面的RemoteConTroller类定义远程连接的控制器__
	
		class RemoteController( Controller ):
    	"Controller running outside of Mininet's control."
    		def __init__( self, name, ip='127.0.0.1',port=6633, **kwargs):
	默认的控制器是本地控制器。ip =127.0.0.1。注意，你可以自己定义你的控制器的名字，这一点是很有趣的，比如我的控制器就叫做：muziController，搞技术的时候，也要考虑技术的感受，不要老搞，要轻松一下嘛。

* __node里面的OVSKernelSwitch定义OVS交换机的类，至关重要。__
 
 
		class OVSLegacyKernelSwitch( Switch ):
    		def __init__( self, name, dp=None, **kwargs ):

	实际上它直接集继承了Switch类，Switch类是一个更加简单的基类，提供了交换机所需要的相关功能。
	
		class OVSSwitch( Switch ):
	
	OVSSwitch（)也继承Switch基类。而superclass:Switch继承的是Node，可以在他的init函数中看出他可以使用哪些参数。你可以设置dpid，很重要的一个属性。

		class Switch( Node ):
    		"""A Switch is a Node that is running (or has execed?)
       		an OpenFlow switch."""

	    	portBase = 1  # Switches start with port 1 in OpenFlow
    		dpidLen = 16  # digits in dpid passed to switch

    		def __init__( self, name, dpid=None, opts='', listenPort=None, **params):

了解完这些重要的代码，我们就是可以开始构建我们的拓扑了。

###创建接口检查函数

	def checkIntf(intf):
		#make sure intface exists and is not configured.
		if(' %s:'% intf) not in quietRun('ip link show'):
			error('Error:', intf, 'does not exist!\n' )
			exit(1)
		ips = re.findall( r'\d+\.\d+\.\d+\.\d+', quietRun	( 'ifconfig ' + intf ) )
		if ips:
			error("Error:", intf, 'has an IP address,'
				'and is probably in use!\n')
			exit(1)

在创建拓扑前，我们必须要做的第一件事情就是了解那些接口是存在的，且没有被定义初始化，也就是，没有被使用的，这些资源是可调用资源。具体代码如上。

###创建拓扑

为了不打破思维的连续性，以下内容由注释先生解说。谢谢收看本期内容，再见。

	if __name__ == "__main__":
		setLogLevel("info")
		OVSKernelSwitch.setup() //开启一个网络
		intfName_1 = "eth2"     //将虚拟机eth2赋值给为变量intfName_1
		intfName_3 = "eth3"
		info("****checking****", intfName_1, '\n')
		checkIntf(intfName_1)    //检查是否可用
		info("****checking****", intfName_3, '\n')
		checkIntf(intfName_3)
	
		info("****creating network****\n")
		net = Mininet(listenPort = 6633)   //创建一个Mininet的实例，端口为6633
	
		mycontroller = RemoteController("muziController", 	ip = "192.168.0.1")//创建远程控制器，ip=192.168.0.1，端口是6633。
	
		switch_1 = net.addSwitch('s1')   //在net里添加交换机s1,mininet中规则为：如果不填充dpid参数，则dpid参数默认取sn的n.即s1的dpid为1。 
		switch_2 = net.addSwitch('s2')
		switch_3 = net.addSwitch('s3')
		switch_4 = net.addSwitch('s4')
	
		net.controllers = [mycontroller] //将远程控制器添加到网络中
	
	
		net.addLink(switch_1, switch_2, 2, 1)# node1, 	node2, port1, port2
		net.addLink(switch_2, switch_3, 2, 1)//将s2的2端口跟s3的1端口连接起来。（物理连接）
		net.addLink(switch_1, switch_4, 3, 1)
		
		
		//需要注意的是，以上连接的链路是一个环形的链路，在没有解决风暴的情况下，会出问题。	
		info("*****Adding hardware interface ", 	intfName_1, "to switch:" ,switch_1.name, '\n')
		info("*****Adding hardware interface ", 	intfName_3, "to switch:" ,switch_3.name, '\n')
	
		_intf_1 = Intf(intfName_1, node = switch_1, port = 	1)//将intfName_1和s1的端口1相连，形成一个接口_intf_1
		_intf_3 = Intf(intfName_3, node = switch_3, port = 	2)

		net.addLink(switch_4, switch_3, 2, 3)//为什么放在这里呢？因为mininet中允许的端口分配方式是从小到大分配，所以，s3的3端口的配置应该放在s3的2端口之后，虽然难看，但是必须这么做，当然你也可以从新分配端口，只要保证端口是从小到大分配就好了。
		
		info("Node: you may need to reconfigure the 	interfaces for the Mininet hosts:\n", 	net.hosts, '\n')
	
		net.start()  //启动net
		CLI(net)     //等待键入命令
		net.stop()   //关闭net