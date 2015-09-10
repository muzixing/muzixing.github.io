title:Docker部署SDN环境
date:2014/12/3
tags:Docker, sdn,RYU
Category:Tech

###前言

5月份的时候，当我还是一个大学生的时候，有个网友问我，你有研究Docker吗？当时我连Docker是什么都不知道。谷歌之后，对Docker产生兴趣，但是一直没有时间去学习。这个周终于将这个学习计划列入了Todolist。所以我花了3天时间，认真地把这[《Docker 从入门到实践》](http://dockerpool.com/static/books/docker_practice/index.html)看完并实践了一遍，收获颇丰。虽然我的导师以及我自己还是觉得我在瞎转，而且我觉得没有方向的日子很痛苦。所以只好自己做计划，学习点新知识，打打基础了。本篇内容主要介绍什么是Docker、Docker简单入门以及如何使用Docker部署SDN环境，以及docker的网络配置等内容。What is Docker和Why Docker部分摘自《Docker从入门到实践》。

###[What is Docker](https://www.docker.com/whatisdocker/)

Docker 是一个开源项目，诞生于 2013 年初，最初是 dotCloud 公司内部的一个业余项目。它基于 Google 公司推出的 Go 语言实现。 项目后来加入了 Linux 基金会，遵从了 Apache 2.0 协议，项目代码在 GitHub 上进行维护。Redhat 已经在其 RHEL6.5 中集中支持 Docker；Google 也在其 PaaS 产品中广泛应用。

Docker 项目的目标是实现轻量级的操作系统虚拟化解决方案。Docker 的基础是 Linux 容器（LXC）等技术。(新版本已修改，并不使用LXC技术)

下面的图片比较了 Docker 和传统虚拟化方式的不同之处，可见容器是在操作系统层面上实现虚拟化，直接复用本地主机的操作系统，而传统方式则是在硬件层面实现。

![](http://dockerpool.com/static/books/docker_practice/_images/virtualization.png)

![](http://dockerpool.com/static/books/docker_practice/_images/docker.png)

图1：Docker和虚拟机对比

###[Why Docker](http://dockerpool.com/static/books/docker_practice/introduction/why.html)

首先，Docker 容器的启动可以在秒级实现，这相比传统的虚拟机方式要快得多。 其次，Docker 对系统资源的利用率很高，一台主机上可以同时运行数千个 Docker 容器。

容器除了运行其中应用外，基本不消耗额外的系统资源，使得应用的性能很高，同时系统的开销尽量小。传统虚拟机方式运行 10 个不同的应用就要起 10 个虚拟机，而Docker 只需要启动 10 个隔离的应用即可。

具体说来，Docker 在如下几个方面具有较大的优势。

####更快速的交付和部署

对开发和运维（devop）人员来说，最希望的就是一次创建或配置，可以在任意地方正常运行。

开发者可以使用一个标准的镜像来构建一套开发容器，开发完成之后，运维人员可以直接使用这个容器来部署代码。 Docker 可以快速创建容器，快速迭代应用程序，并让整个过程全程可见，使团队中的其他成员更容易理解应用程序是如何创建和工作的。 Docker 容器很轻很快！容器的启动时间是秒级的，大量地节约开发、测试、部署的时间。

####更高效的虚拟化

Docker 容器的运行不需要额外的 hypervisor 支持，它是内核级的虚拟化，因此可以实现更高的性能和效率。

####更轻松的迁移和扩展

Docker 容器几乎可以在任意的平台上运行，包括物理机、虚拟机、公有云、私有云、个人电脑、服务器等。 这种兼容性可以让用户把一个应用程序从一个平台直接迁移到另外一个。

####更简单的管理

使用 Docker，只需要小小的修改，就可以替代以往大量的更新工作。所有的修改都以增量的方式被分发和更新，从而实现自动化并且高效的管理。


###Docker简单入门

谷歌出来的教程实在太多了。所以我也不打算太多介绍，只讲一些我觉得对于网络研究人员而言比较有用的命令。

####基本概念

镜像（Image）:镜像是一个只读模板。用户上传制作好的镜像供其他人下载使用。用户可以基于镜像去创建Container。
容器（Container）:容器可以理解为一个隔离起来的linux环境，用于运行应用，Namespace可以帮助你理解。
仓库（Repository）:如果你会使用Git/Github的话，不难理解，就是用于存放镜像的场所。

####Docker安装

本文的实验环境是Ubuntu14.04-amd64。非常需要注意的一点是，目前**Docker只支持64位机器**。Ubuntu14.04安装方式有两种：1）通过系统自带包安装和2）通过Docker源安装。推荐第二种方式，能安装比较新的版本。

	sudo apt-get install apt-transport-https
	sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
	sudo bash -c "echo deb https://get.docker.io/ubuntu docker main > /etc/apt/sources.list.d/docker.list"
	sudo apt-get update
	sudo apt-get install lxc-docker

###获取镜像

首先，推荐到[Docker](hubhub.docke.com)注册帐号，这样可以向使用Git/Github那样使用Docker/Dockerhub。注册和登陆可通过如下命令完成：

	docker login

注册之后，可以通过如下命令进行搜索,如搜索ryu:

	docker search ryu

可以从搜索结果中的Star来确定资源的好坏，从而找到合适的images,如muzixing/ryu。然后使用如下命令，将其拉到本地：

	docker pull  muzixing/ryu

下载完成后，可以通过如下命令查看已存在的images

	docker images

![](http://ww4.sinaimg.cn/mw690/7f593341jw1emxdzs4wf6j20qp04rdh0.jpg)

图2：images


###创建容器

创建容器使用示例如下，-t=tty,  -i=interactive,  -d=debug, -p=port, --name <name>可以用于命名container。 其他的命令可以通过--help来查看。
	
	docker run -i -t --name <name> muzixing/ryu:SDN  /bin/bash

如果你需要对端口映射，或者网络配置方面的设置，还需要仔细去查看手册。举例如下：

	docker run -i -t -p  <ip>:<host port>:<container port>  --name <name> muzixing/ryu:SDN  /bin/bash

以上命令创建并运行了一个名字叫<name>的container，并且将容器内部的端口port映射到主机的某个port，完成了端口映射，允许外网访问容器。这是容器与外界通信的方式之一。如果希望永久绑定到某个固定的 IP 地址，可以在 Docker 配置文件 /etc/default/docker 中指定 DOCKER_OPTS="--ip=IP_ADDRESS"，之后重启 Docker 服务即可生效。设置网络访问的参数默认是 --icc=ture，如果--icc=false,则禁止网络访问。

查看容器：

	docker ps [-opt]

-a为全部容器。

查看打印信息可以通过：

	dokcer logs <name>

暂停容器：

	docker stop <name>

开启暂停的容器：

	docker start <name>

重启容器：

	docker restart <name>

有时候我们开启了容器，但是没有开窗口，在后台运行，可以通过一下命令进入容器：

	docker attach <name>

###部署SDN控制器RYU

首先获取镜像：

	docker pull  muzixing/ryu

然后创建容器，并将容器的6633端口绑定到主机的6633端口。

	docker run -i -t -p  0.0.0.0:6633:6633  --name ryu3.15 muzixing/ryu:SDN  /bin/bash

进入容器之后，运行ryu.

在另一个能ping通运行容器主机的机器上运行mininet.

![](http://ww2.sinaimg.cn/mw690/7f593341jw1emxf7rriqyj20k10cp75p.jpg)

图3：mininet运行图

从上图可以看出控制器IP是172.16.192.128。这个IP地址的主机网卡信息如下：

![](http://ww3.sinaimg.cn/mw690/7f593341jw1emxdzrwx4nj20k20jadkv.jpg)

图4：Host地址信息

从图上可以看出，与mininet通信的是主机（实际情况下会是某台服务器）eth0的地址。但是从下面的图中看出运行的RYU地址是172.17.0.5。为什么可以通信呢？

![](http://ww4.sinaimg.cn/mw690/7f593341jw1emxdzrkaswj20k50hqwjb.jpg)

图5：容器信息

因为做了端口映射，将主机的所有接口的6633端口的地址都转发到容器172.17.0.5的6633端口，从而完成数据通信。其实现的原理是：Docker在启动之后，会创建一个docker0的网桥,从图4可以看到。然后还会创建veth pair。其中一端挂载在网桥上，如图4的vethba5f9f3，另一端是容器的网卡eth0，此案例中是172.17.0.5的网卡。其实这相当与一个link。原理图如下：

![](http://ww3.sinaimg.cn/mw690/7f593341jw1emxfusmbzoj20l30dhmy1.jpg)

图6：Docker网络通信原理

在运行容器的主机上使用iptables命令查看nat规则：
![](http://ww4.sinaimg.cn/mw690/7f593341jw1emxf7rim1mj20jj082dh5.jpg)

图7：iptables查看NAT。


同理mininet，或者其他的应用程序也可以使用容器部署，不再赘述，读者可自行尝试。

###上传镜像

首先需要将部署了应用的容器导出为tar文件。可以使用docker export container > file 命令。举例如下：

	docker export ryu3.15 > ryu.tar	

然后使用docker import命令将其导入为镜像：

	cat ryu.tar | sudo docker import - muzixing/ryu:sdn

以上命令为读取ryu.tar 将其导入成muzixing/ryu:sdn的image。完成之后可通过docker images查看。

确保无误之后，可将其推送到Dockerhub。

	docker push muzixing/ryu

读者也可以尝试更好的自动创建方式。

###网络配置

我们完全可以将Docker理解成一个独立的主机，可以对其网络进行配置，如配置DNS，iptables等。可以通过启动时配置，也可以通过修改文件的方式配置。

	-b BRIDGE or --bridge=BRIDGE --指定容器挂载的网桥
	--bip=CIDR --定制 docker0 的掩码
	-H SOCKET... or --host=SOCKET... --Docker 服务端接收命令的通道
	--icc=true|false --是否支持容器之间进行通信
	--ip-forward=true|false --请看下文容器之间的通信
	--iptables=true|false --禁止 Docker 添加 iptables 规则
	--mtu=BYTES --容器网络中的 MTU

文件配置则如同正常的主机配置，进入到/etc/目录下，修改制定文件即可。同样的，Dokcer可以配置网络链接的网桥，可以不选择docker0网桥，而选择其他网桥，如使用brctl创建的网桥，或者使用OpenvSwitch创建的网桥，具体操作不再赘述。

###后语

工欲善其事，必先利其器。Docker可以允许我们更灵活地使用资源，并且可以很方便地迁移环境。比如以后需要安装RYU的同学就不需要再去关注，为什么six版本不够？为什么gcc报错这些问题了。只需要有一台64位的机器，然后安装docker,理论上是不会有错的。然后将镜像下载下来，创建并运行容易，就可以得到ryu控制器运行的环境。同理Nginx，Tornado和MySQL等软件也可以直接获取，而不需要自己安装配置环境。这大大加快了生产环境的部署，也显著提高了资源的利用率，个人认为将在未来对虚拟机产生强烈的冲击。


















