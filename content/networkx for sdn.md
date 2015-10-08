title:SDN应用路由算法实现工具之Networkx
tags:SDN,networkx
category:Tech
date:2015/9/28

SDN(Software Defined Networking)是一种新型的网络架构，通过集中式的控制平面管理数据层面的转发等操作。网络的联通性是最基础的需求，为保证网络联通性，控制器需要应用相应的图论算法，计算出转发路径，完成数据转发。在开发SDN应用时，为完成基础的路径计算，时常需要开发者独立编写网络算法，不仅麻烦，性能和代码可复用性还受开发者个人编程水平影响。所以本篇文章将介绍网络算法工具networkx，用于完成路径算法开发工作。

[networkx](https://networkx.github.io/)是用于创建、操作和研究复杂网络动态、结构和功能的Python语言包。networkx支持创建简单无向图，有向图和多重图（multigraph）；内置了许多标准的图论算法，节点可为任意数据，如图像文件；支持任意的边值维度，功能丰富，简单易用。

由于Networkx代码经过多次测试，性能方面也做了很多的工作，使用Networkx内置的多种图论算法能给开发SDN应用带来很多的便利，可以节省开发时间，降低代码故障率。networkx的安装和使用，读者可从[官网文档](http://networkx.github.io/documentation/networkx-1.9.1/index.html#)中快速得到，不加赘述。接下来的内容将简要介绍Networkx的经典图论算法内容， 包括[最短路径](http://networkx.github.io/documentation/networkx-1.9.1/reference/algorithms.shortest_paths.html), [KSP(K Shortest Paths)](http://networkx.github.io/documentation/networkx-1.9.1/reference/generated/networkx.algorithms.simple_paths.all_simple_paths.html)算法和[Traversal(遍历)算法](http://networkx.github.io/documentation/networkx-1.9.1/reference/algorithms.traversal.html)BFS（Breadth First Search）/DFS(Depth First Search)。

##最短路径算法Dijkstra和Floyd

计算单源到其他所有节点的最短路径的Dijkstra算法和计算所有节点之间最短路径的Floyd算法是最经典的网络算法之一。在networkx中对于二者的实现将在介绍如下。

###Dijkstra

无论有向图还是无向图均可以使用的Dijkstra算法， G为networkx生成的图数据结构。source为起点，target为终点。起点、终点和权重均为可选参数。

    networkx.shortest_path(G, source=None, target=None, weight=None)
  
  **无权图**

    networkx.single_source_shortest_path(G, source[, cutoff])
    
**有权图**

    networkx.dijkstra_path(G, source, target, weight='weight')
    
###Floyd

对于Floyd算法，有无权图和有权图两种实现：

**无权图**

    networkx.all_pairs_shortest_path(G[, cutoff])

**有权图**

    networkx.all_pairs_dijkstra_path(G[, cutoff, weight])

对于路径的长度的计算可以调用network.XXX_length函数获得，XXX为对应的路径计算算法名称。除了以上提到的几个算法以外，networkx还针对很多需求设计了变种的函数，如返回同样长度的多条最佳路径算法等，读者可根据需求自定义学习内容。

##K-Shortest paths

在研究网络路由算法/转发算法时，除了使用跳数作为计算最优路径的标准以外，还会使用到很多其他的指标，如带宽，时延等，也有可能根据多种指标，建立多维度评价系统，计算加权值，从而计算最佳路径。例如，当涉及到带宽为标准时，计算量就会很大。首先，获取网络链路的剩余带宽数据，然后从源头开始，选途径路径中带宽最大的路径。由于一条链路中的最大剩余带宽取决与剩余带宽最小的那一条，若使用贪心算法逐跳排除，很可能计算错误，所以每遇到一个分支就需要选择一个路径，并保存其他未选择的路径数据。每一个节点都需要对所有的数据进行对比，从而选择当下最优的路径，直至所有的链路都比较完成。这样的算法可以通过修改Dijkstra算法完成，逻辑不困难，但效率并不高，具体实现不加赘述，读者可查看笔者在网上找到的一个介绍文章:[基于SDN的最短路径算法(迪杰斯特拉)dijkstra](http://www.0x94.com/doc/0o3dyiZgX_3k94OWp.html)。

在研究的过程中，发现许多论文提的方法都是基于拓扑信息算法K条最短路径，然后在根据带宽计算最优路径。根据算法可以直接在这K条中选择最大的路径最为最优，也可以设置权重，计算跳数和带宽的加权值，再选择最优。由于跳数的数值和带宽的数值相差甚远，所以二者均需进行归一化/正则化。

考虑跳数的原因在于：每经过一个交换机，消耗的资源就多一份，所以需要考虑在内。举例：路径A带宽100M，跳数为2； 路径B带宽110M，跳数为5,若按照带宽选择则选择B，然而B经过的路径是A的若干倍，消耗的资源更多，产生的传输时延，以及传播时延（假设跳数为5的链路长度大于2， 否则不成立）也更多，所以综合考虑A可能是更好的路径。

传统的KSP算法很多，Yen, Jin Y于1971年发表的论文 "Finding the k Shortest Loopless Paths in a Network"中提出的[Yen's algorithm](https://en.wikipedia.org/wiki/Yen%27s_algorithm)就是经典算法之一，读者可直接查看点击[Yen's algorithm](https://en.wikipedia.org/wiki/Yen%27s_algorithm)的wiki。其算法思想并不复杂，基本思想为：

* Dijkstra选择第1条最优路径， 保存为A[0]
* 外循环，k从1到k。 内循环，以第k-1条（前一条）最优路径为路径，从该路径的第一个点开始作为分叉节点，分叉节点之前的为前一条最优路径与当前路径一致的部分，称之为rootpaths；将分叉点上已选的最优路径分支去掉（权值设置为正无穷），然后再运算dijkstra,将路径计算结果放到临时数据结构B中，随着循环的进行，分叉点不断前进，直至终点前一跳，内循环比较，已选出多条潜在的最优路径。
* 对临时数据结构B中的路径进行排序，找到最优路径，添加到A数据结构中， 存为A[k], 外循环一轮结束。
* 外循环继续，直至找到K条最优路径。

Networkx已经实现了KSP算法，该算法patch于2015年4月份左右才加入networkx项目，由于networkx中all\_shrtest\_paths名字已被使用，所以新加入的算法在networkx中对应函数命名为[all_simple_pay](http://networkx.github.io/documentation/networkx-1.9.1/reference/generated/networkx.algorithms.simple_paths.all_simple_paths.html)，具体参数如下所示：
    
    all_simple_paths(G, source, target, cutoff=None)

其中G为networkx的图数据结构，source为起点，target为终点，cutoff为搜索深度，只返回路径长度短于cutoff的路径。为优化性能，函数返回值为一个generator(生成器)， 读者可通过for循环，生成对应的K shortest paths。采用generator可以逐次计算结果，而不会一次运算全部结果都写入内存，可以大大降低内存使用

##Traversal

在某些网络应用场景中，会使用到遍历算法，如BFS（Breadth First Search）/DFS(Depth First Search)算法， networkx已经定义好的对应函数，具体内容由于篇幅限制，不再介绍。读者可查看networkx官方文档中关于[遍历](http://networkx.github.io/documentation/networkx-1.9.1/reference/algorithms.traversal.html)的文档进行学习。

##总结

在开发SDN应用中，网络联通性是最基本的需求。在开发网络应用时，可采用networkx来保存网络数据，计算路径等，可大大提高开发效率。在学习的过程中，从不断自己造轮子，到逐渐使用成熟的开源软件，接触了很多工具，学习到了很多有用的知识。自己造的轮子很多时候，性能，适用度以及接口的稳定读都是很大的考验，逐渐尝试优秀的开源工具将成为我在未来编程学习的方向。






