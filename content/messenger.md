title:[POX]messenger component getting started
date:2014/3/26
tag:pox
category:Tech

###关于messenger getting started的来历

在POX中，Murphy专门开发了一个叫messenger的模块，用于实现POX与其他程序的通信。我曾有一个想法想实现分布式的POX。于是我在整个Internet上面寻找了好久，依然没有找到什么有用的东西！很忧伤！自己看代码也没有看明白怎么用！后来直接去Stanford的网站上面问Murphy！在我再三脑残的追问之下，终于他觉得应该写一个Getting started了。于是就在POX+wiki上面添加了Messenger的Getting started.

###Messenger 的作用

从以下的英文中，我们可以对Messenger有一定的了解。messenger是一个API,是用与POX与其他程序建立连接的API,通过他实现的有PoxDesk,也就是POX的web ui。


The messenger component provides an interface for POX to interact with external processes via bidirectional JSON-based messages.  The messenger by itself is really just an API, actual communication is implemented by transports.  Currently, transports exist for TCP sockets and for HTTP.  Actual functionality is implemented by services.  POX comes with a few services.  messenger.log_service allows for interacting with the log remotely (reading it, reconfiguring it, etc.).  openflow.of_service allows for some OpenFlow operations (e.g., listing switches, setting flow entries, etc.).  There are also a few small example services in the messenger package, and pox-log.py (in the tools directory) is a small, standalone, external Python application which interfaces with the the logging service over TCP.
By writing a new service, it becomes available over any transport.  Similarly, writing a new transport allows for accessing any service in a new way.
The messenger package in the repository has a fair amount of comments.  Additionally, you can see POXDesk (mentioned elsewhere) as an example of both implementing a new service, and communicating with messenger over HTTP from JavaScript. 

###加载messenger模块 

我们在以下的代码中在运行的POX的时候加载了Messenger组件。同时，我们也把tcp_transport作为组件加载进来，最后我们运行Messenger组件。这个example启动了一个服务端线程，监听本机的7790端口。
 
	
	[pox_dart]$ ./pox.py log.level --DEBUG messenger messenger.tcp_transport messenger.example
	POX 0.3.0 (dart) / Copyright 2011-2014 James McCauley, et al.
	DEBUG:boot:Not launching of_01
	DEBUG:core:POX 0.3.0 (dart) going up...
	DEBUG:core:Running on CPython (2.7.5/Sep 12 2013 21:33:34)
	DEBUG:messenger.tcp_transport:Listening on 0.0.0.0:7790
	DEBUG:core:Platform is Darwin-13.1.0-x86_64-i386-64bit
	INFO:core:POX 0.3.0 (dart) is up.

然后我们开启另一个终端，然后进入到POX的messenger目录之下，运行test\_client文件

	python test_client.py

之后，我们在test\_client的输入框之下，输入：

	{"CHANNEL":"upper","msg":"hello world"}

马上就会收到pox返回的信息：

	Recv: {
	    "count": 1,
	    "msg": "HELLO WORLD",
	    "CHANNEL": "upper"
	}

当然，这个前提是在test\_client的主函数中的IP+Port都设置正确的情况下才会产生，即test_client中开启了一个半连接socket，做为客户端去connect server TCP.


###小提示

如果想让POX运行CLI，你需要在运行POX的时候加上 py ,例如：

	python pox.py py

这就会出现CLI。同时如果想让显示漂亮，可以加上samples.pretty_log。

###后语

更多的尝试我没有继续，因为实在是看不懂这个POX的代码逻辑。最后选择自己去开启一个线程，直接简历socket连接。但是这些连接需要设计一些逻辑，可能工作量还是有一些的。但是不是特别多。如果你对这个感兴趣，你可以尝试。如果你知道更好的方法，你可以给我留言哦！我非常喜欢有人和我交流，一个人做这个很郁闷！

如有问题，请留言。

更多POX相关解答：https://openflow.stanford.edu/display/ONL/POX+Wiki
