date:2014/4/19
title:[c]生产者消费者模式实现
tags:multi_thread
category: Tech

###前言

本文主要内容是：使用多线程，运行生产者函数和消费者函数，去实现队列（临界区）的读写操作。

其意义在与熟悉多线程的互斥过程。生产者消费者模式是最好，最简单的选择。

###数据结构

首先我们要操作的数据结构是队列。那么我首先要构造一个队列：

queue.h

	#ifndef _QUEUE_
	#define _QUEUE_
	
	
	typedef struct _QUEUE_
	{
		int maxsize;
		int buffer[10];  //bad design
		int end;
		int begin;
		
	}queue_t;
	
	void queue_init(queue_t* queue); //队列的初始化。如end,begin，maxsize的设置。
	int get_len(queue_t* queue);     //获取队列的长度
	void put(queue_t* queue,int num);  //入队
	int get(queue_t* queue);			//出队
	
	#endif

接下来是queue的实现：

queue.c

	#include "queue.h"
	#include <stdlib.h>
	#include <stdio.h>
	
	void queue_init(queue_t* queue)
	{
		queue->maxsize =10;
		memset(queue->buffer,'\0',queue->maxsize); //设置queue->buffer指针开始的位置，长度为10的内存为'\0'
		queue->begin = 0;  
		queue->end = 0;
	
	}
	int get_len(queue_t* queue)
	{
		if ( queue->end == queue->begin)
		{
			printf("> queue empty\n");
			return 0;
		}
		else
			//printf("get end:%d\n", queue->end);
			//printf("get begin:%d\n", queue->begin);
			return (queue->maxsize+queue->end - queue->begin)%queue->maxsize;//使用循环数组实现队列
	}
	void put(queue_t* queue,int num)
	{
		if ((queue->end+1)%(queue->maxsize) != queue->begin) // 空余一个存储单位，用于区别空和满的状态。若不空余一个，则无法直接判别空与满的状态。
		{
			*(queue->buffer+queue->end) = num;		
			printf("> put seccessful:%d\n", queue->buffer[queue->end]);
			queue->end = (queue->end+1)%(queue->maxsize); //next available one 
		}
		else
			printf("> queue full.\n");
	}
	int get(queue_t* queue)
	{
		if (queue->begin != queue->end)
		{
			int num = queue->buffer[queue->begin];
			queue->begin =(queue->begin+1)%(queue->maxsize);
			return num; //may have a problem.
		}
		else
		{
			printf("> queue empty.\n");
			return -1;
		}
	}

函数实现很简单，主要需要注意的就是空和满的判断。所以需要空余一个单位来区别这两者。

接下来就是生产者和消费者函数的定义了。

###生产者/消费者

pro_con.h

	#ifndef _PROCON_
	#define _PROCON_
	#include "queue.h"
	
	void producer(void * queue);  //生产者函数，用于入队
	void consumer(void* queue);   //消费者函数，用于出队
	#endif

pro_con.c

	#include <stdlib.h>
	#include <stdio.h>
	#include "pro_con.h"
	#include <pthread.h>
	#include <unistd.h>
	
	pthread_cond_t unempty = PTHREAD_COND_INITIALIZER; //初始化一个条件：unempty
	pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;  //初始化一个互斥锁：lock
	
	//Producer thread
	void producer(void* p)
	{
		//printf(p );
		queue_t* queue = (queue_t*)p;
		while(1)
		{
			printf("producer start\n");
			int num1 = pthread_mutex_lock(&lock); //对临界区进行操作之前，必须lock
			if (!num1)
			{
				printf("producer lock\n");
			}
			else
			{
				printf("producer set lock error \n");
			}
			if (get_len(queue) == queue->maxsize -1) //the queue has been full.
			{
				int flag = pthread_cond_wait(&unempty,&lock);//队列已满，s所以给unempty条件加上锁，让本线程进入等待状态，交出cpu。
				printf("producer flag: %d\n",flag);
			}
			// allow to put.
			put(queue,12345);
			printf("producer_get_len:%d\n",get_len(queue));
			if (get_len(queue)!= 0)
			{
				pthread_cond_signal(&unempty);// 若没有满，则通过signal唤醒因为unempty条件而等待的一个线程。
				printf("producer set signal\n");
			}
	
			int num2 = pthread_mutex_unlock(&lock);//处理完成之后，需要unlock，以让其他线程获得该mutex
			if (!num2)
			{
				printf("producer unlock successful\n");
			}
			else
			{
				printf("prodecer unlock successful\n");
			}
			sleep(1);//sleep and return the cpu to other thread.
		}
	}
	
	
接下来是消费者函数的实现。同样写在pro_con.c文件下。逻辑和生产者差不多，只不过操作是出栈。条件相反而已。

	void consumer(void* p)
	{
		//printf(*p);
		queue_t* queue = (queue_t*)p;
		while(1)
		{
			printf("consumer start\n");
			pthread_mutex_lock(&lock);//同样的，先加锁、
			printf("consumer_get_len:%d\n",get_len(queue));
			if(get_len(queue) == 0)
			{
				//queue empty and wait.
				printf("flag%d",pthread_cond_wait(&unempty,&lock));//若空，则无法读取，进入等待状态
			}
			
			printf("consumer get,%d\n", get(queue));
			if (get_len(queue) <queue->maxsize-1)//非满，通过signal唤醒等待线程中的一个。
			{
				pthread_cond_signal(&unempty);
				printf("consumer set signal\n");
			}
			pthread_mutex_unlock(&lock);//最后打开锁。
			printf("consumer unlock\n");
			sleep(2);
	
		}
	}


###main.c

主函数主要负责调用和测试。代码如下：


	#include <stdlib.h>
	#include <stdio.h>
	#include "queue.h"
	#include "producerandconsumer.h"
	#include <pthread.h>
	//include <unistd.h>
	
	int main(int argc, char const *argv[])
	{
		queue_t* queue = (queue_t*)malloc(sizeof(queue_t));
		queue_init(queue);//初始化队列
		//printf("queue_init%d\n",queue->end );
		
		pthread_t tid_a,tid_b;  定义两个线程号。
		queue = (void*)queue;
		printf("queue:%p\n", queue);
		pthread_create(&tid_b,NULL,producer,queue);//参数表（线程号，NULL，执行程序地址，参数）
		printf("pthread_create producer\n");
	
		pthread_create(&tid_a,NULL,consumer,queue);
		printf("pthread_create consumer\n");
	
		//get(queue);
		while(1){;}
		return 0;
	}

下面给出一些队列数据结构的单元测试用例。

	int i;
	for (i = 0; i < 15; i++)
	{
		put(queue,i);
		printf("len:%d\n",get_len(queue));
	}
	printf("len:%d\n",get_len(queue));
	i=0;
	for (i = 0; i < 5; i++)
	{
		printf("%d\n",get(queue));
		printf("len:%d\n",get_len(queue));
	}
	i =0;
	for (i = 0; i < 6; i++)
	{
		put(queue,i);
		printf("len:%d\n",get_len(queue));
	}
	printf("len:%d\n",get_len(queue));

