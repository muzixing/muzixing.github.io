title:Traffic monitor in RYU
date:2015/3/4
tags:ryu bandwidth
category:Tech

In many scenes, we need to get the real time link bandwidth so that controller can make some decisions in time. For example, load balance, network alert and so on. This article will demostrate how to get the bandwidth of a flow or a port(flow speed or port speed)。


Actually, I wrote my app base on the simple_monitor at [Ryu_book Traffic Monitor](http://osrg.github.io/ryu-book/en/html/traffic_monitor.html)

You can get my source code at:[simple_monitor](https://github.com/muzixing/ryu/blob/master/ryu/app/simple_monitor.py)

In my application, I define some new data structures, and init them in function \_\_int\_\_().  The usage of them show below.

    self.port_speed = {}   	# record the port speed 
    self.flow_speed = {}   	# record the flow speed
    self.sleep = 2		   	# the interval of getting statistic
    self.state_len = 3	   	# the length of speed list of per port and flow.


##SimpleMonitor

The traffic monitor function has been implemented in the SimpleMonitor class which inherited app_manager.RyuApp, therefore, we need to manipulate packet in other application. This design makes SimpleMonitor as a independent application.
###Stats request

First of all, We need to send the OFPPortStatsRequest message and OFPFlowStatsRequest message to request port and flow statistic infomation periodically. 

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

###Stats reply

We define the \_port\_stats\_reply\_handler to manipulate the port stats reply message, so as the flow stats reply message.In function \_port\_stats\_reply\_handler, we use (ev.msg.datapath.id, stat.port_no) as the key of self.port_stats, while the value is (stat.tx_bytes, stat.rx_bytes, stat.rx_errors, stat.duration_sec, stat.duration_nsec).

We use the self.\_get\_speed to calculate port speed.

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body

        for stat in sorted(body, key=attrgetter('port_no')):
            if stat.port_no != ofproto_v1_3.OFPP_LOCAL:
                key = (ev.msg.datapath.id, stat.port_no)
                value = (
                    stat.tx_bytes, stat.rx_bytes, stat.rx_errors,
                    stat.duration_sec, stat.duration_nsec)

                self._save_stats(self.port_stats, key, value, self.state_len)

                # Get port speed.
                pre = 0
                period = self.sleep
                tmp = self.port_stats[key]
                if len(tmp) > 1:
                    pre = tmp[-2][0] + tmp[-2][1]
                    period = self._get_period(
                        tmp[-1][3], tmp[-1][4],
                        tmp[-2][3], tmp[-2][4])

                speed = self._get_speed(
                    self.port_stats[key][-1][0]+self.port_stats[key][-1][1],
                    pre, period)

                self._save_stats(self.port_speed, key, speed, self.state_len)
                print '\n Speed:\n', self.port_speed

###Fixed-Cycle Processing

Finally, we need to create a thread to send requests messages and manipulate reply messages, and the function of thread is \_monitor.

    self.monitor_thread = hub.spawn(self._monitor)

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(self.sleep)

So far, we have finished the simple monitor application in RYU.

**Note that**: I just calculate the speed of port and flow, if you need to get the free bandwidth, you still need to subtract the speed form link bandwidth.

I hope my work can help you.


