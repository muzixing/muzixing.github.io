title:OpenvSwitch2.3.0 and Mininet install
date:2014/11/2
tags:OVS,mininet
category:Tech

###前言

折腾了我两个周的事情是一定要写出来的，后来人就不用继续掉坑里了。在此感谢@南京-小L的帮助。

###安装OpenvSwitch2.3.0

不需要安装。但是友情提供一键安装脚本：
	
    #!/bin/bash

    # Make sure only root can run our script
    if [ "$(id -u)" != "0" ]; then
       echo "You need to be 'root' dude." 1>&2
       exit 1
    fi

    #install
    #apt-get update
    #apt-get install -y build-essential


    echo "====================INSTALL OpenvSwitch-2.3.0===================="
    #apt-get install -y   uml-utilities libtool python-qt4 python-twisted-conch debhelper python-all

    if [  -f openvswitch-2.3.0.tar.gz ]
    then 
    	echo "openvswitch-2.3.0.tar.gz has exist"
    else
    	wget http://openvswitch.org/releases/openvswitch-2.3.0.tar.gz
    fi

    if [  -d openvswitch-2.3.0 ]
    then
       rm -r openvswitch-2.3.0
    fi
    tar -xzf openvswitch-2.3.0.tar.gz

    # Install openvswitch
    cd openvswitch-2.3.0
    make clean
    ./configure --with-linux=/lib/modules/`uname -r`/build 2>/dev/null
    make && make install

    # install Open vSwitch kernel module
    insmod datapath/linux/openvswitch.ko
    make modules_install


    mkdir -p /usr/local/etc/openvswitch
    ovsdb-tool create /usr/local/etc/openvswitch/conf.db vswitchd/vswitch.ovsschema  2>/dev/null
    
    # start ovs server
    sh /usr/local/share/openvswitch/scripts/ovs-ctl restart
    
    # Also, you can start ovs server by below commands.
    #ovsdb-server -v --remote=punix:/usr/local/var/run/openvswitch/db.sock \
    #             --remote=db:Open_vSwitch,Open_vSwitch,manager_options \
    #             --private-key=db:Open_vSwitch,SSL,private_key \
    #             --certificate=db:Open_vSwitch,SSL,certificate \
    #             --bootstrap-ca-cert=db:Open_vSwitch,SSL,ca_cert \
    #             --pidfile --detach

    #ovs-vsctl --no-wait init
    #ovs-vswitchd --pidfile --detach
    ovs-vsctl show
    depmod -A openvswitch

###Mininet安装

如果以前有安装mininet，那么你需要先卸载mininet

	sudo rm -rf /usr/local/bin/mn /usr/local/bin/mnexec \
    		/usr/local/lib/python*/*/*mininet* \
    		/usr/local/bin/ovs-* /usr/local/sbin/ovs-*

	sudo apt-get remove mininet

下载最新版本的mininet

	git clone git://github.com/mininet/mininet

然后运行install.sh -options

	mininet/util/./install.sh [options]

安装的关键在options。查看详细的内容可以通过查看：

	./install.sh -h

而我们需要安装的是OpenFlow13和OpenvSwitch2.3.0,所以命令如下：

	./install.sh -n3V 2.3.0

执行，安装成功！

###后语

再次感谢sdnap群@南京-小L的信息。不然我还要折腾一阵子。然后感兴趣的朋友可以去仔细看看./install.sh -h里面的内容，-y可以装ryu!!-x可以装nox！还是非常有用的！


