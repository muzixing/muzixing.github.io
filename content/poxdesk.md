date:2013-11-29
title:［原］poxdesk实现拓扑显示
category:Tech
tags:SDN,Openflow

###POXDESK实现拓扑的显示

今天实习第二天，开始深入逐渐玩POX跟mininet！之前只是会基本的操作，慢慢的要更加了解！今天早上就实现了一下poxdesk的功能！

####操作步骤如下：

	git clone https://github.com/noxrepo/pox
	cd pox
	git checkout betta
	cd ext
	git clone https://github.com/MurphyMc/poxdesk
	cd poxdesk
	wget http://downloads.sourceforge.net/qooxdoo/qooxdoo-2.0.2-sdk.zip
	unzip qooxdoo-2.0.2-sdk.zip
	mv qooxdoo-2.0.2-sdk qx
	cd poxdesk
	./generate.py
	cd ../../..
	./pox.py samples.pretty_log web messenger messenger.log_service messenger.ajax_transport openflow.of_service poxdesk


按照步骤去操作就可以安装poxdesk了！但是还需要注意的是：

#####1：打开POX的时候需要打开discovery.py所以最后一句应该为：

	./pox.py samples.pretty_log web messenger messenger.log_service messenger.ajax_transport openflow.of_service poxdesk poxdesk.discovery

Samples.pretty.log是一个组件，可以让pox开启的时候有字体有颜色，不添加也可以，但是界面比较难看。

#####2:mininet需要打开，并与pox 连接：
	Sudo mn –controller=remote,ip=127.0.0.1,port=6633
127.0.0.1是本机的IP，端口号默认6633，可不写
为了画出跟更好看，更复杂的拓扑，我们需要在命令之后加上这样一句话：

	--topo=tree,n,m

即为：

	Sudo mn –controller=remote,ip=127.0.0.1,port=6633 --topo=tree,n,m

n为层级，m为每一个层级下面有几个孩子

#####3：建立完连接之后，在浏览器中登录http://127.0.0.1:8000/poxdesk .


![poxdesk](http://h.hiphotos.bdimg.com/album/s%3D550%3Bq%3D90%3Bc%3Dxiangce%2C100%2C100/sign=146a5049c88065387feaa416a7e6d079/b17eca8065380cd7165a77eaa344ad3459828175.jpg?referer=49627d21fffaaf51ddf4b48fef2b&x=.jpg)


点击网页左下角的图标pox,可以打开许多小框。

![poxdesk_1](http://a.hiphotos.bdimg.com/album/s%3D550%3Bq%3D90%3Bc%3Dxiangce%2C100%2C100/sign=29f290f839c79f3d8be1e4358a9abc2c/71cf3bc79f3df8dc31cf5a96cf11728b461028c3.jpg?referer=ef7cef1340a7d933e6bfd04388c1&x=.jpg)

![topo](http://f.hiphotos.bdimg.com/album/s%3D550%3Bq%3D90%3Bc%3Dxiangce%2C100%2C100/sign=d527662f347adab439d01b46bbefc221/8718367adab44aed034d6be3b11c8701a18bfbb2.jpg?referer=74d0dd5a57fbb2fb6d3c6d224550&x=.jpg)
