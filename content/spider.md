title:【python爬虫】抓取淘宝模特图片——20分钟爬虫之旅
date:2014/7/24
tags:python,spider
category:Tech

#前言

很多人说学Python最终需要写一个爬虫才能算是学成出山了，而我就是那个留级生，一直没有写过。炎热的夏日，以及看java的抑郁，让我无聊之中萌生了这个想法。于是在百度的帮助下，写完了这个教程。视频教程可以去百度学堂看，我就是在那里看的。

#spider

代码详解就不多加介绍，注释相信已经很明确了，请看代码。

	import urllib2
	import urllib
	import sys

	class get_mm_pic(object):
	    def __init__(self,page_num):
		self.page_num = page_num
		self.mmurl= "http://mm.taobao.com/json/request_top_list.htm?type=0&page="#抓取的链接
	    def get_pic(self):
		i = 1
		page_num = self.page_num
		temp ='''<img src="'''
		while i<page_num:
		    url = self.mmurl + str(i)
		    up = urllib2.urlopen(url)
		    cont = up.read()#读取页面内容
		    pa = j = 0
		    while True:
		        ahref = '''<a href="http'''
		        target = "target"
		        pa = cont.find(ahref)#匹配字符串
		        pt = cont.find(target, pa)
		        if pa == -1:
		            break
		        modelurl = cont[pa+len(ahref)-4: pt-2]
		        mup= urllib2.urlopen(modelurl)
		        mcont = mup.read()
	   
		        header = "<img style"
		        tail = ".jpg"
		        iph = k = 0
		        while True:
		            iph = mcont.find(header)
		            ipj = mcont.find(tail, iph)
		            if iph == -1:#匹配失败则跳出循环
		                break
		            mpic = mcont[iph : ipj + len(tail)]
		            ips = mpic.find("src")
		            urlpic = mpic[ips +len("src ="):]
		            try:
		                print ">>>downloading : lady_p"+str(i)+"_no_"+str(j)+"_pic_"+str(k)+".jpg......"
		                urllib.urlretrieve(urlpic, "lady_p"+str(i)+"_no_"+str(j)+"_pic_"+str(k)+".jpg")#下载图片
		            except KeyboardInterrupt:
		                print "SIGINT, exit..."
		                sys.exit(0)
		            except:
		                pass
		            mcont = mcont[ipj+1:]
		            k+=1
		        cont = cont[pt+1:]
		        j+=1
		    i += 1
		print ">>>download completed"
	def main(page_num):
	    get_mm_pictures = get_mm_pic(page_num)
	    print "@Author:www.muzixing.com"
	    get_mm_pictures.get_pic()

	if __name__ == '__main__':
	    main(int(sys.argv[1]))#python spider.py number

就是这么一个简单的40+行，就可以将淘女郎大量的图片下载下来了。好好欣赏吧！技术能让生活更有趣！

#后语

如果你还有什么好玩的Python项目，可以告诉我，我也想学！

