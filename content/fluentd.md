title:Fluentd入门教程
tags:Fluentd
Category:Tech
date:2017/2/5

最近发生了一些不可描述的故事，艰难之中换到了现在的组，主要的工作内容是数据挖掘。也终于有机会学习新的知识：Ruby和Fluentd。本文将总结开源软件Fluentd的入门知识，包括如何安装，配置文件语法，插件简介等内容。Fluentd的[官网](http://docs.fluentd.org/v0.12/articles/quickstart)内容非常详尽，内容的组织也尤其清晰，所以网络上关于Fluentd的文档很少。本文主要用于学习记录，也希望能帮助到英语不好的读者。

### Overview

Fluentd是一个完全开源免费的log信息收集软件，支持超过125个系统的log信息收集。其架构图如图1所示。 

<center>![fluentd](http://docs.fluentd.org/images/fluentd-architecture.png)</center>

<center>图1. Fluentd架构图</center>

本质上，Fluentd可以分为客户端和服务端两种模块。客户端为安装在被采集系统中的程序，用于读取log文件等信息，并发送到Fluentd的服务端。服务端则是一个收集器。在Fluentd服务端，我们可以进行相应的配置，使其可以对收集到的数据进行过滤和处理，并最终路由到下一跳。下一跳可以是用于存储的数据库，如MongoDB, Amazon S3, 也可以是其他的数据处理平台，比如Hadoop。

### Install

由于Fluentd的安装较为麻烦，所以业界流行的稳定安装版本其实是有Treasure Data公司提供的td-agent。本文将介绍的也是td-agent的安装和使用。

官网[安装文档](http://docs.fluentd.org/v0.12/articles/install-by-deb)介绍了针对不同系统的安装办法。本文介绍“Ubuntu 14.04 LTS / Trusty 64bit/32bit“系统的安装：

    curl -L https://toolbelt.treasuredata.com/sh/install-ubuntu-trusty-td-agent2.sh | sh

安装完成之后，可运行以下的命令来启动Fluentd服务：

    $ /etc/init.d/td-agent restart
    
    $ /etc/init.d/td-agent status
    td-agent (pid  21678) is running...

通过start, stop, restart等命令可以启动、关闭和重启Fluentd服务。此时默认的Fluentd配置文件的目录是/etc/td-agent/td-agent.conf文件。

### Post Sample Logs via HTTP

默认情况下，/etc/td-agent/td-agent.conf文件已经对td-agent进行了基本的配置。可以接收通过HTTP Post的数据，并将其路由、写入到/var/log/td-agent/td-agent.log中。

可尝试通过以下curl命令来尝试post数据。

    $ curl -X POST -d 'json={"json":"message"}' http://localhost:8888/debug.test

执行之后，可在输出log的最后一行找到我们输入的测试数据。

### Syntax of Config

在Fluentd中，配置文件非常重要，它定义了Fluentd应该执行的操作。其语法很简单，详细内容可点击[配置语法](http://docs.fluentd.org/v0.12/articles/config-file)。

打开/etc/td-agent/td-agent.conf文件，可以看到配置文件的具体内容。配置文件中基本会出现的配置分为以下几种：

* source： 定义输入
* match：定义输出的目标，如写入文件，或者发送到指定地点。 
* filter：过滤，也即事件处理流水线，可在输入和输出之间运行。 
* system：系统级别的设置。
* label：定义一组操作，从而实现复用和内部路由。
* @include：引入其他文件，和Java、python的import类似。

### source

Fluentd支持多输入。每一个输入配置必须包含类型／type，比如tcp数据输入，或者http类型输入。type将指定使用的input plugin。以下的示例中就定义了两个输入源，一个是从24224端口进入的tcp数据流，另一个是从9880端口进入的http数据。

    # Receive events from 24224/tcp
    # This is used by log forwarding and the fluent-cat command
    <source>
      @type forward
      port 24224
    </source>
    
    # http://this.host:9880/myapp.access?json={"event":"data"}
    <source>
      @type http
      port 9880
    </source>

Source指定的input插件将带有{tag, time,record} 三个属性的事件／event提交给Fluentd的引擎，完成数据的输入。

### match

Match配置了数据流的匹配规则和匹配成功后所需执行的动作，和路由表项类似。比如以下的配置中就对匹配myapp.access标签成功的数据包执行file类型动作，将数据写入到路径为/var/log/fluent/access的文件中。

    
    # Match events tagged with "myapp.access" and
    # store them to /var/log/fluent/access.%Y-%m-%d
    # Of course, you can control how you partition your data
    # with the time_slice_format option.
    <match myapp.access>
      @type file
      path /var/log/fluent/access
    </match>

标准的动作有file和forward等。File表明写入文件，而forward表明转发到下一跳。

Match Pattern的设计与正常的正则匹配没有区别，具体的分类如下：
   
    *: 匹配tag的某一部分，比如 a.* 可以匹配 a.b, 但a.b.c无法匹配成功。
    
    **: 匹配0个或者多个tag部分。比如 a.** 可以匹配a.b,a.b.c
    
    {X,Y,Z}：匹配X, Y, or Z,或关系。
    
此外，他们还可以混用，比如a.{b,c,d}.*等等。当<match>标签内，有多个匹配模式时，将支持或逻辑的匹配，即只要匹配成功人一个都执行对应的操作。比如：
    
    <match a b> 匹配a和b.
    <match a.** b.*> 匹配a, a.b, a.b.c

### Logging

Fluentd支持两种类型的logging 配置，一种是全局的，另一种是针对插件的。

* global
* Plugin

支持的log的输出级别有如下几种：

* fatal
* error
* warn
* info
* debug
* trace


介绍完Config file的语法之后，我们还需要了解config file配置的对象Fluentd的Plugin/插件。

### Plugin

Fluentd有5种类型的插件，分别是：

* Input：完成输入数据的读取，由source部分配置
* Parser：解析插件
* Output：完成输出数据的操作，由match部分配置
* Formatter：消息格式化的插件，属于filter类型
* Buffer：缓存插件，用于缓存数据

每一个类型都包含着多种的插件，比如input类型就包含了以下几种插件：

* in_forward
* in_http
* in_tail
* in_exec
* in_syslog
* in_scribe


由于篇幅限制，本文将不会对插件进行展开介绍，读者可以自行阅读[官方文档](http://docs.fluentd.org/v0.12/articles/input-plugin-overview)。

### Route

Route指的是数据在Fluentd中的处理流水线，一般的流程为

* input  -> filter  ->  output
* input  -> filter  ->  output with label

即由输入插件获取数据，然后交给filter做处理，然后交给output插件去转发。同时，也支持数据包／事件的重新提交，比如修改tag之后重新路由等等。

* reroute event by tags
* reroute event by record content
* reroute event to other label

### Use case

此处将选择一个最简单的使用案例来介绍Fluentd的使用。[Fluentd收集Docker的登陆信息](http://docs.fluentd.org/v0.12/articles/docker-logging)案例。

首先创建一个config file, 用于配置Fluentd的行为，可命名为”in_docker.conf“。

    <source>
      type forward
      port 24224
      bind 0.0.0.0
    </source>
    
    <match *.*>
      type stdout
    </match>

然后保存文件。使用以下命令运行Fluentd。

    $ fluentd -c in_docker.conf
    
若运行成功则可见输出信息如下所示：

    $ fluentd -c in_docker.conf
    2015-09-01 15:07:12 -0600 [info]: reading config file path="in_docker.conf"
    2015-09-01 15:07:12 -0600 [info]: starting fluentd-0.12.15
    2015-09-01 15:07:12 -0600 [info]: gem 'fluent-plugin-mongo' version '0.7.10'
    2015-09-01 15:07:12 -0600 [info]: gem 'fluentd' version '0.12.15'
    2015-09-01 15:07:12 -0600 [info]: adding match pattern="*.*" type="stdout"
    2015-09-01 15:07:12 -0600 [info]: adding source type="forward"
    2015-09-01 15:07:12 -0600 [info]: using configuration file: <ROOT>
      <source>
        @type forward
        port 24224
        bind 0.0.0.0
      </source>
      <match docker.*>
        @type stdout
      </match>
    </ROOT>
    2015-09-01 15:07:12 -0600 [info]: listening fluent socket on 0.0.0.0:24224

然后启动docker containner。如果之前没有安装过docker engine，请读者自行安装。由于docker 本身支持Fluentd收集信息，所以可以通过启动命令来启动Fluentd的client／客户端。

    $ docker run --log-driver=fluentd ubuntu echo "Hello Fluentd!"
    Hello Fluentd!
    
以上命令中的ubuntu为一个镜像，如果本地没有，docker engine会自动下载，并在此镜像上创建容器。启动容器后，查看默认的输出信息文件:/var/log/td-agent/td-agent.log,可在最后一行查看到输出的信息。

### 总结

Fluentd是一个优秀的log信息收集的开源免费软件，目前以支持超过125种系统的log信息获取。Fluentd结合其他数据处理平台的使用，可以搭建大数据收集和处理平台，搭建商业化的解决方案。
