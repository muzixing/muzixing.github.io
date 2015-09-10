title:【原创】SDN控制器开发教程——打造属于你自己的控制器
date:2013-12-17
category:Tech
tags:SDN,OpenFlow

---

##前言

SDN(Software Defined Network)这些年越来越火。当我还是大三的小朋友的时候，我的学长带我走进了OpenFlow的世界。一年里，我慢慢学会了许多东西，研究过pox,写过mininet自定义拓扑，画过OpenFlow的数据结构，做过HTTP的流量引导，广播风暴解除等许多小东西。在SDN这条道路上越走越远，也希望有一天，我能在这个领域有所成就，做出一点自己的贡献。

暑假的时候开始来工信部电信研究院实习，开始跟着学长一起开发，后来学长去美帝了，我继续完成剩下的工作。为了实现demo，我们顺便写了一个小小的控制器，其本质很简单，也许简单到你都不屑一顾。但是这个过程，我们需要从底层通信开始搭建，一直到最后的上层应用，无论哪一个环节，都会涉及到。到最后你会发现，其实也许这个控制器并没有太大的用处，但是更多的是这个过程中你学到的知识，那是使用别人开发的控制器说不能得到的宝贵知识。


---

##你能得到的

* 底层通信：基于Tornado架构的socket通信的搭建
* OpenFlow协议数据结构细节
* 通信流程的事件处理
* 若干网络协议的熟悉与掌握。
* 最重要的，你自己从无到有，经历了一个开发过程，所有出现的你想到的想不到的问题，你都需要自己去解决。你会在解决问题的过程中收获太多太多你想不到的财富。
* 自信！你可以大声对自己说，我可以！我可以做很多事情，因为我遇到了很多困难，但是我最终成功了！也许很简单，但是不是每一个人都能坚持去完成一个创新工作！**有想法的人太多，持之以恒的人也很多，但是又想法，有持之以恒的人不多。我可以试着努力成为那样的人！**

---

##在下面的内容你会接触到的名词



* socket
* tronado
* scapy
* mininet

任何需要更多了解的请自行百度，google。

---

##底层通信

我们的控制器的底层通信是由socket通信搭建的。以下关于socket通信的内容均摘自：http://blog.csdn.net/xiaoweige207/article/details/6211577

如果你想更详细地学习socket通信，可以去这个地址查看，也可以自行google。如果你已经了解socket通信，请跳到后面查看。

---

###socket的基本操作

socket操作模式：open ->write/read ->close

基于这个模式，我们需要用到一下的函数。

* socket()函数
* bind()函数
* listen()、connect()函数
* accept()函数
* read()、write()函数等
* close()函数

####socket()函数

	int socket(int domain, int type, int protocol);

这个函数相当于文件打开操作，会创建一个socket，返回的一个和文件描述符类似的标示符，这个标示符唯一对应一个socket。

**参数：**

>* domain：即协议域，又称为协议族（family）。常用的协议族有，AF\_INET、AF\_INET6、AF\_LOCAL（或称AF\_UNIX，Unix域socket）、AF\_ROUTE等等。协议族决定了socket的地址类型，在通信中必须采用对应的地址，如AF\_INET决定了要用ipv4地址（32位的）与端口号（16位的）的组合、AF\_UNIX决定了要用一个绝对路径名作为地址。

>* type：指定socket类型。常用的socket类型有，SOCK\_STREAM、SOCK\_DGRAM、SOCK\_RAW、SOCK\_PACKET、SOCK\_SEQPACKET等等（socket的类型有哪些？）。

>* protocol：故名思意，就是指定协议。常用的协议有，IPPROTO\_TCP、IPPTOTO\_UDP、IPPROTO\_SCTP、IPPROTO\_TIPC等，它们分别对应TCP传输协议、UDP传输协议、STCP传输协议、TIPC传输协议。

**注意：并不是上面的type和protocol可以随意组合的，如SOCK\_STREAM不可以跟IPPROTO\_UDP组合。当protocol为0时，会自动选择type类型对应的默认协议。**

当我们调用socket创建一个socket时，返回的socket描述字它存在于协议族（address family，AF\_XXX）空间中，但没有一个具体的地址。如果想要给它赋值一个地址，就必须调用bind()函数，否则就当调用connect()、listen()时系统会自动随机分配一个端口。

####bind()函数

正如上面所说bind()函数把一个地址族中的特定地址赋给socket。例如对应AF\_INET、AF\_INET6就是把一个ipv4或ipv6地址和端口号组合赋给socket。

int bind(int sockfd, const struct sockaddr *addr, socklen\_t addrlen);
函数的三个参数分别为：

* sockfd：即socket描述字，它是通过socket()函数创建了，唯一标识一个socket。bind()函数就是将给这个描述字绑定一个名字。
* addr：一个const struct sockaddr *指针，指向要绑定给sockfd的协议地址。这个地址结构根据地址创建socket时的地址协议族的不同而不同。

**通常服务器在启动的时候都会绑定一个众所周知的地址（如ip地址+端口号），用于提供服务，客户就可以通过它来接连服务器；而客户端就不用指定，有系统自动分配一个端口号和自身的ip地址组合。**这就是为什么通常服务器端在listen之前会调用bind()，而客户端就不会调用，而是在connect()时由系统随机生成一个。

**TIP:**（具体请看链接）

**在将一个地址绑定到socket的时候，请先将主机字节序转换成为网络字节序，而不要假定主机字节序跟网络字节序一样使用的是Big-Endian。由于这个问题曾引发过血案！公司项目代码中由于存在这个问题，导致了很多莫名其妙的问题，所以请谨记对主机字节序不要做任何假定，务必将其转化为网络字节序再赋给socket。**


####listen()、connect()函数

如果作为一个服务器，在调用socket()、bind()之后就会调用listen()来监听这个socket，如果客户端这时调用connect()发出连接请求，服务器端就会接收到这个请求。

	int listen(int sockfd, int backlog);
	int connect(int sockfd, const struct sockaddr *addr, socklen_t addrlen);
listen 函数的第一个参数即为要监听的socket描述字，第二个参数为相应socket可以排队的最大连接个数。socket()函数创建的socket默认是一个主动类型的，listen函数将socket变为被动类型的，等待客户的连接请求。

connect 函数的第一个参数即为客户端的socket描述字，第二参数为服务器的socket地址，第三个参数为socket地址的长度。客户端通过调用connect函数来建立与TCP服务器的连接。

####accept()函数

TCP服务器端依次调用socket()、bind()、listen()之后，就会监听指定的socket地址了。TCP客户端依次调用socket()、connect()之后就想TCP服务器发送了一个连接请求。TCP服务器监听到这个请求之后，就会调用accept()函数取接收请求，这样连接就建立好了。之后就可以开始网络I/O操作了，即类同于普通文件的读写I/O操作。

int accept(int sockfd, struct sockaddr *addr, socklen_t *addrlen);
accept函数的第一个参数为服务器的socket描述字，第二个参数为指向struct sockaddr *的指针，用于返回客户端的协议地址，第三个参数为协议地址的长度。如果accpet成功，那么其返回值是由内核自动生成的一个全新的描述字，代表与返回客户的TCP连接。

**注意：**accept的第一个参数为服务器的socket描述字，是服务器开始调用socket()函数生成的，称为监听socket描述字；而accept函数返回的是已连接的socket描述字。一个服务器通常通常仅仅只创建一个监听socket描述字，它在该服务器的生命周期内一直存在。内核为每个由服务器进程接受的客户连接创建了一个已连接socket描述字，当服务器完成了对某个客户的服务，相应的已连接socket描述字就被关闭。

####read()、write()等函数

主要的网络IO函数有如下：

* read()/write()
* recv()/send()
* readv()/writev()
* recvmsg()/sendmsg()
* recvfrom()/sendto()

在tronado中我们使用的是read()/write()

read函数是负责从fd中读取内容.当读成功时，read返回实际所读的字节数，如果返回的值是0表示已经读到文件的结束了，小于0表示出现了错误。如果错误为EINTR说明读是由中断引起的，如果是ECONNREST表示网络连接出了问题。

write函数将buf中的nbytes字节内容写入文件描述符fd.成功时返回写的字节数。失败时返回-1，并设置errno变量。 在网络程序中，当我们向套接字文件描述符写时有俩种可能。1)write的返回值大于0，表示写了部分或者是全部的数据。2)返回的值小于0，此时出现了错误。我们要根据错误类型来处理。如果错误为EINTR表示在写的时候出现了中断错误。如果为EPIPE表示网络连接出现了问题(对方已经关闭了连接)。

####close()函数

在服务器与客户端建立连接之后，会进行一些读写操作，完成了读写操作就要关闭相应的socket描述字，好比操作完打开的文件要调用fclose关闭打开的文件。

	int close(int fd);

close一个TCP socket的缺省行为时把该socket标记为以关闭，然后立即返回到调用进程。该描述字不能再由调用进程使用，也就是说不能再作为read或write的第一个参数。

**注意：**close操作只是使相应socket描述字的引用计数-1，只有当引用计数为0的时候，才会触发TCP客户端向服务器发送终止连接请求。

---

###Tornado

我们的底层是利用tornado搭建的。tornado是什么？请看：http://www.tornadoweb.cn/

如果你没有写过tornado，建议去tornado官网上把简单的demo做一做。也可以在本站学习tornado,站内搜索可以找到。


首先我们把需要的文件import进来：

	import errno
	import functools
	import tornado.ioloop as ioloop
	import socket
	import Queue
	import time

>* error是系统错误处理。

>* functools一个python的模块，我们需要用到的是他的partial函数。

	**partial函数**

	通过为已经存在的某个函数指定数个参数，生成一个新的函数，这个函数只需要传入剩余未指定的参数就能实现原函数的全部功能，这被称为偏函数。Python内置的functools模块提供了一个函数partial，可以为任意函数生成偏函数

		functools.partial(func[, *args][, **keywords])

>* 在整个底层通信中我们需要用到tornado的ioloop去进行系统IO的调用，去对socket的内容读取和写入。

>* 调用系统socket

>* import缓存队列,用于存储待发送



>* 系统时间

####创建new_sock函数

其实这个函数只是为了建立多个socket的时候省一些代码，直接调用总比一条一条配置要快一些。

	def new_sock(block):
    	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    	sock.setblocking(block)
    	return sock
目的：返回一个IPV4,字符串格式的的socket。第二句不需要管，我也不是很懂。第一个参数是普通socket的意思。具体的可以去这里查看：http://blog.csdn.net/chary8088/article/details/2486377

####main函数

	if __name__ == '__main__':
	    sock = new_sock(0)
	    sock.bind(("", 6634))
	    sock.listen(30)

		io_loop = ioloop.IOLoop.instance()
	    
	    callback = functools.partial(agent, sock)
	    print sock, sock.getsockname()
	    io_loop.add_handler(sock.fileno(), callback, io_loop.READ)
	    try:
	        io_loop.start()
	    except KeyboardInterrupt:
	        io_loop.stop()
	        print "quit" 

目的是创建一个socket。将其绑定在6634端口上，IP地址为本机地址。然后listen(30),30是允许最大的连接数，我们可以将其增大一点，以适应许多的交换机连接控制器。

调用tornado.ioloop去创建一个IOLoop的实例。

callback函数中是通过epoll方式实现并发。将sock作为agent的指定参数，生成一个可调用的partial对象，赋值给callback,作用相当于函数，实际上就是把sock作为参数传送给了agent函数。

	io_loop.add_handler(sock.fileno(), callback, io_loop.READ)

添加一个句柄处理这个socket。标示为fileno(),处理内容为callback中内容。初始状态为READ(可读)。

最后一个逻辑是启动ioloop,如果键入停止，则stop()。

####accept数据

当我们建立起一个半连接的server_socket之后，我们需要去收取socket的数据。这个时候我们就需要调用到accept函数。

	def agent(sock, fd, events):
	    #print fd, sock, events
	    try:
	        connection, address = sock.accept()
	    except socket.error, e:
	        if e.args[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
	            raise
	        return
	    connection.setblocking(0)
	    handle_connection(connection, address)
	    fd_map[connection.fileno()] = connection
	    client_handle = functools.partial(client_handler, address)
	    io_loop.add_handler(connection.fileno(), client_handle, io_loop.READ)
	    print "i n agent: new switch", connection.fileno(), client_handle
	    message_queue_map[connection] = Queue.Queue()

我们为了统一处理，定义agent函数。accept函数在agent中调用，同时在agent中也有except处理。

	connection, address = sock.accept()

socket.accept()是由数据和地址组成的。connection.setblocking(0)定义阻塞方式为无阻塞，收到数据位空时，马上返回0，而不是继续等待。

调用handle_connection()

	def handle_connection(connection, address):
	        print "1 connection,", connection, address

起作用很简单，打印一些关键信息。**将其放在main函数之前就好。**

同时我们还需要建立一个字典用于保存connection中的数据，key为connection.fileno(),即使用connection的文件标示符。

下一句使用到的函数：

####client_handler(address, fd, events)

	def client_handler(address, fd, events):
	    sock = fd_map[fd]  #以fd为标示符，从map中读取相应的connection数据，即收取到的字符流
	    if events & io_loop.READ:#如果状态是可读的
	        data = sock.recv(1024)    #收取1024字节数据，长度可调。
	        if data == '':            #非阻塞情况下如果收到的是空数据，则取消句柄
	            print "connection dropped"
	            io_loop.remove_handler(fd)
	        if len(data)<8:           #openflow报文最短是8字节，即报头8字节
	    		print "not a openflow message"
        	else:
            	if len(data)>8:
                	rmsg = of.ofp_header(data[0:8])  #封装ofp_header
                	body = data[8:]                  #取出body
            	else:  
                	rmsg = of.ofp_header(data)
				msg = of.ofp_header(type = 0,xid = rmsg.xid)   
                message_queue_map[sock].put(str(msg))    #将msg放入发送队列
                io_loop.update_handler(fd, io_loop.WRITE)#更改IOloop的状态。
				
		if events & io_loop.WRITE:   #如果以上的操作可以执行完，则ioloop状态转变为可写。
        	try:
            	next_msg = message_queue_map[sock].get_nowait()#将队列中的数据取出来
        	except Queue.Empty:
            	#print "%s queue empty" % str(address)
            	io_loop.update_handler(fd, io_loop.READ)#取完数据之后恢复可读状态，等待数据。
        	else:
            	#print 'sending "%s" to %s' % (of.ofp_header(next_msg).type, 	address)
            	sock.send(next_msg)#发送给dpid


这个函数是最重要，也是最核心的函数。其主要作用是对socket进行读写操作。先读后写，正常打开socket的写保护，保证文件锁的顺序，不会出现错误。

这里的重点是ioloop的状态转变，从read初始状态到改变成write，把所有发给改dpid的数据发送完，然后再把ioloop的状态恢复为可读状态，程序执行过程中不断在等待数据到来。可读状态时，则读取数据，对数据进行操作。最后还需要将ioloop状态改为write，使能数据写入。

代码中提到数据结构message_queue_map[sock]，我们需要在程序中定义一个数据结构:

	message_queue_map={}

放在import之后就可以了。

回到**accept**函数：最后一句就是给message_queue_map[connection]初始成一个队列。


至此底层的socket算是搭建完成。

---

##事件处理——OpenFlow协议

当底层通信搭建完成了之后，我们就需要对收到的数据进行一些处理，这些处理的规则就是OpenFlow协议。

如何能实现事件处理？你需要做两件事情：

* 编写一个静态库，用于定义OpenFlow数据结构。
* 按照OpenFlow协议处理socket收取到数据，即事件处理。

首先，我们需要一个静态库，里面是关于OpenFlow中使用到的报文的定义。

###scapy

我们使用scapy来对数据进行封装和解封装。什么是scapy?http://www.secdev.org/projects/scapy/

本博客中也有scapy的简单教程：http://www.muzixing.com/pages/2013/11/29/yuan-chuang-scapyjian-dan-jiao-cheng.html

如果你想详细地了解openflow的数据结构，我建议你照着协议重新画一遍，或者到sdnap.com上搜索一篇叫：openflow美丽的数据结构的文章，稍后也将在搬到本博客。画完之后，我们再使用scapy去定义这些数据结构，经历了这些学习之后，你会对openflow协议有一个非常清晰明了的认识。

scapy的封装非常简单。

如定义ofp\_header:

	class ofp_header(Packet):
	    name = "OpenFlow Header "
	    fields_desc=[ XByteField("version", 1),
	                  ByteEnumField("type", 0, ofp_type),
	                  ShortField("length", 8),
	                  IntField("xid", 1) ]

再如，定义ofp\_phy\_port
	
	class ofp_phy_port(Packet):
	    name = "OpenFlow Port"
	    fields_desc=[ ShortEnumField("port_no", 0, ofp_port),
	                  MACField("hw_addr", "00:00:00:00:00:00"),
	                  StrFixedLenField("port_name", None, length=16),
	 
	                  BitField("not_defined", 0, 25),
	                  BitField("OFPPC_NO_PACKET_IN", 0, 1),
	                  BitField("OFPPC_NO_FWD", 0, 1),
	                  BitField("OFPPC_NO_FLOOD", 0, 1),
	                  BitField("OFPPC_NO_RECV_STP",0, 1),
	                  BitField("OFPPC_NO_RECV", 0, 1),
	                  BitField("OFPPC_NO_STP", 0, 1),
	                  BitField("OFPPC_PORT_DOWN", 0, 1),        
	
	                  #uint32_t for state
	                  BitField("else", 0, 31),
	                  BitField("OFPPS_LINK_DOWN", 0, 1),
	
	                  #uint32_t for Current features
	                  BitField("not_defined", 0, 20),
	                  BitField("OFPPF_PAUSE_ASYM", 0, 1),
	                  BitField("OFPPF_PAUSE", 0, 1),
	                  BitField("OFPPF_AUTONEG", 0, 1),
	                  BitField("OFPPF_FIBER", 0, 1),
	                  BitField("OFPPF_COPPER", 0, 1),
	                  BitField("OFPPF_10GB_FD", 0, 1),
	                  BitField("OFPPF_1GB_FD", 0, 1),
	                  BitField("OFPPF_1GB_HD", 0, 1),
	                  BitField("OFPPF_100MB_FD", 0, 1),
	                  BitField("OFPPF_100MB_HD", 0, 1),
	                  BitField("OFPPF_10MB_FD", 0, 1),
	                  BitField("OFPPF_10MB_HD", 0, 1),
	                  
	                  #uint32_t for features being advised by the port
	                  BitField("advertised", 0, 32),
	
	                  #uint32_t for features supported by the port
	                  BitField("supported", 0, 32),
	
	                  #uint32_t for features advertised by peer
	                  BitField("peer", 0, 32)]

这里面的每一个字段，你都需要照着OpenFlow协议一个个定义。你可能会用到的函数有：

* **Bitfield("name",default_value,length)**
* **XByteField("name",default_value)  length =8**
* **X3ByteField("name",default_value)  length =3X8=24**
* **ByteEnumField("name", default_value, type)  length=8**
* **IntField("name",default_value)   length =32**
* **ShortField("name",default_value) length =16**
* **MACField("name",default_value)  format:"00:00:00:00:00:00"**
* **ShortEnumField("name", default_value, type)**
* **StrFixedLenField("name", default_value, length)**
* **IPField("name",default_value)format ="0.0.0.0"**

还有其他的封装函数，理解起来也很简单，按照以上函数的逻辑去理解其他的函数应该没有问题。

如果你想让自己学到更多，那么自己重新写一遍这些数据结构吧。如果你想直接用，你可以到我的github上去下载Controller中的libopenflow.py文件。里面已经写了很多。你可以去这里查看：https://github.com/muzixing/Controller/blob/master/libopenflow.py

假设你已经写了一些数据包，比如：

* header
* error
* hello
* features
* flow\_mod
* packet\_in
* packet\_out

那么你可以进行下一步了。因为这些数据包是完成数据交换，即下发正确流表需要的最少的报文。

###事件处理

可能很多高级的控制器都有自己定义的事件处理，我编程也是菜鸟水平，暂且以为这是对socket中收取的数据的处理吧，应该就是所谓的事件处理。

####处理规则

**OpenFlow1.0**

我们从socket中读取数据流，并使用scapy对数据进行封装和解封装，使用到的静态库就是上一小节提到的libopenflow。

对socket数据的处理，需要在client\_handler中去处理。

	def client_handler(address, fd, events):
	    sock = fd_map[fd]
	    if events & io_loop.READ:
	        data = sock.recv(1024)
	        if data == '':
	            print "connection dropped"
	            io_loop.remove_handler(fd)
	        if len(data)<8:
	            print "not a openflow message"
	        else:
	            if len(data)>8:
	                rmsg = of.ofp_header(data[0:8])
	                body = data[8:]
	            else:
	                rmsg = of.ofp_header(data)
	            if rmsg.type == 0:               # 判断header中类型。
	                print "OFPT_HELLO"
	                msg = of.ofp_header(type = 5)    #发送ofp_features_request
	                print "OFPT_FEATURES_REQUEST"
	                io_loop.update_handler(fd, io_loop.WRITE)
	                message_queue_map[sock].put(data) #hello放入发送队列
	                message_queue_map[sock].put(str(msg))  #ofp_features_request放入队列。
		if events & io_loop.WRITE:
		        try:
		            next_msg = message_queue_map[sock].get_nowait()
		        except Queue.Empty:
		            #print "%s queue empty" % str(address)
		            io_loop.update_handler(fd, io_loop.READ)
		        else:
		            #print 'sending "%s" to %s' % (of.ofp_header(next_msg).type, address)
		            sock.send(next_msg)  #发送数据。

我们需要将目光注意到这段代码：

	if rmsg.type == 0:               # 判断header中类型。
		print "OFPT_HELLO"
	    msg = of.ofp_header(type = 5)    #发送ofp_features_request
	    print "OFPT_FEATURES_REQUEST"
	    io_loop.update_handler(fd, io_loop.WRITE)
	    message_queue_map[sock].put(data) #hello放入发送队列
	    message_queue_map[sock].put(str(msg))  #ofp_features_request放入队列。

首先，rmsg是取前8字节封装的header(),根据不一样的type触发事件，并对事件进行处理。

下面的代码给出了一些type的处理逻辑：

	elif rmsg.type == 1:
	    print "OFPT_ERROR"
		of.ofp_error_msg(body).show() #当报错的时候我们应该把错误打印出来，以便解决错误
	elif rmsg.type == 2:
		print "OFPT_ECHO_REQUEST"
	   	msg = of.ofp_header(type=3, xid=rmsg.xid)
		message_queue_map[sock].put(str(msg))
	    io_loop.update_handler(fd, io_loop.WRITE)
	elif rmsg.type == 3:
	    print "OFPT_ECHO_REPLY"
	elif rmsg.type == 4:
		print "OFPT_VENDOR"
	elif rmsg.type == 5:
		print "OFPT_FEATURES_REQUEST"

####OFPT\_FEATURES\_REPLY的处理

接下来是一个非常重要的报文的处理：ofp_features_reply的封装与解析

    elif rmsg.type == 6:
        print "OFPT_FEATURES_REPLY"
        msg = of.ofp_features_reply(body[0:24])                     #length of reply msg
        sock_dpid[fd]=msg.datapath_id                          #sock_dpid[fd] comes from here.

        port_info_raw = str(body[24:])                              #we change it into str so we can manipulate it.
        port_info = {}
        print "port number:",len(port_info_raw)/48, "total length:", len(port_info_raw)
        for i in range(len(port_info_raw)/48):
            port= of.ofp_phy_port(port_info_raw[0+i*48:48+i*48])
            print port.port_no
            port_info[port.port_no]= port                           #save port_info by port_no

        features_info[msg.datapath_id] =(msg, port_info)            #features_info[dpid] = (sw_features, port_info{})

首先我们需要将获取到的数据判断类型，将前8字节封装成header，通过查看header（）.type来决定如何处理。当type=6时，这个报文对应的类型是ofp\_features\_reply。通过协议中的数据结构定义，我们知道他的结构是由switch的features和port的features组成。

	msg = of.ofp_features_reply(body[0:24])  

body是data[8:]的字节流，即除去header部分的内容。body[0:24]的内容是switch\_features的内容。将其使用我们自己定义的of.ofp\_features\_reply()去封装，将得到一个ofp\_features\_reply()的结构体。从而我们可以查看和修改相应属性。

	sock_dpid[fd]=msg.datapath_id  

同时，我们应该注意到一个很重要的参数：**datapath_id**

每一个交换机对应一个**datapath\_id**，我们需要通过datapath\_id(以下简称:dpid)对交换机发送消息。当然每一个交换机跟控制器之间都有一个socket连接，每一个socket连接都会有一个fd标志。我们需要建立一个字典去存储这些对应关系：

	sock_dpid={}  

其key-value对应对如上所示。将其放在import之后即可，即作为全局变量存在。

为什么需要建立这么一个字典呢？原因我总结如下：

* 每一个交换机与控制器连接的时候都会建立一个socket连接，但不限于一个socket连接，所以fd并不是唯一一个，但是dpid是唯一的，所以更精确的说法是通过dpid去下发命令，而不是socket下发命令。所以我们需要得到dpid,最简单的存储就是使用fd去对应。

* 以后的若干报文需要使用到dpid字段，使用fd为key存储起来，使用时读取更加方便。


我们先来了解一下features到底有什么字段：

	# No. 6
	# [header|features_reply|port]
	class ofp_features_reply(Packet):
	    name = "OpenFlow Switch Features Reply"
	    fields_desc=[ BitField('datapath_id', None, 64),
	                  BitField('n_buffers', None, 32),
	                  XByteField("n_tables", 0),
	                  X3BytesField("pad", 0),
	                  #features
	                  BitField("NOT_DEFINED", 0, 24),
	                  BitField("OFPC_ARP_MATCH_IP", 0, 1),  #1<<7 Match IP address in ARP packets
	                  BitField("OFPC_QUEUE_STATS", 0, 1),   #1<<6 Queue statistics
	                  BitField("OFPC_IP_STREAM", 0, 1),     #1<<5 Can reassemble IP fragments
	                  BitField("OFPC_RESERVED", 0, 1),      #1<<4 Reserved, must be zero
	                  BitField("OFPC_STP", 0, 1),           #1<<3 802.1d spanning tree
	                  BitField("OFPC_PORT_STATS", 0, 1),    #1<<2 Port statistics
	                  BitField("OFPC_TABLE_STATS", 0, 1),   #1<<1 Table statistics
	                  BitField("OFPC_FLOW_STATS", 0, 1),    #1<<0 Flow statistics
	                  BitField('actions', None, 32),
	                  #port info can be resoved at TCP server
	                ]
	bind_layers( ofp_header, ofp_features_reply, type=6 )


从上面的数据结构中，我们可以知道，features部分有许多功能的使能位。这些都是**极其重要的信息**。我们需要根据这些信息来确定到底使用什么动作，什么样的动作能起效。如OFPC\_FLOW\_STATS位如果没有使能，则在switch在交换数据的时候，并不会去记录流的统计信息。也就是说，我们如果想要读取统计信息，那么这个位必须为1！当然大概率下，switch默认的状态是统计各项数据的。如果发现得不到数据，你可以查看features的内容进行确认。如果没有使能，则需要通过OFPT\_SET\_CONFIG去配置。

回到type=6的处理代码段：

	 port_info_raw = str(body[24:])                              #we change it into str so we can manipulate it.
	        port_info = {}
	        print "port number:",len(port_info_raw)/48, "total length:", len(port_info_raw)
	        for i in range(len(port_info_raw)/48):
	            port= of.ofp_phy_port(port_info_raw[0+i*48:48+i*48])
	            print port.port_no
	            port_info[port.port_no]= port                           #save port_info by port_no
	

其意义在于将后面的字节流按port信息长度48bytes去切割，并封装成of.ofp\_phy\_port。
同时将port保存在port\_info字典中，key为port.port_no。

最后我们需要将这些重要的信息存储起来：

	features_info[msg.datapath_id] =(msg, port_info) 

features\_info字典我们需要在主文件中去声明，将其放在import之后，作为全局变量存在。

这些重要信息存储起来以便接下来的操作使用。

type=7,8,9的类型在这里就不一一作介绍，如果你需要用到她们，你可以自己去写出相应的处理逻辑，其依据就是OpenFlow协议1.0。

####OFPT\_PACKET\_IN的处理

跳过了7，8，9三个类型的处理，我们下面讲的是非常重要的type=10的处理。

packet_in的type=10,其作用如果不清楚，请查看协议，或者查看本博客《OpenFlow协议通信流程解读》，相信读完之后，你会有一个清晰的认识。

packet_in 报文上来之后，由于他本身携带的数据的类型的不确定性，所以处理起来也相对比较麻烦。

首先我们需要将其分为两类：

* 具有广播性质的数据如：ARP
* 普通数据通信报文：如IP

这两者将触发不一样的处理机制，前者会触发packet\_out,而后者会触发flow_mod。

####OFPT\_PACKET\_OUT

当第一个数据包上来的时候，我们默认主机发送的是ARP包，这样我们可以省去很多不必要的逻辑，当然这些逻辑在进一步完善的时候需要添加。

	elif rmsg.type == 10:
	                pkt_in_msg = of.ofp_packet_in(body) #首先将其封装成packet_in数据格式
					raw = pkt_in_msg.load		
	                pkt_parsed = of.Ether(raw)#将payload封装成Ether格式
					pkt =rmsg/pkt_in_msg/pkt_parsed  #将结构体重组
	                dpid = sock_dpid[fd]  #if there is not the key of sock_dpid[fd] ,it will be an error.
	                
	                if isinstance(pkt_parsed.payload, of.ARP):
	                    
	                    pkt_out_ = of.ofp_header()/of.ofp_pktout_header()/of.ofp_action_output()
	                    pkt_out_.payload.payload.port = 0xfffb
	                    pkt_out_.payload.buffer_id = pkt_in_msg.buffer_id
	                    pkt_out_.payload.in_port = pkt_in_msg.in_port
	                    pkt_out_.payload.actions_len = 8
	                    pkt_out_.length = 24
	                    
	                    io_loop.update_handler(fd, io_loop.WRITE)
	                    message_queue_map[sock].put(str(pkt_out_))


首先我们需要的对数据封装，首先把整个body封装成packet\_in报文，然后将packet\_in的装载，此处为load,为什么不是payload呢？payloadd是净荷，下一级是有结构的数据。而load也是净荷，但是此处应是字节流。（不是很了解，求大神纠正）

将packet\_in的load封装成Ether()格式的报文，即pkt\_parsed。Ether()是scapy提供的封装函数。同时，**通过fd，读取出对应的dpid.**同时我们需要将rmsg,pkt\_in\_msg,pkt\_parsed三者组合起来，组装成pkt。用于后面flow\_mod的使用。

若payload的类型是ARP,则会触发pkt\_out。pkt\_out的结构是：

	of.ofp_header()/of.ofp_pktout_header()/of.ofp_action_output()

然后我们再将必要的信息，如发送的端口：0xfffb，也就是FLOOD端口。这个数据包的意义在于：通知交换机可以对这个包进行广播。下一个交换机收到ARP之后，进行同样的操作，出发packet\_in事件，然后下发packet\_out指令。直到找到arp的回应。

当处理完ARP之后，packet\_in会触发ofp\_flow\_mod操作。

####OFPT\_FLOW\_MOD的处理

这一小节是一个特别重要的小节，是整一个控制器通信部分最核心的部分！

首先，packet\_in报上来的报文可能有很多类型，可能是二层的，可能是三层的，可能是四层。有可能是纯IP的，有可能是带有VLAN tags的IP，也有可能是TCP等等。所以我们需要针对不同的类型的数据进行不同的操作。

我们在这里只处理四种类型的数据：

* 四层报文：0x8100带有vlan tags的TCP,UDP,SCTP
* 四层报文：0x800纯IP的TCP,UDP,SCTP
* 三层报文：0x8100带有vlan tags的IP
* 三层报文：0x0800纯IP

由于处理逻辑相对比较复杂，代码量也比较多，所以我们新建一个F\_mod的文件，在文件中定义一个flow\_mod(packet\_in)的函数。用于处理flow\_mod事件。


	def flow_mod(pkt):
		pkt_parsed = pkt.payload.payload#读取三层即以上数据。
		if isinstance(pkt_parsed.payload, of.IP) or isinstance(pkt_parsed.payload.payload, of.IP):
		########################TCP OR UDP OR SCTP(L4)#####################
	        if isinstance(pkt_parsed.payload.payload, of.TCP) or isinstance(pkt_parsed.payload.payload, of.UDP) or isinstance(pkt_parsed.payload.payload, of.SCTP) :
	            if  pkt_parsed.type ==0x8100:#带有vlan_tags
	                flow_mod =of.ofp_flow_wildcards(OFPFW_NW_TOS=1,
	                                                  OFPFW_DL_VLAN_PCP=1,
	                                                  OFPFW_NW_DST_MASK=0,
	                                                  OFPFW_NW_SRC_MASK=0,
	                                                  OFPFW_TP_DST=1,
	                                                  OFPFW_TP_SRC=1,
	                                                  OFPFW_NW_PROTO=1,
	                                                  OFPFW_DL_TYPE=1,
	                                                  OFPFW_DL_VLAN=1,
	                                                  OFPFW_IN_PORT=1,
	                                                  OFPFW_DL_DST=1,
	                                                  OFPFW_DL_SRC=1)\
	                           /of.ofp_match(in_port=pkt.payload.in_port,
	                                         dl_src=pkt_parsed.src,
	                                         dl_dst=pkt_parsed.dst,
	                                         dl_type=pkt_parsed.type,
	                                         dl_vlan=pkt_parsed.payload.vlan,
	                                         nw_tos=pkt_parsed.payload.tos,
	                                         nw_proto=pkt_parsed.payload.proto,
	                                         nw_src=pkt_parsed.payload.src,
	                                         nw_dst=pkt_parsed.payload.dst,
	                                         tp_src = pkt_parsed.payload.payload.sport,
	                                         tp_dst = pkt_parsed.payload.payload.dport)\
	                           /of.ofp_flow_mod(cookie=0,
	                                            command=0,
	                                            idle_timeout=10,
	                                            hard_timeout=30,
	                                            out_port=0xfffb,
	                                            buffer_id=pkt.payload.buffer_id,
	                                            flags=1)
					flow_mod_msg = of.ofp_header(type=14,length=88,xid=pkt.xid)/flow_mod/of.ofp_action_header(type=0)/of.ofp_action_output(type=0, port=0xfffb, len=8)
	
	                return flow_mod_msg

**header**

首先我们需要注意到的是flow\_mod的header里面的信息。没有任何action时的flow\_mod长度为72。前8bytes是header,接下来4个bytes是wildcards，再接下来36bytes是match，最后的24字节是flow\_mod的数据。这些长度值都是应该熟记于心的，如果你认真研究过协议的话。

如果需要添加action，则每增加一个action,长度都会增加8，所以最后的长度必定是8的倍数。正常情况下，建议加上action\_header()。如action\_output()，则需要添加action\_header(type=0)。注意：header中的length必须要填！如果不填，则会包长度错误。血的教训在这里！

**wildcards**

在OpenFlow1.0中，wildcards的性质与常规认知相反，并不是子网掩码性质的直接与，而是中断屏蔽向量形式的逻辑。即1为屏蔽，0为默认匹配。所以wildcards的填写将决定你最后的流能不能通。

**match**

**match域最重要，这是一个流的属性。我们使用packet\_in的信息去填充即可。如in\_port=pkt.payload.in\_port。**

**flow\_mod**

flow\_mod域需要填的东西主要有以下几个：

* command
* idle_timeout
* hard_timeout
* out_port
* buffer_id
* flags

让我们来仔细分析这些字段都有哪些用处。

* command 是flow_mod的动作类型。command=0->add ......command =3->action=del
* idle_timeout 流活跃匹配时间。可设置为0
* hard_timeout   流存在时间，为0时表示永久存在。
* out_port       目前我们还无法获取端口，所以取值为0xfffb，即泛洪。
* buffer_id      使用packet_in的buffer_id
* flags          填1，指明流删除时需要回报一个flow_removed信息。

填写完这些关键信息之后，我们的flow_mod报文基本成型，此时报文长度72bytes。我已经记得很清楚这些长度了，再说一遍，header中的length一定要填对！

**action**

接下来就是action的填写。每一条流表都需要携带action，若没有指定的action则默认将执行drop操作。

action\_header()中我们需要填type。如果是添指定out\_port则type=0。其他的类型查看协议填写既可。添加完action\_header()之后，紧跟其后的是动作实体：如ofp\_action\_output(type =0,port=port,len =8)。

action有许多，如可以设置vlan,剔除vlan等操作。我们可以通过action实现需要功能，特别是在1.3版本中。

至此，四层的带vlan\_tags的flom\_mod封装完成。

同理，三层IP，或者不带四层端口的数据，我们在填充时，可以将四层的端口项设0，同时在wildcards中将四层端口屏蔽。

match中

	tp_src = 0,
	tp_dst = 0

wildcards中

	OFPFW_TP_DST=1,
	OFPFW_TP_SRC=1,

至此我们已经把三层到4层的带vlan\_tags的flow\_mod封装好。

同理对于**Ether中type=0x800**的不带vlan tags的数据，我们无法从packet_in中提取vlan。所以vlan字段我们可以不去填充，默认的会填充某一个默认值。当然我们需要把wildcards中的OFPFW\_DL\_VLAN置1。

也就是说到目前为止，以上提到的四种类型的报文对应的flow\_mod我们都已经有能力封装好。

在rmsg.type==10:的逻辑下,添加如

	else:
		msg = F_mod.flow_mod(pkt)
		message_queue_map[sock].put(str(msg))
		io_loop.update_handler(fd, io_loop.WRITE)


F_mod是你自己写的文件，文件中定义def flow\_mod()函数。当然在文件头部，我们需要
	
	import F\_mod	

至此packet\_in触发的事件大体处理完成。

**不出意外的话，这个时候如果打流，是可以通的！**

但是我们还需要注意到一点：**我们还没有将下发的流表保存起来。**

所以马上建立一个列表：

	flow_cache = []

同时在将上面一段代码改为：

	else:
		msg = F_mod.flow_mod(pkt)
		flow_cache[fd].append=(time.time(),msg)
		message_queue_map[sock].put(str(msg))
		io_loop.update_handler(fd, io_loop.WRITE)

####OFPT\_STATS\_REQUEST的处理

当流表下发成功之后，我们可以通过OFPT\_STATS\_REQUEST去获取流的统计信息。这是许多业务的基础。没有流量统计信息，就没有操作的基础。所以这一小节是自编控制器的提升功能，也是必要功能。

OFPT\_STATS\_REQUEST

* type=16

* 不同的请求对应不同的数据结构。

		ofp_stats_types = { 0: "OFPST_DESC",
		                    1: "OFPST_FLOW",
		                    2: "OFPST_AGGREGATE",
		                    3: "OFPST_TABLE",
		                    4: "OFPST_PORT",
		                    5: "OFPST_QUEUE",
		                    0xffff: "OFPST_VENDOR"}

好吧，我们努力把这6个都是实现吧。很明显，处理完这六个类型的操作，最好写成一个独立的小文件。

我们可以写一个文件：stats\_request，然后import 进来。

在文件里面我们需要定义这样一个函数：

	import libopenflow as of
	def send(Type, flow_1, port =None):
	    flow =str(flow_1)
	    ofp_flow_wildcards=of.ofp_flow_wildcards(flow[8:12])
	    ofp_match =of.ofp_match(flow[12:48])
	    ofp_flow_mod =of.ofp_flow_mod(flow[48:72])
	    if len(flow)>=88:
	        action_header = of.ofp_action_header(flow[72:80])
	        action_output = of.ofp_action_output(flow[80:88])
	    #we need to send the stats request packets periodically
	    msg = { 0: of.ofp_header(type = 16, length = 12)/of.ofp_stats_request(type = 0),                            #Type of  OFPST_DESC (0) 
	            1: of.ofp_header(type = 16, length = 56)/of.ofp_stats_request(type =1)/ofp_flow_wildcards/ofp_match/of.ofp_flow_stats_request(out_port = ofp_flow_mod.out_port),                  #flow stats
		        2: of.ofp_header(type = 16, length =56)/of.ofp_stats_request(type = 2)/ofp_flow_wildcards/of.ofp_match/of.ofp_aggregate_stats_request(),                                  # aggregate stats request
	            3: of.ofp_header(type = 16, length = 12)/of.ofp_stats_request(type = 3),                            #Type of  OFPST_TABLE (0) 
	            4: of.ofp_header(type = 16, length =20)/of.ofp_stats_request(type = 4)/of.ofp_port_stats_request(port_no = port),   # port stats request    
	            5: of.ofp_header(type = 16, length =20)/of.ofp_stats_request(type =5)/of.ofp_queue_stats_request(), #queue request
	            6: of.ofp_header(type = 16, length = 12)/of.ofp_stats_request(type = 0xffff)                        #vendor request
	        } 
		return msg[Type]

首先我们可以看到函数有3个参数。Type,flow\_1,port=None。Type是stats\_request的类型，flow\_1对应某条流表。这条流表，我们可以从之前的flow\_cache中提取。也可以自己填充，这就需要自己在主文件中自己写一个逻辑了，使用raw\_input()应该就可以设计出一个逻辑，用于手动发请求统计信息。我们这里选择最简单的，把flow\_cache[fd]中所有的存在的流都用于填充stats\_request()，即向所有活跃着的流都发送统计信息请求。

在主文件的if events & io_loop.WRITE:之前，与之对齐写下如下代码：
		
	if ready and time.time()-pre_time >period:  
	        print "send stats_requests"
	        for flow in flow_cache[fd]:
	        	message_queue_map[sock].put(str(stats_request.send(1,flow[1])))  
				
	        	io_loop.update_handler(fd, io_loop.WRITE)
				pre_time =time.time()
	
pre\_time,period和ready为全局变量，可以在features\_reply逻辑之后添加代码：
	
	global ready	
	ready=1
	pre_time=time.time() 

period可以任意设置，比如设置为3则为3秒发送一次stats\_request。这样我们就可以实现循环发送stats_request了。

回过来我们，我们关注一下我们发送的是什么东西。介绍一下type=1，到底发送了什么。

	of.ofp_header(type = 16, length = 56)/of.ofp_stats_request(type =1)\
			/ofp_flow_wildcards/ofp_match\
			/of.ofp_flow_stats_request(out_port = ofp_flow_mod.out_port)

header之后紧跟着ofp\_stats\_request(type=1)，代表这个request是请求flow的信息。紧接着是熟悉的wildcards和match。最后是消息实体ofp\_flow\_stats\_request(out\_port=port)

在这里有一些信息我们并没有填出来，但是他们非常重要。比如ofp_flow\_stats_request()中**table_id 我们需要通过table对应的request去获取，如果没有获取，可以填0xff,即没有限制。对于out\_port也是一样，如果无法获取port,则可以填0xffff,即None。同样表示无限制。**

其他的类型就不一一介绍了，细心去看协议都可以写出来。

####OFPT\_STATS\_REPLY的处理
           
交换机收到stats\_request之后，会按照匹配结果向控制器返回stats\_reply。同样的，有多少种stats\_request就会对应有多少种stats\_reply。

所以reply的处理也是一件很重要的事情。

	elif rmsg.type == 17 and len(data)> 12:
	                print "OFPT_STATS_REPLY"
	                reply_header = of.ofp_stats_reply(body[:4])
	                if reply_header.type == 0:
	                    reply_desc = of.ofp_desc_stats(body[4:])
	                    reply.show()
	                elif reply_header.type == 1 and len(data)>92:
	                    reply_body_data1 = of.ofp_flow_stats(body[4:8])
	                    reply_body_wildcards = of.ofp_flow_wildcards(body[8:12])
	                    reply_body_match = of.ofp_match(body[12:48])
	                    
	                    reply_body_data2 = of.ofp_flow_stats_data(body[48:92])
	                    
	                    reply_body_action = []
	                    if len(body[92:])>8:                         #it is very important!
	                        num = len(body[92:])/8
	                        for x in xrange(num):
	                            reply_body_action.append(of.ofp_action_output(body[92+x*8:100+x*8]))
	                            
	                    msg = reply_header/reply_body_data1/reply_body_wildcards/reply_body_match/reply_body_data2
	                    msg.show()
	

代码很长，我们先重点讲一下，我们刚才发送的type=1的flow\_stats\_request对应的reply应该如何解析。首先我们需要按照数据结构将其分割成对应的：

ofp\_flow\_stats()，ofp\_wildcards(),ofp\_match()和ofp\_flow\_stats\_data()4部分。

在第四部分中我们能得到很多信息，如流表生存时间，匹配上的字节数，包数目等关键信息。这些可以在《OpenFlow通信流程解读》中清楚了解到。同理我们将其他类型的报文处理写在了下面。


	                elif reply_header.type == 2:
	                    reply_aggregate = of.ofp_aggregate_stats_reply(body[4:])
	                    reply_aggregate.show()
	
	                elif reply_header.type == 3:
	                    #table_stats
	                    length = rmsg.length - 12
	                    num = length/64
	                    for i in xrange(num):
	                        table_body = body[4+i*64:i*64+68]
	                        reply_table_stats = of.ofp_table_stats(table_body[:36])
	                        table_wildcards = of.ofp_flow_wildcards(table_body[36:40])
	                        reply_table_stats_data = of.ofp_table_stats_data(table_body[40:64])
	                        msg_tmp = reply_header/reply_table_stats/table_wildcards/reply_table_stats_data
	                    msg = rmsg/msg_tmp
	                    msg.show() 
	                elif reply_header.type == 4:
	                    #port stats reply
	                    length = rmsg.length - 12
	                    num = length/104
	                    for i in xrange(num):
	                        offset = 4+i*104
	                        reply_port_stats = of.ofp_port_stats_reply(body[offset:(offset+104)])
	                        msg_tmp = reply_header/reply_port_stats
	                    msg = rmsg/msg_tmp
	                    msg.show()
	                elif reply_header.type == 5:
	                    #queue reply
	                    length = rmsg.length - 12
	                    num = length/32
	                    if num:                     #if the queue is empty ,you need to check it !
	                        for i in xrange(num):
	                            offset = 4+i*32
	                            queue_reply = of.ofp_queue_stats(body[offset:offset+32])
	                            msg_tmp = reply_header/queue_reply
	                        msg = rmsg/msg_tmp
	                        msg.show()
	                elif reply_header.type == 0xffff:
	                    #vendor reply
	                    msg = rmsg/reply_header/of.ofp_vendor(body[4:])

table request可以获取table的内容，如table0中有多少流等等。

port request可以获取端口上的信息。再这里不再展开，读者可自行研究。

至此我们已经顺利处理完stats\_reply的所有类型的数据。我们可以很好地利用统计信息去做文章，比如利用流量统计去做负载均衡的实验等等。

####其他的报文

其他的报文相对于以上的报文不是特别重要，当然如果你有精力，那就把整个OpenFlow整个都实现。相信以上的实现之后，后面的也会变得特别简单。以下就举例介绍两个相对比较重要的报文。

**barrier**

我们无法获知流表下发是否已经写入成功。或者我们想确认某个指令下发到交换机，并已经执行成功，我们应该怎么去得到这个回执呢？

这个时候你就需要使用到barrier。

在你想确认的报文之后下发一条barrier\_request，当交换机执行到barrier的时候，前面的指令都已经执行完。交换机会回复barrier\_reply给控制器，通知已经执行完barrier，即前面的指令已经执行完。控制器默认前面的指令已经执行成功，因为错误的情况会报错。

**flow_removed**

这是一条貌似可有可无的报文，但是事实上非常重要。只要你在下发flow的时候将flags置1，那么当流表失效或者被删除时，switch就会上报一个flow\_removed。我们怎么才能利用这个消息呢？

我们可以把这个消息打印出来，去查看他的内容，看看各个字段是不是想要的值。因为曾经我们就是从这个报文的打印信息中发现我们的流没有下发对的。最后将最麻烦的问题解决了，所以这个报文可以好好利用，可以查看流表在switch上的情况。

---

##上层应用

终于写完了底层通信部分。以上的部分已经可以保证一件事情，可以在非环形网中实现通信，因为环形网会存在网络风暴，而我们上面的代码并没有避免网络风暴的措施。所以说上面的控制器最好**运行在一个树形的网络中，而不应该存在环路。**

如何解决网络风暴？我们需要解决两个问题：

* ARP泛洪时会引起的网络风暴
* 正常通信时引起的环路风暴。

第一个容易解决，有一个最简单的办法就是在控制器上写一个小小的判断逻辑：如果某ARP报文的入口不是记录在字典中的入端口，则丢弃。这样保证同一个ARP包不会再次进入交换机，从而解决网络风暴。

第二个主要解决方法是编写路由算路算法，算出路径，从而在下发流表的时候将原有的port=0xfffb,替换成算路算出来的端口。这样就可以解决这两个问题。同时也可以解决3层路由问题。

更多的上层应用，这里不再介绍，有兴趣的读者可以自己继续研究。

---

##后续

写了这么多，好累好累。但是感觉还不错，起码这四个月的成果算是写得差不多了。还有一些秘密不能写，也不该写，所以就没写。像以上的教程，耐心做下来其实还是很有趣的。其重点也许并不是做一个多么牛逼的控制器，而是通过这个过程，对OpenFlow的了解。SDNAP群里的一个群友说的挺对的：也许通过写一遍控制器代码是最好的学习方法。写完这个控制器之后，我可以从OpenFlow的事件处理，哪一个报文有多长，有多少字段，都有什么用，到底层通信的socket搭建说个大概，我很自信，我能完成这个工作！也许这个控制器很弱，很弱，他甚至没有把算路的功能给大家写出来！（当然已经实现了！哈哈！）也许相比于floodlight，opendaylight,contrial等牛逼的主流控制器都弱上不知道多少倍！甚至连比较的资格都没有！可是那又怎么样呢！我完成了他！一句一句写下来的不仅仅是代码，更是心血！

从来没有这么认真地去完成一件事情！有时候人生就从某一件给你带来巨大成就感的事情开始有了转变！我始终相信，每一站，我都会努力做好着，而这一站，我收获了巨大的成功！我自己认为的巨大成功！没有什么嘉奖，没有什么的名誉！我只是很热爱，很兴奋地去做一件我很自豪的事情！**没有什么事情比带着愉快的心情去做一件让自己充满自豪感的事情更幸福了！**

很高兴我在年轻的时候选择了一个我目前看来很喜欢的方向，并在这条道路上越走越远！很高兴我能在SDNAP这个大家庭里遇到很多好玩的朋友，很多比我大很多很多的大哥，大叔！这里有很多我的老师，比如地球-某某，KKBluE,盛科-卫峰，无厘头等！在完成这个控制器的道路上他们给了我许多指导，特别是地球-某某老师。

最后，当年那两个年轻有为的学长，如今一个在美团，一个在美帝的那两个熟悉的人。带我走进OpenFlow世界，同时这个控制器也是他们首先开始编写的。后来才由我来完成这个小小的控制器！谢谢学长！！

差点忘了，一起奋斗的小伙伴，老伙伴！工信部的adam可是给我很多机会，给我很多帮助的博士哥！一起加班的时候聊天感觉特别好！！能一起奋斗努力完成一件事情真的太幸福了！！还有完成上层建筑的同事兼好朋友yzp学长！一起合作完成一件东西的感觉让我学会了合作，如果天气好，一起骑自行车下班聊天真的是一件特别惬意的事情！！跟你合作很愉快，哈哈！

**谢谢一路上帮助我的人，感谢我们家小乖乖，一直很支持我！明天你会看到更好的我！**


---

