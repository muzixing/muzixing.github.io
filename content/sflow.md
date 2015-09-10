title:sFlow入门初涉
date:2014/11/21
tags:Moniter,sflow,mininet
category:Tech

###前言

[sFlow](http://www.sflow.org/sFlowOverview.pdf)是一个应用在高速交换网络中的监控软件。sFlow需要交换机支持才能使用，万幸OpenvSwitch支持这个功能。netflow同样也是类似功能的软件，可惜没有接触过，也只是听过名字而已。第一次接触到sFlow之后，就觉得很感兴趣，跟着[SDNLAB](http://www.sdnlab.com/3760)的教程做了一遍之后，记录下自己的学习过程。

###安装sFlow

下载sFlow代码：
	
	http://pan.baidu.com/s/1mgmOVck

解压缩，安装：
	
	tar -zxvf sflow.tar.gz
	cd sflow/sflow-rt
	./start.sh
	
此时通过浏览器127:0.0.1:8008可以查看到生成的页面。

###实验步骤

本实验步骤将介绍如何在一台机器上完成sflow流量监控实验。实验需要运行一个控制器，可以使用mininet自带的控制器，也可以使用RYU等控制器。然后运行mininet，设置OVS的sFlow功能，从而从8008端口上查看到相应的数据。

###启动mininet

	sudo mn

或者
	
	sudo mn --controller=remote,ip=[controllerip]

####开启OVS的sFlow功能

为了让mininet中创建的OVS和本地网卡相连，从而使得8008端口可以通过网卡获取到mininet中流量数据，我们需要将某个网卡加入到OVS生成的bridge上。选择最简单的eth0即可，不过如果eth0是连接外网的网卡的话，很可能添加到bridge之后，就无法上网了。

	ovs-vsctl add-port s1 eth0

设置s1的IP，使得交换机可以作为sFlow agent与sFlow Collector通信。例如，给s1使用eth的IP：10.108.144.45，此举确保IP是可用的。

	 ifconfig s1 10.108.144.45 netmask 255.255.255.248

配置之后，查看配置是否生效：

	ifconfig s1

开启OVS的sFlow功能：

	ovs-vsctl -- --id=@sflow_id create sFlow agent=s1 target=\"127.0.0.1:6343\" header=128 sampling=64 polling=1 -- set bridge s1 sflow=@sflow_id

其中agent指的是需要作为sFlow agent的网卡，target是目标的sFlow Collector。

查看配置是否生效：

	ovs-vsctl list sflow

查看结果如下图：

![](http://ww1.sinaimg.cn/mw690/7f593341jw1emisnsk7gmj20fb06emxu.jpg)

list功能可以查看很多内容，如：
	
	ovs-vsctl list port
	ovs-vsctl list queue
	ovs-vsctl list qos

###监控网络流量

打开127.0.0.1：8008，点击agent等栏目能看到对应的信息。在mininet中使用pingall，iperf iperfudp等命令产生流量，并查看统计情况。实例如下：

![](http://ww4.sinaimg.cn/mw690/7f593341jw1emismf2z9nj21da0dz0wn.jpg)

###后语

在网络中，如果能实时监控到网络的流量，那么就可以根据网络流量数据做出许多Traffic Engineering的操作。所以对于一个网络而言，实时的网络流量数据至关重要。本篇教程是在阅读了SDNLAB网站的教程之后，自己总结的单机版sFlow部署。更多详细的内容，大家可以到[SDNLAB](http://www.sdnlab.com)去查看。