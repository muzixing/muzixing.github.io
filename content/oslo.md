title:RYU学习:Oslo
date:2014/12/19
tags:ryu,oslo
category:Tech

前段时间开始认真看了一下RYU的源码，发现OSLO是一个非常方便的命令行解析库，可以用于CLI和CONF的解析。oslo是[OpenStack](https://wiki.openstack.org/wiki/Oslo)发起的项目，全称为OpenStack Common Libraries,是OpenStack Projects共享的基础库。

###Oslo

在RYU的目录下可以找到cfg.py文件，这个文件中import了oslo的相关模块，以便调用时减少引用数目。从文件中可以发现oslo.config.cfg文件是关键文件，其在系统中的文件位置在：/usr/local/lib/python2.7/dist-packages/oslo/config/cfg.py。想查看源码的读者可以自行查看。在该cfg.py文件中 定义了ConfigOpts类，包含了_opts, _groups等成员变量。该类完成了命令行和配置参数的解析。

如果要快速学习某一个知识，最好的办法就是把它用起来。所以首先我会介绍一个入门的教程。如果你没有看懂，可以去看原始的[教程](http://www.giantflyingsaucer.com/blog/?p=4822)。

首先安装[python-virtualenv](https://virtualenv.pypa.io/en/latest/virtualenv.html)，此python库可以用于创建一个虚拟的，与外界隔离的运行环境，听起来和docker好像有点像。

	sudo apt-get install python-virtualenv
	virtualenv example-app
	cd example-app
	source bin/activate
	pip install oslo.config
	touch app.py
	touch app.conf

然后修改app.conf。添加了两个group:simple和morestuff。simple组中有一个BoolOpt:enable。morestuff组有StrOpt, ListOpt, DictOpt, IntOpt,和FloatOpt。

	[simple]
 
	enable = True
 
	[morestuff]
 
	# StrOpt
	message = Hello World
 
	# ListOpt
	usernames = ['Licheng', 'Muzixing', 'Distance']
 
	# DictOpt
	jobtitles = {'Licheng': 'Manager', 'Muzixing': 'CEO', 'Distance': 'Security Guard'}
 
	# IntOpt
	payday = 20
 
	# FloatOpt
	pi = 3.14

修改app.py文件。首先定义两个group，再对两个group的option进行定义。最后使用register_group和register_opts函数来完成group和option的注册。



	from __future__ import print_function
	from oslo.config import cfg
 
 
	opt_simple_group = cfg.OptGroup(name='simple',
	                         title='A Simple Example')
 
	opt_morestuff_group = cfg.OptGroup(name='morestuff',
	                         title='A More Complex Example')
 
	simple_opts = [
	    cfg.BoolOpt('enable', default=False,
	                help=('True enables, False disables'))
	]
 
	morestuff_opts = [
	    cfg.StrOpt('message', default='No data',
	               help=('A message')),
	    cfg.ListOpt('usernames', default=None,
	                help=('A list of usernames')),
	    cfg.DictOpt('jobtitles', default=None,
	                help=('A dictionary of usernames and job titles')),
	    cfg.IntOpt('payday', default=30,
	                help=('Default payday monthly date')),
	    cfg.FloatOpt('pi', default=0.0,
	                help=('The value of Pi'))
	]
 
	CONF = cfg.CONF
 
	CONF.register_group(opt_simple_group)
	CONF.register_opts(simple_opts, opt_simple_group)
 
	CONF.register_group(opt_morestuff_group)
	CONF.register_opts(morestuff_opts, opt_morestuff_group)
 
 
	if __name__ == "__main__":
	    CONF(default_config_files=['app.conf'])
	    print('(simple) enable: {}'.format(CONF.simple.enable))
	    print('(morestuff) message :{}'.format(CONF.morestuff.message))
	    print('(morestuff) usernames: {}'.format(CONF.morestuff.usernames))
	    print('(morestuff) jobtitles: {}'.format(CONF.morestuff.jobtitles))
	    print('(morestuff) payday: {}'.format(CONF.morestuff.payday))
	    print('(morestuff) pi: {}'.format(CONF.morestuff.pi))

完成之后，运行app.py文件。可以查看到相关输出。

回到RYU中，之前一篇[博客](http://www.muzixing.com/pages/2014/12/10/ryuxue-xi-eventlet.html)介绍了RYU的main函数。在ryu/ryu/cmd/manager.py文件中我们可以看到如下的代码：

	CONF.register_cli_opts([
	    cfg.ListOpt('app-lists', default=[],
	                help='application module name to run'),
	    cfg.MultiStrOpt('app', positional=True, default=[],
	                    help='application module name to run'),
	    cfg.StrOpt('pid-file', default=None, help='pid file name'),
	])

以上的注册了三个Option，其中的app-lists和app参数是运行ryu-manager时的参数，即APP的名称。在以下的main函数中，我们可以看到首先获取了输入的参数，若参数为空，则默认开启ofp_handler应用。

	def main(args=None, prog=None):
	    try:
	        CONF(args=args, prog=prog,
	             project='ryu', version='ryu-manager %s' % version,
	             default_config_files=['/usr/local/etc/ryu/ryu.conf'])
	    except cfg.ConfigFilesNotFoundError:
	        CONF(args=args, prog=prog,
	             project='ryu', version='ryu-manager %s' % version)

	    log.init_log()

	    if CONF.pid_file:
	        import os
	        with open(CONF.pid_file, 'w') as pid_file:
	            pid_file.write(str(os.getpid()))
            
	    app_lists = CONF.app_lists + CONF.app
	    # keep old behaivor, run ofp if no application is specified.
	    if not app_lists:
	        app_lists = ['ryu.controller.ofp_handler']

oslo模块使用能够使得整个工程的不同模块可以使用同一个配置文件，从而减少了命令冲突的可能，此外，oslo提供的模板，可以让命令解析更方便。在oslo.config之外，还有oslo.db,oslo.messaging等。

###Argparse

oslo模块中使用了[argparse](https://docs.python.org/2/howto/argparse.html)。argparse是python标准库中的模块。以下以一个简单例子介绍此模块，更详细的中文教程，可以查看[《Python中的命令行解析工具介绍》](http://lingxiankong.github.io/blog/2014/01/14/command-line-parser/)。

在argparse模块中定义了ArgumentParser类。我们可以调用该类的add_argument函数添加参数。其函数说明如下：

	ArgumentParser.add_argument(name or flags...[, action][, nargs][, const][, default][, type][, choices][, required][, help][, metavar][, dest])

从以上说明可以看出，add_argument函数可以添加action, type, choices，help等重要的属性。具体参数解释，引用自[《Python中的命令行解析工具介绍》](http://lingxiankong.github.io/blog/2014/01/14/command-line-parser/)如下：

* name or flags - 参数的名字.

* action - 遇到参数时的动作，默认值是store。store_const，表示赋值为const；append，将遇到的值存储成列表，也就是如果参数重复则会保存多个值; append_const，将参数规范中定义的一个值保存到一个列表；

* count，存储遇到的次数；此外，也可以继承argparse.Action自定义参数解析；

* nargs - 参数的个数，可以是具体的数字，或者是?号，当不指定值时对于Positional argument使用default，对于Optional argument使用const；或者是*号，表示0或多个参数；或者是+号表示1或多个参数.

* const - action和nargs所需要的常量值.

* default - 不指定参数时的默认值.

* type - 参数的类型.

* choices - 参数允许的值.

* required - 可选参数是否可以省略(仅针对optionals). 

* help - 参数的帮助信息，当指定为argparse.SUPPRESS时表示不显示该参数的帮助信息.

* metavar - 在usage说明中的参数名称，对于必选参数默认就是参数名称，对于可选参数默认是全大写的参数名称. 

* dest - 解析后的参数名称，默认情况下，对于可选参数选取最长的名称，中划线转换为下划线.


使用案例举例如下：

	
	#filename:prog.py
	import argparse
	parser = argparse.ArgumentParser()
	
	# parser.add_argument("echo", help="Print the arguments.")
	
	parser.add_argument("-v", "--verbosity", default=0,
	                    action="count", help="increase output verbosity.")
	parser.add_argument("x", type=int, help="the base")
	parser.add_argument("y", type=int, help="the exponent")
	
	#parser.add_argument("square", help="Return square of given number.", type=int)
	
	args = parser.parse_args()
	answer = args.x**args.y
	
	if args.verbosity >= 2:
	    print "{} to the power {} equals {}".format(args.x, args.y, answer)
	elif args.verbosity >= 1:
	    print "{}^{} =={}".format(args.x, args.y, answer)
	else:
	    print answer

可以通过一下命令运行prog.py去查看到相关信息：

	python prog.py -h
	python prog.py
	python prog.py  2 5 -v
	python prog.py  2 5 -vv

###总结

每一个项目都会有自己的CLI或者配置文件，而使用oslo可以简化命令解析的问题。比自己使用sys.argv手动写解析要更高效且优雅。所以推荐大家在工程中使用oslo。后续会继续推出RYU学习系列文章，希望能在记录自己学习过程的同时，给其他人提供更多的帮助。自己对OpenStack没有了解，文中有不正确之处敬请指出，谢谢了！希望在不久的将来能学习OpenStack的Neutron。


