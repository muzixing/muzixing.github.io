title:基于SDN的网络状态测量
date:2016/1/27
tags:measure
Category:Tech


为了更好地管理和运行网络，非常有必要收集网络资源及其状态信息。在很多网络场景中，SDN控制器的决策都取决时延，带宽和拓扑等网络状态。在开发SDN应用的过程中，笔者总结了一些有用的网络状态测量的解决方案，可以为初学者在解决网络问题时提供一些启发。本文将主要介绍如何通过SDN控制器和OpenFlow协议来测量和收集网络中的时延、带宽以及拓扑状态等信息。

### 时延

时延的测试在终端会显得很容易，但是在交换机节点上测试时延就比较麻烦。在SDN中，可以通过一下步骤实现交换机之间链路的时延。

（1）控制器向交换机A下发一个Packet\_out报文。报文的数据段携带了任意一个约定好的协议报文，其报文的数据段携带了控制器下发报文时的时间戳。Packet\_out报文的动作指示交换机将其泛洪或者转发到某端口。
（2）交换机B收到了交换机A发送过来的数据包，无法匹配对应流表项，从而packet\_in到控制器。控制器接收到这个数据包之后，和当下时间相减，得到时间差T1。其时间差约等于数据包从控制器到交换机A + 交换机A到交换机B + 交换机B到控制器的时延。
（3）同理，控制器向交换机B发送一个类似的报文。然后控制器从交换机A收到Packet\_in报文，记录下时间差T2。所以T1+T2=控制器到交换机A的RTT+控制器到交换机B的RTT+交换机A到交换机B的时延RTT。
（4）控制器向交换机A和交换机B分别发送带有时间戳的Echo request。交换机收到之后即刻回复携带echo request时间戳的echo reply消息。所以控制器可以通过Echo reply的时间戳减去Echo reply携带的时间，从而得到对应交换机和控制器之间的RTT。通过这种方法测得控制器到交换机A,B的RTT分别为Ta，Tb。
（5）T1+T2-Ta-Tb则得到交换机A到交换机B的RTT。假设往返时间一样，则交换机A到交换机B的链路时延为（T1+T2-Ta-Tb）/2。

这种方法可以相对准确地测试到链路的实验，无法计算而忽略掉的部分时间是数据包在交换机中的处理时延。而这种简单的方法已经被申请专利了，不知道我这么写会不会有问题。

### 带宽

带宽数据是网络状态中的重要数据。在SDN网络中获取带宽可以通过OpenFlow协议，也可以通过第三方的测量软件获取数据，如sFlow。此处仅介绍如何通过OpenFlow协议来获取可用带宽。

一条链路的带宽由两个端口的能力决定。所以我们可以通过获取端口的流量来得到链路的流量。OpenFlow协议中可以通过统计报文来获取端口、流表、流表项、组表和meter表的统计信息。以端口的统计信息为例，控制器通过周期下发Port statistics消息可以获得交换机端口的统计信息，其返回的统计消息格式如下：

    struct ofp_port_stats {
        uint32_t port_no;
        uint8_t pad[4];/* Align to 64-bits. */
        uint64_t rx_packets;/* Number of received packets. */
        uint64_t tx_packets;/* Number of transmitted packets. */
        uint64_t rx_bytes;/* Number of received bytes. */
        uint64_t tx_bytes;/* Number of transmitted bytes. */
        uint64_t rx_dropped;/* Number of packets dropped by RX. */
        uint64_t tx_dropped;/* Number of packets dropped by TX. */
        uint64_t rx_errors;/* Number of receive errors. This is a super-set
                             of more specific receive errors and should be
        uint64_t tx_errors; /*
        uint64_t rx_frame_err;
        uint64_t rx_over_err;
        uint64_t rx_crc_err;
        uint64_t collisions;
        uint32_t duration_sec;
        uint32_t duration_nsec;
    };

从消息格式中可以发现可获取到收发的包数、字节数以及这个统计持续的时间。如果把两个不同时间的统计消息的字节数相减，再除以两个消息差也即统计时间差则可以得到统计流量速度。如果想得到剩余带宽则可以用端口最大带宽减去当前流量带宽，则得端口剩余带宽。同理，可以计算出对应流表项或者组表等的统计流量。基于以上计算出来的端口剩余带宽等数据，可为部署负载均衡等流量优化工程提高数据支撑。

### 拓扑

拓扑的发现比较容易理解。控制器通过将携带dpid+port\_no信息的LLDP数据包从对应端口packet\_out出去，然后LLDP数据包被对端交换机Packet\_in到控制器，最后再由控制器结合Packet\_in消息报头的DPID和in\_port和LLDP报文中的DPID和Port\_no从而得出一条链路信息。依次类推，控制器可以发现全部的链路信息，从而发现网络拓扑。

以上的解决方案需要向每个端口下发packet\_out，而此举会产生很多的OpenFlow消息，消耗OpenFlow channel宝贵的带宽资源。所以可以采用以下的优化结局方式。

（1）收集swicth features时记录交换机上端口号和端口mac的对应关系。
（2）弃用port\_id的tlv，转而使用端口的mac作为端口的标记。
（3）下发packet\_out时，actions中添加对每个端口的OFPActionSetField(eth\_src=port\_infor.hw\_addr)动作和OFPActionOutput(port\_infor.port\_no)动作,从而使得仅对交换机下发一个Packet\_out就可以完成对所有的端口进行LLDP发送的操作。在每个端口发送数据之前，都需要对数据的src\_mac地址置位成端口的mac地址。而控制器收到LLDP的packet\_in时，通过mac和port\_id的对应关系找出链路。通过这种方法可以将packet\_out的数目大大降低，从每个端口发送端口数目N个降低至到1个。

以上的解决方案仅能发现OpenFlow的网络，如果OpenFlow网络中间存在传统网络设备形成的子网络，则以上的解决方案将会将与传统网络连接的端口误认为是接入端口。

这个问题可以通过LLDP和发送广播包的方式解决。首先通过LLDP发现OpenFlow的拓扑。然后再往“边缘端口”（与传统网络相连的端口此时也被认为是边缘端口）发送广播包，如果广播包从某一个交换机端口回来，则说明这个端口之外未知的地方还有一些交换设备，则证明这个端口不是主机的接入端口。但是传统设备如果不通过其他形式去发现还是无法发现具体的网络拓扑的信息。

###总结

本文总结了在SDN网络中如何发现和测量网络的一些基础的信息，比如链路的时延和带宽，网络的拓扑等等。发现和测量这些基础的网络状态可以用于其他的网络决策，从而使得网络运行更加合理，进而提高资源利用率。以上部分内容以实现并公布，比如带宽测量模块可查看[《SDN网络感知服务与最短路径应用》](http://www.muzixing.com/pages/2015/07/08/sdnwang-luo-gan-zhi-fu-wu-yu-zui-duan-lu-jing-ying-yong.html)。

作者简介：
李呈，2014/09-至今，北京邮电大学信息与通信工程学院未来网络理论与应用实验室（FNL实验室）攻读硕士研究生。

个人博客：www.muzixing.com





