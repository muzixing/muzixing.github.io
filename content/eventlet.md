title:RYU学习:eventlet
date:2014/12/10
tags:ryu, eventlet
category:Tech

##前言

从OpenDaylight转到RYU以来一直都没有机会好好学习RYU的源码,只学会了编写简单的Application。但是如果要熟悉一个控制器，就要熟悉它的运行原理，熟悉它数据结构，熟悉它的设计模式等等。最近终于有时间好好看RYU的代码，但在看代码的过程中却发现RYU并不简单，其编码风格也非常优雅，非常值得学习。本篇博文主要讲述RYU中使用到的eventlet。

##从RYU开始

运行ryu的时候，命令是：ryu-manager app.py。第一个要找到就是ryu-manager到底会触发什么程序。在/cmd中没有找到之后，在/bin中找到了两个可执行文件：ryu和ryu-manager。打开ryu-manager，显示如下：

    from ryu.cmd.manager import main
    main()

找到/ryu/cmd/manager.py，发现这个文件中的main()函数是整个ryu的入口函数。

    def main(args=None, prog=None):
        try:
            CONF(args=args, prog=prog,
                 project='ryu', version='ryu-manager %s' % version,
                 default_config_files=['/usr/local/etc/ryu/ryu.conf'])
        except cfg.ConfigFilesNotFoundError:
            CONF(args=args, prog=prog,
                 project='ryu', version='ryu-manager %s' % version)
    
        log.init_log()

        if CONF.pid_file:
            import os
            with open(CONF.pid_file, 'w') as pid_file:
                pid_file.write(str(os.getpid()))
        
        app_lists = CONF.app_lists + CONF.app
        # keep old behaivor, run ofp if no application is specified.
        if not app_lists:
            app_lists = ['ryu.controller.ofp_handler']

        app_mgr = AppManager.get_instance()
        app_mgr.load_apps(app_lists)
        contexts = app_mgr.create_contexts()
        services = []
        services.extend(app_mgr.instantiate_apps(**contexts))
    
        webapp = wsgi.start_service(app_mgr)
        if webapp:
            thr = hub.spawn(webapp)
            services.append(thr)

        try:
            hub.joinall(services)
        finally:
            app_mgr.close()

这个main()函数的内容主要是完成了RYU的初始化配置和启动。Configure使用了oslo，这个在后续的博文中应该会提到。初始化的构成主要包括将app\_list里面的内容加入App\_Manager的列表中，然后开启协程去协调这些APP完成工作。hub是from ryu.lib import hub的。继续查看ryu/lib/hub.py。最终找到许多关于eventlet的内容。在hub.py中定义了Event,StreamServer和WSGIServer等类，还有一些重要的重要函数如spawn()等。为了更好地学习RYU，学习coroutine和eventlet就非常有必要了。

##[Coroutine](http://en.wikipedia.org/wiki/Coroutine#Implementations_for_Python)

协程[coroutine]是一个程序组件。相比subroutine, coroutine更一般。coroutine相对与thread而言，又不一样。thread是资源抢占式的存在，而coroutine是通过yield来转移执行权，协程之间是平等的，没有等级关系。multi-thread一旦开始运行，就无法确定某一时刻到底是哪一个thread在占用cpu，临界资源也要加互斥锁。而coroutine则是需要程序员自己决定程序如何运行，同时也需要自己负责程序的风险。协程和线程一样，只共享堆，不共享栈。

##[Eventlet](http://eventlet.net/)

eventlet是一个可以提供高性能并发处理能力的python库。我们可以在/usr/lib/python2.7/dist-packages/eventlet中找到对应的文件。

###Installation

    
    pip install eventlet


###Examples

为了更好的理解eventlet的内容，我花了半天认真地抄了一遍[官网](http://eventlet.net/doc/examples.html)的例子。具体实例举例如下。

**GreenPile**


    """Spawn multiple workers and collect their results.

    Demonstrates how to use the eventlet.green.socket module.
    """
    
    import eventlet
    from eventlet.green import socket


    def geturl(url):
        con = socket.socket()
        ip = socket.gethostbyname(url)
        con.connect((ip, 80))
        print('%s connected' % url)
        con.sendall('GET /\r\n\r\n')
        return con.recv(1024)


    urls = ['www.muzixing.com', 'www.baidu.com', 'www.python.org']
    pile = eventlet.GreenPile()
    for x in urls:
        pile.spawn(geturl, x)
    
    for url, result in zip(urls, pile):
        print('%s: %s' % (url, repr(result)[:100]))

以上的代码对指定url发送了GET请求。重点在与eventlet.GreenPile()的使用。GreenPile类源码如下所示：

    class GreenPile(object):
        def __init__(self, size_or_pool=1000):
            if isinstance(size_or_pool, GreenPool):
                self.pool = size_or_pool
            else:
                self.pool = GreenPool(size_or_pool)
            self.waiters = queue.LightQueue()
            self.used = False
            self.counter = 0

        def spawn(self, func, *args, **kw):
            """Runs *func* in its own green thread, with the result available by
            iterating over the GreenPile object."""
            self.used =  True
            self.counter += 1
            try:
                gt = self.pool.spawn(func, *args, **kw)
                self.waiters.put(gt)
            except:
                self.counter -= 1
                raise

        def __iter__(self):
            return self

        def next(self):
            """Wait for the next result, suspending the current greenthread until it
            is available.  Raises StopIteration when there are no more results."""
            if self.counter == 0 and self.used:
                raise StopIteration()
            try:
                return self.waiters.get().wait()
            finally:
                self.counter -= 1

从__init__函数可以看出，GreenPile内部有一个GreenPool对象和一个Queue对象：waiters。GreenPool的作用相当与线程池的作用，这点后续会继续介绍。上述例子用到的spawn函数完成了协程（被称之为green thread）的启动。可以看出spawn函数的参数是（函数，参数），在上述例子中为： pile.spawn(geturl, x)。从spawn函数中，也可以看出spawn()方法的返回值被保存在waiters队列中。next()方法的实现使其具有迭代性质。

**GreenPool**

下面的例子使用到了GreenPool类，完成了一个非常暴力的迭代爬虫，理论上，如果你让他去爬取某一个网站，然后不去管它，它会从这个网站出发，找到所有的链接，然后跳到各自的链接，然后继续迭代，直到最后把整个互联网的网站都爬一遍。而且，它不尊重你网站的robot.txt，这意味这它什么都会爬取。


    from __future__ import with_statement
    from eventlet.green import urllib2
    import eventlet
    import re
    
    
    # http://daringfireball.net/2009/11/liberal_regex_for_matching_urls
    url_regex = re.compile(r'\b(([\w-]+://?|www[.])[^\s()<>]+(?:\([\w\d]+\)|([^[:punct:]\s]|/)))')
    
    
    def fetch(url, seen, pool):
        '''Fetch A url, stick any found urls into the seen set,
        and dispatch any new  ones to te pool.'''
        print "fetching", url
        data = ''
        with eventlet.Timeout(5, False):
            data = urllib2.urlopen(url).read()
        for url_match in url_regex.finditer(data):
            new_url = url_match.group(0)
            # You can only send requests to muzixing.com so as not to destroy internet
            if new_url not in seen:  # and ’muzixing.com' in new_url:
                seen.add(new_url)
                # While this seems stack-recursive, it is actually not.
                # Spawned greenthreads start their own stacks
                pool.spawn_n(fetch, new_url, seen, pool)
    
    
    def crawl(start_url):
        '''Recrusively crawl starting from *start_url*.Return a set of
        urls that were found.
        '''
        pool = eventlet.GreenPool()
        seen = set()
        fetch(start_url, seen, pool)
        pool.waitall()
        return seen
    
    seen = crawl("http://www.muzixing.com")
    print "I saw there urls:", seen
    # print '\n'.join(seen)


首先爬虫从[http://www.muzixing.com](http://www.muzixing.com)网站开始搜索url。然后继续迭代寻找url，不断扩大查找范围。实验结果如下所示：

![](http://ww4.sinaimg.cn/mw690/7f593341jw1en5uqubim7j20m10n1dn9.jpg)

图1：迭代爬虫显示信息

从上图可以看到爬虫抓取了[www.muzixing.com](http://www.muzixing.com)的网页中存在的url如[http://ikimi.net](http://ikimi.net)，然后我们可以看到爬虫又跳到了[http://ikimi.net](http://ikimi.net)上爬取页面的其他url,如[http://www.ikimi.net/wp-includes](http://www.ikimi.net/wp-includes)。如果将起始页面换成[bbs.byr.cn](bbs.byr.cn)会发现爬虫会以更快的速度在整个互联网蔓延开来！

上述例子中可以学习到GreenPool类的使用。GreenPool可以类比于线程池，这有利于理解。在GreenPool中的元素都是GreenThread。其中最重要的函数是spawn/spawn_n函数。

    def spawn(self, function, *args, **kwargs):
    """Run the *function* with its arguments in its own green thread.
            Returns the :class:`GreenThread <eventlet.greenthread.GreenThread>`
            object that is running the function, which can be used to retrieve the
            results.
    """

该函数启动了一个GreenThread，参数是需要执行的function和function对应的参数。返回值是执行该函数的GreenThread类。

    def spawn_n(self, function, *args, **kwargs):
            """Create a greenthread to run the *function*, the same as
            :meth:`spawn`.  The difference is that :meth:`spawn_n` returns
            None; the results of *function* are not retrievable.
            """


spawn_n函数功能上差不多，只是返回的是None。其他的函数举例简单说明如下：

* waitall():等待所有greenthread执行完毕。

* running(): 返回目前正在执行的greenthread。

* imap():从迭代器中取出数据項作为func的参数去执行，并返回结果。
* starmap(): 和imap类似，但是取参数的方式有所差异。从[openstack nova 基础知识——eventlet](http://blog.csdn.net/hackerain/article/details/7836993)中摘取举例如下：
        
        imap(pow, (2,3,10), (5,2,3)) --> 32 9 1000
        starmap(pow, [(2,5), (3,2), (10,3)]) --> 32 9 1000

* free(): 返回当前可获取的greenthread的数目。

以上代码上的with语句是python中的一个非常方便的关键字。使用with关键字可以让代码更严谨且简洁。其封装了__enter__()函数和__exit__()函数，用于执行信息和退出处理。其等价于以下代码：
    
    try:
        __enter__()
    finally:
        __exit__()

上述是关于GreenPool类的使用案例，使用该类可以高效完成并发操作。

**Convenience**

接下来再介绍一个更好玩的程序，多人群聊程序，可以让我们在学习eventlet的时候充满成就感。代码如下：

    import eventlet
    from eventlet.green import socket
    
    PORT = 3001
    participants = set()
    
    
    def read_chat_forever(writer, reader, address):
        line = reader.readline()
        while line:
            print('Chat:', line.strip())
            for p in participants:
                try:
                    if p is not writer:  # Don't echo
                        msg = address[0] + ':'
                        msg += line
                        p.write(msg)
                        p.flush()
                except socket.error as e:
                    # ignore broken pipes, they just mean the participant
                    # closed its connection already
                    if e[0] != 32:
                        raise
            line = reader.readline()
        participants.remove(writer)
        print("participant left chat")
    
    
    try:
        print("ChatServer starting up on port %s" % PORT)
        server = eventlet.listen(('0.0.0.0', PORT))
        while True:
            new_connection, address = server.accept()
            print("Participant joined chat.")
            new_writer = new_connection.makefile('w')
            participants.add(new_writer)
            eventlet.spawn_n(
                read_chat_forever,
                new_writer,
                new_connection.makefile('r'),
                address)
    except (KeyboardInterrupt, SystemExit):
        print("ChatServer exiting")

try语句块中完成了服务端socket的建立和监听。然后在while循环中完成了消息的处理。

首先关注第一个函数：eventlet.listen((addr,port))。在eventlet文件夹中，打开__init__文件可以查看到一些为了方便而初始化的定义，举例如下：

    version_info = (0, 9, 16)
    __version__ = ".".join(map(str, version_info))
    
    try:
        from eventlet import greenthread
        from eventlet import greenpool
        from eventlet import queue
        from eventlet import timeout
        from eventlet import patcher
        from eventlet import convenience
        import greenlet
    

        
        GreenPool = greenpool.GreenPool
        GreenPile = greenpool.GreenPile
        
        Queue = queue.Queue
        
        import_patched = patcher.import_patched
        monkey_patch = patcher.monkey_patch
    
        connect = convenience.connect
        listen = convenience.listen
        serve = convenience.serve
        StopServe = convenience.StopServe
        wrap_ssl = convenience.wrap_ssl

所以我们直接可以使用eventlet.listen调用convenience.listen函数。listen函数完成了一个server socket的绑定和监听。


    def listen(addr, family=socket.AF_INET, backlog=50):
        sock = socket.socket(family, socket.SOCK_STREAM)
        if sys.platform[:3] != "win":
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(addr)
        sock.listen(backlog)
        return sock

socket.accept()函数将返回一个（connection，address）元组。socket.makefile([mode[, bufsize]])返回一个文件对象用于读写缓存。

eventlet.spawn_n函数将read_chat_forever函数及其三个参数作为参数，创建GreenThread去执行任务。eventlet主要完成的工作就是帮助你如何去协调你的任务，而不是去实现你的任务，这一点在这里得到体现。其实对比于线程池就容易理解读多了。

试验结果截图如下：

![](http://ww1.sinaimg.cn/mw690/7f593341jw1en5tcjidm2j20gt0crabx.jpg)

图2：多人群聊server运行界面

![](http://ww4.sinaimg.cn/mw690/7f593341jw1en5tcj7dvej20ln0crwh8.jpg)

图3：多人群聊client运行界面

从client运行界面可以看出不同的用户发送的信息会以IP：message的形式展示出来，代码很简单，但是非常有趣。

以上例子均可以在官网找到，读者可以到官网去查看更多案例。

**Patcher**

Patch是eventlet中的一个重要模块。用于替换系统自带的模块。其中有import_patched和monkey_patch两个函数，后者可以提供运行时替换。具体例子可以查看[openstack nova 基础知识——eventlet](http://blog.csdn.net/hackerain/article/details/7836993)

##回到RYU

前两行代码调用了hub.patch()函数，查看hub.py中发现patch = eventlet.monkey\_patch，实现了运行时替换模块。

    from ryu.lib import hub
    hub.patch()

接下来的CONF文件由于oslo的内容比较多，所以会在后续博文中详细介绍。首先关注main()函数的主要内容。

    def main(args=None, prog=None):
        try:
            CONF(args=args, prog=prog,
                 project='ryu', version='ryu-manager %s' % version,
                 default_config_files=['/usr/local/etc/ryu/ryu.conf'])
        except cfg.ConfigFilesNotFoundError:
            CONF(args=args, prog=prog,
                 project='ryu', version='ryu-manager %s' % version)
    
        log.init_log()

        if CONF.pid_file:
            import os
            with open(CONF.pid_file, 'w') as pid_file:
                pid_file.write(str(os.getpid()))
        
        app_lists = CONF.app_lists + CONF.app
        # keep old behaivor, run ofp if no application is specified.
        if not app_lists:
            app_lists = ['ryu.controller.ofp_handler']

        app_mgr = AppManager.get_instance()
        app_mgr.load_apps(app_lists)
        contexts = app_mgr.create_contexts()
        services = []
        services.extend(app_mgr.instantiate_apps(**contexts))
    
        webapp = wsgi.start_service(app_mgr)
        if webapp:
            thr = hub.spawn(webapp)
            services.append(thr)

        try:
            hub.joinall(services)
        finally:
            app_mgr.close()

从CONF文件中取出app信息，存在app_lists内，若没有启动其他app,则默认启动ofp_handler应用，用于处理基础的事件，如协议协商等。然后声明一个AppManager的类，用于初始化和管理APP。load_apps函数完成了APP的加载。最后try语句块中的joinall()使得进程需要等待所有的services完成之后才能退出。至此RYU初始运行学习完成，后续的博文将分别介绍：oslo, 事件处理机制，RYUAPP类以及RYU数据结构和API使用等内容。


##后语

Evenlet是个不错的python库，简单却很高效。相比于thread,coroutine的行为是可控的，切换成本也要更小。在单核情况下，coroutine要比thread开销小，但是multithread可以在多CPU的情况下发挥更大的能力。RYU是使用Python编写的控制器，比同样使用Python编写的POX，无论从代码的规范，优雅度，还是从性能上，都有很大的优势，此外，这个纯SDN控制器对OpenFlow协议的支持可以说是最稳定，最全面的。虽然我还会继续研究ONOS，学习大型分布式框架。但是RYU会成为我开发Application的利器。相比之下，Java编写的ODL，过于复杂和不稳定。新生儿ONOS相比之下用户体验更好，且没有使用YANG，大大降低了学习难度。周一的时候，还在Docker中安装了ONOS，并使用Cbench测试对比了ONOS和RYU的吞吐量。同样环境下，单节点的ONOS性能几乎是RYU的两倍，这让我有些忧伤。也许匕首只适合敏捷作战，而大刀才是开疆扩土的利器吧。




























