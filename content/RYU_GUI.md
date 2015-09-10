title:RYU3.16 GUI安装与Topology模块分析
date:2015/4/21
category:Tech
tags:ryu


最近很多SDN研究人员问起如何安装RYU的GUI，网上也有一些教程。但是由于RYU版本问题，导致安装没有成功。本片博文将介绍RYU3.16版本下如何安装GUI，以及对RYU拓扑模块进行简单分析。


###安装GUI

[Linton的博客](http://linton.tw/2014/02/11/note-how-to-set-up-ryu-controller-with-gui-component/)已经有详细介绍，我在这里将一些可能出现问题的地方再提醒一次。

####第一步：依赖安装及修改代码

建议查看[Linton的博客](http://linton.tw/2014/02/11/note-how-to-set-up-ryu-controller-with-gui-component/)，比较简单，不赘述。


####第二步：运行相关组建

* **运行RYU相关APP**

		ryu-manager --verbose --observe-links app/simple_switch_13.py ryu.topology.switches ryu.app.rest_topology ryu.app.ofctl_rest
	
	![运行截图](http://ww2.sinaimg.cn/mw690/7f593341jw1erdi3oujndj20k60co75c.jpg)

	运行截图如下：
	![](http://ww2.sinaimg.cn/mw690/7f593341jw1erdi90ztcij20jx0cqqa0.jpg)

* **运行controller.py文件**

	进入到gui目录，运行controller.py文件。

		python controller.py

	![](http://ww1.sinaimg.cn/mw690/7f593341jw1erdi91ct7ej20mh0im12r.jpg)


* **访问页面**

	打开浏览器，访问http://127.0.0.1:8000页面。查看到connected to 127.0.0.1:8080信息则为连接成功。

	![](http://ww3.sinaimg.cn/mw690/7f593341jw1erdi91p3wbj20md07kab5.jpg)

	Note that: 如果没有显示connected to 127.0.0.1:8000等信息，而显示Disconnected, 那么需要重新启动RYU的相关APP，再刷新网页，重新链接。运行controller.py的终端不需要动。

	若连接成功，启动mininet与控制器连接，则可发现网页逐步在显示网络拓扑，点击交换机图标可查看详细信息。

	![](http://ww2.sinaimg.cn/mw690/7f593341jw1erdi923lypj20mb0hy0wf.jpg)

	众多网友表示3.19+版本无法成功使用GUI，可参考：[RYU3.20 GUI DOC](http://ryu.readthedocs.org/en/latest/gui.html) 进行安装使用。

###TOPOLOGY源码分析

有一个小伙伴已经在我之前发布了详细的代码介绍，我不再赘述，大家有兴趣的可以前往查看：[Ryu拓扑发现原理分析](http://blog.csdn.net/sdnexplorer/article/details/44940907)

在topology目录中，switches.py最重要。在switches.py文件中，核心的类是class Switches。

在Switches类中，我们仅仅需要关注几个重要的函数即可将大体的拓扑发现逻辑理清。

* \__init__()
 	
	初始化函数初始化了一些重要的内容，如dps,ports,links等。并将lldp\_loop和link\_loop这两个函数加入线程（协程）。

* packet\_in_handler()

	此函数用于解析LLDP报文，从而提取出对应的信息，得到link信息。

* lldp\_loop()

	调用了send\_lldp_packet()函数，循环发送LLDP报文的函数。 

* link\_loop()

	实时检测link事件，及时发现拓扑变化，生产对应的event，并通过send\_event_to_observers提供和观察者。


####使用Switches模块

在实验过程中，实验人员往往需要得到网络拓扑的信息，不仅仅是dpid,link,port这些零散的元素，而是一张图。这张图往往由邻接矩阵或关联矩阵。所以一下的内容将介绍如何将dpid,link等信息转化成邻接矩阵和关联矩阵，以便后续的算路算法使用。

在你开发的模块中，将Switches作为context加载，并在\__init__函数中将其赋值给某一变量。

	_CONTEXTS = {'switches': switches.Switches }

	def __init__(self, *args, **kwargs):
	        super(yourapp, self).__init__(*args, **kwargs)

        	self.switches = kwargs['switches']

        	self.threads = []
        	self.threads.extend([hub.spawn(self._link_monitor),])

self.threads用于保存线程。将\_link_monitor函数作为执行体，加入线程执行。函数简单定义如下：

	def _link_monitor(self):
        	while(self.is_active):
	            if self.links != self.dp_tracker.links.keys():
        	        self.dps = self.dp_tracker.dps
                	self.links = self.dp_tracker.links.keys()
	            hub.sleep(1)

从\_link_monitor函数中可以获取到dps,links等数据。这些数据需要整理存储，以便使用，get\_graph函数就是用于将数据存储在图中的函数：定义函数get_graph，函数返回值是两张图，其中图graph\_cap记录两个交换机之间的链路能力，图graph\_port则记录的是从src到dst的源端口，目的端口信息保存在图的对称节点上。详细代码如下：

	    def get_graph(self):
	        graph_cap = {}
	        graph_port = {}
	        for dpid in self.dps.keys():
	            for link in self.links:
	                if link.src.dpid == dpid:
	                    graph_cap.setdefault(dpid, {})
	                    graph_port.setdefault(dpid, {})
	                    neighbor = link.dst.dpid
	                    capacity = link.dst.curr_speed
	                    graph_cap[dpid][neighbor] = capacity
	                    graph_port[dpid][neighbor] = link.src.port_no
	        return graph_cap, graph_port

至此，网络拓扑图生成完毕。在运行最短路径或者其他的路径计算算法时，可使用get\_graph返回的数据。

###总结

一直以来做实验并不需要可视化拓扑界面，直到最近发现许多研究者频繁提问，才想起来尝试这个实验。但事实上，我觉得Switches模块的使用是一个更重要的内容。很多情况下，我们需要的是原始的数据，而不是展示出来的界面。本文内容比较简单，希望能帮助到一些SDN学习者。



	
















































