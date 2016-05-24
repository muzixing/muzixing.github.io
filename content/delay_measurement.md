title:Ryu:网络时延探测应用
tags:ryu, delay
category:Tech
date:2016/5/24

之前，笔者已经发布了网络感知应用和基于跳数的最短路径转发应用。本文将介绍笔者开发的网络时延探测应用。该应用通过LLDP数据包的时延和Echo数据包的时延计算得出链路的时延数据，从而实现网络链路时延的感知。详细原理和实现步骤将在文章中详细介绍。

### 测试原理

网络时延探测应用利用了Ryu自带的Switches模块的数据，获取到了LLDP数据发送时的时间戳，然后和收到的时间戳进行相减，得到了LLDP数据包从控制器下发到交换机A，然后从交换机A到交换机B，再上报给控制器的时延T1，示例见图1的蓝色箭头。同理反向的时延T2由绿色的箭头组成。此外，控制器到交换机的往返时延由一个蓝色箭头和一个绿色箭头组成，此部分时延由echo报文测试，分别为Ta，Tb。最后链路的前向后向平均时延T=（T1+T2-Ta-Tb）/2。

<center>![link delay](http://ww1.sinaimg.cn/mw690/7f593341jw1f40i7d39ouj20fr09lgm6.jpg)</center>
<center>图1. 测量链路时延原理图</center>

### 获取LLDP时延

获取T1和T2的逻辑一样，均需要使用到Switches模块的数据。计算LLDP时延的处理逻辑如下代码所示。首先从Packet\_in中解析LLDP数据包，获得源DPID，源端口。然后根据发送端口的数据获取到portdata中的发送时间戳数据，并用当下的系统时间减去发送时间戳，得到时延，最后将其保存到graph数据中。

```py
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        try:
            src_dpid, src_port_no = LLDPPacket.lldp_parse(msg.data)
            dpid = msg.datapath.id
            in_port = msg.match['in_port']
            if self.sw_module is None:
                self.sw_module = lookup_service_brick('switches')

            for port in self.sw_module.ports.keys():
                if src_dpid == port.dpid and src_port_no == port.port_no:
                    port_data = self.sw_module.ports[port]
                    timestamp = port_data.timestamp
                    if timestamp:
                        delay = time.time() - timestamp
                        self._save_lldp_delay(src=src_dpid, dst=dpid,
                                              lldpdelay=delay)
        except LLDPPacket.LLDPUnknownFormat as e:
            return
```

### 获取Echo时延

之后，我们还需要测试控制器到交换机之间的echo往返时延。其测量方法是通过在控制器给交换机发送携带有时间戳的echo\_request报文，然后解析交换机返回的echo\_reply，并用当下时间减去data部分解析的发送时间，获得往返时间差。所以我们需要完成echo\_request的定时发送和解析的实现，详细示例代码如下：

```py
    def _measure(self):
        while True:
            self._send_echo_request()
            hub.sleep(self.SLEEP_PERIOD)

    def _send_echo_request(self):
        for datapath in self.datapaths.values():
            parser = datapath.ofproto_parser
            data = "%.6f" % time.time()
            echo_req = parser.OFPEchoRequest(datapath, data=data)
            datapath.send_msg(echo_req)

    @set_ev_cls(ofp_event.EventOFPEchoReply, MAIN_DISPATCHER)
    def echo_reply_handler(self, ev):
        try:
            latency = time.time() - eval(ev.msg.data)
            self.echo_latency[ev.msg.datapath.id] = latency
        except:
            return
```

完成echo时延的计算之后，将其保存到echo\_latency字典中，已备后续计算使用。

### 计算链路时延

完成时延数据获取之后，还需要基于这些数据，计算出链路的时延，公式就是T=（T1+T2-Ta-Tb）/2。所以编写计算方法，示例代码如下。其中get\_delay方法用于计算对应交换机之间的链路时延，\_save\_delay\_data可以用于计算和存储lldp的时延和链路时延，其功能根据传入参数而定。而calculate\_link\_delay方法则用于调用计算方法，并将时延结果存储到networkx图数据结构中。

```py
    def get_dalay(self, src, dst):
        try:
            fwd_delay = self.graph[src][dst]['lldpdelay']
            re_delay = self.graph[dst][src]['lldpdelay']
            src_latency = self.echo_latency[src]
            dst_latency = self.echo_latency[dst]

            delay = (fwd_delay + re_delay - src_latency - dst_latency)/2
            return max(delay, 0)
        except:
            return float('inf')

    def _save_lldp_delay(self, src=0, dst=0, lldpdelay=0):
        try:
            self.graph[src][dst]['lldpdelay'] = lldpdelay
        except:
            if self.graph is None:
                self.network_aware = lookup_service_brick('network_aware')
                self.graph = self.network_aware.graph
            return

    def create_link_delay(self):
        try:
            for src in self.graph:
                for dst in self.graph[src]:
                    if src == dst:
                        self.graph[src][dst]['delay'] = 0
                        continue
                    self.graph[src][dst]['delay'] = self.get_dalay(src, dst)
        except:
            if self.graph is None:
                self.network_aware = lookup_service_brick('network_aware')
                self.graph = self.network_aware.graph
            return
```

至此关于网络拓扑中链路时延的获取应用开发完成。需要注意的是，本应用需要依赖Ryu的topology/switches.py模块，所以如果单独使用时，需要配套启动switches.py。另外，与前面发表的应用相互结合，此应用中的graph是之前的network\_aware模块感知的网络拓扑数据graph。

时延探测应用运行结果截图如图2所示。

<center>![](http://ww1.sinaimg.cn/mw690/7f593341jw1f3ye9xt1nuj20o90fjgr4.jpg)</center>
<center>图2.时延监控应用运行结果</center>

### 总结

网络时延数据是网络重要数据，是许多网络决策的重要依据，所以网络时延数据测量非常重要。本文介绍了如何在Ryu中开发时延探测应用，并粘贴了关键的代码，希望对读者的学习提供一定的帮助。此外，还需要注意两点：（1）此时延探测模块十分初级，并没有精确性方面的考虑，比如需要将其放在核心层实现，在发送的最后时刻才添加时间戳，收到数据包的第一时刻马上解析时间戳等等，所以精确性不足。在Mininet模拟场景下，最开始的几组数据将会异常，但很快就可以恢复正常。（2）此处的拓扑数据均基于两个交换机之间仅有单链路存在的假设。若存在多链路，则数据会被最后获取的链路覆盖。解决这一问题的办法就是采用Neworkx的MultiGraph图结构来存储数据。最后希望本文能给读者带来一定的帮助，完整代码将于6月发布，敬请期待。


