date:2014/5/4
title:nox实现nat功能
tags:sdn,openflow,nox
category:Tech

###前言

nat功能是一个非常简单，但却非常重要的功能。保留10，127,192三个网段作为公网地址，通过nat实现地址复用，可以解决现网IPV4地址不够用的尴尬局面。本篇主要讲如何使用nox实现nat的demo.

###环境

* nox  安装比较困难，请参看其他教程
* mininet    网络环境搭建神器

###控制器

首先在nox/src/coreapps/switch中找到switch.cc。
在class switch中添加成员变量uint32_t src_ip，nat_ip；由于只是一个简单的demo，就不做映射列表了。



handle\_packet\_in中将if(setup_flows && out_port!=-1)的逻辑修改如下：

    if (setup_flows && out_port != -1)
    {
        auto fm = v1::ofp_flow_mod().match(flow).buffer_id(pi.buffer_id())
                   .cookie(0).command(v1::ofp_flow_mod::OFPFC_ADD).idle_timeout(5)
                   .hard_timeout(v1::OFP_FLOW_PERMANENT)
                   .priority(v1::OFP_DEFAULT_PRIORITY);
        if (pi.in_port()== 1) //将in_port为1的数据进行nat转换
        {   
            nat_ip = uint32_t(inet_addr("10.0.168.192"));//由于机器中字节序和网络字节序不一样，所以ip为倒序，你可以使用函数将变成网络字节序
            cout<<">>nat_ip:"<<nat_ip<<endl;
            src_ip= flow.nw_src();//保存src_ip
            cout<<">>src_ip:"<<src_ip<<endl;
            auto aset = v1::ofp_action_nw_src().nw_addr(nat_ip);
            fm.add_action(&aset);//添加动作，修改数据的src_ip为nat_ip
            cout<<">>set_nw_src:"<<nat_ip<<endl;
        }

        cout<<">>flow.nw_dst:"<<flow.nw_dst()<<endl;  
        cout<<">>nat_ip:"<<nat_ip<<endl;
        if ((nat_ip!=0)&&(flow.nw_dst()==nat_ip))//若dst_ip为nat_ip，则修改为src_ip，完成对接
        {
            auto aset_dst = v1::ofp_action_nw_dst().nw_addr(src_ip);
            fm.add_action(&aset_dst);
            cout<<">>set_nw_dst:"<<src_ip<<endl;
        }
        auto ao = v1::ofp_action_output().port(out_port);
        fm.add_action(&ao);
        dp.send(&fm);
    }

最后，非常重要的一点：

**由于修改完src_ip之后，其他主机并不能接受改数据，因为arp列表中没有此项。所以需要添加静态arp。**

###主机

* 在mininet中，查看nat转换的主机的mac信息：h2 ifconfig

* 在其他主机如h3中 添加静态arp: h3 arp -s nat_ip h2_mac

此时pingall可通。

###后语

arp缓存表很重要！Openflow1.0中没有修改arp的功能，1.3才有。考虑通信需要从全局的角度考虑，不能只考虑ICMP的转换，ICMP之前的arp的转换是必不可少的过程。希望读者能从中加深对网络通信流程的理解。感谢@地球-某某老师长久支持和教导！哈哈！

###修改

台湾-linton同学提供了更好的解决方案：在nat之前，给目的主机发送arp\_request,sender\_ip为nat\_ip,以此来给目的主机添加arp信息。
只需要在下发flow_mod之前，下发一个pkt\_out，用于发送nat arp即可。不再赘述。


以上的解决方案并不完美，如果目标主机arp缓存表刷新之后，nat arp数据丢失，到达主机的数据将被丢弃。所以必须保证在发送数据之前发送arp\_request。@地球-某某 老师解决方案为：周期发送arp\_request，这能一定程度上解决这个问题。flow\_mod的周期小于arp缓存表刷新周期也能一定程度解决这个问题。解决这个问题的根本是要保证数据发送之前，发送arp\_request，以保证dst host的arp缓存表中有对应项。
