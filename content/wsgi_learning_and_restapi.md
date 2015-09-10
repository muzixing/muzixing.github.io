title:RYU中WSGI学习笔记与RESTAPI开发
tags:wsgi,ryu
category:Tech
date:2015/5/13

另一篇博文中已经介绍如何使用RYU的RESTAPI，本篇将继续介绍相关内容，主要分为WSGI学习总结和以ofctl\_rest.py为例的RESTAPI的实现与内部机制。由于第一次学习WSGI，还有许多地方不是特别理解，所学知识均来自Google。文中若有错误之处，敬请指出，谢谢。

###WSGI

[Web服务器网关接口](http://zh.wikipedia.org/wiki/Web%E6%9C%8D%E5%8A%A1%E5%99%A8%E7%BD%91%E5%85%B3%E6%8E%A5%E5%8F%A3)（Python Web Server Gateway Interface，缩写为WSGI）是为Python语言定义的Web服务器和Web应用程序或框架之间的一种简单而通用的接口。为了理解WSGI，可以尝试一下的小例子。

```python
from cgi import parse_qs
from cgi import escape
import logging


def hello_world(environ, start_response):
    parameters = parse_qs(environ.get('QUERY_STRING', ''))

    if 'subject' in parameters:
        subject = escape(parameters['subject'][0])
    else:
        subject = 'World.'

    start_response('200 OK', [('Context-Type', 'text/html')])
    return ['''Hello %(subject)s
    Hello %(subject)s!''' %{'subject': subject}]


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    IP = 'localhost'
    port = 8080
    server = make_server(IP, port, hello_world)
    logging.basicConfig(level=logging.INFO)
    LOG = logging.getLogger('wsgi')
    LOG.info('listening on %s: %d'%(IP, port))
    server.serve_forever()
```

运行之后，在浏览器地址栏输入：
    
    http://localhost:8080/?subject=muzixing.com

可以观察到浏览器输出：

    Hello muzixing.com
    Hello muzixing.com!

在写这个小例子的时候，我遇到一个让我非常疑惑的地方，函数hello\_world的参数在哪里赋值？为什么网上的例子参数都是environ和start\_response，难道这两个名字是特殊的？在运行时会默认已经被赋值？经过一系列谷歌以及查看源码之后，我终于还是没有搞明白。

这不科学！！

于是我尝试修改一下形参的名字，果然，还是可以运行的。这验证了这并不是特殊的名字，那么只有一种可能就是在创建对象的时候，已经给赋值了。那么输出一下这两个变量的内容是不错的尝试。尝试之后发现后者是一个对象，前者是一些列的内容。这验证了谷歌出来的各种说法：environ和start\_response，environ是一个字典包含了CGI中的环境变量，start\_response也是一个callable，接受两个必须的参数，status（HTTP状态）和response\_headers（响应消息的头）。而这个赋值过程并不需要开发者去开发，在初始化时已经完成赋值。

为了进一步验证想法，找到了ryu使用的eventlet相关的文件：/usr/lib/python2.7/dist-packages/eventlet/wsgi.py。在这个文件中定义了class HttpProtocol(BaseHTTPServer.BaseHTTPRequestHandler)。在该类中定义了函数： handle\_one\_request和handle\_one\_response。在handle\_one\_request函数中初始化了如下两个重要的内容(line:227)：

```python
    self.environ = self.get_environ()
    self.application = self.server.app
```
在handle\_one\_request函数中还调用了handle\_one\_response。在handle\_one\_response函数中，定义了函数start\_response。查看代码时，终于发现了一句极为重要的语句(line:336)：

```python
    result = self.application(self.environ, start_response)
```
start_restart函数在这句语句之前有定义(line:316)。至此，终于明白，为什么没有给形参赋值，实际上，这都是背后的故事。

wsgi.py文件中定义了Server类，用于开启一个服务端socket，处理socket通信。文件中还定义了一个重要的接口函数：server。server函数主要完成了功能是启动一个wsgi server去处理来自客户端的请求。启动之后将永久循环，直到被关闭。

    Start up a wsgi server handling requests from the supplied server
    socket.  This function loops forever.  The *sock* object will be closed after server exits,
    but the underlying file descriptor will remain open, so if you have a dup() of *sock*,
    it will remain usable.

在RYU中，同样也有一个wsgi.py文件。该文件定义了一系列的WSGI的类，用于实现WSGI，为webapp提供支持。此外，hub.py文件中也有对应的内容，这些内容的分析将在下一小节ofctl_rest模块进行分析。


###Ofctl_rest.py

在ofctl\_rest.py文件中定义了class RestStatsApi(app\_manager.RyuApp)和class StatsController(ControllerBase)。其中class RestStatsApi(app\_manager.RyuApp)是一个RYUAPP模块，实现了 statistic相关的相关RESTAPI; class StatsController则是具体的API运行实体。class RestStatsApi(app\_manager.RyuApp)部分源码如下：
    
```python
class RestStatsApi(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION,
                    ofproto_v1_2.OFP_VERSION,
                    ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {
        'dpset': dpset.DPSet,
        'wsgi': WSGIApplication
    }

    def __init__(self, *args, **kwargs):
        super(RestStatsApi, self).__init__(*args, **kwargs)
        self.dpset = kwargs['dpset']
        wsgi = kwargs['wsgi']
        self.waiters = {}
        self.data = {}
        self.data['dpset'] = self.dpset
        self.data['waiters'] = self.waiters
        mapper = wsgi.mapper

        wsgi.registory['StatsController'] = self.data
        path = '/stats'
        uri = path + '/switches'
```
    
OFP\_VERSIONS指的是支持的OpenFlow的协议版本。
\_CONTEXTS部分的内容是依赖的模块。dpset模块的DPSet类是一个RYUAPP类，会被当作一个service启动。DPSet类中主要完成了datapath链接的管理，比如dps字典内容的构建，交换机端口的信息收集，以及负责switches\_features和port\_status等消息的处理。具体细节，读者可自行查看/ryu/controller/dpset.py文件。wsgi模块负责完成了       请求路由的功能，相信内容直接查看wsgi.py介绍部分，此处不赘述。\_CONTEXT中的'wsgi'值为WSGIApplication，所以在启动的时候需要将其作为RYU service启动。然而，这只是一个APPLICATION的类，启动WSGIServer另有玄机。很难发现到底在哪里启动了WSGIServer模块，我们只能在wsgi.py中找到一个没有被本文件使用的全局函数：start\_service(app_mgr),一切线索似乎都断了。

山重水复疑无路，柳暗花明又一村。

这么好玩的源码解析，怎么能就这么结束了呢。从参数中我们发现app_mgr，难道！记忆深处，还记得大明湖畔的那个[启动函数](http://www.muzixing.com/pages/2014/12/27/ryujie-du-ofphandlercontrollerryuapphe-appmanager.html)：

```python
def main(args=None, prog=None):
    '''
    more code 
    '''
    app_lists = CONF.app_lists + CONF.app
    # keep old behaivor, run ofp if no application is specified.
    if not app_lists:
        app_lists = ['ryu.controller.ofp_handler']

    app_mgr = AppManager.get_instance()
    app_mgr.load_apps(app_lists)
    contexts = app_mgr.create_contexts()
    services = []
    services.extend(app_mgr.instantiate_apps(**contexts))

    webapp = wsgi.start_service(app_mgr)  //here is the point!!!
    if webapp:
        thr = hub.spawn(webapp)
        services.append(thr)

    try:
        hub.joinall(services)
    finally:
        app_mgr.close()
```
从代码中可以看到，启动RYU的时候，肯定会执行wsgi.start_service()函数：
```python
def start_service(app_mgr):
    for instance in app_mgr.contexts.values():
        if instance.__class__ == WSGIApplication:
            return WSGIServer(instance)

    return None
```

返回了WSGIServer(WSGIServer instance)的对象，该对象作为一个模块在RYU中得到启动。class WSGIServer类的基类是hub.WSGIServer类，终于我们找到了在hub.WSGIServer中找到了eventlet.wsgi的实例。

```python
#wsgi.WSGIServer
class WSGIServer(hub.WSGIServer):
    def __init__(self, application, **config):
        super(WSGIServer, self).__init__((CONF.wsapi_host, CONF.wsapi_port),
                                         application, **config)
    def __call__(self):
        self.serve_forever()
```
```python
#hub.WSGIServer
class WSGIServer(StreamServer):
    def serve_forever(self):
        self.logger = LoggingWrapper()
        eventlet.wsgi.server(self.server, self.handle, self.logger)
```

至此函数调用链终于被发现。函数调用举例：
ofctl\_rest.py模块被运行，RestStatsApi被加载之前\_CONTEXT的内容被当作service加载。启动RYU时，调用wsgi.start\_service函数，因为WSGIApplication放到了app\_list内，所以判断WSGIApplication成功，将WSGIServer加载。至此WSGIServer和WSGIApplication以及其他模块加载完成。

在WSGIApplication类中使用到了routes模块的[Mapper](http://routes.readthedocs.org/en/latest/introduction.html)和URLGenerator,前者用于URL的路由，后者用于URL的产生。RYU运行之后，WSGIServer负责完成请求到APPlication的分发。WSGIApplication收到请求之后，通过mapper，将对应的请求分发给制定的处理函数。处理函数解析请求，并回复请求。mapper在初始化的时候，添加的connect规则如下：

```python
path='stats'
uri = path + '/flow/{dpid}'
mapper.connect('stats', uri,
               controller=StatsController, action='get_flow_stats',
               conditions=dict(method=['GET', 'POST']))
```

映射的分类属于stats分类，或者路径为stats。uri为/stats/flow/{dpid},dpid数值将在请求中被实例化为某一数值。交给的controller是StatsController，action是该类的get\_flow\_stats函数，请求的类型是GET或者POST，具体种类由请求明确。get\_flow\_stats函数具体如下：

```python
def get_flow_stats(self, req, dpid, **_kwargs):

    if req.body == '':
        flow = {}

    else:

        try:
            flow = ast.literal_eval(req.body)

        except SyntaxError:
            LOG.debug('invalid syntax %s', req.body)
            return Response(status=400)

    if type(dpid) == str and not dpid.isdigit():
        LOG.debug('invalid dpid %s', dpid)
        return Response(status=400)

    dp = self.dpset.get(int(dpid))

    if dp is None:
        return Response(status=404)

    _ofp_version = dp.ofproto.OFP_VERSION

    _ofctl = supported_ofctl.get(_ofp_version, None)
    if _ofctl is not None:
        flows = _ofctl.get_flow_stats(dp, self.waiters, flow)

    else:
        LOG.debug('Unsupported OF protocol')
        return Response(status=501)

    body = json.dumps(flows)
    return Response(content_type='application/json', body=body)
```
函数获取了req之后，进行解析。先获取了flow的信息，然后在调用\_ofctl.get\_flow\_stats(dp, self.waiters, flow)函数获取到了flow的统计信息，然后使用json格式编码，最后返回一个Response.Response是webob的模块的一个类，用于返回一个WSGI的回应。详情可以查看[webob文档](http://webob.readthedocs.org/en/latest/reference.html#id2)。最后我们就可以在网页上查看到我们获取的信息了。

    The webob.Response object contains everything necessary to make a WSGI response. Instances of it are in fact WSGI applications, but it can also represent the result of calling a WSGI application (as     noted in Calling WSGI Applications). It can also be a way of accumulating a response in your WSGI application.

至此RYU中以ofctl_rest.py为例子的REST相关源码分析结束。

###开发RESTAPI

本部分内容将以RYUBOOK上的一个简单案例介绍如何在RYU上开发RESTAPI。更多详细的内容大家可以点击[原链接](http://osrg.github.io/ryu-book/en/html/rest_api.html)查看。

```python
import json
import logging

from ryu.app import simple_switch_13
from webob import Response
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib import dpid as dpid_lib

simple_switch_instance_name = 'simple_switch_api_app'
url = '/simpleswitch/mactable/{dpid}'

class SimpleSwitchRest13(simple_switch_13.SimpleSwitch13):

    _CONTEXTS = { 'wsgi': WSGIApplication }

    def __init__(self, *args, **kwargs):
        super(SimpleSwitchRest13, self).__init__(*args, **kwargs)
        self.switches = {}
        wsgi = kwargs['wsgi']
        wsgi.register(SimpleSwitchController, {simple_switch_instance_name : self})

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        super(SimpleSwitchRest13, self).switch_features_handler(ev)
        datapath = ev.msg.datapath
        self.switches[datapath.id] = datapath
        self.mac_to_port.setdefault(datapath.id, {})

    def set_mac_to_port(self, dpid, entry):
        mac_table = self.mac_to_port.setdefault(dpid, {})
        datapath = self.switches.get(dpid)

        entry_port = entry['port']
        entry_mac = entry['mac']

        if datapath is not None:
            parser = datapath.ofproto_parser
            if entry_port not in mac_table.values():

                for mac, port in mac_table.items():

                    # from known device to new device
                    actions = [parser.OFPActionOutput(entry_port)]
                    match = parser.OFPMatch(in_port=port, eth_dst=entry_mac)
                    self.add_flow(datapath, 1, match, actions)

                    # from new device to known device
                    actions = [parser.OFPActionOutput(port)]
                    match = parser.OFPMatch(in_port=entry_port, eth_dst=mac)
                    self.add_flow(datapath, 1, match, actions)

                mac_table.update({entry_mac : entry_port})
        return mac_table

class SimpleSwitchController(ControllerBase):

    def __init__(self, req, link, data, **config):
        super(SimpleSwitchController, self).__init__(req, link, data, **config)
        self.simpl_switch_spp = data[simple_switch_instance_name]

    @route('simpleswitch', url, methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def list_mac_table(self, req, **kwargs):
        simple_switch = self.simpl_switch_spp
        dpid = dpid_lib.str_to_dpid(kwargs['dpid'])

        if dpid not in simple_switch.mac_to_port:
            return Response(status=404)

        mac_table = simple_switch.mac_to_port.get(dpid, {})
        body = json.dumps(mac_table)
        return Response(content_type='application/json', body=body)

    @route('simpleswitch', url, methods=['PUT'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def put_mac_table(self, req, **kwargs):

        simple_switch = self.simpl_switch_spp
        dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
        new_entry = eval(req.body)

        if dpid not in simple_switch.mac_to_port:
            return Response(status=404)

        try:
            mac_table = simple_switch.set_mac_to_port(dpid, new_entry)
            body = json.dumps(mac_table)
            return Response(content_type='application/json', body=body)
        except Exception as e:
            return Response(status=500)
```

上述应用的代码中主要定义了两个类：SimpleSwitchRest13和SimpleSwitchController。其中SimpleSwitchRest13是SimpleSwitch13的派生类。此外，还需要启动一个WSGIApplication模块和WSGIServer模块提供服务。SimpleSwitchController类是作为WSGIApplication的controller类存在，用于实现对应的RESTAPI的内容。整个应用提供了两个RESTAPI的接口：

* 获取MAC地址表 API

    获取Switching hub中MAC Table的内容，并以JSON格式返回MAC：PORT内容:

```python
@route('simpleswitch', url, methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
def list_mac_table(self, req, **kwargs):
```

* 添加MAC地址表项 API
    
    将指定的MAC：PORT信息加入到MAC Table中，同时根据更新后的MAC Table内容，添加对应的Flow enrties.

```python
@route('simpleswitch', url, methods=['PUT'], requirements={'dpid': dpid_lib.DPID_PATTERN})
def put_mac_table(self, req, **kwargs):
```

对应的执行函数被route装饰器修饰，当route收取到对应的信息，如URL为：host:port/simpleswitch/mactable/{dpid}，动作类型为GET时，就会调用list\_mac\_table函数，返回mac\_table的信息。


####**运行验证**

* 将以上的代码写入yourapp.py
* 然后使用ryu-manager运行yourapp.py
* 启动mininet连接控制器，并pingall
* 使用POSTMAN（或其他）下发RESTAPI请求验证。

实验截图如下：

RYU运行截图如下：

![](http://ww3.sinaimg.cn/mw690/7f593341jw1es2fi9cv7pj20k80auwih.jpg)

POSTMAN获取信息截图如下：

![](http://ww1.sinaimg.cn/mw690/7f593341jw1es2fi9n5kwj20yh0cimyj.jpg)

另一个验证不再贴图，以此类推即可。

###总结

在学习RYU的过程中会接触到许多之前没有接触的技术，沉下心来认真读一读代码，越发感觉工程师在设计RYU时的精妙之处。写程序并不是逻辑的堆砌，而是一个half art, half science的存在。不仅需要追求性能上的优越，满足科学的要求，还需要注意到在实现过程中充满艺术感的设计过程。模块的划分，逻辑的抽象，以及系统结构的设计与搭建，都是非常重要的，直接影响到运行的效率。希望RYU源码分析之旅，能让我学会更多SDN的知识。当文章写得越来越偏向程序，代码分析的时候，就显得不够SDN，但是事实上，我们除了Network,以及实现SDN的OpenFlow协议以外，SDN的S也是值得学习的地方之一。希望我的学习记录能够帮助到更多的人。
