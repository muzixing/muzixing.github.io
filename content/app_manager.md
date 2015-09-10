title:RYU核心源码解读：OFPHandler,Controller,RyuApp和AppManager
date:2014/12/27
tags:ryu,sdn
category:Tech


每接触一个控制器我都会习惯性的把控制器的源码读一读，走一走处理流程，RYU也不例外。本篇博文将从main函数入手，讲述RYU的ryuapp基类细节、app\_manager类如何load apps，注册并运行application，Event的产生以及分发，还有最重要的应用ofp\_handler。文章将以RYU真实运行流程作为主线，详细讲述RYU如何运作。如果文中出现理解错的地方，敬请指出，万分感谢！转载请声明原出处。

##main()

RYU的main函数在ryu/cmd/manager.py文件中。main函数中CONF部分已经在在前一篇[《RYU学习：oslo》](http://www.muzixing.com/pages/2014/12/19/ryuxue-xi-oslo.html)已经有所介绍，所以这次关注的重点的是后续部分，如app\_manager如何工作。

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

首先从CONF文件中读取出app list。如果ryu-manager 命令任何参数，则默认应用为ofp\_handler应用。紧接着实例化一个AppManager对象，调用load\_apps函数将应用加载。调用create\_contexts函数创建对应的contexts, 然后调用instantiate\_apps函数将app\_list和context中的app均实例化。启动wsgi架构，提供web应用。最后将所有的应用作为任务，作为coroutine的task去执行，joinall使得程序必须等待所有的task都执行完成才可以退出程序。最后调用close函数，关闭程序，释放资源。以下的部分将以主函数中出现的调用顺序为依据，展开讲解。

##OFPHandler

上文说到，如果没有捕获Application输入，那么默认启动的应用是OFPHandler应用。该应用主要用于处理OpenFlow消息。在start函数初始化运行了一个OpenFlowController实例。OpenFlowController类将在后续介绍。

	def start(self):
        	super(OFPHandler, self).start()
	        return hub.spawn(OpenFlowController())

OFPHandler应用完成了基本的消息处理，如hello_handler：用于处理hello报文，协议版本的协商。其处理并不复杂，但是值得注意的一点是装饰器：Decorator的使用。

	@set_ev_handler(ofp_event.EventOFPHello, HANDSHAKE_DISPATCHER)
	   def hello_handler(self, ev):
	       self.logger.debug('hello ev %s', ev)
	       msg = ev.msg
	       datapath = msg.datapath

###Decorator

如果你已经了解Decorator，可以直接跳过本部分。

装饰器是什么？[Python Decorator](https://wiki.python.org/moin/PythonDecorators)

coolshell上的介绍[Python修饰器的函数式编程](http://coolshell.cn/articles/11265.html)

Python Decorator可以看作是一种声明，一种修饰。以下举例参考自Coolshell。举例如下：

	@decorator
	def foo():
		pass

实际上等同于foo = decorator(foo), 而且它还被执行了。举个例子：

	def keyword(fn):	
	    print "you   %s  me!" % fn.__name__[::-1].upper()
	 
	@keyword
	def evol():
	    pass

运行之后，就会输出:you love me。

多个decorator:

	@decorator_a
	@decorator_b
	def foo():
		pass

这相当于：

	foo = decorator_a(decorator_b(foo))

而带参数的decorator:

	@decorator(arg1, arg2)
	def foo():
		pass

相当于
	
	foo = decorator(arg1,arg2)(foo)

decorator(arg1,arg2)将生成一个decorator。

**class式的 Decorator**

	class myDecorator(object):

	    def __init__(self, fn):
	        print "inside myDecorator.__init__()"
        	self.fn = fn

	    def __call__(self):
	        self.fn()
	        print "inside myDecorator.__call__()"


	@myDecorator
	def aFunction():
	    print "inside aFunction()"

	print "Finished decorating aFunction()"

	aFunction()


@decorator使用时，\_\_init\_\_被调用，当function被调用是，执行\_\_call\_\_函数，而不执行function,所以在\_\_call\_\_函数中需要写出self.fn = fn


更多内容可以直接访问[Python Decorator Library](https://wiki.python.org/moin/PythonDecoratorLibrary)

##OpenFlowController

前一部分提到OFPHandle的start函数会将OpenFlowController启动。本小节介绍OpenFlowController类。该类的定义在ryu/cmd/controller.py文件中。OpenFlowController.\_\_call\_\_()函数启动了server\_loop()函数，该函数实例化了hub.py中的StreamServer类，并将handler函数初始化为datapath\_connection\_factory函数，并调用serve\_forever()，不断进行socket的监听。StreamServer定义如下：

	class StreamServer(object):
        	def __init__(self, listen_info, handle=None, backlog=None,
                	     spawn='default', **ssl_args):
	            assert backlog is None
        	    assert spawn == 'default'

	            if ':' in listen_info[0]:
	                self.server = eventlet.listen(listen_info,
	                                              family=socket.AF_INET6)
	            else:
	                self.server = eventlet.listen(listen_info)
	            if ssl_args:
	                def wrap_and_handle(sock, addr):
	                    ssl_args.setdefault('server_side', True)
	                    handle(ssl.wrap_socket(sock, **ssl_args), addr)
	
	                self.handle = wrap_and_handle
	            else:
	                self.handle = handle
	
	        def serve_forever(self):
	            while True:
	                sock, addr = self.server.accept()
	                spawn(self.handle, sock, addr)


###Datapath

Datapath类在RYU中极为重要，每当一个datapath实体与控制器建立连接时，就会实例化一个Datapath的对象。
该类中不仅定义了许多的成员变量用于描述一个datapath，还管理控制器与该datapath通信的数据收发。其中\_recv\_loop函数完成数据的接收与解析，事件的产生与分发。

	@_deactivate
	    def _recv_loop(self):
	        buf = bytearray()
	        required_len = ofproto_common.OFP_HEADER_SIZE
	
	        count = 0
	        while self.is_active:
	            ret = self.socket.recv(required_len)
	            if len(ret) == 0:
	                self.is_active = False
	                break
	            buf += ret
	            while len(buf) >= required_len:
	                (version, msg_type, msg_len, xid) = ofproto_parser.header(buf)
	                required_len = msg_len
	                if len(buf) < required_len:
	                    break
	
	                msg = ofproto_parser.msg(self,
	                                         version, msg_type, msg_len, xid, buf)  #  解析报文
	                # LOG.debug('queue msg %s cls %s', msg, msg.__class__)
	                if msg:
	                    ev = ofp_event.ofp_msg_to_ev(msg)  # 产生事件
	                    self.ofp_brick.send_event_to_observers(ev, self.state)  # 事件分发
	
	                    dispatchers = lambda x: x.callers[ev.__class__].dispatchers
	                    handlers = [handler for handler in
	                                self.ofp_brick.get_handlers(ev) if
	                                self.state in dispatchers(handler)]
	                    for handler in handlers:
	                        handler(ev)
	
	                buf = buf[required_len:]
	                required_len = ofproto_common.OFP_HEADER_SIZE
	
	                # We need to schedule other greenlets. Otherwise, ryu
	                # can't accept new switches or handle the existing
	                # switches. The limit is arbitrary. We need the better
	                # approach in the future.
	                count += 1
	                if count > 2048:
	                    count = 0
	                    hub.sleep(0)

@\_deactivate修饰符作用在于在Datapath断开连接之后，将其状态is\_active置为False。self.ofp\_brick.send\_event\_to\_observers(ev, self.state) 语句完成了事件的分发。self.brick的初始化语句可以在self.\_\_init\_\_函数中找到：

	        self.ofp_brick = ryu.base.app_manager.lookup_service_brick('ofp_event')

由上可知，self.ofp\_brick实际上是由service\_brick（中文可以称为：服务链表？）中的“ofp\_event”服务赋值的。在每一个app中，使用@set\_ev\_cls(ev\_cls,dispatchers)时，就会将实例化ofp_event模块，执行文件中最后一句：

	handler.register_service('ryu.controller.ofp_handler')

register\_service函数实体如下：

	def register_service(service):
	    """
	    Register the ryu application specified by 'service' as
	    a provider of events defined in the calling module.
	
	    If an application being loaded consumes events (in the sense of
	    set_ev_cls) provided by the 'service' application, the latter
	    application will be automatically loaded.
	
	    This mechanism is used to e.g. automatically start ofp_handler if
	    there are applications consuming OFP events.
	    """
	
	    frm = inspect.stack()[1]
	    m = inspect.getmodule(frm[0])
	    m._SERVICE_NAME = service


其中inspect.stack()[1]返回了调用此函数的caller, inspect.getmodule(frm[0])返回了该caller的模块，当前例子下，module=ofp\_event。

我们可以通过ryu-manager --verbose来查看到输出信息，从而印证这一点。

	muzi@muzi-OptiPlex-390:~/ryu/ryu/app$ ryu-manager --verbose
	loading app ryu.controller.ofp_handler
	instantiating app ryu.controller.ofp_handler of OFPHandler
	BRICK ofp_event
	  CONSUMES EventOFPErrorMsg
	  CONSUMES EventOFPEchoRequest
	  CONSUMES EventOFPPortDescStatsReply
	  CONSUMES EventOFPHello
	  CONSUMES EventOFPSwitchFeatures

所以当运行ofp\_handler应用时，就会注册ofp\_event service，为后续的应用提供服务。分发事件之后，还要处理自身订阅的事件，所以首先找到符合当前state的caller,然后调用handler。\_caller类可以在handler.py文件中找到，包含dispatchers和ev_source两个成员变量。前者用于描述caller需要的state,后者是event产生者的模块名称。

对应的发送循环由\_send\_loop完成。self.send\_q是一个深度为16的发送queue。


   	 @_deactivate
	    def _send_loop(self):
	        try:
	            while self.is_active:
	                buf = self.send_q.get()
	                self.socket.sendall(buf)
	        finally:
	            q = self.send_q
	            # first, clear self.send_q to prevent new references.
	            self.send_q = None
	            # there might be threads currently blocking in send_q.put().
	            # unblock them by draining the queue.
	            try:
	                while q.get(block=False):
	                    pass
	            except hub.QueueEmpty:
	                pass


serve函数完成了发送循环的启动和接收循环的启动。启动一个coroutine去执行self.\_send\_loop()， 然后马上主动发送hello报文到datapath(可以理解为交换网桥：Bridge)，最后执行self.\_recv\_loop()。

	def serve(self):
        	send_thr = hub.spawn(self._send_loop)

	        # send hello message immediately
	        hello = self.ofproto_parser.OFPHello(self)
	        self.send_msg(hello)
	
	        try:
	            self._recv_loop()
	        finally:
	            hub.kill(send_thr)
	            hub.joinall([send_thr])

而serve函数又在datapath\_connection\_factory函数中被调用。当然向外提供完整功能的API就是这个。所以在OpenFlowController类中可以看到在初始化server实例的时候，handler赋值为datapath\_connection\_factory。其中使用到的contextlib module具体内容不作介绍，读者可[自行学习](https://docs.python.org/2/library/contextlib.html)

	def datapath_connection_factory(socket, address):
	    LOG.debug('connected socket:%s address:%s', socket, address)
	    with contextlib.closing(Datapath(socket, address)) as datapath:
	        try:
	            datapath.serve()
	        except:
	            # Something went wrong.
	            # Especially malicious switch can send malformed packet,
	            # the parser raise exception.
	            # Can we do anything more graceful?
	            if datapath.id is None:
	                dpid_str = "%s" % datapath.id
	            else:
	                dpid_str = dpid_to_str(datapath.id)
	            LOG.error("Error in the datapath %s from %s", dpid_str, address)
	            raise

到此为止，OFPHandler应用的功能实现介绍完毕。RYU启动时，需要启动OFPHandler，才能完成数据的收发和解析。更多的上层应用逻辑都是在此基础之上进行的。若要开发APP则需要继承RyuApp类，并完成observer监听事件，以及注册handler去完成事件处理。


##RyuApp

RyuApp类是RYU封装好的APP基类，用户只需要继承该类，就可以方便地开发应用。而注册对应的observer和handler都使用@derocator的形式，使得开发非常的简单高效，这也是Python的优点之一吧。RyuApp类的定义在ryu/base/app\_manager.py文件中。该文件实现了两个类RyuApp和AppManager。前者用于定义APP基类，为应用开发提供基本的模板，后者用于Application的管理，加载应用，运行应用，消息路由等功能。

app\_manager.py文件中import了[instpect](https://docs.python.org/2/library/inspect.html)和[itertools](https://docs.python.org/2/library/itertools.html) module，从而使得开发更方便简洁。inspect模块提供了一些有用的方法，用于类型检测，获取内容，检测是否可迭代等功能。itertools则是一个关于迭代器的模块，可以提供丰富的迭代器类型，在数据处理上尤其有用。


###\_CONTEXT

这是一个极其难理解的概念。博主的理解是，\_CONTEXT内存储着name:class的key value pairs。为什么需要存储这个内容？实际上这个\_CONTEXT携带的信息是所有本APP需要依赖的APP。需要在启动本应用之前去启动，以满足依赖的，比如一个simple\_switch.py的应用，如果没有OFPHandler应用作为数据收发和解析的基础的话，是无法运行的。具体文档如下：

	_CONTEXTS = {}
	    """
	    A dictionary to specify contexts which this Ryu application wants to use.
	    Its key is a name of context and its value is an ordinary class
	    which implements the context.  The class is instantiated by app_manager
	    and the instance is shared among RyuApp subclasses which has _CONTEXTS
	    member with the same key.  A RyuApp subclass can obtain a reference to
	    the instance via its __init__'s kwargs as the following.
	
	    Example::
	
	        _CONTEXTS = {
	            'network': network.Network
	        }
	
	        def __init__(self, *args, *kwargs):
	            self.network = kwargs['network']
	    """
###\_EVENTS

用于记录本应用会产生的event。但是当且仅当定义该event的语句在其他模块时才会被使用到。但是目前我还没有遇见过在哪里使用，如果你知道其正确的用法，恳请告知，相互学习。

###self.\_\_init\_\_

\_\_init\_\_函数中初始化了许多重要的成员变量，如self.event\_handler用于记录向外提供的事件处理句柄，而self.observer则刚好相反，用于通知app\_manager本应用监听何种类型的事件。self.event是事件队列。

	def __init__(self, *_args, **_kwargs):
        	super(RyuApp, self).__init__()
	        self.name = self.__class__.__name__
	        self.event_handlers = {}        # ev_cls -> handlers:list
	        self.observers = {}     # ev_cls -> observer-name -> states:set
	        self.threads = []
	        self.events = hub.Queue(128)
	        if hasattr(self.__class__, 'LOGGER_NAME'):
	            self.logger = logging.getLogger(self.__class__.LOGGER_NAME)
	        else:
	            self.logger = logging.getLogger(self.name)
	        self.CONF = cfg.CONF
	
	        # prevent accidental creation of instances of this class outside RyuApp
	        class _EventThreadStop(event.EventBase):
	            pass
	        self._event_stop = _EventThreadStop()
	        self.is_active = True

###self.start

start函数将启动coroutine去处理\_event\_loop，并将其加入threads字典中，为什么名字叫threads呢？我也不知道。也许我理解错了？

###self.\_event_loop

\_event\_loop函数用于启动事件处理循环，通过调用self.get\_handlers(ev, state)函数来找到事件对应的handler，然后处理事件。


	    def get_handlers(self, ev, state=None):
	        """Returns a list of handlers for the specific event.
	
	        :param ev: The event to handle.
	        :param state: The current state. ("dispatcher")
	                      If None is given, returns all handlers for the event.
	                      Otherwise, returns only handlers that are interested
	                      in the specified state.
	                      The default is None.
	        """
	        ev_cls = ev.__class__
	        handlers = self.event_handlers.get(ev_cls, [])
	        if state is None:
	            return handlers

	    def _event_loop(self):
	        while self.is_active or not self.events.empty():
	            ev, state = self.events.get()
	            if ev == self._event_stop:
	                continue
	            handlers = self.get_handlers(ev, state)
	            for handler in handlers:
	                handler(ev)

###event dispatch

应用中可以通过@set\_ev\_cls修饰符去监听某些事件。当产生event时，通过event去get observer，得到对应的观察者，然后再使用self.send\_event函数去发送事件。在这里，实际上就是直接往self.event队列中put event。

    def _send_event(self, ev, state):
        self.events.put((ev, state))

    def send_event(self, name, ev, state=None):
        """
        Send the specified event to the RyuApp instance specified by name.
        """

        if name in SERVICE_BRICKS:
            if isinstance(ev, EventRequestBase):
                ev.src = self.name
            LOG.debug("EVENT %s->%s %s" %
                      (self.name, name, ev.__class__.__name__))
            SERVICE_BRICKS[name]._send_event(ev, state)
        else:
            LOG.debug("EVENT LOST %s->%s %s" %
                      (self.name, name, ev.__class__.__name__))

    def send_event_to_observers(self, ev, state=None):
        """
        Send the specified event to all observers of this RyuApp.
        """

        for observer in self.get_observers(ev, state):
            self.send_event(observer, ev, state)


其他函数如注册handler函数：register\_handler，注册监听函数：register\_observer等都是非常简单直白的代码，不再赘述。

##AppManager

AppManager类是RYU应用的调度中心。用于管理应用的添加删除，消息路由等等功能。

首先从启动函数开始介绍，我们可以看到run\_apps函数中的代码和前文提到的main函数语句基本一样。首先获取一个对象，然后加载对应的apps，然后获取contexts，context中其实包含的是本应用所需要的依赖应用。所以在调用instantiate\_apps函数时，将app\_lists内的application和contexts中的services都实例化，然后启动协程去运行这些服务。

    @staticmethod
    def run_apps(app_lists):
        """Run a set of Ryu applications

        A convenient method to load and instantiate apps.
        This blocks until all relevant apps stop.
        """
        app_mgr = AppManager.get_instance()
        app_mgr.load_apps(app_lists)
        contexts = app_mgr.create_contexts()
        services = app_mgr.instantiate_apps(**contexts)
        webapp = wsgi.start_service(app_mgr)
        if webapp:
            services.append(hub.spawn(webapp))
        try:
            hub.joinall(services)
        finally:
            app_mgr.close()

###load\_apps

首先从创建一个apps\_lists的生成器（个人理解应该是生成器而非迭代器）。在while循环中，每次pop一个应用进行处理，然后将其本身和其context中的内容添加到services中，再去调用get\_dependent\_services函数获取其依赖应用，最后将所有的依赖services添加到app\_lists中，循环至最终app\_lists内元素全都pop出去，完成application的加载。

	def load_apps(self, app_lists):
	        app_lists = [app for app
	                     in itertools.chain.from_iterable(app.split(',')
	                                                      for app in app_lists)]
	        while len(app_lists) > 0:
	            app_cls_name = app_lists.pop(0)
	
	            context_modules = map(lambda x: x.__module__,
	                                  self.contexts_cls.values())
	            if app_cls_name in context_modules:
	                continue
	
	            LOG.info('loading app %s', app_cls_name)
	
	            cls = self.load_app(app_cls_name)
	            if cls is None:
	                continue
	
	            self.applications_cls[app_cls_name] = cls
	
	            services = []
	            for key, context_cls in cls.context_iteritems():
	                v = self.contexts_cls.setdefault(key, context_cls)
	                assert v == context_cls
	                context_modules.append(context_cls.__module__)
	
	                if issubclass(context_cls, RyuApp):
	                    services.extend(get_dependent_services(context_cls))
	
	            # we can't load an app that will be initiataed for
	            # contexts.
	            for i in get_dependent_services(cls):
	                if i not in context_modules:
	                    services.append(i)
	            if services:
	                app_lists.extend([s for s in set(services)
	                                  if s not in app_lists])
	
###create_contexts

context实例化函数将context中name:service class键值对的内容实例化成对应的对象，以便加入到services 列表中，从而得到加载。首先从列表中取出对应数据，然后判断是否时RyuApp的子类，是则实例化，否则直接赋值service class。load\_app函数在读取的时候还会再次判断是否是RyuApp子类。

    def create_contexts(self):
        for key, cls in self.contexts_cls.items():
            if issubclass(cls, RyuApp):
                # hack for dpset
                context = self._instantiate(None, cls)
            else:
                context = cls()
            LOG.info('creating context %s', key)
            assert key not in self.contexts
            self.contexts[key] = context
        return self.contexts

###instantiate_apps

此函数调用了self.\_instantiate函数，在\_instantiate函数中又调用了register\_app()函数，此函数将app添加到SERVICE\_BRICKS字典之中，然后继续调用了ryu.controller.handler 中的 register\_instance函数，最终完成了应用的注册。此后继续调用self.\_update\_bricks函数完成了服务链表的更新，最后启动了所有的应用。

    def instantiate_apps(self, *args, **kwargs):
        for app_name, cls in self.applications_cls.items():
            self._instantiate(app_name, cls, *args, **kwargs)

        self._update_bricks()
        self.report_bricks()

        threads = []
        for app in self.applications.values():
            t = app.start()
            if t is not None:
                threads.append(t)
        return threads


    def _instantiate(self, app_name, cls, *args, **kwargs):
        # for now, only single instance of a given module
        # Do we need to support multiple instances?
        # Yes, maybe for slicing.
        #LOG.info('instantiating app %s of %s', app_name, cls.__name__)

        if hasattr(cls, 'OFP_VERSIONS') and cls.OFP_VERSIONS is not None:
            ofproto_protocol.set_app_supported_versions(cls.OFP_VERSIONS)

        if app_name is not None:
            assert app_name not in self.applications
        app = cls(*args, **kwargs)
        register_app(app)
        assert app.name not in self.applications
        self.applications[app.name] = app
        return app


###\_update\_bricks

此函数完成了更新service\_bricks的功能。首先从获取到service实例，然后再获取到service中的方法，若方法有callers属性，即使用了@set\_ev\_cls的装饰符，拥有了calls属性。（caller类中的ev\_source描述了产生该event的source module， dispatcher描述了event需要在什么状态下才可以被分发。如：HANDSHAKE\_DISPATCHER，CONFIG\_DISPATCHER等。）最后调用register\_observer函数注册了observer。

    def _update_bricks(self):
        for i in SERVICE_BRICKS.values():
            for _k, m in inspect.getmembers(i, inspect.ismethod):
                if not hasattr(m, 'callers'):
                    continue
                for ev_cls, c in m.callers.iteritems():
                    if not c.ev_source:
                        continue

                    brick = _lookup_service_brick_by_mod_name(c.ev_source)
                    if brick:
                        brick.register_observer(ev_cls, i.name,
                                                c.dispatchers)

                    # allow RyuApp and Event class are in different module
                    for brick in SERVICE_BRICKS.itervalues():
                        if ev_cls in brick._EVENTS:
                            brick.register_observer(ev_cls, i.name,
                                                    c.dispatchers)


###ryu.controller.handler.register_instance

以上的部分介绍了App的注册，observer的注册，handler的查找和使用，但是，始终没有提到handler在何处注册。实际上，handler的注册在register\_instance部分完成了。为什么他的位置在handler文件，而不在app\_manager文件呢？个人认为可能是为了给其他非Ryu APP的模块使用吧。

	def register_instance(i):
	    for _k, m in inspect.getmembers(i, inspect.ismethod):
	        # LOG.debug('instance %s k %s m %s', i, _k, m)
	        if _has_caller(m):
	            for ev_cls, c in m.callers.iteritems():
	                i.register_handler(ev_cls, m)


##Conclusion

总体而言，RYU使用了协程，在很大程度上提高了单核性能。同时也使用了许多高效的语句和库，使得代码量非常精简易读。优势方面，RYU开发门槛低，性能好，稳定度强，而且代码迎合OpenStack编写，适合用于数据中心等云场景。劣势方面，RYU还没有实现分布式版本，在大规模网络中只能使用多个单节点分担负载。实现细节上还存在细微的问题，如虽然提供了存储依赖关系的数据结构和获取依赖关系的函数，但是并没有指定一个默认的依赖关系。不过这一点其实並不算大问题，甚至不是问题，因为开发者可以手动去指定。

认真读完RYU底层的实现代码，觉得学习一门语言需要学习的内容太多，而只有真正去使用时，才会真正的学会和理解。严谨的逻辑，优雅的编码风格，清晰的模块划分能让程序的可读性更高，代码可复用性更强。如果从一个产品的角度讲，RYU算是一个不错的产品，小而美。没有ONOS,OpenDaylight那样庞大，但是作为一个纯SDN控制器而言，用户体验算是非常好的一个了。

写完这篇之后，估计这个学期就不会再写了，非科研狗非产品狗非bababala狗的渣硕要开始预习期末考试了。希望未来的我会更好。

##References

**itertools**：python关于[迭代器](https://docs.python.org/2/library/itertools.html)的库。

**contextlib**：[contextlib](https://docs.python.org/2/library/contextlib.html)

**yield**：类似与return,但是返回的是一个生成器。[中文翻译教程](http://pyzh.readthedocs.org/en/latest/the-python-yield-keyword-explained.html)


**decorator**：[Python Decorator](https://wiki.python.org/moin/PythonDecorators)

coolshell上的介绍[Python修饰器的函数式编程](http://coolshell.cn/articles/11265.html)



**迭代器**：就是一个可以迭代的数据结构，可以使用for x in 语法去读取，每次返回一个列表。

**生成器**：具有可迭代性，但是每一次只能读取一个元素。



