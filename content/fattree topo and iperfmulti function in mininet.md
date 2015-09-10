title:Fattree topo and iperfmulti function in mininet
date:2015/2/22
tags:SDN,mininet, fattree, data center
category:Tech

This article will show you 1)how to build a [fattree](http://ccr.sigcomm.org/online/files/p63-alfares.pdf) topo and 2)how to extend the iperfmulti function in mininet.

本篇博文将讲述1）如何搭建fatree网络拓扑和2）如何在mininet中拓展iperfmulti功能。

众所周知，数据中心是目前网络研究的一个热门领域。随着云计算的兴起与发展，会对数据中心网络提出更多的需求，也为学术研究提供了更多的课题。TE（Traffic Engineering）是网络研究中最基础的研究之一，在TE中Load balance是比较主要的研究内容之一。 然而由于数据中心网络的流量走势与传统网络不同，导致数据中心网络与传统网络的架构有所不同。在传统网络中上下行流量在总流量中占据很大比重，而相比之下，数据中心的流量分类中，横向流量的比重要远远大于传统网络架构的比重。为了更好解决数据中心网络流量问题，数据中心架构的设计就变得非常重要，在众多网络架构中，Fat-tree架构是比较出名和成功的。

SDN兴起于校园网，盛开于数据中心，这是一种比较准确的描述。目前SDN的研究领域内，数据中心占据了一席之地。所以很多的研究者都试图通过在控制器开发应用以及使用mininet模拟网络来进行网络实验。博主最近也做了一个关于Fat-tree的实验，在实验过程中，碰到了许多问题，深深觉得这一方面的知识在互联网中还比较缺乏。特此记录下来，分享出去，首先是作为自己的笔记，备忘，其次也给其他同样研究这方面的同学一些帮助。我掉过的坑，我不愿意别人继续掉。

科学的发展是需要许多人奠定基础，才能逐步发展。而只有分享经验，传递知识，才能让后人能站在前人的基础之上继续前进。重复劳动力在一些基础的无关紧要的环节，是整个社会资源的浪费。特此感谢乐于分享的各种网络中的老师，特别是为人十分和蔼，温和，良师益友@地球-某某老师。


##Fattree topo

这个python文件最初的原型是参考了roan's Blog的博文[SDN Lab 2$ Use Mininet create Fat Tree Topology](http://roan.logdown.com/posts/191753-sdn-lab-2-use-mininet-create-fat-tree-topology)中给出的代码。并在次基础上做了一些修改。在此感谢台湾的小伙伴的分享。

在此基础上我进行了修改，可点击[fattree源码](https://github.com/muzixing/fattree/blob/master/fattree_8_4.py)获取代码。


###Fattree特征

Fattree中，K是一个很重要的参数。如K=8，则core节点个数为(K/2)^2,pod个数为K,每一个POD有K个交换机，每一个交换机有K个inter link（内部链路）。aggregation层有K^2/2=64/2=32个交换机，同理 edge也是K^2/2=32个交换机。host可以是K/2个host，也可以任意指定。在我写的脚本中，K和host density都是可以设置的参数。

部分源码：
	
	class Fattree(Topo):
	    logger.debug("Class Fattree")
	    CoreSwitchList = []
	    AggSwitchList = []
	    EdgeSwitchList = []
	    HostList = []
	
	    def __init__(self, k, density):  # K 为fattree pod个数。 density是tor下的主机个数。
	        logger.debug("Class Fattree init")
	        self.pod = k 
	        self.iCoreLayerSwitch = (k/2)**2
	        self.iAggLayerSwitch = k*k/2
	        self.iEdgeLayerSwitch = k*k/2
	        self.density = density
	        self.iHost = self.iEdgeLayerSwitch * density
	
	        #Init Topo
	        Topo.__init__(self)
	
	    def createTopo(self):
	        self.createCoreLayerSwitch(self.iCoreLayerSwitch)
	        self.createAggLayerSwitch(self.iAggLayerSwitch)
	        self.createEdgeLayerSwitch(self.iEdgeLayerSwitch)
	        self.createHost(self.iHost)
	
	    """
	    Create Switch and Host
	    """
	
	    def _addSwitch(self, number, level, switch_list):
	        for x in xrange(1, number+1):
	            PREFIX = str(level) + "00"
	            if x >= int(10):
	                PREFIX = str(level) + "0"
	            switch_list.append(self.addSwitch('s' + PREFIX + str(x)))
	
	    def createCoreLayerSwitch(self, NUMBER):
	        logger.debug("Create Core Layer")
	        self._addSwitch(NUMBER, 1, self.CoreSwitchList)
	
	    def createAggLayerSwitch(self, NUMBER):
	        logger.debug("Create Agg Layer")
	        self._addSwitch(NUMBER, 2, self.AggSwitchList)
	
	    def createEdgeLayerSwitch(self, NUMBER):
	        logger.debug("Create Edge Layer")
	        self._addSwitch(NUMBER, 3, self.EdgeSwitchList)
	
	    def createHost(self, NUMBER):
	        logger.debug("Create Host")
	        for x in xrange(1, NUMBER+1):
	            PREFIX = "h00"
	            if x >= int(10):
	                PREFIX = "h0"
	            elif x >= int(100):
	                PREFIX = "h"
	            self.HostList.append(self.addHost(PREFIX + str(x)))
	
	    """
	    Add Link   createLink函数用于创建links,修改了原始版本写死的代码。
	    """

	    def createLink(self, bw_c2a=0.2, bw_a2e=0.1, bw_h2a=0.5):
	        logger.debug("Add link Core to Agg.")
	        end = self.pod/2
	        for x in xrange(0, self.iAggLayerSwitch, end):
	            for i in xrange(0, end):
	                for j in xrange(0, end):
	                    self.addLink(
	                        self.CoreSwitchList[i*end+j],
	                        self.AggSwitchList[x+i],
	                        bw=bw_c2a)
	
	        logger.debug("Add link Agg to Edge.")
	        for x in xrange(0, self.iAggLayerSwitch, end):
	            for i in xrange(0, end):
	                for j in xrange(0, end):
	                    self.addLink(
	                        self.AggSwitchList[x+i], self.EdgeSwitchList[x+j],
	                        bw=bw_a2e)
	
	        logger.debug("Add link Edge to Host.")
	        for x in xrange(0, self.iEdgeLayerSwitch):
	            for i in xrange(0, self.density):
	                self.addLink(
	                    self.EdgeSwitchList[x],
	                    self.HostList[self.density * x + i],
	                    bw=bw_h2a)
	
	    def set_ovs_protocol_13(self,):
	        self._set_ovs_protocol_13(self.CoreSwitchList)
	        self._set_ovs_protocol_13(self.AggSwitchList)
	        self._set_ovs_protocol_13(self.EdgeSwitchList)
	
	    def _set_ovs_protocol_13(self, sw_list):
	            for sw in sw_list:
	                cmd = "sudo ovs-vsctl set bridge %s protocols=OpenFlow13" % sw
	                os.system(cmd)
	
	def createTopo():
	    logging.debug("LV1 Create Fattree")
	    topo = Fattree(8, 4)
	    topo.createTopo()
	    topo.createLink(bw_c2a=0.2, bw_a2e=0.1, bw_h2a=0.05)
	
	    logging.debug("LV1 Start Mininet")
	    CONTROLLER_IP = "127.0.0.1"
	    CONTROLLER_PORT = 6633
	    net = Mininet(topo=topo, link=TCLink, controller=None, autoSetMacs=True,
	                  autoStaticArp=True)
	    net.addController(
	        'controller', controller=RemoteController,
	        ip=CONTROLLER_IP, port=CONTROLLER_PORT)
	    net.start()



##Iperfmulti function

在mininet中拓展功能的文章可参考[@赵伟辰](http://richardzhao.me/)的博客。

在mininet中增加新功能其实不难。主要分为3步：
 
* 修改net.py增加函数实体；
* 修改cli.py，增加对应do_function函数，用于命令解析；
* 修改mn函数，用于声明命令。 

net.py和cli.py均在mininet/mininet目录，mn文件在在mininet/bin目录中。

###修改net.py

    def iperf_single( self,hosts=None, udpBw='10M', period=5, port=5001):
            """Run iperf between two hosts using UDP.
               hosts: list of hosts; if None, uses opposite hosts
               returns: results two-element array of server and client speeds"""
            if not hosts:
                return
            else:
                assert len( hosts ) == 2
            client, server = hosts
            filename = client.name[1:] + '.out'
            output( '*** Iperf: testing bandwidth between ' )
            output( "%s and %s\n" % ( client.name, server.name ) )
            iperfArgs = 'iperf -u '
            bwArgs = '-b ' + udpBw + ' '
            print "***start server***"
            server.cmd( iperfArgs + '-s' + ' > /home/muzi/log/' + filename + '&')
            print "***start client***"
            client.cmd(
                iperfArgs + '-t '+ str(period) + ' -c ' + server.IP() + ' ' + bwArgs
                +' > /home/muzi/log/' + 'client' + filename +'&')

    def iperfMulti(self, bw, period=5):
        base_port = 5001
        server_list = []
        client_list = [h for h in self.hosts]
        host_list = []
        host_list = [h for h in self.hosts]

        cli_outs = []
        ser_outs = []
        
        _len = len(host_list)
        for i in xrange(0, _len):
            client = host_list[i]
            server = client
            while( server == client ):
                server = random.choice(host_list) 
            server_list.append(server)
            self.iperf_single(hosts = [client, server], udpBw=bw, period= period, port=base_port)
            sleep(.05)
            base_port += 1
        self.hosts[0].cmd('ping -c10'+ self.hosts[-1].IP() + ' > /home/muzi/log/delay.out')
        sleep(period)

以上代码完成iperfmulti函数实现：随机选取SC对，并进行iperf 打流。

###修改cli.py

    def do_iperfmulti( self, line ):
        """Multi iperf UDP test between nodes"""
        args = line.split()
        if len(args) == 1:
            udpBw = args[ 0 ]
            self.mn.iperfMulti(udpBw)
        elif len(args) == 2:
            udpBw = args[ 0 ]
            period = args[ 1 ]
            err = False
            self.mn.iperfMulti(udpBw, float(period))
        else:
            error('invalid number of args: iperfmulti udpBw \n' +
                   'udpBw examples: 1M\n') 


###修改mn

在mininet/bin目录下修改mn文件，将iperfmulti加入到对应的列表中。


	# optional tests to run
	TESTS = [ 'cli', 'build', 'pingall', 'pingpair', 'iperf', 'all', 'iperfudp',
	          'none'，'iperfmulti' ]
	
	ALTSPELLING = { 'pingall': 'pingAll',
	                'pingpair': 'pingPair',
	                'iperfudp': 'iperfUdp',
	                'iperfUDP': 'iperfUdp',
					'iperfmulti': 'iperfmulti'}

###重新安装mininet

进入mininet/util目录，输入以下命令重新编译安装mininet core:
	
	./install.sh -n

重启mininet，输入iperf，可使用table补全iperfmulti，从而可使用iperfmulti进行测试。


##总结

在做实验的过程中，遇到了很多问题，也学会了很多。学会了谷歌找资料，学会了给论文作者发邮件，也学会了如何协同工作。特别是协同工作这一点，以前写代码，做实验都是自己来，没有明确定义的接口，也更没有分工合作，版本管理也是自己随意定。在这个实验过程中，不仅学到了很多知识，更重要的是学会了和小伙伴北邮-张歌的相处，团队协作是一个非常重要的能力，我将在未来的日子里继续努力学习和提高这方面的能力。希望他的[博客](http://www.zhangge208.com/)能慢慢写起来，以后一起做更多好玩有用的实验。
