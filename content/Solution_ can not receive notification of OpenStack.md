title: Solution: can not receive notification of OpenStack
date:2016/12/21
tags: Openstack, neutron, notification
Category: Tech

If you set up a AMQP connection to listen to Rabbit message queue, and can not receive any notification when connection is correct. Stucking queue may be the reason of this problem. As I proposed in [ask.openstack.org](https://ask.openstack.org/en/question/100102/can-not-receive-neutron-notification-while-can-receive-nova-notification/), you can purge the queue to clear all the message in queue. In this way, the new message won't be stucked in the queue.

the command is:

    rabiitmqctl purge_queue queue_name
    
please use the specified queue name like 'notifications.nova' to replace the 'queue_name'.

It is recommended to restart the services if purging queue does not help. Command example like,

    /etc/init.d/neutron-service restart

the command patern is,

    /etc/init.d/xxx start
    /etc/init.d/xxx stop
    /etc/init.d/xxx restart

Hope this blog can help you.





