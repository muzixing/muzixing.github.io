title:Listen to OpenStack Notification
date:2016/9/30
tags:OpenStack, kombu
category:Tech

在许多应用场景下，需要监听OpenStack的消息来做一些操作，从而实现事件驱动／消息驱动的业务。本文将介绍如何使用[kombu](http://kombu.readthedocs.io/en/latest/introduction.html#installation)库来监听OpenStack的消息，包括neutron，nova等相关类型的notification。

### Kombu, AMQP, RabbitMQ

[Kombu](https://github.com/celery/kombu)是Python的消息库，封装来许多消息的报文，支持包括[AMQP](https://www.amqp.org/)等多种消息协议。而在OpenStack端，Notification的发布系统由[RabbitMQ](http://www.rabbitmq.com/)实现。为了监听OpenStack发出的Notification, 我们需要在本地用Kombu库建立一个connection, 连接到OpenStack的消息发布系统。

### Terminology 

在学习过程中，会遇到Exchange, Queue等术语，此处将简要介绍这些概念：

* Producers

消息生产者，产生消息，并发送到交换器。

* Exchanges

消息交换器，接受生产者发送过来的消息，根据对应的routing\_key，来将消息路由到对应的队列。

* Queues

队列接收来自交换器发来的消息，队列由消费者定义，自然也为消费者使用，用于存储消息。

* Consumers

消费者从队列中读取消息，并进行处理。消费者声明和定义队列，并将队列绑定到对应的exchange上。

* Routing keys

每一种消息都有路由键（routing\_key）,可以被exchange用来判定如何路由消息到对应的队列。根据交换的类型不用，routing\_key的解析过程不同。

### Exchange type

AMQP协议中主要定义了3种exchange type，包括：

* Direct exchange

根据routing\_key的值，将匹配成功的消息发送到指定的队列。

* Fan-out exchange

将消息发送到所有队列，和交换机的flood操作类似。


* Topic exchange

根据给定topic以及匹配规则来实现消息的路由。比如匹配的pattern为*.muzixing.#, 则hello.muzixing.info匹配成功，而muzixing.info匹配失败。

<center>![topic](http://www.rabbitmq.com/img/tutorials/python-five.png)</center>


### Kombu Example

首先，需要先[安装Kombu](http://kombu.readthedocs.io/en/latest/introduction.html#installation)。安装之后，可以通过以下的示例代码来连接到OpenStack。注意需要将user，pwd，host和port修改成对应的OpenStack消息服务器的用户名，登陆密码，ip地址和传输层端口号。 完成之后，运行该python文件，即可监听OpenStack的通知。

```py
    from kombu import Queue, Exchange
    from kombu.log import get_logger
    from kombu.mixins import ConsumerMixin
    
    logger = get_logger(__name__)
    
    
    class Worker(ConsumerMixin):
        event_queues = [
            Queue('notification.nova',
                  Exchange('nova', 'topic', durable=False),
                  durable=False, routing_key='#'),
            Queue('notifications.neutron',
                  Exchange('neutron', 'topic', durable=False),
                  durable=False, routing_key='#')
        ]
    
        def __init__(self, connection):
            self.connection = connection
    
        def get_consumers(self, Consumer, channel):
            return [Consumer(queues=self.event_queues,
                             accept=['json'],
                             callbacks=[self.process_task])]
    
        def process_task(self, body, message):
            print("Receive message: %r" % (body, ))
            message.ack()
    
    if __name__ == '__main__':
        from kombu import Connection
        from kombu.utils.debug import setup_logging
    
        # setup root logger
        setup_logging(loglevel='DEBUG', loggers=[''])
        connect_url = 'amqp://' + user + ':' + pwd + '@' + host + ':' + port + '//'
        with Connection(connect_url) as conn:
            try:
                print(conn)
                worker = Worker(conn)
                worker.run()
            except KeyboardInterrupt:
                print('Stopped')
```

以上示例代码中有两个地方需要注意。首先是需要将用户名等信息修改正确，其次是Queue的定义。在Worker类中，定义了event\_queues列表，列表中是对应的Queue，用来接收️Notification。为了接收nova的信息，需要构造一个Exchange instance作为Queue的参数，其中第一个参数‘nova’是exchange的名字，代表着这个队列将绑定到nova的消息exchange上。同样的，为了接受neutron的消息，我们还定义了另一个队列，队列绑定到了名字叫‘neutron’的exchange上。同理，若希望绑定到对应的exchange，继续添加Queue即可。Routing的参数类型这里设置为topic, durable参数表示消息数据的持久化特性。routing\_key则是路由的键值。此处接受所有来自对应名称exchange的消息。event\_queue将作为Consumer类初始化实例的参数，用于实例化消费者。

```py
    class Worker(ConsumerMixin):
        event_queues = [
            Queue('notification.nova',
                  Exchange('nova', 'topic', durable=False),
                  durable=False, routing_key='#'),
            Queue('notifications.neutron',
                  Exchange('neutron', 'topic', durable=False),
                  durable=False, routing_key='#')
        ]
```

### 总结

OpenStack目前在云环境中应用十分广泛，是非常值得喜欢云计算和SDN的同学去学习和研究的。作为一个大型的项目，OpenStack采用了AMQP来分发事件。作者在工作过程中需要使用OpenStack的事件，因此总结来这一篇文章。特别感谢谷歌给予的大力支持，没有谷歌我就查不到解决问题的正确姿势[1]。希望能给读者带来一些帮助。


## References

[1] "Listen to OpenStack Neutron Messages from RabbitMQ using Kombu messaging library", http://thetaooftech.blogspot.com/2014/04/listen-to-openstack-neutron-messages.html
