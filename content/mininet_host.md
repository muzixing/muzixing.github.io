date:2014/3/25
title:mininet与外部host通信
tag:mininet
category:Tech

###前言

好多同学都在尝试使用mininet搭建拓扑。有的同学在尝试如何让mininet与外网通信，比如虚拟机，比如mininet之外的另一个网络。问题已经存在很久，本文将介绍如何使用mininet的接口实现与外界通信。

###Intf()接口

在mininet的源码中，我们可以找到一个link的文件，也是一个类。这个文件中有一个接口类Intf()

	class Intf( object ):
	
	    "Basic interface object that can configure itself."

	    def __init__( self, name, node=None, port=None, link=None, **params ):

使用这个接口类，可以把安装mininet的机器的网卡接到mininet的ovs之上。

剩下的就简单了。最重要的接口解决之后一切就都解决了。

如果需要例子，可以在本站查看：mininet搭建自定义拓扑
http://www.muzixing.com/pages/2013/12/06/yuan-chuang-mininetda-jian-zi-ding-yi-wang-luo-tuo-bu-by-muzi.html

另，也可以查看mininet中的hwintf文件。

希望能对你有帮助。
