title:OpenDayLight中MD-SAL学习笔记
date:2014/8/13
tags:opendaylight,md-sal
category:Tech

##前言

在学习opendaylight的过程中，总是遇到AD-SAL( API-Driven SAL)和MD-SAL（Model-Driven SAL）等概念。在努力查找资料学习之后，有了一点学习笔记，写出来加深印象。同时也给同样迷惑的同学一点帮助。

转载请声明：北邮-李呈：www.muzixing.com


##About MD-SAL

MD-SAL使得在SDN控制器那些丰富的服务和模块可以使用统一的数据结构和南向和北向的API。

![sal-comparison](https://wiki.opendaylight.org/images/4/4d/SAL-Comparison.png)


上图引用地址：https://wiki.opendaylight.org/images/4/4d/SAL-Comparison.png

MD-SAL提供请求路由（request routing）和基础设施去支持服务的适配，但它不提供服务的适应本身;业务适配是由插件提供。MD-SAL认为适配插件是一个普通的插件：它向SAL提供数据，并通过模型生产的API来读取消费数据。

###Request outing

为SAL中，request routing可用于消费者的请求路由，从而寻找到对应的生产者。当一个plugin注册之后，就会在routing table中有对应记录，consumer向SAL发起RPC应用申请的时候，会由request routing查找routing table，找到对应的plugin。

在md-sal/sal-binding-api/...、binding/api/rpc目录下可以找到RpcRouter.java等文件，都与RPC routing有关。当然request routing还有notification的routing,并不仅仅只是rpc。


##Bundle register

###AbstractBrokerAwareActivator

**在一个具体的plugin实现中会继承AbstractBindingAwareProvider类,而AbstractBindingAwareProvider继承了AbstractBrokerAwareActivator类。**

当一个bundle启动时就会调用AbstractBrokerAwareActivator。这个类实现了org.osgi.framework.BundleActivator接口。BunbleActivator中的start（BundleContext context）和stop(BundleContext context)方法用于开启bundle和关闭bundle.在AbstractBrokerAwareActivator中，实现了start和stop两个方法，分别调用了startImpl和stopImpl两个具体的方法。startImpl是在bundle开始的时候，用于初始化，资源申请等。同理，stopImpl是bundle关闭时，资源的释放。

同理，消费者类似。

###onSessionInitialized

每一个消费者或生产者和SAL之间的通信都可以具体称之为Session(会话)。上一小节提到的BundleActivator接口中有两个方法start和stop的参数都是BundleConetxt.在BundleContext接口中定义了许多方法，如：

	registerService(java.lang.Class<S\> clazz, S service, java.util.Dictionary<java.lang.String,?> properties) 

可实现bundle的注册。具体链接：http://www.osgi.org/javadoc/r4v43/core/org/osgi/framework/BundleContext.html

在onSessionInitialized方法中，通常会调用session.addRpcImplementation(Class<T> Serviceinterface,T implementation)。其方法定义在RpcProvider.java中，用于指明bunlde初始化时的接口和实现等运行实体。

##Register to MD-SAL

###BindingAwareBroker

BindingAwareProvider和BindingAwareConsumer都实现了BindingAwareBroker interface,用
于实现生产者和消费者的在MD-SAL注册。此接口可以消除生产者和消费者之间的直接关系。

其他文件的功能根据文件名称基本可以了解。博主也没有太多深究。

###RPC register

调用**addRpcImplementation(class <T\> serviceInterface, T implementation)**方法将RPC注册到MD-SAL,具体可查看RpcProviderRegister.java。举例如下：

	providerContext.addRpcImplementation(ShapeService.class, shape);

具体链接：http://sdntutorials.com/how-to-register-a-service-to-md-sal/

消费者可以通过**getRpcService(class <T/> serviceInterface)**调用对应的RPC。

	session.getRpcService(ShapeService.class)


##Plugin development process

![plugin_development_process](https://wiki.opendaylight.org/images/3/39/Plugin_design_process.png)

上图引用地址：https://wiki.opendaylight.org/images/3/39/Plugin_design_process.png

在ODL中开发一个plugin的流程如上所示。以[Ping](http://www.muzixing.com/pages/2014/08/06/opendaylightzhong-kai-fa-mo-kuai-ping.html)为例，首先需要使用YANG定义一个model,即model-ping。使用maven编译的时候，会调用YANG Tools自动生成对应的API.然后生成API OSGI Bundle。

接着我们需要对接口进行实现，也即plugin source code.在ping例子中ping-plugin就是plugin source code。通过maven编译生成plugin OSGI Bundle.最后都部署到OSGI上。将对应的jar包放到controller对应目录中，运行controller时就会和控制器一起运行。但是在全局编译的时候还需要再对应的pom.xml中对其进行描述，从而使得在编译时将对应的bundle编译并生成对应的jar，从而成功在controller中添加功能。

###Example

借用[官网](https://wiki.opendaylight.org/view/OpenDaylight_Controller:MD-SAL:FAQ)的一张图，解（翻）释（译）一下添加新流表时，ODL内部运行的场景。

![add_flow_case](https://wiki.opendaylight.org/images/1/17/Add_Flow_use_case.png)

   1. 当plugin/app启动时，对应的bundle已经完成了注册。a）流编程服务(还是flow programmer service舒服)在md-sal注册，提供流数据配置通知服务。b）OF 插件和其他的插件在SAL上注册AddFlow RPF实现。注意RPC在plugin model中定义，而API是在编译过程中生成的。
   2. 一个客户app通过控制器提供的REST API请求add flow。客户端app需要提供这个REST调用的全部参数。
   3. 从“add flow”来的数据发序列化，然后一个新流就在flow service 配置数据树上创建了。若成功REST调用马上回回复调用者成功信息。
   4. 由于flow programmer service已经注册去接收在flow service data tree上的数据变化消息的通知。MD-SAL产生一个data changed的通知并发给Flow programmer service.
   5. flow programmer service 读取该消息，并产生添加动作。
   6. 在这个过程中还其他的操作中，flow programmer service 需要告诉OF plugin在适当的交换机上添加flow。Flow programmer service 使用OF plugin生成的API去创建"AddFlow"RPC所需要的输入参数DTO(data transfer obiect).
   7. Flow programmer service 获取到服务的实例，然后引用服务中的“AddFlow”RPC。MD-SAL将会将请求路由到适当的OF plugin。
   8. "AddFlow"RPC 请求被路由到OF plugin，然后“AddFlow”RPC的实现方法被引用。
   9. “AddFlow”RPC实现通过OF plugin API去读取RPC 输入参数的DTO.
   10. "AddFlow"RPC 被远程运行，相应的flow_mod被下发到相应的交换机。

##后语

对于MD-SAL，我只是有一个概念，离真正了解还有很多距离。文中若有错误指出，敬请指出，共同进步！

其实官网上已经有很多资料，在学习的过程中，OpenDaylight SDN研究群（194240432）的共享资料帮助了我很多。接下来我将学习官网教程toaster,希望能在那个例子中得到实践经验，为以后的工程开发打下基础。以目前的状况来看，我还需要花很多时间来学习ODL，之后才是真正的SDN应用开发。
