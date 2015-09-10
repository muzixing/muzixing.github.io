title:QEMU+virt-manager+phoronix-test-suite服务器测试
date:2014/9/17
tag:qemu,virt-manager,phoronix
category:Tech

###前言

这是研究生开学的第一个任务，学习测试服务器性能。首先我们需要在一台新服务器上面安装ubuntu12.04，这个步骤很简单。安装完之后，可以使用top命令查看系统的cpu,mem等性能指标。然后我们就需要安装phoronix-test-suite，用于测试服务器的某些性能。接下来，使用qemu安装虚拟机，在虚拟机有负载的情况下，继续测量服务器的性能。

###PHORONIX-TEST-SUITE

这是一个相当牛逼的服务器测试工具：[phoronix-test-suite]:http://www.phoronix-test-suite.com/

下载安装：http://get.ubuntusoft.com/app/phoronix-test-suite

先将安装包下载到本地，然后解压。进入phoronix-test-suite目录，运行install_sh进行安装。

安装之后可以通过
	
	phoronix-test-suite  list-available  

查看可使用的测试列表。

选择某一个测试项进行测试

	phoronix-test-suite  benchmark <test name>

如：
	
	phoronix-test-suite  benchmark c-ray

接下来只需要按照步骤将测试结果提交给网站，你就可以通过网站查看到测试结果。若想保存测试结果页面，在chrome浏览器中打开，选择打印页面->保存页面为pdf,则可以将网页保存为pdf文件。

更多的测试工具如IOZONE等，可自行google.

###QEMU

QEMU is a generic and open source machine emulator and virtualizer.

When used as a machine emulator, QEMU can run OSes and programs made for one machine (e.g. an ARM board) on a different machine (e.g. your own PC). By using dynamic translation, it achieves very good performance.

When used as a virtualizer, QEMU achieves near native performances by executing the guest code directly on the host CPU. QEMU supports virtualization when executing under the Xen hypervisor or using the KVM kernel module in Linux. When using KVM, QEMU can virtualize x86, server and embedded PowerPC, and S390 guests.

QEMU是一套由Fabrice Bellard所编写的模拟处理器的自由软件。它与Bochs，PearPC近似，但其具有某些后两者所不具备的特性，如高速度及跨平台的特性。经由kqemu这个开源的加速器，QEMU能模拟至接近真实电脑的速度。

简单的说就是一个开源的虚拟化软件，可通过qemu创建虚拟机。

* 安装

		sudo apt-get install qemu

按照提示将依赖全部安装好即可。若不成功，可自行google.

* 创建虚拟磁盘

	qemu-img create -f qcow2 ubuntu.img 10G

创建一个10G大小的格式为qcow2的虚拟磁盘ubuntu.img，磁盘名字用户自定。 -f为format参数，格式fmt=qcow2,是qemu中最常见的格式。

* 安装虚拟机

创建完虚拟磁盘之后，需要将系统安装到这个磁盘上。

	qemu-system-x86_64 -hda ubuntu.img -cdrom ubuntu.iso -localtime -m 1024 -smp 2

参数介绍：-hda指定虚拟磁盘位置，如我们创建的ubuntu.img，-cdrom，指定光驱位置，可以是光驱，也可以是iso文件。 -localtime是本地时间。-m 指定内存， -smp指定cpu个数。

进入虚拟机有一些简单的快捷键可以进行窗口的切换。如 ctrl+alt+f 切换全屏等。

当然这是在有图形化界面的情况下。若没有图形化界面就会报错：could not initialize SDL.

这个时候我们就需要在另一台有图形化界面的linux上ssh远程登录，进行后续操作。

###SSH登录

在另一台有图形化界面的linux系统上远程登录服务器。

	ssh -X hostname@IP 

输入对应密码进入系统。然后在服务器上安装libvirt和virt-manager。

###Libvirt和Virt-manager


**libvirt**

libvirt is:

* A toolkit to interact with the virtualization capabilities of recent versions of Linux (and other OSes), see our project goals for details.
* Free software available under the GNU Lesser General Public License.
* A long term stable C API
* A set of bindings for common languages
* A CIM provider for the DMTF virtualization schema
* A QMF agent for the AMQP/QPid messaging system
* A technical meritocracy, in which participants gain influence over a project through recognition of their contributions.

more:http://libvirt.org/

我们所需要使用的virt-manager是通过libvirt来远程管理虚拟机的。

* 安装
	
	sudo apt-get install libvirt


**virt-manager**
 
 
The virt-manager application is a desktop user interface for managing virtual machines through libvirt. It primarily targets KVM VMs, but also manages Xen and LXC (linux containers). It presents a summary view of running domains, their live performance & resource utilization statistics. Wizards enable the creation of new domains, and configuration & adjustment of a domain’s resource allocation & virtual hardware. An embedded VNC and SPICE client viewer presents a full graphical console to the guest domain.

virt-manager是一个有可视化窗口的，通过libvirt管理虚拟机的管理平台。

* 安装

	sudo apt-get install virt-manager

按照提示安装完所有的依赖。

###Virt-manager管理虚拟机

virt-manager是一个远程虚拟机管理软件，可以提供可视化的操作界面来创建虚拟机和管理虚拟机。

远程登录到服务器安装完virt-manager之后，运行virt-manager

	sudo virt-manager

如果之前的ssh没有加-X参数的话，这个命令不会任何反应。加了-X参数之后，virt-manager会弹出一个运行窗口。

点击左上角的创建虚拟机，在指定步骤选择由qemu创建好的img文件和以下载的iso文件。点击确定进行安装。这一步相信不难。接下来就是普通的安装系统，这里不再赘述。

###Libvirt管理虚拟机

通过libvirt可以在不需要图形化界面的情况下管理虚拟机。这将使用到virsh。virsh是libvirt的一套shell指令。

我们通过virsh可以创建和管理虚拟机。

help: 	        显示该命令的说明

quit:	        结束 virsh，回到 Shell

connect:	        连接到指定的虚拟机服务器

create:        启动一个新的虚拟机

destroy:	        删除一个虚拟机

start:        开启（已定义的）非启动的虚拟机

define:	        从 XML 定义一个虚拟机

undefine:        取消定义的虚拟机

dumpxml:	        转储虚拟机的设置值

list:	        列出虚拟机

reboot:	        重新启动虚拟机

save:	        存储虚拟机的状态

restore:	        回复虚拟机的状态

suspend:	        暂停虚拟机的执行

resume:	        继续执行该虚拟机

dump:	        将虚拟机的内核转储到指定的文件，以便进行分析与排错

shutdown:        关闭虚拟机

setmem:	        修改内存的大小

setmaxmem:       设置内存的最大值

setvcpus:        修改虚拟处理器的数量

如关闭一个正在运行的名称为ubuntu的虚拟机：

	virsh shutdown ubuntu


**克隆虚拟机**

在创建虚拟机之后，我们还可以通过克隆虚拟机来快速创建虚拟机。实例如下：

	virt-clone --connect=qemu:///system -o template -n clone -f clone.img

其中template替换成被克隆虚拟机名称，clone替换成克隆输出的虚拟机名称，clone.img是格式化好的虚拟磁盘，可使用qemu制作。

###测试

目前位置我们已尽完成了服务器性能测试和虚拟机创建和管理，只需要重复以上工作即可完成指定要求的服务器性能测试。

###后语

至此为止我们完成了服务器测试的准备工作。在搭建环境的过程中学习到了许多有用的知识，如虚拟化技，ssh登录等等。感觉非常好玩。通过scp去拖拽文件，让我感觉网络的神奇，我在不知不觉中就被小伙伴修改了许多文件。感觉被偷了还不知道。囧囧的。scp例子如下：

	scp root@10.108.144.100:/home/root/music.mp3 /home/music/music.mp3

将10.108.144.100root用户的/home/root/music.mp3 复制到本机的home/music，命名为music.mp3。传文件的远端类似，将参数位置调换即可。

在如今云计算的时代，虚拟化技术已经是最基本的技术，有时间学一学还是很好玩的。














  

