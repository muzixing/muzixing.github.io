date:2013-11-29
title:【原创】scapy简单教程
category:Tech
tags:scapy


如果你是网络研究的爱好者，有一个工具是对你很有用的，那就是scapy!

scapy能够封装出目前网络上绝大多数（不确定是不是全部）的数据包，如IP，ARP,ICMP。有了这些数据包，你再也不需要为如何产生某些数据包而烦恼了。

###首先我们需要先安装scapy

具体可以自行google,baidu,或者查看：http://www.secdev.org/projects/scapy/doc/installation.html

###构建一个简单的IP包

	ip_paket = IP(dst = '10.0.0.1')

这样你就可以构造出一个IP包了。括弧里面填写的内容就是相关字段的内容。

###查看字段

如果你想知道有那些字段，那么你就需要用到ls()命令。如：

	ls（IP）
 
运行结果：

![ls](http://e.hiphotos.bdimg.com/album/s%3D550%3Bq%3D90%3Bc%3Dxiangce%2C100%2C100/sign=a1592a2c0cf41bd5de53e8f161e1f0f6/d31b0ef41bd5ad6e0183a9ed83cb39dbb6fd3cbb.jpg?referer=d6124b2ee9c4b7456d8382267c5a&x=.jpg)

ls在scapy中可以直接对任何结构体进行解析。可以把数据包的内容展现在你面前。


#####我们还可以直接查看某一个字段


![view](http://c.hiphotos.bdimg.com/album/s%3D550%3Bq%3D90%3Bc%3Dxiangce%2C100%2C100/sign=2b5a4b2cb251f819f525034fea8f3bd0/b21bb051f81986182432228348ed2e738bd4e644.jpg?referer=1ab2a90a249759ee134755fb425a&x=.jpg)
 
Payload为数据包的净荷，可以由以下的代码可以查看payload。

![PAYLOAD](http://a.hiphotos.bdimg.com/album/s%3D550%3Bq%3D90%3Bc%3Dxiangce%2C100%2C100/sign=ee699c54f4246b607f0eb271dbc36b71/6a63f6246b600c33d7241ccf184c510fd9f9a15c.jpg?referer=fd54aeb5b0b7d0a222de31ad0f32&x=.jpg)
	
我们继续感受一下scapy的便捷。
 
#####我们也可以看看scapy的封装解封装能力！
 
![packet](http://h.hiphotos.bdimg.com/album/s%3D550%3Bq%3D90%3Bc%3Dxiangce%2C100%2C100/sign=fc0780c7f536afc30a0c3f6083229af9/79f0f736afc37931f51d4b2ee9c4b74543a91144.jpg?referer=5649b43f6c061d95245102085f5b&x=.jpg)

#####数据包的发送与接收：

 ![send](http://d.hiphotos.bdimg.com/album/s%3D550%3Bq%3D90%3Bc%3Dxiangce%2C100%2C100/sign=7f8a8529d01b0ef468e8985bedff20e7/7c1ed21b0ef41bd5762625f353da81cb39db3d44.jpg?referer=a279f262b119ebc4996f43a97b5b&x=.jpg)

我们可以发现第一次发送的时候，在选路过程中，收到了27个数据包回复。接下来就越来越少，最后只剩下一个了。
 ![type](http://e.hiphotos.bdimg.com/album/s%3D550%3Bq%3D90%3Bc%3Dxiangce%2C100%2C100/sign=15a850b1cb177f3e1434fc0840f44afa/a686c9177f3e67090d5d87f839c79f3df8dc555c.jpg?referer=1067c2cde4cd7b89b07b0fb39332&x=.jpg)
我们可以看到是echo_reply的类型。


原创作品，转载请说明。
