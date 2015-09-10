title:OpenVirteX文档详解（一）——Overview and Components
date:2014/10/23
tags:Network Virtualization
Category:Tech

##前言

本篇博文将按照OpenVirteX Documentation的顺序详细介绍OpenVirteX的相关内容。完整翻译版，请查看@北邮-张歌 翻译的文章。转载请声明出处。

##Overview

OpenVirteX(以下简称OVX)是onlab开发的一个网络虚拟化平台，可以实现多租户的网络虚拟化。对于租户而言，需要在OVX上注册，申请资源，配置自己的网络，指定自己的控制器。剩下的工作就由OVX完成了。OVX可以根据租户的需求，将租户的网络拓扑映射到具体的物理拓扑上，完成网络的联通。对于租户而言，看到的是一个虚拟的网络，无法看到真实的物理拓扑，也不需要关心，即租户“认为”得到了一个属于自己的真实网络。而OVX的位置相当于一个介于租户控制器和交换机之间的转换平台。面对租户，OVX就是一个物理的网络，而面对交换机，OVX就是控制器。（这种转换平台的角色可以实现很多功能，不仅仅是网络虚拟化，还可以模拟许多信息，比如在某个项目中我们将OVS模拟成一个OTN的交换机，验证了一些想法）

###网络虚拟化

网络虚拟化允许多租户占用同一个网络基础设施，同时允许租户对其网络的控制能力，对于租户而言，感觉上是自己控制了整个网络。OVX通过使租户能够获取到自己的虚拟拓扑和全网的地址空间来实现网络虚拟化。前者可以允许租户自定义网络拓扑，后者则是用于隔离不同租户的流量，防止冲突。

与flowspace的切分slice，使租户使用网络的一部分不一样的是，OVX通过同一个header space来区分所有租户的数据。举个例子就是：两个用户可以设置同样的IP，子网掩码，相同的TCP/UDP端口号，而不会引起冲突，这在flowspace理论下是不能成立的。其根本的区别在于OVX做了地址虚拟化，即面向用户的地址是OVXIPAddress，而真正在core datapath中使用的地址其实还是PhysicalIPAddress，只是在edge port的地方，OVX需要做一个translation，把地址把OVXIPAddress的地址映射成唯一的PhysicalIPAddress,而在core datapath的数据转发过程中，其实数据一直是有OVX来处理，而不需要转发到tenant的controller，从而实现了地址虚拟化。这一部分是OVX最重要最核心的部分，我将在后续的部分中详细介绍。

与切分slice原理不一样的另一点是，以前切分的slice限制在底层网络的同构子图中，即用户的虚拟拓扑实际上是物理真实拓扑的一个同构子图，也就是说，租户是可以看到真实的网络拓扑的。而在OVX中不一样的是，用户不需要关心底层的拓扑，而可以任意的定义自己的虚网拓扑，OVX会完成虚网拓扑到物理网络拓扑的映射，这是OVX区别于FlowVisor的重要特性。

OVX作为一个翻译者（代理），存在于租户的控制器和底层网络之间。对于租户而言，OVX通过修改、重写OpenFlow报文来实现租户控制器与租户租用的物理网元之间的通信。这种方法使得OVX具有以下两种能力：

* 提供支持OpenFlow的可编程虚拟网络，从而使得租户可以指定自己的控制器来控制器网络。

* OVX是透明的，对于租户而言，OVX是一个底层网络，而对于底层网络而言，OVX是一个控制器。


值得注意的一点是，整个OVX的虚拟化过程中都是基于主机只属于一个虚网的假设的。主机地址的虚拟化是整个网络虚拟化的核心，同时主机的硬件地址是用来区分租户的流量的关键。下图说明了基于OVX的网络虚拟化。


![OVX](http://ovx.onlab.us/wp-content/uploads/2014/04/Figure1-1.png)


###OpenVirteX:更高级的网络视图

OVX不仅拥有底层物理网络拓扑，而且还有每个租户的虚拟网络拓扑。底层的物理网络拓扑是通过OVX下发LLDP报文获取到的，而上层的虚拟网络拓扑则是由OVX生成的。即租户的控制器下发的LLDP报文不会直接送到底层物理网络，而是在OVX上通过查询底层物理拓扑，从而模拟了LLDP的过程，向上提供网络拓扑。

OVX通过映射算法，解耦了底层网络和租户网络。即南向上，OVX作为控制器，接收底层物理设备的信息，并下发流表等报文到底层设备。北向上，OVX作为交换机集合，向租户的控制器发送OF报文。从而将一条完整的控制通路，变成了两段相互独立的控制通路。而这两者之间的映射关系，保存在Global Map中。在下图中，蓝色部分是面向租户的，而橙色部分是面向交换机的。两者之间互不可见，即租户看不到物理的交换机数据。而绿色部分是两者结合的纽带，保存了网络映射的数据。在数据上行、下行的过程中通过查表修改的方式，翻译成正确的数据。如下图右侧所示，上行数据需要调用virtualize()函数，而下行数据需要调用devirtualize()函数。

![](http://ovx.onlab.us/wp-content/uploads/2014/04/Figure1-2.png)


##Components

接下来的部分将分成以下的小节分析，顺序和官网的文档一样。

* Overview
* Component State Machines
* Component Persistence
* Switches
* Ports
* Links and Routes
* Addresses
* Hosts
* Network Topologies
* Shared Global Mappings
* Messages

###Overview

在OVX中，无论物理的还是虚拟的网络，都是由交换机，端口，链路等基础的对象组成的。对于租户而言，他们面对的虚拟的交换机，本质上和真实的交换机没有差别。全局映射表（Global map）描述了虚拟交换机和物理交换机之间的n:1的映射关系，在这里的映射实现上是OVXSwitch和PhysicalSwitch之间的映射，本质上是租户测看到的虚拟交换机和真实物理交换机之间的映射。n:1映射给交换机复用提供了条件，从而使得不同的租户的交换机可以映射到同一台真实的物理交换机。

以下是OVX中的一些主要的Class的说明。

<table class="table-bordered table-striped table-condensed">
    <tr>
        <td><strong>Base Class</strong></td>
		<td><strong>Representation</strong></td>
    </tr>
	<tr>
		<td>Network</td>
		<td>The full topology </td>
	</tr>
	<tr>
		<td>Switch</td>
		<td>A switch </td>
	</tr>
	<tr>
		<td>Port</td>
		<td>A port on switch</td>
	</tr>
	<tr>
		<td>Link</td>
		<td>A connection between two ports</td>
	</tr>
	<tr>
		<td>Host</td>
		<td>A network host</td>
	</tr>
	<tr>
		<td>IPAddress</td>
		<td>An IP Address </td>
	</tr>
</table>

接下来是继承这些类的子类的一些情况介绍。


<table class="table-bordered table-striped table-condensed">
    <tr>
        <td><strong>Base Class</strong></td>
		<td><strong>Physical Component Class</strong></td>
		<td><strong>Virtual Component Class(es)</strong></td>
    </tr>
	<tr>
		<td>Network</td>
		<td>PhysicalNetwork</td>
		<td>OVXNetwork</td>
	</tr>
	<tr>
		<td>Switch</td>
		<td>PhysicalSwitch</td>
		<td>OVXSwitch</td>
	</tr>
	<tr>
		<td>Port</td>
		<td>PhysicalPort</td>
		<td>OVXPort</td>
	</tr>
	<tr>
		<td>Link</td>
		<td>PhysicalLink</td>
		<td>OVXLink, SwitchRoute</td>
	</tr>
	<tr>
		<td>Host</td>
		<td>--</td>
		<td>Host</td>
	</tr>
	<tr>
		<td>IPAddress</td>
		<td>PhysicalIPAddress</td>
		<td>OVXIPAddress</td>
	</tr>
</table>

举例说明，PhysicalSwicth是底层交换机对应的对象，而租户中的交换机则对应的是OVXSwitch。

**特别需要注意的是Host只有在租户中才有定义。**

OVX通过对这些类进行实例化的方式去创建一个网络。可以有实例化交换机或者端口等类的过程去触发PhysicalNetwork的实例化，因为任何一个交换机或者交换机上的端口都应该属于某一个网络。即这些类的以来关系是Link依赖Port，Port依赖Switch,Switch依赖Network,显而易见的，这是真实网络中的依赖关系。

###Component State Machines

容易想象，每一个交换机，端口等都应该有某些状态，如端口的Down，Up等等。而且不同的网元之间的状态是有一定关系的。比如交换机down掉之后，它的所有端口以及连接到它上面的link都会Down掉，这一点非常容易理解。

为了让OVX能够跟踪和描述不同网元的状态变化的相互关系，我们定义了一个有限状态机（Finite State Machines）来描述这些状态逻辑。

####基本的状态

除去Address和OVXSingleSwitch和OVXBigSwitch以外，其他的component（switch，port，link e.g.）都有如下几个简单的状态：

* INIT:只是创建了一个实例的时候，仅仅是实例化了一个Object
* INACTIVE：将实例通过映射算法，存储到数据库中。实现初步的初始化状态，等待握手。
* ACTIVE：正常的运行状态
* STOPPED：销毁了Object。

####Component FSM Interface

FSM的转换需要一些接口函数来触发，具体如下图所示,函数的功能介绍也很简单，我直接把官网的原文摘抄了过来。

![](http://ovx.onlab.us/wp-content/uploads/2014/04/Figure2-1.png)

* register() [INIT -> INACTIVE] : add component to mappings and storage, checking that dependencies are met (Example: A new port may not be created if a switch doesn’t exist)

* boot() [INACTIVE -> ACTIVE] : open control channels, activate dependent components (Example: bring a link up if the ports on both end are boot()ed)

* teardown() [ACTIVE -> INACTIVE] : close control channels, deactivate dependent components (Example: If a port is torn down, links to/from it are also torn down)

* unregister() [INACTIVE -> STOPPED] : remove from mappings and storage, deactivating or unregistering dependent components as necessary (Example: A link will no longer exist, so must be unregister()ed if either one or both ports it connects is unregister()ed)

从图中我们也可以看出，在这个FSM中，并不是所有的状态都可以相互转换的。比如只有在INACTIVE状态才能通过调用boot()函数来将状态转换成ACTIVE,而不能直接从INIT状态转换成ACTIVE，显然这是非常合理的。

###Component Persistence

租户希望即使OVX重启或者升级之类的，租户的信息以及网络的状态都可以恢复，保持。在OVX中确实也有这方面的功能:OVX通过存储用户的配置信息来完成租户网络的重建。这样就可以保证即使OVX down掉，也没有关系，只要数据库没有损坏就可以恢复了。具体的接口这里不在赘述，详情可以直接查看官网：http://ovx.onlab.us/documentation/architecture/components/

###Switches

一个Switch类是一个datapath的描述，包含了端口的信息和它的DPID，以及他的features，正如features_reply中的信息一样，当然还有某些其他成员，如isConnected,具体的Switch类的成员变量如下所示：

	protected boolean isConnected = false;          // Channel liveness indication
	protected OVXDescriptionStatistics desc = null; // Switch statistics
	// T extends Port.
	protected HashMap<Short, T> portMap             // The ports on this switch, keyed by port number
	protected OFFeaturesReply featuresReply         // The Features Reply
	protected Long switchId                         // The DPID of the switch
	protected Channel channel                       // The control channel to the datapath

继承了Switch基类的子类PhysicalSwitch和OVXSwitch在整个OpenFlow Channel中扮演非常重要的重要。

* PhysicalSwitch类是用于描述物理交换机的类。
* OVXSwitch是描述了面向租户的交换机实体。

PhysicalSwitch作为南向控制通道的终点，用户保存物理交换机的信息；OVXSwitch作为北向控制通路的起点，向租户控制器发送数据，进行通信。其两者的映射关系，以及消息的转发规则都记录在Global Map中。

而OVXSwitch作为基类，还派生了两个子类:OVXSingleSwitch和OVXBigSwitch

* OVXSingleSwitch: map to a single switch
* OVXBigSwitch: map to multiple swtiches

OVXBigSwitch(BVS)映射成多个交换机，同时这些交换机之间的连接，可以等同于一个大交换机内部的交换网络，所以BVS需要保存这些内部交换网络的流表，也即需要保存多个交换机内部连接的流表，详情如下图：

![](http://ovx.onlab.us/wp-content/uploads/2014/04/Figure2-2.png)

###Ports

Port基类存储于交换机的PortMap表中。和网络中真实网络一致，OVX定义的Port以is_edge位标示端口是否属于边源端口。

Ports基类同样也派生了两个子类:PhysicalPort和OVXPort

* PyhsicalPort:描述了底层物理交换机的端口，拥有ovxPortMap表，在up stream的转化过程中需通过此表来找到对应的OVXPort.
* OVXPort:描述了OVXSwitch的端口，包含有重要的tenantId字段和对应的物理Port记录。

###Links and Routes

同样的Link基类也派生两个子类：PhysicalLink和OVXLink。

* PhysicalLink：1:1记录了底层网络的信息。包含了linkId等关键字段。
* OVXLink: 是面向租户的数据结构，描述了租户网络中的Link。拥有tenantId等关键字段。
* SwitchRoute：当映射的两个交换机之间的物理链路不止一段时，OVX需要将中间节点的流表等信息保存起来，在保证物理网络连通的情况下，向用户展现只有一跳的链路。另一方面，多个交换机组成一个大的交换机的情况也是如此。举例请看下图。

![](http://ovx.onlab.us/wp-content/uploads/2014/04/Figure2-3.png)

(摘自官网原文)

Top) Two PhysicalLinks connecting PhysicalPorts (white circles) on three PhysicalSwitches (ps1, ps2, and ps3). Middle) An OVXLink connects two OVXSwitches (vs1, vs2) by their OVXPorts (black circles). vs1 and vs2 map to ps1 and ps3, respectively. The OVXLink maps over two PhysicalLinks, but appears as a single hop to a tenant, to which ps2 is invisible. Bottom) A SwitchRoute internally connects two OVXPorts on the same BVS. A SwitchRoute has an external (OVXPort) and internal (PhysicalPort) endpoints.

![](http://ovx.onlab.us/wp-content/uploads/2014/04/Figure2-4.png)

（摘自官网原文）

various Links with respect to the network mappings. On the top are two tenants, and bottom, OVX’s network view (PhysicalNetwork). Note, there is only one PhysicalNetwork instance but we show two for clarity. Right) Tenant 1 has two OVXLinks, vlink1 and vlink2. Vlink1 corresponds to the path ps1-ps3-ps2 across PhysicalLinks l2 and l3, whereas vlink2 is a 1:1 mapping onto l5. Left) Tenant 2 contains both OVXLinks (red) and a SwitchRoute joining the ports in the OVXBigSwitch vs2, the latter mapped to l3 (blue).

###Address

与其他部分一样，同样分为PhysicalIPAddress和OVXIPAddress两个子类。但是OVX最核心的部分也是最复杂的部分就是地址的虚拟化！将在后续章节进行详细描述。

###Hosts

Host类相对其他类要特殊一些，因为他只有并没有派生成其他子类。因为OVX并没有对Host进行虚拟化，而且也没有必要对Host进行虚拟化。Host类中的Mac地址是区分不同租户的关键标识。通过不同的Host硬件地址，判断属于不同的虚网，且必须遵循每一个Host只属于一个虚网的假设，否则在添加tenantId时会产生冲突，从而无法产生唯一对应的tenantId，影响到流量隔离的功能。所以整个OVX的虚拟化的根基都是基于物理地址全网唯一，而对不同的Host打tenanId来实现虚网隔离，或者流量隔离的。

租户可以任意设置Host的IP，但是OVX必须将这些可能和其他租户地址冲突的虚拟IP地址转化成底层物理网络中唯一的IP地址，然后流量在core datapath中将使用PhysicalIPAddress进行交换与路由，其处理逻辑都由OVX完成，而不需要上交tenant的控制器。只有在边缘端口处才会通过重写IP的方式，将数据的IP换成租户定义的IP，从而实现网络的通信。这一点应该得到重视，这是OVX虚拟化的核心部分。

###Networks

Network基类，包含了switchSet，linkSet等成员，储存了整个网络的信息。同时和其他的基类一样，也会派生两个子类：PhysicalNetwork和OVXNetwork

PhysicalNetwork是1:1与底层基础设施对应的，并保存了真实的网络数据，包括交换机，端口，链路和网元状态等。

OVXNetwork面向租户描述了网络的状况。OVX为每一个租户维持了一个OVXNetwork的类，并通过唯一的tenantId来映射到底层的网络设施。同时这个唯一的tenantId将出现在OVXNetwork中所有的交换机，端口以及链路等数据结构中，从而使得OVX能够根据这个ID来识别OpenFlow消息的正确翻译和转发。

###Shared Global Mappings

OVX保存着物理网络和租户网络之间的映射关系表，其存储在全局共享的OVXMap的结构中。其包含的Map表如下所示：

<table class="table-bordered table-striped table-condensed">
    <tr>
        <td><strong>HashMap</strong></td>
		<td><strong>Key</strong></td>
		<td><strong>Values</strong></td>
    </tr>
	<tr>
		<td>virtualSwitchMap</td>
		<td>OVXSwitch</td>
		<td>PhysicalSwitches</td>
	</tr>
	<tr>
		<td>physicalSwitchMap</td>
		<td>PhysicalSwitch</td>
		<td>Map(TenantID,OVXSwitch)</td>
	</tr>
	<tr>
		<td>virtualLinkMap</td>
		<td>PhysicalLink</td>
		<td>Map(TenantID,OVXLink)</td>
	</tr>
	<tr>
		<td>routetoLinkMap</td>
		<td>SwitchRoute</td>
		<td>PhysicalLinks</td>
	</tr>
	<tr>
		<td>phyLinktoRouteMap</td>
		<td>PhysicalLink</td>
		<td>SwitchRoutes using PhysicalLink, keyed on TenantID</td>
	</tr>
	<tr>
		<td>networkMap</td>
		<td>TenantID</td>
		<td>OVXNetwork</td>
	</tr>
	<tr>
		<td>physicalIPMap</td>
		<td>PhysicalIPAddress (as String)</td>
		<td>OVXIPAddress</td>
	</tr>
	<tr>
		<td>virtualIPMap</td>
		<td>OVXIPAddress</td>
		<td>PhysicalIPAddress</td>
	</tr>
	<tr>
		<td>macMap</td>
		<td>MACAddress (as String)</td>
		<td>Tenant ID as integral value</td>
	</tr>
</table>

###Messages

面向租户的的数据流量需要隔离，同样的，交换机到租户控制器的OpenFlow消息也需要隔离。在这个过程中，OVX扮演着中继或者代理角色。接收交换机的消息，并保存到对应的OF的数据结构中，然后将对应字段做映射，如xid,保证上行的OF消息能准确地送到正确的租户控制器，也需要保证接受到的多个租户控制器的消息能够反向翻译成下行正确的数据，发送给对应的交换机。从而实现OF信道的完整性和隔离性。转换之后的消息保存在OVX开头的数据结构中，与OF开头的消息数据结构相对应。在这个转换的过程中使用到了两个接口函数：

* Virtualizable(): 处理来自底层datapath到tenant controller的消息，判定消息发送到哪一个租户控制器等功能。
* Devirtualizable()： 处理从租户控制器下发到底层datapath的消息，并将由OVXSwitch里的消息正确映射到PhysicalSwitch,从而完成下行信令的发送。

###后语

以上部分是我对OVX的理解，当然逻辑顺序是按照官网的内容顺序写下来的。如有错误指出，希望您能给我宝贵意见！后续的还有一片专门讲内部如何实现的，对应官网文档第三部分。另外，我的小伙伴@北邮-张歌完成了这些官网文档的翻译，阅读可到：www.sdnlab.com
