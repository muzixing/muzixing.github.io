title:Script for ONOS installation
date:2015/11/02
tags:onos
category:Tech


工欲善其事，必先利其器。在部署SDN实践时，通常需要安装OVS和控制器等软件，经历过的同学都知道，很多是时候会被一些细节卡住，影响生产效率。有时由于实验需要还需要多次部署同样的内容，重复敲多遍同样的命令，浪费时间。所以很有必要将安装过程转化为一键安装脚本。本文总结的一键安装脚本就是在部署ONOS集群时，为提高安装ONOS效率而整理的，希望能帮助到同样需要多次安装ONOS的其他人。

###安装脚本

安装脚本将安装ONOS及其依赖软件的所有命令都写到了shell文件，并加一些必要判断语句，使得安装脚本使用起来更加人性化。需要注意的是，此文件仅完成了ONOS的安装，并没有完成ONOS启动之前的配置，需要启动相关服务，还需手动进行配置。脚本内容如下所示：

```sh
    #!/bin/bash
    #make sure only root can run our script.
    if [ "$(id -u)" != "0" ]; then
       echo "You need to be 'root' dude." 1>&2
       exit 1
    fi
    
    _version="1.0"
    
    echo "========================INSTALL ONOS======================="
    
    # Download and unzip apache-karaf
    if [ -d /root/Applications ]
    then 
    	cd /root/Applications
    else
    	mkdir /root/Applications
    	cd /root/Applications
    fi
    
    if [ -f apache-karaf-3.0.2.tar.gz ]
    then 
    	echo "apache-karaf-3.0.2.tar.gz has exist"
    else 
    	wget http://apache.fayea.com/karaf/3.0.2/apache-karaf-3.0.2.tar.gz
    	tar -xzf apache-karaf-3.0.2.tar.gz
    fi
    
    # Download and install apache-maven
    
    if [ -f apache-maven-3.2.5-bin.tar.gz ]
    then
    	echo "apache-maven-3.2.5.bin.tar.gz has exist"
    else 
    	wget http://mirror.bit.edu.cn/apache/maven/maven-3/3.2.5/binaries/apache-maven-3.2.5-bin.tar.gz
    	tar -xzf apache-maven-3.2.5-bin.tar.gz
    	mv apache-maven-3.2.5 /usr/local/apache-maven
    
    	# set environment
    	echo "export M2_HOME=/usr/local/apache-maven" >> /etc/profile
    	source /etc/profile
    	echo "export PATH=$PATH:$M2_HOME/bin" >> /etc/profile
    	source /etc/profile
    	# in case of failure of setting environment
    	export PATH=$PATH:$M2_HOME/bin
    fi
    
    # Install java-8-oracle
    
    if which java
    then 
    	echo "java-8 has been installed."
    else
            apt-get install python-software-properties
    	sudo add-apt-repository ppa:webupd8team/java -y
    	sudo apt-get update
    	sudo apt-get install oracle-java8-installer oracle-java8-set-default -y
    	# set JAVA_HOME
    	echo "export JAVA_HOME=/usr/lib/jvm/java-8-oracle" >> /etc/profile
    	source /etc/profile
    fi
    # show the info of java and maven to check.
    
    java -version
    mvn --version
    
    # Download ONOS
    if [ -d /home/onos ]
    then 
    	cd /home/onos
    else
    	mkdir /home/onos
    	cd /home/onos
    fi
    
    if which zip
    then 
    	echo "zip has been installed"
    else
    	apt-get install zip
    fi
    
    if [ -f onos-$_version.zip ] 
    then 
    	echo "onos-$_version.zip has exist"
    else
    	wget https://github.com/opennetworkinglab/onos/archive/onos-$_version.zip
    	unzip onos-$_version.zip
    
    	# set environment of ONOS
    
    	echo "export ONOS_ROOT=/home/onos/onos-onos-$_version" >> /etc/profile
    	echo "export KARAF_ROOT=/root/Applications/apache-karaf-3.0.2" >> /etc/profile
    
    	source /etc/profile
    	source $ONOS_ROOT/tools/dev/bash_profile
    fi
    # Build ONOS
    
    cd onos-onos-$_version/
    mvn clean install
```

Note: 若需下载其他版本ONOS，直接修改**下载源码部分和ONOS_ROOT**即可，无需修改Karaf，maven，java8等内容。

###初始化配置

在安装完ONOS之后，还需要进行一些必要的配置，才能启动运行了制定服务的ONOS。需要编辑$KARAF_ROOT/etc/org.apache.karaf.features.cfg文件，脚本中即为/root/Applications/apache-karaf-3.0.2/etc/org.apache.karaf.features.cfg。 在该文件中的 featuresRepositories部分和featuresBoot部分分别添加如下内容：

    featuresRepositories：mvn:org.onosproject/onos-features/1.0.0/xml/features（逗号隔开，加到最后即可）
    featuresBoot：onos-api,onos-core-trivial,onos-cli,onos-openflow,onos-app-fwd,onos-app-mobility,onos-gui

更多逐步安装和初始化配置内容可以查看SDNLAB的文章[《Ubuntu14.04源码安装ONOS》](http://www.sdnlab.com/4603.html)

###下载地址

脚本下载地址为：[muzixing/onosinstallhelper](https://github.com/muzixing/onosinstallhelper)。在github/muzixing上还有[muzixing/ovsinstallhelper](https://github.com/muzixing/ovsinstallhelper), 和fork过来的[ryuinstallhelper](https://github.com/muzixing/ryuInstallHelper)可供下载，可以大大减少重复安装OVS和控制器时的重复劳动，提高生产效率。
