title:[c]线程池的实现
date:2014/4/28
tags:c,thread_pool
category:Tech

###前言

这是C语言培训的最后一题，线程池，今天看了看控制器的代码，看到了线程池的影子，然后发现应该赶紧写完这篇了。哎，文笔不行，写书写成屎了！希望再修改几次能不丢人吧。

本篇主要介绍如何实现一个线程池模型，task是简单的打印，当然如果你想让线程池完成你的功能线程的管理，只需要将task换成你的线程就可以了。

###线程池

（摘自百度百科）线程池是一种多线程处理形式，处理过程中将任务添加到队列，然后在创建线程后自动启动这些任务。线程池线程都是后台线程。

组成：

* 线程池管理器（ThreadPoolManager）:用于创建并管理线程池
* 工作线程（WorkThread）: 线程池中线程
* 任务接口（Task）:每个任务必须实现的接口，以供工作线程调度任务的执行。
* 任务队列:用于存放没有处理的任务。提供一种缓冲机制。

更多可访问：http://baike.baidu.com/link?url=caXqYSEEEDLS28VYuSzSxPbTM3dt_5WwXqF2-TUxR8ptJxggJaJHfTZ3_9Hs4urU#2

###threadpool.h

threadpool.h的功能主要是定义工作线程的结构和线程池结构，声明相关的函数，如创建函数。

	#ifndef _THREADPOOL_
	#define _THREADPOOL_
	//#include <stdlib.h>
	//#include <pthread.h>
	
	typedef struct threadpool_work
	{
		void (*process)(void*);
		void* arg;
		struct threadpool_work* next; //use the link for save thread.
	
	}tpool_work_t;
	
	typedef struct tpool
	{
		int num_thread;//count of thread.
		int max_queue_size;  //max number of thread.
	
		pthread_t* tid; //thread id;
		tpool_work_t *queue; //the queue header.
		int front,rear; //the header and end.
	
		int closed; //close putting ,but can run the existed threads.
		int shutdown;   //shutdown all thread works.
	
		pthread_mutex_t queue_lock;      //lock the queue
		pthread_cond_t queue_has_task;   //task condition.
		pthread_cond_t queue_has_space;  //space condition
		pthread_cond_t queue_empty;      //empty condition
	
	}*tpool_t; 
	
	void *thread_creat(void*); //void* pointer.
	
	void tpool_init(tpool_t* tpool_p, int num_thread ,int max_queue_size);
	
	int tpool_add_work(tpool_t tpool,void(*routine)(void*),void* arg); //第二个参数是任务函数的地址，*arg是任务函数的参数、
	
	int tpool_destroy(tpool_t tpool, int finish); 
	int get_size(tpool_t pool);
	int full(tpool_t pool);
	int empty(tpool_t pool);
	
	#endif


###threadpool.c

threadpool.c是threadpool.h的实现。主要实现了，threadpool.h中定义的所有函数。

	#include <stdlib.h>
	#include <stdio.h>
	#include "threadpool.h"
	#include <pthread.h>
	#include <unistd.h>
	#include <sys/types.h>
	#include <string.h>
	
	void tpool_init(tpool_t* tpool_p, int num_thread ,int max_queue_size)
	{
		int i;
		tpool_t pool;
	
		pool = (tpool_t)malloc(sizeof(struct tpool));
		if (pool ==NULL)
		{
			perror("malloc");
			exit(0);//return normal?
		}
	
		pool->num_thread = 0;
		pool->max_queue_size = max_queue_size+1; //为了留出一个位置，用于区别队列满和空的区别，详情看博客中循环队列那篇。
		pool->num_thread = num_thread;
		pool->tid = NULL;                        //thread id
		pool->front = pool->rear = 0;
		pool->closed = pool->shutdown = 0;
	//init
		if (pthread_mutex_init(&pool->queue_lock,NULL) == -1)//failed.
		{
			perror("pthread_mutex_init");
			free(pool);
			exit(0);
		}
		if (pthread_cond_init(&pool->queue_has_task,NULL) == -1)//初始化
		{
			perror("pthread_cond_init:queue_has_task");
			free(pool);
			exit(0);
		}
			if (pthread_cond_init(&pool->queue_has_space,NULL) == -1)
		{
			perror("pthread_cond_init:queue_has_space");
			free(pool);
			exit(0);
		}
			if (pthread_cond_init(&pool->queue_empty,NULL) == -1)
		{
			perror("pthread_cond_init:queue_empty");
			free(pool);
			exit(0);
		}
	
		if ((pool->queue = malloc(sizeof(struct threadpool_work)*pool->max_queue_size)) == NULL)
		{
			perror("malloc pool->queue:");
			free(pool);
			exit(0);
		}
	
		if ((pool->tid = malloc(sizeof(pthread_t)*num_thread))==NULL)
		{
			perror("malloc pool->tid");
			free(pool->queue);
			free(pool);
			exit(0);
		}
	
		for (i = 0; i < num_thread; i++)
		{
			
			if (pthread_create(&pool->tid[i],NULL,thread_creat,(void*)pool)!=0)//创建线程，执行实体为thread_creat函数。
			{
				perror("pthread_create error");
				exit(0);
			}
		}
	
		*tpool_p = pool;
	
	}
	void *thread_creat(void* arg) //use for creating threads.
	{
		tpool_t pool = (tpool_t)(arg);
		tpool_work_t* work;
		
		//printf("thread_creat start\n");
		for(;;) //loop forever
		{
			pthread_mutex_lock(&pool->queue_lock);//在操作数据之前，需要先lock
			while(empty(pool)&&!pool->shutdown) //if the queue is empty and wait for add.
			{
				printf("I am sleep..\n");
				pthread_cond_wait(&pool->queue_has_task,&pool->queue_lock); 
			}
			printf("I am awake\n");
			if (pool->shutdown ==1)
			{
				printf("exit\n");
				pthread_mutex_unlock(&pool->queue_lock);
				pthread_exit(NULL);
			}
			int is_full = full(pool);  
			work = pool->queue+pool->front;//that is a queue
			//printf("pool->front:%d\n",pool->front );
			pool->front = (pool->front+1)%pool->max_queue_size;
			//printf("pool->front(after)%d\n",pool->front );
	
			if (is_full)
			{
				pthread_cond_broadcast(&pool->queue_has_space);  //broadcast to all thread that has been full.
			}
			if (empty(pool))
			{
				pthread_cond_signal(&pool->queue_empty);
			}
			pthread_mutex_unlock(&pool->queue_lock);//读写完成，解锁
			(*(work->process))(work->arg);
		}
	}
	
	int tpool_add_work(tpool_t tpool,void(*process)(void*),void* arg)//添加任务函数
	{
		tpool_work_t *temp;
		pthread_mutex_lock(&tpool->queue_lock);
	
		while(full(tpool) && (!tpool->shutdown) &&(!tpool->closed))
		{
			printf("queue full\n");
			pthread_cond_wait(&tpool->queue_has_space,&tpool->queue_lock);//if full and do not shutdown and do not closed ,then we wait.
		}	
		if(tpool->shutdown ||tpool->closed)
		{
			printf("shutdown\n");
			pthread_mutex_unlock(&tpool->queue_lock);
			return -1;
		}
	
		int is_empty = empty(tpool);
		//printf("is empty:%d\n", is_empty);
		int size =get_size(tpool);
		//printf("len:%d\n",size);
		temp = tpool->queue +tpool->rear;  //add a node of link.
		temp->process = process;
		temp->arg = arg;
		tpool->rear = (tpool->rear+1)%tpool->max_queue_size;
	
		if (is_empty)
		{		
			printf("signal has task\n");
			pthread_cond_broadcast(&tpool->queue_has_task);
			printf("pthread_cond_broadcast\n");
		}
		//pthread_cond_broadcast(&tpool->queue_has_task);
		pthread_mutex_unlock(&tpool->queue_lock);
	
		return 0;
	}
	
	
	
	
	int tpool_destroy(tpool_t tpool, int finish)
	{
		printf("tpool_destroy\n");
		int i;
		pthread_mutex_lock(&tpool->queue_lock);
		tpool->closed = 1;// wait for all works done
	
		if (finish ==1)
		{
			printf("wait for all work done\n");
			while(!empty(tpool))
			{
				pthread_cond_wait(&tpool->queue_empty,&tpool->queue_lock);
			}
		}
		tpool->shutdown = 1;
		pthread_mutex_unlock(&tpool->queue_lock);
		pthread_cond_broadcast(&tpool->queue_has_task);
	
		printf("wait for worker thread exit\n");
		
	
		for (i = 0; i < tpool->num_thread; i++)
		{
			pthread_join(tpool->tid[i],NULL);  //All awake and find out shotdown ,and exit.
		}
		printf("free thread pool\n");
	
		free(tpool->tid);
		free(tpool->queue);
		free(tpool);
	}
	
	int empty(tpool_t pool)
	{
		return pool->front ==pool->rear;
	}
	
	int full(tpool_t pool)
	{
		return ((pool->rear+1)%pool->max_queue_size ==pool->front);//+1用于区别循环链表中的full and empty
	}
	int get_size(tpool_t pool)
	{
		return (pool->rear+pool->max_queue_size-pool->front)%pool->max_queue_size;
	}


###main.c

main函数主要负责调用，测试线程池。工作任务是最简单的打印。

	#include <stdlib.h>
	#include <pthread.h>
	#include "threadpool.h"
	
	char *str[] ={"string 0","string 1","string 2","string 3","string 4","string 5","string 6",};
	
	void job(void *str)
	{
		long i,x =0;
		for (i = 0; i < 10000000; ++i)//loop for watching the print.
		{
			x=x+i;
		}
		printf("%s\n",(char*)str);
	}
	int main(int argc, char const *argv[])
	{
		int i;
		tpool_t test_pool;
	
		tpool_init(&test_pool,8,18);//工作线程为8，最大为18个
	
		for (i = 0; i < 6; ++i)
		{
			//printf("loop\n");
			tpool_add_work(test_pool, job, str[i]);
		}
		tpool_destroy(test_pool,1);
	
		return 0;
	}


###后续

现在写教程都不知道说什么好了，感觉要说的都在代码，注释里，就不多废话了。有问题的请评论。希望能对你有帮助。另外你可能需要在添加完县城之后，将线程join一下才能看打印。释放的时候可以运行等待的线程。

c语言培训题到此结束。希望是一个新的开始！
