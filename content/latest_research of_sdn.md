title:SDN最新研究进展
date:2016/6/28
tags:sdn
category:Tech


自SDN出现以来，关于SDN的研究一直没有停止，只是不同的阶段关于SDN的研究的重点不同。比如最开始的时候，探讨最多的是SDN的可行性，以及如何将SDN应用到对应的网络场景中。本文是笔者在最近阅读2015年至今的若干SDN论文后总结的SDN最新研究进展，希望对读者提供一些帮助。

###  SDN/NFV

SDN和NFV都是当下网络界研究的热点，而如何将两者整合部署，也是研究的热点之一。设计SDN/NFV整合部署框架的研究是这个研究方向的主要研究切入点之一，比如参考文献[1]中就提出了一个SDN/NFV的整体架构。框架中的NFV协调器可以和云管理平台配合使用，SDN控制器也支持与云平台结合。由于此类方案是SDN与其他技术/框架的集合，本身没有太多创新性，论文中也仅仅介绍了其实现方案，所以此处不加赘述。

SDN/NFV结合还可以部署在很多场景，比如WiFi场景。OpenSDWN[2]就是一种软件定义的家庭/企业WiFi架构框架。 将SDN与其他技术结合并应用在特定网络场景是一种主要的研究方向之一。

### 流表优化

OpenFlow所支持的细粒度流管理是SDN最大的优势之一，但是细粒度的管理是需要付出代价的。为满足细粒度的管理，则需要更粒度的流表项。但是像OpenFlow协议这种细粒度的管理会带来一定的时延，对于时延敏感的短流业务而言，这个时延带来的影响是不可忽视的，这很可能会抵消了SDN带来的好处。所以如何通过流表来匹配流，从而减少流表项下发次数，是降低时延影响的有利手段。

此外，当网络流数目过多时，交换机的流表空间就无法满足需求。当流表满时，为了下发新的流表项，就需要将其他活跃的流表项删除，这会让更多的数据包转发给控制器，从而增加了控制器的负担，还也带来了更大的时延，也会发生数据包丢弃现象。对于大象流而言，等待下发流表项的时延并没有太大的影响。但是，对于短流而言，特别是对时间敏感的短流而言，时延的影响就很明显。为了避免这种情况出现，很有必要对流表项进行聚合优化。

OpenFlow协议支持通过通配符的方式来将数据流进行聚合，从而将多条流聚合成一条流来进行处理，比如交换机可以将目的IP为10.0.3.0/16的数据包都统一处理，发送到端口1，而不是对每一个IP都下发一条流表项。这种通配符的方式大大减少了流表项的数目。但是，通配的方式也存在问题，比如使用通配符会提高编程复杂度。为了降低使用通配流表项的难度，也为了提高性能，ReWiFlow[3]提出了限制型通配符。限制型通配符定义了完整的匹配域排序规则，使得匹配域不能任意搭配，必须按照顺序搭配。低优先级的匹配域需要在高优先级的匹配域被填充使用时才可以被使用。这样的排序限制了匹配域组合的自由度，但是却让管理流表项更容易。由于匹配域是固定顺序的，所以可以通过前缀属性来更简单地管理流表项集合。

此外，为满足更多的流表项需求，ReWiFlow还支持使用多维度、不同匹配域优先序列的流表项。在实验中，可以通过5组ReWiFlow的规则就可以描述超过1600条的ACL表项。这样的流表空间压缩率是非常可观的。

关于流表项的优化一直都是SDN/OpenFlow领域研究的热点和重点，读者可以通过ReWiFlow的参考文献顺藤摸瓜进行深入研究。

### 数据分类/流表查找

本质上，交换机将数据分类的过程也就是流表查找的过程。目前的OpenFlow支持的匹配域已经超过了40个，所以数据分类是一个漫长的过程。而且随着新技术的出现，这个匹配域将会继续增加。所以如何设计一个更高效、更具有可拓展性的分类算法来解决数据分类过程中的问题是下一阶段SDN领域的研究方向之一。

数据分类的关键问题在于提升数据查找的速度。面对超过40维度的查找，如果简单的逐维度，顺序匹配，那会带来十分高的时间复杂度。许多网络业务对时延很敏感，这种低效率的做法无法适应网络设备的要求。从算法的角度来讲，通过多次模糊查找，逐渐分类并缩小查找范围，最后再精确查找是一种可行的思路。

”Many-Field Packet Classification for Software-Defined Networking Switches“[4]论文就提出了一种可拓展的多域数据分类算法，其由选择性位连接的多维度划分来实现数据分类算法（A scalable many-field packet
classification algorithm using multidimensional-cutting via selective bit-concatenation (MC-SBC) for OpenFlow-based SDN switches）。其核心的思路是通过获取多个域的不同比特位，并将其连到一起作为key，然后具体有相同key的流规则放在一个集合中。不同的比特位选取的结果左右不同的样本空间，从而形成多维度的样本空间。在查找时，通过取不同比特位组合的key可以快速地找到样本空间，然后取样本空间的交集即为对应的分类，也就是对应的流表项。

<center>![](http://ww3.sinaimg.cn/mw690/7f593341jw1f55bvh3gohj20ft0hzmyk.jpg)</center>
<center>图1. 分类器架构图</center>
### Policies Composition/Consistency

网络中存在着许多网络策略，比如ACL和SFC。同时，网络中的策略往往是由不同人群制定的，他们可能是网络的管理员或用户，也可能是虚拟租户网的租户。不同网络使用者的决策是相互独立的，也是动态的，所以很多时候不同的策略之间会产生策略冲突。目前的策略冲突解决方案仅仅实现了运行态的冲突检测，即只有当策略被部署之后，网络在运行时发生故障，性能出现恶化时，安全漏洞等问题才暴露出来。而这只是一种冲突检测，其无法实现冲突的预防，更不能实现策略的编排，解决策略冲突。

为解决这个问题，PGA（Policy Graph Abstraction）[5]提出了使用图结构来检测来自多个用户之间的策略冲突，并实现冲突解除。PGA支持在策略下发到底层设备之前完成策略冲突检测和冲突解除，且其提供的抽象模型实现了策略与底层网络之间的解耦合，从而降低了用户在制定网络策略时的压力。PGA支持ACL以及SFC等多种策略的冲突检测和协调，其关注点只是部署策略前的检测和协调，并不关注运行态的冲突检测。通过使用大型企业网数据的测试，验证了PGA其可行性，证明了PGA不仅支持大量数据的处理，同时时延表现还很好。

此外，多控制器在协同工作的时候，还需要对数据进行同步。在没有数据同步的情况下，相互独立的控制器对交换机安装的策略都是没有经过冲突检测的，可能存在竞争和冲突，所以多控制器系统的信息同步非常有必要。交换机上发生策略冲突主要是因为控制器没有办法获取到交换机上的策略状况，无法进行策略冲突检测，所以如果能在交换机上进行策略冲突检测，就可以解决这个问题。相比通过带外方式实现的控制平面的数据同步和策略冲突检测，在交换机上实现冲突检测的办法更简单，消耗的资源更少。

“In-Band Synchronization for Distributed SDN Control Planes”[6]论文提出了通过带内方式实现的分布式控制平面的同步机制。其核心的思想是使用交换机的部分配置内存来做冲突检测，然后保证所有的事务都是原子操作，从而保障数据的一致性。当多控制器同时并发给交换机写入策略时，很可能带来竞争和冲突，所以很有必要通过加锁来实现策略写入的原子性，从而保障数据读取和修改的一致性。论文中提出了使用部分交换机的内存作为冲突检测所需的内存，用于存储那些等待执行的指令。论文还设计了“compare and set”原语集，支持命令执行的冲突检测等行为。在安装FlowMod等操作时，需要检测是否有策略冲突，若无冲突，则可以安装，否则放弃。控制器也可以通过读取状态原语来获取交换机上的配置信息，以便作出没有冲突的策略。本质上，这是一种在数据平面上保证数据一致性的解决方案。

但是，就算控制器策略计算正确，多控制器之间操作也没有冲突，也无法保证数据包在数据平面按照控制器制定的策略去处理。目前关注于控制器平面的策略正确性的研究已经很多，他们普遍努力于如何解决策略冲突，但是控制平面的正确策略不能保障数据平面的正确，所以还需要对数据平面进行监控，来保证数据平面的策略一致性。

VeriDP[7]提出了监控数据平面策略一致性的解决方案。其核心思想十分简单：控制器在计算数据转发路径的时候，将数据包头和转发路径信息映射关系存储起来；在数据平面上，交换机需要对转发的数据打标签，从而记录数据转发的路径；当数据离开网络之前，将数据包头和标签上报给VeriDP服务器；VeriDP服务器可以将报头信息和控制器存储的映射关系进行对比，若匹配成功则说明数据平面的实际表现和策略一致，否则数据平面出现了故障。选择集中式的服务器进行检验是因为单节点的交换机无法感知全局的策略，所以在数据包丢失等情况时，并不知道这是策略指导还是发生了故障，但集中的控制器掌握全局的策略，所以它的信息可以用来进行判断策略一致性。

当然，除了以上的问题，流表一致性问题也是值得研究的课题。控制器给多个交换机下发新流表时，没有办法做到同时修改，所以必然存在一个时间段，使得有的交换机的流表项已经更新，而其他的交换机还保留了原有的流表项，这就可能造成环路或者丢包的现象。为解决这一问题，“Monitoring Dynamic Modification of Routing Information in OpenFlow Networks”[8]论文提出了一种监控和分析解决方案，可以对路由信息改变时网络的行为进行监控，并对其行为进行系统整合分析，从而进行优化，减少丢包率等现象。

### 安全相关

SDN的集中控制给解决网络安全问题提供了很多方便。一直以来，网络安全都是研究的课题，当SDN出现之后，如何利用SDN去更好地解决网络安全问题成为了新的研究课题。此外，SDN本身的安全成为了新的研究课题。比如攻击者可以通过数据包返回的时间来获取到什么样的数据包会上交控制器，进而利用这一信息攻击控制器[9]。

###  Debugging/Trouble Shooting

网络与软件不同，其调试和故障排查十分复杂，所以SDN的调试和故障排查一直是研究热点。

“One Tool to Rule Them All”[10]这篇论文主要提出的是一个轻量级的框架，可以灵活组合现有的故障排查工具来实现复杂而多样的故障排查功能。由于计算机网络的分布和异构，在网络中进行故障排查一直以来都是非常困难的事情。而SDN的到来也带来了更多的问题，不仅需要检查网络的故障，控制器/VNF/交换机等软件的实现是否存在BUG也成为新的需要解决的问题。

面对这么多的问题需要排查，目前已经有了许多解决方案，比如NICE[11]等。但是这些解决方案都是针对特定的网络问题，无法全面地解决网络故障。然而在解决一个网络故障时，往往需要到多个软件组合才能完成。所以还需要一个整合平台来实现多个工具之间的灵活组合，这就是“One Tool to Rule Them All”论文的主要切入点和贡献。论文中设计了故障排除的图（Trouble Shooting Graph）来给故障排除建模。然后针对故障模型，可以配置对应的故障排除信息，从而通过调用多个工具来实现复杂的网络故障排除。

在很多网络业务场景中，需要掌握数据包的转发路径信息，从而更好地诊断网络。原有的转发路径跟踪解决方案的思路主要有带外和带内两种。基于带外的解决方案需要消耗大量的流表空间，也产生大量的带外数据，但是带外方式节省了报头的空间，没有对数据包进行额外的修改。基于带内的解决方案则对数据包头进行了修改，从而节省了大量的流表空间，也不会产生带外的开销。极端的带内解决方案是给网络中的链路独立的编号，然后将编号插入到数据包的报头，从而实现数据包转发路径的追踪，但是这样产生了过大的报头开销。

CherryPick[12]则在现有带内解决方案的基础上进行了改进。由于数据中心网络Fattree拓扑的规律性，可以通过计算关键链路来映射出完整的转发路径，从而节省报头开销。CherryPick的主要贡献是设计了一套算法，从而将报头开销降到最小，其规则如下：

* ToR: 如果ToR收到了Agg发来的数据包，而且数据包的源地址与目的地址都在同一个pod内，则ToR记录连到Agg的入口链路的ID。如果源地址和目的地址都在同一个pod内，而且不经过Agg,也即在一个ToR上，将忽略入端口。其他情况下，均不记录链路。
* Agg: 如果Agg从ToR收到数据包，且数据包的终点在同一个pod内，则入链路被选中，其他情况将不记录链路。（有的时候，数据包会在ToR和Agg中转圈，然后再到达真正的目的地）
* Core: 核心层交换机始终只挑选入链路。

在此算法之下，可以通过记录路径上的关键链路来映射出完整的数据包的转发路径，从而将报头开销降到最小。

<center>![cherrypick](http://ww1.sinaimg.cn/mw690/7f593341jw1f55bvhqp32j20nj088jue.jpg)</center>
<center>图2.CheeryPick选取关键链路示意图</center>


### SDN应用到WiFi无线场景， IOT，ADHOC等场景

SDN作为一种新的网络模式，目前正在被用于如5G网络，IOT，Ad-Hoc等网络场景，也产出了OpenSDWN等研究成果[2]。将新技术框架放在不同场景的做法是研究中最常见的做法之一，但这和SDN本身的研究并没有太大关系，所以此处不再展开，有兴趣的读者可以自行研究。
 
### Scalability

SDN的控制平面能力是有限的，当SDN的规模扩展到足够大的时候，就需要对其进行分域治理。而且出于业务场景的要求，许多大的网络的子网络分别使用着不同的网络技术，使用着不同的控制平面，所以就需要实现多控制器之间的合作。多域控制器的协同工作一直是SDN研究领域的一个大方向，但同时也是一个很艰难的方向。

STRAUSS[13]项目提出了一个解决方案。其设计了一个“控制器的控制器”作为Domain控制器的协调者，从而实现跨域端到端的通信。由于各个域采用的技术不同，所以这些异构的域在相互协同时就需要进行抽象，从而消除具体技术带来的差异性，进而让网络编排控制器统一管理。为实现控制器之间的通信，论文设计了一种COP协议（Control Orchestration Protocol）。

同样的解决思路还有OXP协议，其协议内容目前还无法公开。OXP实现的多域异构控制器之间的协调工作，提升了SDN的可拓展性。此外，其还提供了多种模式，可适应多种网络场景的具体需求。

更多的关于SDN可拓展行的研究[14]，读者可以阅读相关调研[15]。

### Fault Tolerance/Consistency

由于SDN是一种集中式的架构，所以单节点的控制器成为了整个网络的中心。当控制器产生故障或者错误时，网络就会瘫痪。为了解决控制器故障给网络带来的故障，分布式控制器等多控制器方案早就已经被提出。相比单控制器而言，多控制器可以保证高可用性(High Availability)，从而使得在某个控制器实例发生故障时，不影响整体网络的运行。另外，为保障业务不终端、不冲突，多控制器之间信息还需要保持一致性，才能实现Fault Tolerance。

当故障发生时，多控制器之间的信息一致性能为接管的控制器提供正确管理交换机的基础。然而，当前的一致性研究内容还仅仅关于控制器状态信息方面，而没有考虑到交换机的状态信息，这将导致交换机重复执行命令等问题。然而，许多操作并非幂等操作，多次操作将带来更多问题，所以不能忽略命令重新执行的问题。而且由于没有关于交换机状态的记录，交换机也无法回退到一个安全的状态起点，所以简单状态回退也是不可取的。更好的办法是记录接收事件的顺序以及处理信息的顺序及其状态。此外，还需要利用分布式系统保持全局的log信息一致性，才能让交换机在切换控制器时不会重复执行命令。

因此Jennifer教授团队提出了Ravana[16]，设计了一个拥有两个阶段的协议，用于记录事件接收顺序和事件处理顺序。当事件从交换机上报给主控制器时，主控制器会将这个事件的顺序信息记录下来，然后与从控制器同步。当交换机执行完事件的处理命令时，会返回执行完成信号给主控制器。主控制器从而结束整个事件/事务处理的周期，并将处理完成的状态信息同步给所有的从控制器，从而完成数据同步。通过这种方式，控制器可以收集到事件处理的具体状态，从而使得当控制器发生故障时，其他控制器可以精确地了解到事件处理的状态，从而继续完成事件处理。这种设计不但保障了控制器状态的一致性，也同步了交换机的状态数据，使得无论控制器还是交换机发生故障时，都不会影响到业务的正常进行，从而实现无故障的应用运行。  

### SDN与大数据

SDN与大数据等其他技术的结合也是一个研究方向。当大数据和SDN[17]结合时，SDN可以提高大数据网络的性能，而大数据的数据处理能力也可以给SDN决策提供更好的指导。由于这种研究属于应用范畴，不加赘述。

### 总结

在笔者阅读论文的时候，发现目前主要的SDN研究方向有：多控制器协同的可拓展性问题，网络调试和故障排查，策略编排，流表优化等方向。当然SDN与NFV、大数据等其他技术的结合也是一个研究方向。此外，SDN应用在各种网络场景中的研究依然层出不穷。在2015年到2016年这段时间内，还没有更多关于SDN数据平面可编程性的研究成果，其主要原因在与2014年左右的POF和P4已经走在前列，而更多的研究还来不及发表。但笔者坚信，SDN数据平面可编程性以及SDN编程语言等研究将是未来研究的一个大方向。但是这个方向门槛较高，所以研究的人员比其他方向少一些。本文是笔者最近调研成果，希望可以给读者带来一些帮助。


作者简介：

李呈，2014/09-至今，北京邮电大学信息与通信工程学院未来网络理论与应用实验室（FNL实验室）攻读硕士研究生。

个人博客：http://www.muzixing.com


### 参考文献

[1] Muñoz, R., Vilalta, R., Casellas, R., Martinez, R., Szyrkowiec, T., Autenrieth, A., … López, D. (2015). Integrated SDN/NFV Management and Orchestration Architecture for Dynamic Deployment of Virtual SDN Control Instances for Virtual Tenant Networks [Invited]. Journal of Optical Communications and Networking, 7(11), B62. http://doi.org/10.1364/JOCN.7.000B62

[2] Schulz-Zander, J., Mayer, C., Ciobotaru, B., Schmid, S., & Feldmann, A. (2015). OpenSDWN: Programmatic Control over Home and Enterprise WiFi. Sosr, 16:1–16:12. http://doi.org/10.1145/2774993.2775002

[3] Shirali-Shahreza, S., & Ganjali, Y. (2015). ReWiFlow. ACM SIGCOMM Computer Communication Review, 45(5), 29–35. http://doi.org/10.1145/2831347.2831352

[4] Hsieh, C.-L., & Weng, N. (2016). Many-Field Packet Classification for Software-Defined Networking Switches. Proceedings of the 2016 Symposium on Architectures for Networking and Communications Systems - ANCS ’16, 13–24. http://doi.org/10.1145/2881025.2881036

[5] Prakash, C., Zhang, Y., Lee, J., Turner, Y., Kang, J.-M., Akella, A., … Sharma, P. (2015). PGA: Using Graphs to Express and Automatically Reconcile Network Policies. Proceedings of the 2015 ACM Conference on Special Interest Group on Data Communication - SIGCOMM ’15, 29–42. http://doi.org/10.1145/2785956.2787506

[6] Schiff, L., Schmid, S., Kuznetsov, P., Argyraki, K., Schmid, S., & Kuznetsov, P. (2016). In-Band Synchronization for Distributed SDN Control Planes. ACM Sigcomm Computer Communication Review, 46(1), 37–43. http://doi.org/10.1145/2875951.2875957

[7] Zhang, P., Li, H., Hu, C., Hu, L., & Xiong, L. (2016). Stick to the Script: Monitoring The Policy Compliance of SDN Data Plane. Proceedings of the 12th ACM/IEEE Symposium on Architectures for Networking and Communications Systems (ANCS 2016), 81–86. http://doi.org/10.1145/2881025.2881038

[8] Yamaguchi, S., Nakao, A., Oguchi, M., Goto, A., & Yamamoto, S. (2016). Monitoring Dynamic Modification of Routing Information in OpenFlow Networks. Proceedings of the 10th International Conference on Ubiquitous Information Management and Communication - IMCOM ’16, 1–7. http://doi.org/10.1145/2857546.2857574

[9] Sonchack, J., Aviv, A. J., & Keller, E. (2016). Timing SDN Control Planes to Infer Network Configurations. Proceedings of the 2016 ACM International Workshop on Security in Software Defined Networks &#38; Network Function Virtualization, 19–22. http://doi.org/10.1145/2876019.2876030

[10] Pelle, I., Lévai, T., Németh, F., & Gulyás, A. (2015). One tool to rule them all. Proceedings of the 1st ACM SIGCOMM Symposium on Software Defined Networking Research - SOSR ’15, 1–7. http://doi.org/10.1145/2774993.2775014

[11] M. Canini, D. Venzano, P. Peresini, D. Kostic, J. Rexford, et al. A nice way to test openflow applications. In NSDI, volume 12, pages 127–140, 2012.

[12] Tammana, P., Agarwal, R., & Lee, M. (2015). CherryPick. Proceedings of the 1st ACM SIGCOMM Symposium on Software Defined Networking Research - SOSR ’15, 1–7. http://doi.org/10.1145/2774993.2775066

[13] Muñoz, R., Vilalta, R., Casellas, R., & Martínez, R. (2015). SDN orchestration and virtualization of heterogeneous multi-domain and multi-layer transport networks: The STRAUSS approach. 2015 IEEE International Black Sea Conference on Communications and Networking, BlackSeaCom 2015, 142–146. http://doi.org/10.1109/BlackSeaCom.2015.7185103

[14] Lange, S., Gebert, S., Zinner, T., Tran-Gia, P., Hock, D., Jarschel, M., & Hoffmann, M. (2015). Heuristic Approaches to the Controller Placement Problem in Large Scale SDN Networks. IEEE Transactions on Network and Service Management, 12(1), 4–17. http://doi.org/10.1109/TNSM.2015.2402432

[15] Blial, O., Mamoun, M. Ben, & Benaini, R. (2016). An Overview on SDN Architectures with Multiple Controllers, 2016.

[16] Katta, N., Zhang, H., Freedman, M., & Rexford, J. (2015). Ravana. Proceedings of the 1st ACM SIGCOMM Symposium on Software Defined Networking Research - SOSR ’15, 1–12. http://doi.org/10.1145/2774993.2774996

[17] Cui, L., Yu, F. R., & Yan, Q. (2016). When big data meets software-defined networking: SDN for big data and big data for SDN. IEEE Network, 30(1), 58–65. http://doi.org/10.1109/MNET.2016.7389832

