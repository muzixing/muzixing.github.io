title:基于SDN的RYU应用——ARP_PROXY
date:2014/10/19
tags:SDN,ARP_PROXY,RYU
category:Tech

###前言

在传统网络中，存在着一定的广播流量，占据了一部分的网络带宽。同时，在有环的拓扑中，如果不运行某些协议，广播数据还会引起网络风暴，使网络瘫痪。传统的解决方案是运行STP（生成树协议），来解决环路带来的风暴隐患。但是这样的难题在SDN之后，解决起来似乎变得要简单一些。本文将介绍如何在控制器RYU上开发ARP代理模块，用于代理回复ARP请求，以及解决环状拓扑风暴的问题。


###算法逻辑

具体的算法流程图如下：

	packet_in
		|
		|
	  ARP learning
	  MAC_to_Port learning
		|
		|
		|		 		No	
	Multicast? -------------------------------------------->|
		|													|
	   	| Yes												|
		|													|
		|													|
		|	   No											|
	   loop? ----->(dpid,eth_src,dst_ip)learning			|
		|					|								|
		|					|								|
		|					|				No           	|         No
		|Yes		dst_ip in arp_table? ------->dst in mac_to_port? ---->Flood
		|					|								|				|
		|					|Yes							|Yes			|
		|					|								|				|
	   drop				ARP_REPLY						flow_mod			|
		|					|								|				|
		|					|								|				|
		|<------------------|<------------------------------|<--------------|				
	   	|
		|
		end



###解决环路风暴

在回复ARP请求之前，必须要解决的是网络环路问题。我们的解决方案是：以（dpid, eth\_src,arp_dst_ip）为key，记录第一个数据包的in\_port，并将从网络中返回的数据包丢弃，保证同一个交换机中的某一个广播数据包只能有一个入口，从而防止成环。在此应用中默认网络中发起通信的第一个数据包都是ARP数据包。
	
	sw[(datapath.id, eth_src, arp_dst_ip)] = in_port

**代码如下：**

    if eth_dst == ETHERNET_MULTICAST and ARP in header_list:
        arp_dst_ip = header_list[ARP].dst_ip
        if (datapath.id, eth_src, arp_dst_ip) in self.sw:  # Break the loop
            if self.sw[(datapath.id, eth_src, arp_dst_ip)] != in_port:
                out = datapath.ofproto_parser.OFPPacketOut(
                    datapath=datapath,
                    buffer_id=datapath.ofproto.OFP_NO_BUFFER,
                    in_port=in_port,
                    actions=[], data=None)
                datapath.send_msg(out)
                return True
        else:
            self.sw[(datapath.id, eth_src, arp_dst_ip)] = in_port

###ARP回复

解决完环路拓扑中存在的广播风暴问题之后，我们还需要利用SDN控制器可获取网络全局的信息的能力，去代理回复ARP请求，从而减少网络中泛洪的ARP请求数据。这个逻辑非常简单，和二层学习原理基本一样，也是通过自学习主机ARP记录，再通过查询记录并回复。具体代码实现如下：

    if ARP in header_list:
        hwtype = header_list[ARP].hwtype
        proto = header_list[ARP].proto
        hlen = header_list[ARP].hlen
        plen = header_list[ARP].plen
        opcode = header_list[ARP].opcode

        arp_src_ip = header_list[ARP].src_ip
        arp_dst_ip = header_list[ARP].dst_ip

        actions = []

        if opcode == arp.ARP_REQUEST:
            if arp_dst_ip in self.arp_table:  # arp reply
                actions.append(datapath.ofproto_parser.OFPActionOutput(
                    in_port)
                )

                ARP_Reply = packet.Packet()
                ARP_Reply.add_protocol(ethernet.ethernet(
                    ethertype=header_list[ETHERNET].ethertype,
                    dst=eth_src,
                    src=self.arp_table[arp_dst_ip]))
                ARP_Reply.add_protocol(arp.arp(
                    opcode=arp.ARP_REPLY,
                    src_mac=self.arp_table[arp_dst_ip],
                    src_ip=arp_dst_ip,
                    dst_mac=eth_src,
                    dst_ip=arp_src_ip))

                ARP_Reply.serialize()

                out = datapath.ofproto_parser.OFPPacketOut(
                    datapath=datapath,
                    buffer_id=datapath.ofproto.OFP_NO_BUFFER,
                    in_port=datapath.ofproto.OFPP_CONTROLLER,
                    actions=actions, data=ARP_Reply.data)
                datapath.send_msg(out)
                return True
    return False

###后语

在环状拓扑中解决广播风暴问题基本都是使用STP协议，而SDN的网络架构，给我们提供了一个更高效的解决方案。不仅如此，我们还可以在解决风暴之后，进一步完成ARP代理应用。然而这个简单的APP，并没有很好地解决ARP的问题，因为ARP也有生存时间。而过时的数据会影响网络的正常运行，所以，进一步的优化将是设置ARP记录的刷新时间。以及sw{dpid, eth_src,arp_dst_ip}的刷新时间。以保证数据的有效性。

推而广之，我们可以按照这样的模式去处理其他的广播数据，如DHCP。更多的功能数据包或者信令数据包的代理，都可以模仿本篇的流程实现。文章的最后，附上完整的代码实现。

	# Author:muzixing
	# Time:2014/10/19
	#
	
	from ryu.base import app_manager
	from ryu.controller import ofp_event
	from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
	from ryu.controller.handler import set_ev_cls
	from ryu.ofproto import ofproto_v1_3
	from ryu.lib.packet import packet
	from ryu.lib.packet import ethernet
	from ryu.lib.packet import arp
	
	ETHERNET = ethernet.ethernet.__name__
	ETHERNET_MULTICAST = "ff:ff:ff:ff:ff:ff"
	ARP = arp.arp.__name__
	
	
	class ARP_PROXY_13(app_manager.RyuApp):
	    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	
	    def __init__(self, *args, **kwargs):
	        super(ARP_PROXY_13, self).__init__(*args, **kwargs)
	        self.mac_to_port = {}
	        self.arp_table = {}
	        self.sw = {}
	
	    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	    def switch_features_handler(self, ev):
	        datapath = ev.msg.datapath
	        ofproto = datapath.ofproto
	        parser = datapath.ofproto_parser
	
	        # install table-miss flow entry
	        #
	        # We specify NO BUFFER to max_len of the output action due to
	        # OVS bug. At this moment, if we specify a lesser number, e.g.,
	        # 128, OVS will send Packet-In with invalid buffer_id and
	        # truncated packet data. In that case, we cannot output packets
	        # correctly.
	
	        match = parser.OFPMatch()
	        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
	                                          ofproto.OFPCML_NO_BUFFER)]
	        self.add_flow(datapath, 0, match, actions)
	
	    def add_flow(self, datapath, priority, match, actions):
	        ofproto = datapath.ofproto
	        parser = datapath.ofproto_parser
	
	        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
	                                             actions)]
	
	        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
	                                idle_timeout=5, hard_timeout=15,
	                                match=match, instructions=inst)
	        datapath.send_msg(mod)
	
	    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	    def _packet_in_handler(self, ev):
	        msg = ev.msg
	        datapath = msg.datapath
	        ofproto = datapath.ofproto
	        parser = datapath.ofproto_parser
	        in_port = msg.match['in_port']
	
	        pkt = packet.Packet(msg.data)
	
	        eth = pkt.get_protocols(ethernet.ethernet)[0]
	        dst = eth.dst
	        src = eth.src
	        dpid = datapath.id
	
	        header_list = dict(
	            (p.protocol_name, p)for p in pkt.protocols if type(p) != str)
	        if ARP in header_list:
	            self.arp_table[header_list[ARP].src_ip] = src  # ARP learning
	
	        self.mac_to_port.setdefault(dpid, {})
	        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)
	
	        # learn a mac address to avoid FLOOD next time.
	        self.mac_to_port[dpid][src] = in_port
	
	        if dst in self.mac_to_port[dpid]:
	            out_port = self.mac_to_port[dpid][dst]
	        else:
	            if self.arp_handler(header_list, datapath, in_port, msg.buffer_id):
	                # 1:reply or drop;  0: flood
	                print "ARP_PROXY_13"
	                return None
	            else:
	                out_port = ofproto.OFPP_FLOOD
	                print 'OFPP_FLOOD'
	
	        actions = [parser.OFPActionOutput(out_port)]
	
	        # install a flow to avoid packet_in next time
	        if out_port != ofproto.OFPP_FLOOD:
	            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
	            self.add_flow(datapath, 1, match, actions)
	
	        data = None
	        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
	            data = msg.data
	        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
	                                  in_port=in_port, actions=actions, data=data)
	        datapath.send_msg(out)
	
	    def arp_handler(self, header_list, datapath, in_port, msg_buffer_id):
	        header_list = header_list
	        datapath = datapath
	        in_port = in_port
	
	        if ETHERNET in header_list:
	            eth_dst = header_list[ETHERNET].dst
	            eth_src = header_list[ETHERNET].src
	
	        if eth_dst == ETHERNET_MULTICAST and ARP in header_list:
	            arp_dst_ip = header_list[ARP].dst_ip
	            if (datapath.id, eth_src, arp_dst_ip) in self.sw:  # Break the loop
	                if self.sw[(datapath.id, eth_src, arp_dst_ip)] != in_port:
	                    out = datapath.ofproto_parser.OFPPacketOut(
	                        datapath=datapath,
	                        buffer_id=datapath.ofproto.OFP_NO_BUFFER,
	                        in_port=in_port,
	                        actions=[], data=None)
	                    datapath.send_msg(out)
	                    return True
	            else:
	                self.sw[(datapath.id, eth_src, arp_dst_ip)] = in_port
	
	        if ARP in header_list:
	            hwtype = header_list[ARP].hwtype
	            proto = header_list[ARP].proto
	            hlen = header_list[ARP].hlen
	            plen = header_list[ARP].plen
	            opcode = header_list[ARP].opcode
	
	            arp_src_ip = header_list[ARP].src_ip
	            arp_dst_ip = header_list[ARP].dst_ip
	
	            actions = []
	
	            if opcode == arp.ARP_REQUEST:
	                if arp_dst_ip in self.arp_table:  # arp reply
	                    actions.append(datapath.ofproto_parser.OFPActionOutput(
	                        in_port)
	                    )
	
	                    ARP_Reply = packet.Packet()
	                    ARP_Reply.add_protocol(ethernet.ethernet(
	                        ethertype=header_list[ETHERNET].ethertype,
	                        dst=eth_src,
	                        src=self.arp_table[arp_dst_ip]))
	                    ARP_Reply.add_protocol(arp.arp(
	                        opcode=arp.ARP_REPLY,
	                        src_mac=self.arp_table[arp_dst_ip],
	                        src_ip=arp_dst_ip,
	                        dst_mac=eth_src,
	                        dst_ip=arp_src_ip))
	
	                    ARP_Reply.serialize()
	
	                    out = datapath.ofproto_parser.OFPPacketOut(
	                        datapath=datapath,
	                        buffer_id=datapath.ofproto.OFP_NO_BUFFER,
	                        in_port=datapath.ofproto.OFPP_CONTROLLER,
	                        actions=actions, data=ARP_Reply.data)
	                    datapath.send_msg(out)
	                    return True
	        return False
