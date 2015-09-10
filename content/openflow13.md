title:OpenFlow1.3学习笔记
date:2014/8/10
tags:openflow
category:Tech

##前言

OpenFlow1.3比1.0版本复杂太多了。由于交换机和控制器没有太多支持，所以关于OpenFlow的应用大多是基于1.0版本的，但是1.3版本相当经典，其中许多内容都是值得学习的。今天翻看了一下1.3版本的OF协议，觉得收获颇多，将学习笔记写下来加深印象，也给后人学习提供一点帮助吧。笔记不是协议翻译，只总结一些疑难点。

##OpenFlow端口

OF端口是OF处理流程和网络其他部分进行转发数据包的网络接口。
OF交换机通过OF接口和其他交换机建立逻辑连接。OF交换机必须支持的端口类型为

* 物理端口
* 逻辑端口
* 保留端口

逻辑端口和物理端口的不同在于，逻辑端口比物理端口更高一级，是对物理端口的虚拟化，提高可复用性，逻辑端口的数据包需要有tunnel_id，而物理端口没有。	

 保留端口中又分为：

* ALL
* CONTROLLER
* TABLE
* IN_PORT
* ANY
* LOCAL
* NORMAL
* FLOOD

其中所有OF交换机都要支持ALL,CONTROLLER,TABLE,IN_PORT,ANY类型端口，OF_ONLY不要求支持LOCAL,NORMAL,FLOOD端口。

##OpenFlow Table

OpenFlow Table分为255级，最低级为0.

一条flow entry的结构为：

<table class="table-bordered table-striped table-condensed">
    <tr>
        <td>Match Fields</td>
		<td>Priority</td>
		<td>Counters</td>
		<td>Instructions</td>
		<td>Timeouts</td>
		<td>Cookie</td>
    </tr>
</table>

此处有一个区别于1.0版本的instruction,	用于修改动作及或者处理流程，作用于各级流表之间。匹配过程可查看协议。

###Miss_table

每一个flow\_table都需要支持table\_miss，table_miss明确了如何处理未匹配的流，动作可能是DROP,也有可能是其他。

table\_miss flow entry 并不是缺省存在与流表中的。我们可通过控制器随时进行添加或删除。

##Group Table

Group Table不是一个Flow Table。他是一个动作组的集合。一个动作组称之为group entry。它的结构如下：

<table class="table-bordered table-striped table-condensed">
    <tr>
        <td>Group Identifier</td>
		<td>Group Type</td>
		<td>Counters</td>
		<td>Action Buckets</td>
    </tr>
</table>

当flow entry中有ofp_action_group时，将指明该flow entry选择执行的group table的ID。结构为：

	/* Action structure for OFPAT_GROUP. */
	struct ofp_action_group {
		uint16_t type; /* OFPAT_GROUP. */
		uint16_t len; /* Length is 8. */
		uint32_t group_id; /* Group identifier. */
	};

###Group Type

* all:执行action buckets中所有的动作。适用于multicast or broadcast forwarding。

* select:选择其中若干组执行，适用于Load balancing。可以简单轮询，也可以根据权重执行。

* indirect：只执行group中的一个bucket,这个组只支持一个bucket,允许多流表和组表指到这个组。可用于链路聚合（link aggregation)，支持快速的，高效的收敛。

* fast failover：选择第一个活跃的bucket执行。可以在不询问控制器的情况下改变转发决策。但是要使用这个，还需要制定一个bucket的生存机制。可用于动态的负载均衡。

##Instructions和Action的区别

1.0版本中没有instruction。而在1.3中，instruction又和action有一些相似之处。仔细阅读之后发现两者是不一样的。instructions作用于流表之间，用于控制processing和修改action set。可以说是action的生产指令。而action则是对数据包修改的动作。

###Instruction

instructions的类型有：

* (Optional)Meter meter_id:将数据包直接交给某一个meter.
 
* (Optional)Apply-Actions actions(s):在不修改action set的情况下立即应用actions中的action。
 
* (Optional)Clear-Actions:立即清除action set中的所有action

* (Required)Write-Actions actions(s):立即向action set中添加action，若已存在，覆盖，否则添加。

* (Optional)Write-Metadata metadata/mask:添加metadata

* （Required）Goto-table next\_tale\_id:跳转到下一个table,跳转对象id必须大于当前的，也就是说不可以跳回来。最后一个table必然不存在这个指令。

* (Optional)Experimenter:用于试验 

###Action

* Action set 

	每一个数据包都有一个action set,用于记录action。在processing中，action set在流表之间传递。

* Action list
	
	集合和列表的区别显而易见。Apply-action和Packet_out消息包含action_list。因为这两者执行的动作是可重复的。如多个action_output.

* Actions

	* Required **Out\_put**
	* Optional **Set\_queue**
	* Reqiured **Drop**
	* Reqiured **Group**指明动作类型为group.从而流表选择group中的action bucket。
	* Optional **Push\_Tag/Pop\_Tag**
	* Optional **Set\_Field**
	* Optional **Change\_TTL**
	
	具体细节可查看协议，不再赘述。
 

##Multicle Controller

在1.3版本的OF中支持多控制器。但是这个多控制器只是相对于交换机而已。因为OF协议只是定义了交换机和控制器之间的通信过程。具体的控制器协同工作内容不是OF的范围。也许我可以开发一个这样的协议哦！

在多控制器内容中，相对于交换机而言，控制器可以有3中身份：equal,master和slave。控制器可以在任何时候改变角色。

###Equal

Equal表明这个控制器并没有什么特殊之处，他和其他同样为equal的控制器是同等级的。比如一个交换机连接了3个控制器，且这三个控制器都是equal属性，那么这三个控制器对于交换机而言是等价的。equal类型控制器相当于一个独立的，具有完全权限的控制器。


###Master and Slave

* Master

	**Master角色具有和Equal一样的完全权限。**

	当多控制器中某一个控制器申请成为Master时，其他控制器将成为Slave角色。

* Slave

	**作为Slave角色的控制器对交换机仅有可读权限,不能接受异步消息**
	
	（除去port\_status以外的其他异步等消息）
	
	不能向交换机发送写消息（ofp\_flow\_mod等），若交换机收到slave控制器发送的写消息，将产生ERROR。	

##Mininet启动1.3版本OF

	sudo mn --topo single,3 --mac --controller remote --switch ovsk,protocols=OpenFlow13

从以上可知，启动1.3版本的命令是protocols=OpenFlow13,但是这只是启动了mininet的1.3版本，还需要对交换机进行配置。命令如下： 

	ovs-vsctl set bridge s1 protocols=OpenFlow13

查看1.3版本的流表命令为：

	sudo ovs-ofctl dump-flows s1 -O OpenFlow13

##OpenFlow教程

	http://archive.openflow.org/wk/index.php/OpenFlow_Tutorial

##后语

OF1.3内容实在太多，目前博主还未使用1.3版本进行实验，所以了解不多，若文中出现不正确的地方，欢迎在评论中指出。希望我能给你一些帮助。
