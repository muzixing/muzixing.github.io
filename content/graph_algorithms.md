title:Graph algorithms: Prim,Kruskal, Dijkstra, Floyd
tags:graph algorithm
date:2015/5/31
category:Tech

最近有了一点点空闲时间，想想以后的项目肯定是需要用到图中的路径算法，于是花了一些时间把4大经典算法实现了一遍。算法实现水平不高，时间复杂度都太高了一点。但是逻辑相对比较清晰，测试结果正确。如果读者发现算法中的问题，敬请指出，万分感谢。

###Prim

[Prim](http://zh.wikipedia.org/wiki/%E6%99%AE%E6%9E%97%E5%A7%86%E7%AE%97%E6%B3%95)算法是最小生成树算法的一种，其算法逻辑为：

从单一顶点开始，普里姆算法按照以下步骤逐步扩大树中所含顶点的数目，直到遍及连通图的所有顶点。
输入：一个加权连通图，其中顶点集合为V，边集合为E；

初始化：Vnew = {x}，其中x为集合V中的任一节点（起始点），Enew = {}；
重复下列操作，直到Vnew = V：

1：在集合E中选取权值最小的边（u,v），其中u为集合Vnew中的元素，而v则是V中没有加入Vnew的顶点（如果存在有多条   满足前述条件即具有相同权值的边，则可任意选取其中之一）；
2：将v加入集合Vnew中，将（u, v）加入集合Enew中；

输出：使用集合Vnew和Enew来描述所得到的最小生成树。

算法实现采用数据结构为邻接矩阵,实现如下：

```python
    def prim(graph, root):
        assert type(graph)==dict
    
        nodes = graph.keys()
        nodes.remove(root)
        
        visited = [root]
        path = []
        next = None
    
        while nodes:
            distance = float('inf') 
            for s in visited:
                for d in graph[s]:
                    if d in visited or s == d:
                        continue
                    if graph[s][d] < distance:
                        distance = graph[s][d]
                        pre = s
                        next = d
            path.append((pre, next))
            visited.append(next)
            nodes.remove(next)
    
        return path
    
    
    if __name__ == '__main__':
        graph_dict = {  "s1":{"s1": 0, "s2": 2, "s10": 3, "s12": 4, "s5":3},
                        "s2":{"s1": 1, "s2": 0, "s10": 4, "s12": 2, "s5":2},
                        "s10":{"s1": 2, "s2": 6, "s10": 0, "s12":3, "s5":4},
                        "s12":{"s1": 3, "s2": 5, "s10": 2, "s12":0,"s5":2},
                        "s5":{"s1": 3, "s2": 5, "s10": 2, "s12":4,"s5":0},
        }
    
        path = prim(graph_dict, 's12')
        print path
```

###Kruskal
[Kruskal](http://zh.wikipedia.org/wiki/%E5%85%8B%E9%B2%81%E6%96%AF%E5%85%8B%E5%B0%94%E6%BC%94%E7%AE%97%E6%B3%95)是另一种最小生成树的算法，相比Prim算法，Kruskal算法采用避圈法进行最小树生长。算法逻辑为：

1：新建图G，G中拥有原图中相同的节点，但没有边
2：将原图中所有的边按权值从小到大排序
3：从权值最小的边开始，如果这条边连接的两个节点于图G中不在同一个连通分量中，则添加这条边到图G中
4：重复3，直至图G中所有的节点都在同一个连通分量中

实现代码如下：

```python
    def kruskal(graph):
        assert type(graph)==dict
    
        nodes = graph.keys()   
        visited = set()
        path = []
        next = None
    
        while len(visited) < len(nodes):
            distance = float('inf') 
            for s in nodes:
                for d in nodes:
                    if s in visited and d in visited or s == d:
                        continue
                    if graph[s][d] < distance:
                        distance = graph[s][d]
                        pre = s
                        next = d
    
            path.append((pre, next))
            visited.add(pre)
            visited.add(next)
    
        return path
    
    
    if __name__ == '__main__':
        graph_dict = {  "s1":{"s1": 0, "s2": 6, "s10": 3, "s12": 4, "s5":3},
                        "s2":{"s1": 1, "s2": 0, "s10": 4, "s12": 3, "s5":4},
                        "s10":{"s1": 2, "s2": 6, "s10": 0, "s12":3, "s5":4},
                        "s12":{"s1": 1, "s2": 5, "s10": 2, "s12":0,"s5":2},
                        "s5":{"s1": 3, "s2": 5, "s10": 7, "s12":4,"s5":0},
        }
    
        path = kruskal(graph_dict)
        print path
```

###Dijkstra

[Diikstra](http://zh.wikipedia.org/wiki/%E6%88%B4%E5%85%8B%E6%96%AF%E7%89%B9%E6%8B%89%E7%AE%97%E6%B3%95)算法是用于计算某源点到其他节点的最短路径的算法。其算法逻辑为：

这个算法是通过为每个顶点 v 保留目前为止所找到的从s到v的最短路径来工作的。初始时，原点 s 的路径长度值被赋为 0 （d[s] = 0），若存在能直接到达的边（s,m），则把d[m]设为w（s,m）,同时把所有其他（s不能直接到达的）顶点的路径长度设为无穷大，即表示我们不知道任何通向这些顶点的路径（对于 V 中所有顶点 v 除 s 和上述 m 外 d[v] = ∞）。当算法结束时，d[v] 中存储的便是从 s 到 v 的最短路径，或者如果路径不存在的话是无穷大。 Dijkstra 算法的基础操作是边的拓展：如果存在一条从 u 到 v 的边，那么从 s 到 v 的最短路径可以通过将边（u, v）添加到尾部来拓展一条从 s 到 v 的路径。这条路径的长度是 d[u] + w(u, v)。如果这个值比目前已知的 d[v] 的值要小，我们可以用新值来替代当前 d[v] 中的值。拓展边的操作一直运行到所有的 d[v] 都代表从 s 到 v 最短路径的花费。这个算法经过组织因而当 d[u] 达到它最终的值的时候每条边（u, v）都只被拓展一次。
算法维护两个顶点集 S 和 Q。集合 S 保留了我们已知的所有 d[v] 的值已经是最短路径的值顶点，而集合 Q 则保留其他所有顶点。集合S初始状态为空，而后每一步都有一个顶点从 Q 移动到 S。这个被选择的顶点是 Q 中拥有最小的 d[u] 值的顶点。当一个顶点 u 从 Q 中转移到了 S 中，算法对每条外接边 (u, v) 进行拓展。

算法实现如下：

```python
    def dijkstra(graph,src):
        length = len(graph)
        type_ = type(graph)
        if type_ == list:
            nodes = [i for i in xrange(length)]
        elif type_ == dict:
            nodes = graph.keys()
    
        visited = [src]
        path = {src:{src:[]}}
        nodes.remove(src)
        distance_graph = {src:0}
        pre = next = src
    
        while nodes:
            distance = float('inf')
            for v in visited:
                 for d in nodes:
                    new_dist = graph[src][v] + graph[v][d]
                    if new_dist <= distance:
                        distance = new_dist
                        next = d
                        pre = v
                        graph[src][d] = new_dist
    
    
            path[src][next] = [i for i in path[src][pre]]
            path[src][next].append(next)
    
            distance_graph[next] = distance
    
            visited.append(next)
            nodes.remove(next)
    
        return distance_graph, path
    
    
    if __name__ == '__main__':
        graph_list = [   [0, 2, 1, 4, 5, 1],
                [1, 0, 4, 2, 3, 4],
                [2, 1, 0, 1, 2, 4],
                [3, 5, 2, 0, 3, 3],
                [2, 4, 3, 4, 0, 1],
                [3, 4, 7, 3, 1, 0]]
    
        graph_dict = {  "s1":{"s1": 0, "s2": 2, "s10": 1, "s12": 4, "s5":3},
                        "s2":{"s1": 1, "s2": 0, "s10": 4, "s12": 2, "s5":2},
                        "s10":{"s1": 2, "s2": 1, "s10": 0, "s12":1, "s5":4},
                        "s12":{"s1": 3, "s2": 5, "s10": 2, "s12":0,"s5":1},
                        "s5":{"s1": 3, "s2": 5, "s10": 2, "s12":4,"s5":0},
        }
    
        distance, path = dijkstra(graph_list, 2)
        #print distance, '\n', path
        distance, path = dijkstra(graph_dict, 's1')
```

###Floyd

[Floyd](http://zh.wikipedia.org/wiki/Floyd-Warshall%E7%AE%97%E6%B3%95)是一种计算图中所有点到其他点最短路径的算法。与Dijkstra算法相比，可以允许边值为负数。算法逻辑如下：

设D_{i,j,k}为从i到j的只以(1..k)集合中的节点为中间节点的最短路径的长度。

若最短路径经过点k，则D_{i,j,k}=D_{i,k,k-1}+D_{k,j,k-1}；
若最短路径不经过点k，则D_{i,j,k}=D_{i,j,k-1}。

因此，D_{i,j,k}=\mbox{min}(D_{i,j,k-1},D_{i,k,k-1}+D_{k,j,k-1})。

代码实现如下：

```python
    def floyd(graph):
        length = len(graph)
        path = {}
    
        for i in xrange(length):
            path.setdefault(i, {})
            for j in xrange(length):
                if i == j:
                    continue
    
                path[i].setdefault(j, [i,j])
                new_node = None
    
                for k in xrange(length):
                    if k == j:
                        continue
    
                    new_len = graph[i][k] + graph[k][j]
                    if graph[i][j] > new_len:
                        graph[i][j] = new_len
                        new_node = k
                if new_node:
                    path[i][j].insert(-1, new_node)
    
        return graph, path
    
    def floyd_dict(graph):
        length = len(graph)
        path = {}
    
        for src in graph:
            path.setdefault(src, {})
            for dst in graph[src]:
                if src == dst:
                    continue
                path[src].setdefault(dst, [src,dst])
                new_node = None
    
                for mid in graph:
                    if mid == dst:
                        continue
    
                    new_len = graph[src][mid] + graph[mid][dst]
                    if graph[src][dst] > new_len:
                        graph[src][dst] = new_len
                        new_node = mid
                if new_node:
                    path[src][dst].insert(-1, new_node)
    
        return graph, path
    
    
    if __name__ == '__main__':
        ini = float('inf')
        graph_list = [   [0, 2, 1, 4, 5, 1],
                [1, 0, 4, 2, 3, 4],
                [2, 1, 0, 1, 2, 4],
                [3, 5, 2, 0, 3, 3],
                [2, 4, 3, 4, 0, 1],
                [3, 4, 7, 3, 1, 0]]
    
        graph_dict = {  "s1":{"s1": 0, "s2": 2, "s10": 1, "s12": 4},
                        "s2":{"s1": 1, "s2": 0, "s10": 4, "s12": 2},
                        "s10":{"s1": 2, "s2": 1, "s10": 0, "s12":1},
                        "s12":{"s1": 3, "s2": 5, "s10": 2, "s12":0},
        }
    
        #new_graph, path= floyd_dict(graph_dict)    
        new_graph, path = floyd(graph_list)
        print new_graph, '\n\n\n', path
```

###总结

这几个算法都是图论中的经典算法，会在网络应用中经常用到。然而我的实现只是最简单逻辑的实现，并没有考虑太多性能上的问题。如果需要追求性能，我想还是需要谷歌一下，或者到Github上随意挑选。获取代码可点击链接：[graph algorithms](https://github.com/muzixing/graph_algorithm)。
