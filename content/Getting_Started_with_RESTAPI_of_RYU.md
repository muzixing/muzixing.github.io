title:Getting started with RESTAPI of RYU
category:Tech
tags:RYU,REST
date:2015/5/10


在使用RYU的过程中，有时需要使用web拓扑，有时也需要通过API去下发流表等操作。这些操作在RYU中都会使用到RESTAPI。在学习RYU的过程中多次涉及到REST相关的内容，总是不知道如何实现和使用。最近在做实验需要这方面的知识，才有机会去学习REST并总结成博文。希望能给其他学习者提供帮助。本篇博文将简要介绍两部分内容：

* What is REST?
* How to use REST API in RYU?

##What is REST

[REST](http://zh.wikipedia.org/zh/REST):表征性状态传输（英文：Representational State Transfer，简称REST）是Roy Fielding博士在2000年他的博士论文中提出来的一种软件架构风格。更多REST的相关介绍可以查看[视频介绍](http://www.restapitutorial.com/lessons/whatisrest.html).

REST架构风格中，资源是通过URI来描述的。对资源的操作采用了HTTP的GET，POST，PUT和DELETE方法相对应。资源的表现形式可以是json或xml。REST的架构是Client-Server架构，同时链接是无状态的。所以要求在传输的过程中需要包含状态信息。此外，可以使用cache机制增进性能。在上述视频中提到REST的6中限制为：

* Uniform Interface
* Stateless
* Cacheable
* Client-Server
* Layered System
* Code on Demand (optional)

满足以上的API才是符合REST风格的API。


##How to use REST API in RYU

在SDN控制器RYU的源代码中，我们可以发现RYU已经完成了一些RESTAPI的定义，实验人员可以直接使用对应的RESTAPI来进行编程。


在ryu的app目录，可以发现许多rest相关的文件，比如ofctl_rest.py，rest.py,和rest_topology.py等。其中rest.py提供了基本的RESTAPI，ofctl_rest.py提供了与OpenFlow相关的RESTAPI，如查看、添加、修改流表等API。以ofctl_rest.py举例如何使用RYU中的RESTAPI。

###启动RYU相关组件

在终端中输入如下命令，打开RYU运行ofctl_rest.py以及其他需要的模块，本案列中打开了simple_swich_13.py模块。

	ryu-manager ofctl_rest.py simple_switch_13.py

运行RYU之后，可以查看到wsgi启动，监听端口为8080。

![ryu_rest](http://ww2.sinaimg.cn/mw690/7f593341jw1erzfzm7vthj20k50cwgq2.jpg)

在ofctl_rest.py源码的前面部分，我们可以查看到写成注释形式的RESTAPI的使用方法，节选如下：

    # REST API
    #
    # Retrieve the switch stats
    #
    # get the list of all switches
    # GET /stats/switches
    #
    # get the desc stats of the switch
    # GET /stats/desc/<dpid>
    #
    # get flows stats of the switch
    # GET /stats/flow/<dpid>
    #
    # get flows stats of the switch filtered by the fields
    # POST /stats/flow/<dpid>
    #
    # get aggregate flows stats of the switch
    # GET /stats/aggregateflow/<dpid>
    #
    # get aggregate flows stats of the switch filtered by the fields
    # POST /stats/aggregateflow/<dpid>
    #
    # get ports stats of the switch
    # GET /stats/port/<dpid>
    


###打开mininet连接控制器
    
打开mininet，运行任意拓扑，连接控制器RYU。并执行pingall,检测网络联通性。

![mininet](http://ww4.sinaimg.cn/mw690/7f593341jw1erzg3km6n7j20k10cqjv4.jpg)

    
###使用RESTAPI

推荐使用chrome插件[POSTMAN](https://chrome.google.com/webstore/detail/postman-rest-client/fdmmgilgnpjigdojojpjoooidkmcomcm)来操作RESTAPI，取代终端的curl命令。
在POSTMAN中输入正确的内容就可以下发请求信息。如请求dpid为1的交换机上的流表信息：

    http://localhost:8080/stats/flow/1

选择动作类型为GET，点击send，可以马上获得交换机1上的流表信息。

![](http://ww3.sinaimg.cn/mw690/7f593341jw1erzgdc9pobj217k0h6aen.jpg)

详细流表内容如下。可见目前交换机上有三条流表项，其中第一条是默认的miss\_table\_entry.后两条是h1和h2通信的双向流表项。

![](http://ww2.sinaimg.cn/mw690/7f593341jw1erzgeh5iz5j20mg0no78j.jpg)

尝试对流表进行修改，可以使用POST动作类型，下发一个flow_mod消息，对现有流表进行操作。输入资源URI如下：

    http://localhost:8080/stats/flowentry/modify

message body 如下：

    {
    "dpid": 1,
    "match":{
    	"dl_dst": "00:00:00:00:00:02",
        "in_port":1
            },
    "actions":[]
    }
send之后，返回200状态码，提示成功。RYU返回消息内容为1.

![](http://ww1.sinaimg.cn/mw690/7f593341jw1erzgehkqtaj20yc0g7jtm.jpg)

此时重新获取交换机上的刘表，可以观察到流表修改已经成功。

![](http://ww4.sinaimg.cn/mw690/7f593341jw1erzgehwfpmj20ka0n0wiq.jpg)

在Mininet中重新pingall测试联通性，果然不通，修改流表结果正确。

![](http://ww4.sinaimg.cn/mw690/7f593341jw1erzgei7hyjj20k60csjub.jpg)

其他RESTAPI的示例不再赘述，读者可自行尝试。  由于篇幅限制，后续的源码分析部分将在另一个文章中详细介绍。
