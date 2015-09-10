date:2013-11-29
title:基于tornado的简单socket通信建立
category:Tech
tags:tornado


配图版请查看：http://user.qzone.qq.com/350959853/blog/1375093527

###安装tornado

这里有比较全的介绍，写得非常好。http://sebug.net/paper/books/tornado/

###hello world
首先，下载安装好tornado之后，我们就可以去使用tornado里面的库了。
照着官网的简单的例子抄了一遍，写了一个hello world!

![hello](http://e.hiphotos.bdimg.com/album/s%3D550%3Bq%3D90%3Bc%3Dxiangce%2C100%2C100/sign=1382f91cba99a9013f355b332dae7b46/e824b899a9014c0862b40dad087b02087bf4f42e.jpg?referer=77791a7ef01fbe094549f72434e4&x=.jpg)

显示效果如下：

![res](http://e.hiphotos.bdimg.com/album/s%3D550%3Bq%3D90%3Bc%3Dxiangce%2C100%2C100/sign=0683c331b1de9c82a265f98a5cbaf137/d009b3de9c82d15858647eb9820a19d8bd3e42d7.jpg?referer=68d8807dd488d43fa9bea5c2aecd&x=.jpg)
 


###基于tornado的简单的socket连接通信实现

代码如下：


	import errno
	import functools
	from tornado.ioloop import IOLoop
	import socket
	import time
	import Queue
	
	sock = socket.socket	(socket.AF_INET,socket.SOCK_STREAM,0)
	#sock.setsockopt	(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
	sock.setblocking(0)
	server_address=("localhost",12346)
	sock.bind(server_address)
	sock.listen(5)
	
	fd_map = {}
	message_queue_map = {}
	
	fd = sock.fileno()
	fd_map[fd]=sock
	
	ioloop = IOLoop.instance()
	
	def handle_client(cli_addr,fd, event):
		print event , IOLoop.WRITE
		s=fd_map[fd]
		if event&IOLoop.READ: #receive the data
			data = s.recv(1024)
			if data:
				print"receive %s from %s" %(data,cli_addr) 
				ioloop.update_handler(fd,IOLoop.WRITE)
				message_queue_map[s].put(data)
			else:
				print "closing %s  " %cli_addr
				ioloop.remove_handler(fd)
				s.close()
				del message_queue_map[s]
		if event &IOLoop.WRITE:
			try:
				next_msg= message_queue_map[s].get_nowait	()
			except Queue.Empty:
				print"%s Queue Empty"% cli_addr
				ioloop.update_handler(fd,IOLoop.READ)	#CHANGE THE SITUATION
			else:
				print"sending %s to %s " % (next_msg, 	cli_addr)
				s.send(next_msg)
				ioloop.update_handler(fd,IOLoop.READ)#
		if event &IOLoop.ERROR:
			print"%s EXCEPTION ON"%cli_addr
			ioloop.remove_handler(fd)
			s.close()
			del message_queue_map[s]
	
	def handle_server(fd,event):
		s=fd_map[fd]
		if event &IOLoop.READ:
			get_connection,cli_addr =s.accept()
			print"connection %s "%cli_addr[0]
			get_connection.setblocking(0)
			get_connection_fd = get_connection.fileno()
			fd_map[get_connection_fd]=get_connection
			handle = functools.partial	(handle_client,cli_addr[0])
			ioloop.add_handler	(get_connection_fd,handle,IOLoop.READ)
			message_queue_map[get_connection]=Queue.Queue()
	io_loop=IOLoop.instance()
	io_loop.add_handler(fd,handle_server,io_loop.READ)
	try:
	    io_loop.start()
	except KeyboardInterrupt:
		print "exit"
		io_loop.stop()
		
首先，我们的目的是利用tornado的库函数，去实现简单的也是很重要的socket通信。

####第一步：

我们需要建立一个半连接的socket，也就是，本机开了一个socket，等待对方来匹配，连接通信。这一点是非常必要的！

####第二步：

我们需要定义两个函数，一个是作为tcpserver的函数，另一个是作为client的函数。相对来说，server的要简单一些，因为只需要接受即可。在图中为handle_serve（）函数。比较困难的是handle_client（）函数，因为需要考虑的问题比较多！第一个需要考虑的是收到的数据是否为空的问题，非空之后，需要将其打印出来，并将源数据发送回去。当然，具体的操作可以由编程者决定，原样返还是比较简单的操作。同时，我们还需要关注的是，这些处理的过程中，需要关注的socket的读写状态！当数据包到来时，我们应该为可读状态，讲数据读出之后，要记得把socket的状态改为可写，等待数据的写入。

####第三步：
资源的释放。当程序执行完毕时，我们需要对系统调用的程序进行释放。**32**行的else就是其中一个操作。最后的ioloop.stop()也是必须的！

实验结果如下：
 
![result](http://a.hiphotos.bdimg.com/album/s%3D550%3Bq%3D90%3Bc%3Dxiangce%2C100%2C100/sign=2fcd8e17050828386c0ddc1188a2d83c/9f2f070828381f30e196a8a1ab014c086e06f02e.jpg?referer=909062360ef3d7ca55e10b4630e4&x=.jpg)

基于这个简单的通信，我们可以去创建更大规模的通信，实现更为复杂的传输。如SDN中controller与交换机之间的通信。
