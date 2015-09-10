title:[c]time_server
date:2014/4/18
category:Tech
tags:c,socket

###前言

本篇内容主要是介绍如何编写一个通过socket通信，实现获取服务器当前时间的例子。

###实现

首先我们需要定义两个函数：

	int time_server(int port);
	char* get_time(int ip, int port);

这两个函数是用于提供时间获取服务和，客户端调用去获取时间的函数。

以下是time_server.h的内容：

	#ifndef _TIME_SERVER_
	#define _TIME_SERVER_
	#include <sys/socket.h>
	#include <string.h>
	
	int time_server(int port);
	char* get_time(int ip, int port);
	#endif


time\_server.c文件是实现time\_server中的函数声明。
头文件如下：

	#include <stdlib.h>
	#include "time_server.h"
	#include <stdio.h>
	#include <time.h>
	#include <sys/types.h>
	#include <sys/socket.h>
	#include <netinet/in.h>

我们需要把系统时间返回所以需要用到time.h

需要使用socket，所以需要include <socket.h>

netinet/in.h则是因为要使用inet_addr()函数。

**time_server函数实现如下：**
	
	int time_server(int port)//You should change the ip addr into int.
	{
		int server_fd;    //用于记录socket的fd
		int client_fd;
		struct sockaddr_in server_addr, client_addr;
		int sock_size;//size of socket_in.
		
		printf("> server start.\n");
		//create a socket.
		server_fd = socket(AF_INET,SOCK_STREAM,0); //若成功返回一个非-1的整数fd，若失败，返回-1
		if(-1==server_fd)
		{
			printf("> create socket failed.\n");
			return -1;
		}
		printf("> create socket successful.\n");
	
		//set the parameters of socket
		bzero(&server_addr,sizeof(struct sockaddr_in));//fill 0 of server_addr
		server_addr.sin_family = AF_INET;//设置协议族为IPV4。另还有其他几种如AF_UNIX,可google.
		server_addr.sin_addr.s_addr = inet_addr("0.0.0.0");//将十进制点分ip,转化为32bit的整数，同时0.0.0.0 为监听所有地址。服务器可能不止一个地址。
		server_addr.sin_port = htons(port);//htons()函数是将port转化为网络字节序（大小端问题）
	
		//bind to port
		if (-1 == bind(server_fd,(struct sockaddr*)(&server_addr),sizeof(struct sockaddr)))
		{
			printf("> bind failed\n");
			return -1;
		}
		printf("> bind seccessful\n");
		//listen 
		if (-1== listen(server_fd,10))//listen(socket_fd, listen number)
		{
			printf("> listen failed\n");
			return -1;
		}
		printf("> listen seccessful\n");
		//recv
		while(1)
		{
			sock_size = sizeof(struct sockaddr_in);
			client_fd = accept(server_fd,(struct sockaddr*)(&client_addr),&sock_size);//(server_socket_fd,store_mem,length)
			if (-1 ==client_fd)
			{
				printf("> accept failed.\n");
				return -1;
			}
			printf("> accept seccessful\n");
	
			time_t t;
			time(&t);
			
			if (-1 == send(client_fd,asctime(localtime((const time_t*)&time)),sizeof(asctime(localtime((const time_t*)&time))),0))//send the system time
			{
				printf("> send failed.\n");
				return -1;
			}
			printf("send time seccessful\n");
			close(client_fd);
		}
	close(server_fd);
	
	return 0;
	}
	

以上是time\_server的函数实现。但是比较忧伤的是我使用的time的格式不太对，发送过去的星期。接下来是客户端的代码。两个函数都写在一个time\_server.c文件里就好了。直接通过函数名调用即可。

**get_time()**

	char* get_time(int ip, int port)//参数是server_ip 和 port
	{	
		int client_fd;
		int recv_length;
		int sock_size = sizeof(struct sockaddr_in);
		char buffer[1024] = {0};
		struct sockaddr_in server_addr, client_addr;
	
		printf("> client start.\n");
		//create a socket.
		client_fd = socket(AF_INET,SOCK_STREAM,0);
		if(-1==client_fd)
		{
			printf("> create socket failed.\n");
			return -1;
		}
		printf("> create socket successful.\n");
	
		//set the parameters of socket
		bzero(&server_addr,sizeof(struct sockaddr_in));//set the server addr.
		server_addr.sin_family = AF_INET;
		server_addr.sin_addr.s_addr = ip;
		server_addr.sin_port = htons(port);
	
		if (-1 == connect(client_fd,(struct sockaddr*)(&server_addr),sizeof(struct sockaddr)))
		{
			printf("connect failed\n");
			return -1;
		}
		printf("connect successful\n");
		if (-1 == (recv_length =recv(client_fd,buffer,1024,0)))
		{
			printf("receive failed\n");
			return -1;
		}
		printf("receive:\n");
		buffer[recv_length] = '\0';//end of buffer.
		printf("%s\n", buffer);
	
		getchar();
		close(client_fd);
		return buffer;
	}

基本上time_server.c就是以上的内容，并不复杂。

**main.c**

	#include <stdlib.h>
	#include <stdio.h>
	#include "time_server.h"
	#include <sys/socket.h>
	#include <netinet/in.h>
	#include <sys/types.h>
	int main(int argc, char const *argv[])
	{	
		int server_ip = inet_addr("0.0.0.0");
		//time_server(50000);
		char * time = get_time(server_ip,50000);
		printf("%s\n",time );
	
		return 0;
	}
主函数也非常简单，在一台服务器机器上运行time_server(port).

在客户端上，运行get_time(server_ip,port)即可。

另，启动顺序是先启动server,再启动client,不然会有refused。
