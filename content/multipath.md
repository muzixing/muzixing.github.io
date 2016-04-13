title:Load balance(Multipath) Application on RYU
date:2014/11/7
tags:multipath,qos,queue,SDN,RYU,load balance
CATEGORY:Tech

##前言

本篇博文介绍的是如何在RYU上通过使用select group 来实现multipath，从而实现流量的调度，完成简单的负载均衡Demo。OpenFlow13中有group table,可用于实现组播和冗余容灾等功能。实验中还是用了queue,完成了链路带宽的保障。

##相关工作

要完成多径传输，那么网络拓扑必然有loop，所以首先要解决由于loop而可能产生的storm。解决方案在之前一个[博文](http://www.muzixing.com/pages/2014/10/19/ji-yu-sdnde-ryuying-yong-arp_proxy.html)中已经提出。本应用就是利用了这个思想，实现了环路风暴的解除（可能有的情况下不成功，原因未知）

###网络拓扑

网络拓扑文件内容如下所示，也可以到github上下载，详情查看文章结尾。

	"""Custom loop topo example

	   There are two paths between host1 and host2.

	                |--------switch2 --------|
	   host1 --- switch1        |            switch4 ----host2
	                |           |            |  |______host3
	                -------- switch3 ---------
	                            |
	                          host4

	Adding the 'topos' dict with a key/value pair to generate our newly defined
	topology enables one to pass in '--topo=mytopo' from the command line.
	"""

	from mininet.topo import Topo


	class MyTopo(Topo):
	    "Simple loop topology example."

	    def __init__(self):
	        "Create custom loop topo."

	        # Initialize topology
	        Topo.__init__(self)

	        # Add hosts and switches
	        host1 = self.addHost('h1')
	        host2 = self.addHost('h2')
	        host3 = self.addHost('h3')
	        host4 = self.addHost('h4')
	        host5 = self.addHost('h5')
	        host6 = self.addHost('h6')
	        switch1 = self.addSwitch("s1")
	        switch2 = self.addSwitch("s2")
	        switch3 = self.addSwitch("s3")
	        switch4 = self.addSwitch("s4")
	        switch5 = self.addSwitch("s5")

	        # Add links
	        self.addLink(switch1, host1, 1)
	        self.addLink(switch1, switch2, 2, 1)
	        self.addLink(switch1, switch3, 3, 1)
	        self.addLink(switch2, switch4, 2, 1)
	        self.addLink(switch3, switch4, 2, 2)
	        self.addLink(switch2, switch3, 3, 4)
	        self.addLink(switch5, switch1, 1, 4)
	        self.addLink(switch5, switch2, 2, 4)

	        self.addLink(switch4, host2, 3)
	        self.addLink(switch4, host3, 4)
	        self.addLink(switch5, switch4, 3, 5)
	        self.addLink(switch3, host4, 3)
	        self.addLink(switch5, switch3, 4, 5)
	        self.addLink(switch2, host5, 5)
	        self.addLink(switch4, host6, 6)

	topos = {'mytopo': (lambda: MyTopo())}




##Multipath

解决网络可能形成风暴的问题之后，可以使用select类型的group_table来实现多径功能。

    def send_group_mod(self, datapath):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        port_1 = 3
        actions_1 = [ofp_parser.OFPActionOutput(port_1)]

        port_2 = 2
        actions_2 = [ofp_parser.OFPActionOutput(port_2)]

        weight_1 = 50
        weight_2 = 50

        watch_port = ofproto_v1_3.OFPP_ANY
        watch_group = ofproto_v1_3.OFPQ_ALL

        buckets = [
            ofp_parser.OFPBucket(weight_1, watch_port, watch_group, actions_1),
            ofp_parser.OFPBucket(weight_2, watch_port, watch_group, actions_2)]

        group_id = 50
        req = ofp_parser.OFPGroupMod(
            datapath, ofp.OFPFC_ADD,
            ofp.OFPGT_SELECT, group_id, buckets)

        datapath.send_msg(req)

不知道现在OVS的select的key是否已经改变，原先的key为dl\_dst。匹配成功的flow，在执行select时，是以dl\_dst为key,进行判断，从而从buckets中选择一个action\_list。

查看组表信息：

	sudo ovs-ofctl dump-groups s1 -O OpenFlow13

查看流表信息：

	sudo ovs-ofctl dump-flows s1 -O OpenFlow13

##QoS

首先我们知道OpenFlow无法创建队列。所以我们可以通过[ovsdb来配置队列](http://osrg.github.io/ryu-book/ja/html/rest_qos.html)，也可以直接使用ovs命令配置:

	ovs-vsctl -- set Port s1-eth2 qos=@newqos \
		 -- --id=@newqos create QoS type=linux-htb other-config:max-rate=250000000 queues=0=@q0\
		 -- --id=@q0 create Queue other-config:min-rate=8000000 other-config:max-rate=150000000\
	
	ovs-vsctl -- set Port s1-eth3 qos=@defaultqos\
		-- --id=@defaultqos create QoS type=linux-htb other-config:max-rate=300000000 queues=1=@q1\
		 -- --id=@q1 create Queue other-config:min-rate=5000000 other-config:max-rate=200000000
	
	ovs-vsctl list queue

以上代码在s1-eth2上创建了queue 0,在s1-eth3上创建了queue 0和queue 1。并配置了max\_rate和min\_rate。

查看queue的信息可以使用：
	
	sudo ovs-ofctl queue-stats s1 2  -O OpenFlow13

列举port查看qos：

	ovs-vsctl list port
	
列举queue：
	
	ovs-vsctl list queue 

删除QOS:

	sudo ovs-vsctl --all destroy qos
	sudo ovs-vsctl --all destroy queue

区别于OpenFlow1.0, OpenFlow1.3中的入队操作只有一个queue_id,需要额外指定port。即指定数据如某一个队列的话需要如下的actions:

    actions_2 = [ofp_parser.OFPActionSetQueue(0), ofp_parser.OFPActionOutput(port_2)]

所以使用group的情况下，完成QoS功能函数如下：

	    def send_group_mod(self, datapath):
	        ofp = datapath.ofproto
	        ofp_parser = datapath.ofproto_parser
	
	        port_1 = 3
	        queue_1 = ofp_parser.OFPActionSetQueue(0)
	        actions_1 = [queue_1, ofp_parser.OFPActionOutput(port_1)]
	
	        port_2 = 2
	        queue_2 = ofp_parser.OFPActionSetQueue(0)
	        actions_2 = [queue_2, ofp_parser.OFPActionOutput(port_2)]
	
	        weight_1 = 50
	        weight_2 = 50
	
	        watch_port = ofproto_v1_3.OFPP_ANY
	        watch_group = ofproto_v1_3.OFPQ_ALL
	
	        buckets = [
	            ofp_parser.OFPBucket(weight_1, watch_port, watch_group, actions_1),
	            ofp_parser.OFPBucket(weight_2, watch_port, watch_group, actions_2)]
	
	        group_id = 50
	        req = ofp_parser.OFPGroupMod(
	            datapath, ofp.OFPFC_ADD,
	            ofp.OFPGT_SELECT, group_id, buckets)
	
	        datapath.send_msg(req)

##Load balancing

![mininet](http://ww1.sinaimg.cn/mw690/7f593341jw1em5uu5i76qj20k40cr0v8.jpg)

从图中我们可以看到，pingall连通性没有问题。第一个iperf是在没有设置队列的情况下，由于找不到队列，所以不如队，只转发，此时带宽为26.4Gbits/sec。之后的测试数据为设置队列之后的数据。可以看出h1到h2之间的带宽是300Mbits/sec，而h1到h3的带宽是150Mbits/sec。 

原因在于我们将h1到h2的数据流在组表中选择了s1-eth3的queue 0，而该队列的最大带宽是300M。

同时另一个从h1到h3的数据流，在hash过程中，选择了s1-eth2端口的queue 0，该队列的最大速度为150M。

下图为queue information：

![](http://ww2.sinaimg.cn/mw690/7f593341jw1em5uu6ecr8j20k30cuq63.jpg)

可以看到，port 2 queue 0和port 3 queue 0有数据，而port 3 queue 1没有数据。

![](http://ww2.sinaimg.cn/mw690/7f593341jw1em5uu5dgjfj20k80cu0xb.jpg)

上图为s1和s4的组表和流表信息，从s4的流表信息（后部分流表）可知，同样是s1到s4的数据，dl\_dst为h2的数据从port 2进入，而dl\_dst为h3的数据从port 1进入，验证了数据传输过程使用了多径传输，合理利用了带宽空间。多径传输可以充分利用链路带宽，提高链路利用率。同时这个实验简单粗暴地完成了两条链路的负载均衡（将不同的数据流平均地分摊到了两条path上，由于对不同Path限制了不同的带宽，所以，流量并不是平均的）。根据拓扑及流量情况，添加算法计算合理流量路径，可以完成更灵活有效的负载均衡功能。

##后语

这其实是简单的实验，但是由于在安装OVS的过程中遇到了很多的问题，所以过程比较痛苦，写下来，以备不时之需，也有可能帮助到别人吧。提供一个纯从[OVS上配置的方案](http://hwchiu.logdown.com/posts/207387-multipath-routing-with-group-table-at-mininet)，相比之下比开发控制要简单一些。之前的博文的名字是：Multipath and QoS Application on RYU,但是后来导师提醒Multipath 和QoS不是一个层面的，才发现自己学识粗浅。需要努力的地方还太多。所以本篇博文被我生生改成Load balance的题目，虽然很牵强，但是相比之下，犯的错误更少一些。

全部代码文件在github的[multipath](https://github.com/muzixing/ryu/tree/master/ryu/app/multipath),请读者到github查看具体的实验步骤。

