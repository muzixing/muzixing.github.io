title:[C语言]两个栈实现队列
date:2014/4/15
tags:c
category:Tech

###前言

这是学习c语言的第一个训练题。刚开始写得真的非常差！！后来在大男哥的知道下学会了如何写c语言。本篇教程是：如何使用两个栈实现队列的功能。基本上这个代码也是他手把手教的。

###算法

如何使用两个栈实现队列？
大家都能想到需要在pop的时候从一个栈到另一个栈倒一下，再pop，这样就有做到先入先出了。但是如何判别哪一个是目前正在使用的，而哪一个又是用来接收第一个栈pop数据的呢？

其实有一个好办法就是，指定一个是专门用于入栈的栈in\_stack，所有数据入栈的时候必须入到这个栈中，而出栈的时候，需要将数据pop到另一个栈中，然后再从另一个栈中出栈。第二次出栈的时候直接从out\_stack。直到out\_stack的数据为空，则将in_stack的数据pop到out_stack中。这样就能保证出栈的顺序是FIFO了。

同时，in\_stack的深度就是队列的最小深度。

最大深度是len(in\_stack+out\_stack).当且仅当第一次push时，全部push到满，然后pop数据，之后继续push直到满。严格意义上来说应该是len(in\_stack+out\_stack)-1，因为有一个pop掉了。

###实现

####stack的实现

首先我们要实现stack。以下是stack.h
	
	/*
	##################
	Author: muzi
	Date:2014/4/10
	TODO: Using the stack to complete the list function.
	##################
	*/
	#ifndef _STACK_H_
	#define _STACK_H_
	
	typedef struct _stack
	{
		void ** buttom;
		int top;
		int max_size;
	}stack_t;
	stack_t * stack_create();
	
	void stack_destroy(stack_t * stack);
	void * stack_push(stack_t * stack, void * data);
	void * stack_pop(stack_t * stack);
	
	#endif

stack.h中定义了stack的结构体，以及以下相关的函数，如push，pop等。当然类似于面向对象中的构造函数的stack_create()也是必须的。最后还不忘定义destroy去释放内存。


	#include <stdlib.h>
	#include "stack.h"
	
	stack_t* stack_create(){
		stack_t * p = (stack_t *)malloc(sizeof(stack_t));
		p->max_size = 10;
		p->buttom = (void **)malloc(sizeof(void *) * p->max_size);
		p->top = 0;
		return p;
	}
	
	void stack_destroy(stack_t * stack){
		free(stack->buttom);
		free(stack);
	}
	
	void * stack_push(stack_t * stack, void * data)
	{
		if(stack->top >= stack->max_size)
		{
			return NULL;
		}
		stack->buttom[stack->top] = data;
		stack->top++;
		return data;
	}
	
	void * stack_pop(stack_t * stack)
	{
		if (stack->top > 0)
		{
			stack->top--;
			return (stack->buttom[stack->top]);
		}
		return NULL;
	}

这些都是基本的函数，相比应该不难，不做更多解释。

####queue的实现

同样的先，先写queue.h

	#ifndef _QUEUE_H_
	#define _QUEUE_H_
	#include "stack.h"
	
	typedef struct _QUEUE_H_
	{
		stack_t * in;
		stack_t * out;
	}queue_t;
	
	queue_t * queue_create();
	void queue_destroy(queue_t * queue);
	void * queue_push(queue_t * queue, void * data);
	void * queue_pop(queue_t * queue);
	
	
	#endif

这个文件定义了struct queue_t,成员有 两个stack的指针。（喜欢python的人是绝对不喜欢c的指针的，比如我。不过不得不说，不会c的程序员，真不好意思说自己是程序员。）

我们要在queue.c中去实现queue.h定义的内容。

关键算法也在这里。


	#include "queue.h"
	#include <stdlib.h>
	
	queue_t * queue_create()
	{
		queue_t * queue = (queue_t *)malloc(sizeof(queue_t));
		queue->in = stack_create();
		queue->out = stack_create();
		return queue;
	}
	void queue_destroy(queue_t * queue)
	{
		stack_destroy(queue->in);
		stack_destroy(queue->out);
	}
	
	void * queue_push(queue_t * queue, void * data)
	{
		return stack_push(queue->in, data);
	}
	
	void * queue_pop(queue_t * queue)
	{
		if(queue->out->top == 0)  //最关键的其实就是这个判断以及这个判断所执行的语句(如果out stack都出栈了，那么需要从in中倒换过来。)
		{
			while(queue->in->top > 0) //如果in中有数据的话。
			{
				stack_push(queue->out,stack_pop(queue->in));
			}
		}
		return stack_pop(queue->out);//始终返回的是out_stack的数据
	}

就是这么简单，就把功能实现了。跟着大男哥学习c语言编程，还是有很多收获的。

####main函数测试。

	#include <stdio.h>
	#include <stdlib.h>
	#include "queue.h"
	//#include "stack2list.h"
	
	
	void int_printer(void * data);
	int main()
	{
		queue_t * queue = queue_create();
	
		int * data = (int *)malloc(sizeof(int));
		*data = 1;
		queue_push(queue,data);
		data = (int *)malloc(sizeof(int));
		*data = 2;
		queue_push(queue,data);
		data = (int *)malloc(sizeof(int));
		*data = 3;
		queue_push(queue,data);
		data = (int *)malloc(sizeof(int));
		*data = 4;
		queue_push(queue,data);
		data = (int *)malloc(sizeof(int));
		*data = 5;
		queue_push(queue,data);
	
		int i = 0;
		for(i = 0; i<2 ; i++)
		{
			data = (int *)queue_pop(queue);
			printf("%d,",*data);
			free(data);
		}
		data = (int *)malloc(sizeof(int));
		*data = 6;
		queue_push(queue,data);
		data = (int *)malloc(sizeof(int));
		*data = 7;
		queue_push(queue,data);
		for(i = 0; i<5 ; i++)
		{
			data = (int *)queue_pop(queue);
			printf("%d,",*data);
			free(data);
		}
		return 0;
	}
	
	void int_printer(void * data)
	{
		printf("%d",*((int *)data));
	}

至此功能实现。

在写代码的过程中，发现设计的重要性，一个好的逻辑思维，设计风格，能让代码写得非常优雅。其实写代码也是一个有讲究的活。就像一个工程师设计一个模型一样，既要美观实用，又要能随时被拿走，放到别处使用。代码的风格，结构的设计，实现方案等等，都是一个很好玩的事情。

希望不久之后我能学好c语言！感谢大男哥的帮助！
