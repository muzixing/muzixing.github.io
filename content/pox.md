date:2013-11-28
title:【原创】POX运行机制 　　by李呈
tags:SDN,Openflow
category:Tech

###Pox以及组件的启动

配图版请浏览：http://user.qzone.qq.com/350959853/blog/1376471361


SDNAP链接： http://www.sdnap.com/sdnap-post/2058.html 


#####1：启动pox.py。
	python pox.py

Pox.py 里面除了一堆的注释以外，真正有用的只有几句会运行的：

	from pox.boot import boot
    	if __name__ == '__main__':
  			boot()
  
boot()函数在pox.boot里，有什么内容呢？

######1：把pox和ext两个文件夹的路径加入系统path中。

######2：由\_do_ import添加各个模块

######3：\_do_launch去启动各个模块，启动pox

######4：定义Options和POXoptions两个类，用于定义选项

######5：定义了其他预启动项，如写日记等等。
 
 
核心的启动代码是以下的代码：

	def boot ():
	  """
	  Start up POX.
	  """

	  # Add pox directory to path
	  sys.path.append(os.path.abspath(os.path.join(sys.path[0], 'pox')))
	  sys.path.append(os.path.abspath(os.path.join(sys.path[0], 'ext')))
	
	  try:
	    argv = sys.argv[1:]
	
	    # Always load cli (first!)
	    #TODO: Can we just get rid of the normal options yet?
	    pre = []
	    while len(argv):
	      if argv[0].startswith("-"):
	        pre.append(argv.pop(0))
	      else:
	        break
	    argv = pre + "py --disable".split() + argv
	
	    if _do_launch(argv):
	      _post_startup()
	      core.goUp()
	    else:
	      return
	
	  except SystemExit:
	    return
	  except:
	    traceback.print_exc()
	    return
	
	  if _main_thread_function:
	    _main_thread_function()
	  else:
	    #core.acquire()
	    try:
	      while core.running:
	        time.sleep(10)
	    except:
	      pass
	    #core.scheduler._thread.join() # Sleazy
	
	 try:
    	pox.core.core.quit()
	 except:
		pass

 
**\_do\_launch()启动了pox及相关组件。之后通过\_post\_startup()启动openflow.of_01。core.goUp则启动了core里面的登记Debug信息和事件机制。
core.py里面最后一句：core=POXCore(),使得整个类有了实例化，在外部调用时，直接使用core。**


###组件加载

在启动pox的时候，相应会启动pox的许多组件，而不是单一的仅仅启动一个pox的主程序。启动了相关组件之后，才能去管理各个组件，并通过handler去管理消息队列中的不同的事件，实现事件的管理。组件的加载与初始化在boot()文件里的\_do\_launch()函数里，代码如下：

	def _do_launch (argv):
	  component_order = []
	  components = {}
	
	  curargs = {}
	  pox_options = curargs
	
	  for arg in argv:
	    if not arg.startswith("-"):
	      if arg not in components:
	        components[arg] = []
	      curargs = {}
	      components[arg].append(curargs)
	      component_order.append(arg)
	    else:
	      arg = arg.lstrip("-").split("=", 1)
	      arg[0] = arg[0].replace("-", "_")
	      if len(arg) == 1: arg.append(True)
	      curargs[arg[0]] = arg[1]
	
	  _options.process_options(pox_options)
	  _pre_startup()
	
	  inst = {}
	  for name in component_order:
	    cname = name
	    inst[name] = inst.get(name, -1) + 1
	    params = components[name][inst[name]]
	    name = name.split(":", 1)
	    launch = name[1] if len(name) == 2 else "launch"
	    name = name[0]
	
	    r = _do_import(name)
	    if r is False: return False
	    name = r
	    #print(">>",name)

 

首先创建component_order的列表，用于存放组件的名称。然后再逐个启动，初始化。

第**162**行，讲名字分为两部分。

**163**行则决定了启动的默认顺序。
 
    name = name.split(":", 1)
	launch = name[1] if len(name) == 2 else "launch"
	 
使用\_do_import()函数将相关组件模块引入。
 
第**171**行：

	if launch in sys.modules[name].__dict__:

检查launch是否属于sys.modules这个字典。而\_\_dict__是python里面的特性字典，，用于存放类的实例的所有特性。
 

第**172**行：
     
	 f = sys.modules[name].__dict__[launch]从模块中，实例化函数。

第**199**行 初始化函数：
 
      try:
        f(**params)

###举例：
L2\_learning作为pox里面最重要的一个二层组件之一，再适合不过了。

	def launch (transparent=False, hold_down=_flood_delay):
	  """
		Starts an L2 learning switch.
  	  """
  		try:
    		global _flood_delay
		    _flood_delay = int(str(hold_down), 10)
		    assert _flood_delay >= 0
		except:
    		raise RuntimeError("Expected hold-down to be a number")

  		core.registerNew(l2_learning, str_to_bool(transparent))


可以看到launch()函数里面仅有一句话是可执行的：

	core.registerNew(l2\_learning, str\_to\_bool(transparent))

 
让我们去看一看core.registerNew()这个函数。

	  def registerNew (self, __componentClass, *args, **kw):
	    """
	    Give it a class (and optional __init__ arguments), and it will
	    create an instance and register it using the class name.  If the
	    instance has a _core_name property, it will use that instead.
	    It returns the new instance.
	    core.registerNew(FooClass, arg) is roughly equivalent to
	    core.register("FooClass", FooClass(arg)).
	    """
	    name = __componentClass.__name__
	    obj = __componentClass(*args, **kw)
	    if hasattr(obj, '_core_name'):
	      # Default overridden
	      name = obj._core_name
	    self.register(name, obj)
	    return obj
 
可执行语句很少，基本上注释已经完全涵盖了这个函数的作用。主要是在pox注册一个新的线程，如果已存在名字则重载，返回新的实例。同时我们看到在这个函数里面使用到了register()函数，函数定义如下：

	def register (self, name, component=None):
    	"""
    	Makes the object "component" available as pox.core.core.name.
	
    	If only one argument is specified, the given argument is registered
    	using its class name as the name.
    	"""
    	#TODO: weak references?
    	if component is None:
    	  component = name
    	  name = component.__class__.__name__
    	  if hasattr(component, '_core_name'):
    	    # Default overridden
    	    name = component._core_name
	
    	if name in self.components:
    	  log.warn("Warning: Registered '%s' multipled times" % (name,))
    	self.components[name] = component
    	self.raiseEventNoErrors(ComponentRegistered, name, component)
    	self._try_waiters()
 
Register()实现了在初始化的时候，将相关组件加入到了pox.core.core之中。Core raise了一个ComponentRegistered事件，componentRegistered类定义如下，接着进入等待阶段。

	class ComponentRegistered (Event):
	  """
	  This is raised by core whenever a new component is registered.
	  By watching this, a component can monitor whether other components it
	  depends on are available.
	  """
	  def __init__ (self, name, component):
	    Event.__init__(self)
	    self.name = name
	    self.component = component


进行到这里，我们需要做的还有一件事，就是将组件的event_handler与相应的events绑定到一起。
那么在哪里实现了这一个绑定关系呢？
###事件绑定
在每一个组件里面都会有初始函数，而每一个初始函数里面多包含事件绑定的开始们那就是listenTo()函数：

	  def __init__ (self, transparent):
    	self.listenTo(core.openflow)
    	self.transparent = transparent

listenTo()函数在哪里出现呢？寻找之后，你会发现他出现在一个非常重要的文件——revent.py里面。

  	def listenTo (self, source, *args, **kv):
    	"""
    	Automatically subscribe to events on source.
	
	    This method tries to bind all _handle_ methods on self to events
	    on source.  Kind of the opposite of addListeners().
	
	    See also: addListeners(), autoBindEvents()
	    """
	    return autoBindEvents(self, source, *args, **kv)
 
继续调用autoBindEvents()函数实现绑定。

	def autoBindEvents (sink, source, prefix='', weak=False, priority=None):
	  """
	  Automatically set up listeners on sink for events raised by source.
	
	  Often you have a "sink" object that is interested in multiple events
	  raised by some other "source" object.  This method makes setting that
	  up easy.
	  You name handler methods on the sink object in a special way.  For
	  example, lets say you have an object mySource which raises events of
	  types FooEvent and BarEvent.  You have an object mySink which wants to
	  listen to these events.  To do so, it names its handler methods
	  "_handle_FooEvent" and "_handle_BarEvent".  It can then simply call
	  autoBindEvents(mySink, mySource), and the handlers are set up.
	
	  You can also set a prefix which changes how the handlers are to be named.
	  For example, autoBindEvents(mySink, mySource, "source1") would use a
	  handler named "_handle_source1_FooEvent".
	
	  "weak" has the same meaning as with addListener().
	
	  Returns the added listener IDs (so that you can remove them later).
	  """
	  if len(prefix) > 0 and prefix[0] != '_': prefix = '_' + prefix
	  if hasattr(source, '_eventMixin_events') is False:
	    # If source does not declare that it raises any events, do nothing
	    print("Warning: source class %s doesn't specify any events!" % (
	          source.__class__.__name__,))
	    return []
	
	  events = {}
	  for e in source._eventMixin_events:
	    if type(e) == str:
	      events[e] = e
	    else:
	      events[e.__name__] = e
	
	  listeners = []
	  # for each method in sink
	  for m in dir(sink):
	    # get the method object
	    a = getattr(sink, m)
	    if callable(a):
	      # if it has the revent prefix signature, 
	      if m.startswith("_handle" + prefix + "_"):
	        event = m[8+len(prefix):]
	        # and it is one of the events our source triggers
	        if event in events:
	          # append the listener
	          listeners.append(source.addListener(events[event], a, weak=weak,
	                                              priority=priority))
	          #print("autoBind: ",source,m,"to",sink)
	        elif len(prefix) > 0 and "_" not in event:
	          print("Warning: %s found in %s, but %s not raised by %s" %
	                (m, sink.__class__.__name__, event,
	                 source.__class__.__name__))
	
	  return listeners

 
从注释中我们可以看出这个函数的作用:
无非就是讲handler端的sink和event的source连接起来，方式为：

     listeners.append(source.addListener(events[event], a, weak=weak,
                                              priority=priority))

其中用到的addListener()是这个连接的关键，代码如下：

	  def addListener (self, eventType, handler, once=False, weak=False,
	                   priority=None, byName=False):
	    """
	    Add an event handler for an event triggered by this object (subscribe).
	
	    eventType : event class object (e.g. ConnectionUp). If byName is True,
	                should be a string (e.g. "ConnectionUp") 
	    handler : function/method to be invoked when event is raised 
	    once : if True, this handler is removed after being fired once
	    weak : If handler is a method on object A, then listening to an event
	           on object B will normally make B have a reference to A, so A
	           can not be released until after B is released or the listener
	           is removed.
	           If weak is True, there is no relationship between the lifetimes
	           of the publisher and subscriber.
	    priority : The order in which to call event handlers if there are
	               multiple for an event type.  Should probably be an integer,
	               where higher means to call it earlier.  Do not specify if
	               you don't care.
	    byName : True if eventType is a string name, else an Event subclass
	
	    Raises an exception unless eventType is in the source's
	    _eventMixin_events set (or, alternately, _eventMixin_events must
	    be True).
	
	    The return value can be used for removing the listener.
	    """
	    self._eventMixin_init()
	    if (self._eventMixin_events is not True
	        and eventType not in self._eventMixin_events):
	      # eventType wasn't found
	      fail = True
	      if byName:
	        # if we were supposed to find the event by name, see if one of the
	        # event names matches
	        for e in self._eventMixin_events:
	          if issubclass(e, Event):
	            if e.__name__ == eventType:
	              eventType = e
	              fail = False
	              break
	      if fail:
	        raise RuntimeError("Event %s not defined on object of type %s"
	                           % (eventType, type(self)))
	    if eventType not in self._eventMixin_handlers:
	      # if no handlers are already registered, initialize
	      handlers = self._eventMixin_handlers[eventType] = []
	      self._eventMixin_handlers[eventType] = handlers
	    else:
	      handlers = self._eventMixin_handlers[eventType]
	
	    eid = _generateEventID()
	
	    if weak: handler = CallProxy(self, handler, (eventType, eid))
	
	    entry = (priority, handler, once, eid)
	
	    handlers.append(entry)
	    if priority is not None:
	      # If priority is specified, sort the event handlers
	      handlers.sort(reverse = True, key = operator.itemgetter(0))
	
	    return (eventType,eid)

 
第400行的if建立一个与eventType对应的handlers：

    if eventType not in self._eventMixin_handlers:
      # if no handlers are already registered, initialize
      handlers = self._eventMixin_handlers[eventType] = []
      self._eventMixin_handlers[eventType] = handlers
    else:
      handlers = self._eventMixin_handlers[eventType]

 
第413行：

    if priority is not None:
      # If priority is specified, sort the event handlers
      handlers.sort(reverse = True, key = operator.itemgetter(0))

    return (eventType,eid)

将带有handler和eid等信息的entry添加到handlers队列中，priority决定这个handlers在处理时的优先级，若无特殊优先级，则按正常顺序放在队尾。

  	def _eventMixin_init (self):
    	if not hasattr(self, "_eventMixin_events"):
   	   		setattr(self, "_eventMixin_events", True)
    	if not hasattr(self, "_eventMixin_handlers"):
      		setattr(self, "_eventMixin_handlers", {})


在_eventMixin_init()函数里，我们发现在这里我们setattr()了一个_eventMixin_events的特性和_eventMixin_handlers的列表。


这些数据在autoBindEvents()里面有使用到：

	  if hasattr(source, '_eventMixin_events') is False:
	    # If source does not declare that it raises any events, do nothing
	    print("Warning: source class %s doesn't specify any events!" % (
	          source.__class__.__name__,))
	    return []

 
一个很重要的问题是，handlers在哪里？没有handlers就无法就行连接，更不用说接下来的事件处理了。我们来再看一次autoBindEvents()函数，我们观察到source.我们去查看source这个类就会发现问题的答案在哪里了。

	class Source (EventMixin):
	  # Defining this variable tells the revent library what kind of events
	  # this source can raise.
	  _eventMixin_events = set([ComponentRegistered])

	  def __init__ (self):
	    foo()

	  def foo (self):
	    # We can raise events as follows:
	    component = "fake_pox_component"
	    self.raiseEvent(ComponentRegistered(component))

	    # In the above invocation, the argument is an instance of
	    # ComponentRegistered (which is a subclass of Event).  The following is
	    # functionally equivalent, but has the nice property that 
    	# ComponentRegistered is never instantiated if there are no listeners.
    	#self.raiseEvent(ComponentRegistered, component)
    	# In both cases, "component" is passed to the __init__ method for the
    	# ComponentRegistered class.

    	# The above method invocation will raise an exception if an event
    	# handler rauses an exception.  To project yourself from exceptions in
    	# handlers, see raiseEventNoErrors().
 
Source类中调用了raiseEvent()函数，我们再去查看raiseEvent()函数。
在这个函数里面我们找到了handlers的赋值（提取）语句：
 
    # Create a copy so that it can be modified freely during event
    # processing.  It might make sense to change this.
    handlers = self._eventMixin_handlers.get(eventType, [])

整个事件绑定的过程大概可以总结如下：
在事件发生段，即源端在产生事件的时候要raise一个event, 监听端使用监听函数如：ListenTo()不断监听端口，有消息进来，则建立连接，存于对应字典，同时将handler注册到_eventMixin_handlers这个列表中。

###事件处理：
事件处理的函数主要有：raiseEventsNoErrors()和raiseEvents()函数。
但是raiseEventsNoErrors()	函数里面其主要的语句一样是使得最终的条件满足从而调用raiseEvents()函数，所以让我们来看一看raiseEvents()函数的注释：

  	def raiseEvent (self, event, *args, **kw):
    	"""
    	Raises an event.
    	If "event" is an Event type, it will be initialized with args and kw,
    	but only if there are actually listeners.
    	Returns the event object, unless it was never created (because there
    	were no listeners) in which case returns None.
    	"""
 
主要的作用是raise一个event，这个显而易见。
 
    # Create a copy so that it can be modified freely during event
    # processing.  It might make sense to change this.
    handlers = self._eventMixin_handlers.get(eventType, [])
    for (priority, handler, once, eid) in handlers:
      if classCall:
        rv = event._invoke(handler, *args, **kw)
      else:
        rv = handler(event, *args, **kw)
      if once: self.removeListener(eid)
      if rv is None: continue
      if rv is False:
        self.removeListener(eid)
      if rv is True:
        if classCall: event.halt = True
        break
      if type(rv) == tuple:
        if len(rv) >= 2 and rv[1] == True:
          self.removeListener(eid)
        if len(rv) >= 1 and rv[0]:
          if classCall: event.halt = True
          break
        if len(rv) == 0:
          if classCall: event.halt = True
          break
      #if classCall and hasattr(event, "halt") and event.halt:
      if classCall and event.halt:
        break
    return event


L278:

	handlers = self._eventMixin_handlers.get(eventType, [])

从handlers中按照eventType提取出handler,然后对handler遍历。如果once =true(L284)则把监听器去除，即将handler移除。最后入伙遭遇停止标记event.halt则退出循环。事件处理队列终止。

	


###后续
之后再读了北邮泛网无线教育部重点实验室李德民学长的一篇关于pox的文章（Ref: http://lidemin.pw/190）之后再写了一点东西如下：
在启动pox以及各个组件的时候，core=POXCore()的实例化中有提到：
 
这个scheduler是上文一直都没有提到的。
Core.scheduler线程的动作如下：
第一次连接时，建立socket连接，实例化一个connection的类。
接下来的通信过程就需要进一步的学习才能写出来了。

###感想:

自己还是太年轻，太浮夸，从来没有好好看过代码，好好研究过POX的运行机制，还好有实验室的学长写过的一些文章可以读，然后自己照着做一遍，做完之后会有深刻的理解，但是目前，整一个Openflow协议在动态过程中的通信流程并不是特别了解。下一阶段的学习目标是把Openflow协议的通信过程学习一遍，结合之前画过的静态的数据结果，我相信效果应该会很好。Openflow协议的扩展也在很努力地做，有了这些基础之后，如何求改协议，比以前已经变得轻松多了。在此感谢两位学长留下的财富。




参考文献：


李德民学长主页:http://lidemin.pw/190
 
赵伟辰学长主页:http://richardzhao.me/?p=594
