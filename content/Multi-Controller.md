title:Mininet搭建多控制器拓扑
date:2015/8/5
tags:mininet, multi-controller
category:Tech

Mininet是一款非常轻巧但是功能很强大的网络模拟器。网络研究者可以使用Mininet创建支持OpenFlow的SDN拓扑。随着SDN研究的发展，多控制器协作成为未来的研究方向，所以使用Mininet构建多控制器网络拓扑也成为一种需求。本篇将讲述如何使用Mininet搭建多控制器网络拓扑。

###Multi-Controller

多控制器有两种理解，一种理解是面向交换机的多控制器。即一个交换机会连接多个控制器，控制器之间的关系可以是equal，也可以是master/slave模式。关于多控制器的介绍，有兴趣的读者可以参考OpenFlow1.3协议的multi-controller部分内容。另一种理解是面向控制器的多控制器。即，多个控制器分别管理各自的数据平面网络，且数据平面之间有链路互联。这种模式下，控制器之间没有关系，控制器所控制的数据平面也没有关系。关于多控制器方面的研究，笔者会在后续的博客中大篇幅介绍。

本篇将针对这两种理解，介绍如何搭建多控制器的Mininet拓扑。

###面向交换机的多控制器网络拓扑

对于一个交换机而言，可以连接多个控制器，其实现方式非常简单， 在Mininet的源码中已经实现。从Mininet的[node.py](https://github.com/mininet/mininet/blob/master/mininet/node.py)文件中，我们可以找到有用的代码：

```python
    def start( self, controllers ):
            """Start OpenFlow reference user datapath.
               Log to /tmp/sN-{ofd,ofp}.log.
               controllers: list of controller objects"""
            # Add controllers
            clist = ','.join( [ 'tcp:%s:%d' % ( c.IP(), c.port )
                                for c in controllers ] )
            ofdlog = '/tmp/' + self.name + '-ofd.log'
            ofplog = '/tmp/' + self.name + '-ofp.log'
            intfs = [ str( i ) for i in self.intfList() if not i.IP() ]
            self.cmd( 'ofdatapath -i ' + ','.join( intfs ) +
                      ' punix:/tmp/' + self.name + ' -d %s ' % self.dpid +
                      self.dpopts +
                      ' 1> ' + ofdlog + ' 2> ' + ofdlog + ' &' )
            self.cmd( 'ofprotocol unix:/tmp/' + self.name +
                      ' ' + clist +
                      ' --fail=closed ' + self.opts +
                      ' 1> ' + ofplog + ' 2>' + ofplog + ' &' )
            if "no-slicing" not in self.dpopts:
                # Only TCReapply if slicing is enable
                sleep(1)  # Allow ofdatapath to start before re-arranging qdisc's
                for intf in self.intfList():
                    if not intf.IP():
                        self.TCReapply( intf )
```

start函数发起了交换机到控制器的网络连接。传入的参数controllers是一个可迭代的数组，clist是整合之后的控制器信息，包括控制器的IP和控制器的端口。之后调用self.cmd函数启动连接，连接到控制器。

start函数在UserSwitch和OVSSwitch等交换机类中均有对应实现。所以，只需在启动交换机时，传入对应的控制器列表即可。

关键代码举例如下：

```python
    net = Mininet(controller=None, switch=OVSSwitch, link=TCLink)
    s1 = net.addSwitch('s1')
    controller_list = []
    
    for i in xrange(3):
        name = 'controller%s' % str(i)
        c = net.addController(name, controller=RemoteController,
                          port=6661 + i)
        controller_list.append(c)
    
    s1.start(controller_list)
```

其余代码如头文件引入，主函数等请参考后续示例代码。


###面向控制器的多控制器网络拓扑

面向控制器的多控制器网络拓扑定义了多个交换机，并使其分别连接到不同的控制器，从而完成拓扑搭建。在下列示例代码中，我们定义了7个网络分别连接到7个控制器，每一个网络中有5个全连接的交换机，不同网络之间还有链路，使得7个网络彼此联通。代码比较简单，不再赘述，读者可自行阅读。


```python
    #!/usr/bin/python
    
    """
        This example create 7 sub-networks to connect 7  domain controllers.
        Each domain network contains at least 5 switches.
        For an easy test, we add 2 hosts for one switch.
        So, in our topology, we have at least 35 switches and 70 hosts.
        Hope it will work perfectly.
    """
    
    from mininet.net import Mininet
    from mininet.node import Controller, RemoteController, OVSSwitch
    from mininet.cli import CLI
    from mininet.log import setLogLevel, info
    from mininet.link import Link, Intf, TCLink
    from mininet.topo import Topo
    import logging
    import os
    
    
    def multiControllerNet(con_num=7, sw_num=35, host_num=70):
        "Create a network from semi-scratch with multiple controllers."
        controller_list = []
        switch_list = []
        host_list = []
    
        net = Mininet(controller=None, switch=OVSSwitch, link=TCLink)
    
        for i in xrange(con_num):
            name = 'controller%s' % str(i)
            c = net.addController(name, controller=RemoteController,
                                  port=6661 + i)
            controller_list.append(c)
            print "*** Creating %s" % name
    
        print "*** Creating switches"
        switch_list = [net.addSwitch('s%d' % n) for n in xrange(sw_num)]
    
        print "*** Creating hosts"
        host_list = [net.addHost('h%d' % n) for n in xrange(host_num)]
    
        print "*** Creating links of host2switch."
        for i in xrange(0, sw_num):
            net.addLink(switch_list[i], host_list[i*2])
            net.addLink(switch_list[i], host_list[i*2+1])
    
        print "*** Creating interior links of switch2switch."
        for i in xrange(0, sw_num, sw_num/con_num):
            for j in xrange(sw_num/con_num):
                for k in xrange(sw_num/con_num):
                    if j != k and j > k:
                        net.addLink(switch_list[i+j], switch_list[i+k])
    
        print "*** Creating intra links of switch2switch."
    
        # 0-4  5-9 10-14 15-19 20-24 25-29 30-34
        # domain1 -> others
        net.addLink(switch_list[4], switch_list[6])
        net.addLink(switch_list[4], switch_list[10])
        net.addLink(switch_list[1], switch_list[15])
        net.addLink(switch_list[1], switch_list[20])
    
        # domain2 -> others
        net.addLink(switch_list[6], switch_list[10])
        net.addLink(switch_list[8], switch_list[12])
        net.addLink(switch_list[8], switch_list[18])
        net.addLink(switch_list[7], switch_list[25])
    
        # domain3 -> others
        net.addLink(switch_list[10], switch_list[16])
        net.addLink(switch_list[12], switch_list[16])
        net.addLink(switch_list[10], switch_list[21])
        net.addLink(switch_list[12], switch_list[27])
    
        # domain4 -> others
        net.addLink(switch_list[16], switch_list[21])
        net.addLink(switch_list[18], switch_list[27])
        net.addLink(switch_list[18], switch_list[31])
        net.addLink(switch_list[19], switch_list[34])
    
        # domain5 -> others
        net.addLink(switch_list[21], switch_list[27])
        net.addLink(switch_list[23], switch_list[31])
    
        # domain6 -> others
        net.addLink(switch_list[25], switch_list[31])
        net.addLink(switch_list[27], switch_list[32])
    
        #domain7 has not need to add links.
    
        print "*** Starting network"
        net.build()
        for c in controller_list:
            c.start()
        
        _No = 0
        for i in xrange(0, sw_num, sw_num/con_num):
            for j in xrange(sw_num/con_num):
                switch_list[i+j].start([controller_list[_No]])
            _No += 1
    
        #print "*** Testing network"
        #net.pingAll()
    
        print "*** Running CLI"
        CLI(net)
    
        print "*** Stopping network"
        net.stop()
    
    if __name__ == '__main__':
        setLogLevel('info')  # for CLI output
        multiControllerNet(con_num=7, sw_num=35, host_num=70)
```



###总结

Mininet功能很强大，基本可以满足日常的科研需求。更多的参考案例，可查看mininet的examples目录。最后，简单的启动脚本可以供参考。该脚本可以启动7个窗口，分别在不同的端口上启动7个ryu控制器，从而使得7个网络的交换机可以连接到对应的网络。

```shell
    for i in $(seq 1 7);
        do
        let port=i+6660
        xterm -title "app$i" -hold -e ryu-manager ryu/app/simple_switch_13 --ofp-tcp-listen-port=$port &
        done

```

希望自己的研究能够顺利进行，最终面世。
