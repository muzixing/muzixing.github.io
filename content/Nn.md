date:2013-11-29
title:N个整数，求其中任意N-1个数的乘积中的最大的一个(禁用除法)
category:Tech
tags:算法


刚才看程序员面试宝典的时候看到这个有趣的题目，也是google2007年的笔试题目。**只能用乘法，不能用除法。**

看了网上一些扯到不行算法之后，我决定把我自己的想法写一下，不一定对。

PS：好久没写C++,语法都忘了，跟python语法混乱了……哎。。

###整个问题只会有一下3种情况
*	有两个0，最大必为0。

*	数组全非负，最好办，在没有两个及以上的0的情况下，把最小的剔除即可。

*	数组有正有负，有0，最困难。

具体代码如下：

	//数组a[n]
	//——————————————————————————————————————————————
	int min1 = -65534,min2=65535,No,No_1,No_2 = 0,total=1,z_num=-1;//初始化参数；
	for(int i=0,j=0;(i<n)||(j<1);i++)
	{	
    	 if(a[i]==0)
	    {
    	    j++;
    	    z_num=i;//保留第一个0的位置，，如果两个零，第二个零	的位置也没有必要存储了。
    	}
    	if(abs(a[i])<min)//记录最小的项，并跳过
    	{
    	    min = a[i];No =i； 
    	    continue;//跳过这个最小项。
    	}
    	if(a[i]>0)//正数记最小的
    	{
    	    if(a[i]<min2)
    	    {
    	        min2=a[i],No_2=i;//记录下最小的正数据
    	    }
    	}
    	else://负数记最大的，绝对值最小
    	{
    	    if(a[i]>min1)
    	    {
    	    min1=a[i],No_1=i;//记录下最小的正数据    
    	    }
    	}
    	total = a[i]*total
	}	
	if（j==2)   //超过1个零
	{
    	return 0
	}
	elif(j==1)//只有一个零,求乘积，结果可能就是这个结果。
	{
    	total=1;//初始化
    	for(int i= 0;i<n;i++)
    	{
    	    if(i!=z_num)
    	    {
    	        total=a[i]*total;
    	    }
    	    else
    	        continue;//跳过
    	}
    	if(total>0)
    	{
    	    return total;
    	}
    	else//total<0
    	{
    	    return 0;
    	 }
	 //_____________________________________________________________    
	elif(total>0)//无零情况,这个total是第一次循环算出来的。大于0则必为最大。
	{    
    	  return total;//
	}
	else://total小于0
	{    
    	if(min<0)//最小为负数，则使用最小的正数与之交换，最小的正数为min2
    	   {
    	        total=1;
          	  	for（int i=0;i<n；i++）//求乘积
            	{   
	                if(i!=No_2)
                	{
                    	 total = a[i]*total;
                	}
                	else：
                    	continue;
            	}            
        	}
    	else://min>0,需要把最小的负数拿来交换,最小的复数为min1
    	{	
        	total=1;
        	for（int i=0;i<n；i++）//求乘积
        	{   
        	    if(i!=No_1)
        	    {
        	        total = a[i]*total;
        	    }
        	    else：
        	        continue;
        	    }
    	}	
    	return total;
	}
	//_________________________________________________finished.But it is so comlplicated! 

按道理说应该是没有错的。但是不可能这么长，所以，应该有更快，更好的方法。如果你知道的话，告诉我一下。谢谢！
