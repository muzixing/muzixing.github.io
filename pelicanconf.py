#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'muzi'
SITENAME = u'Code the world'
SITEURL ='http://www.muzixing.com'
TIMEZONE = 'Asia/Shanghai'


RELATIVE_URLS = True
DEFAULT_DATE_FORMAT = '%Y-%m-%d'
DEFAULT_LANG = u'zh'
ARCHIVES_URL = 'archives.html'
ARTICLE_URL = 'pages/{date:%Y}/{date:%m}/{date:%d}/{slug}.html'
ARTICLE_SAVE_AS = 'pages/{date:%Y}/{date:%m}/{date:%d}/{slug}.html'

# Feed generation is usually not desired when developing
FEED_DOMAIN = SITEURL
#FEED_ALL_RSS = 'feed.xml'
#FEED_MAX_ITEMS = 20
FEED_RSS = 'feeds/all.rss.xml'
CATEGORY_FEED_RSS ='feeds/%s.rss.xml'
#FEED_ALL_ATOM = None
#CATEGORY_FEED_ATOM = None
#TRANSLATION_FEED_ATOM = None



THEME = 'tuxlite_tbs'
GOOGLE_ANALYTICS = 'UA-45955656-1'
GOOGLE_CUSTOM_SEARCH_SIDEBAR = '012982755945402637510:n-kn9yflnfu'

DISQUS_SITENAME = 'muzixinggithubio'
PLUGIN_PATH = u"pelican-plugins"
PLUGINS =['sitemap']
SITEMAP = {
	"format":"xml",
	"priorities":{
		"articles":0.7,
		"indexes":0.5,
		"pages":0.3
	},
	"changefreqs":{
		"articles":"monthly",
		"indexes":"daily",
		"pages":"monthly",
	}
}
# Blogroll
LINKS =  (('sdnap', 'http://www.sdnap.com/'),
		  ('Richardzhao', 'http://www.richardzhao.me/'),
          ('Kimi Yang', 'http://ikimi.net/'),)

# Social widget
SOCIAL = (('github', 'https://github.com/muzixing'),
          (u'qzone', 'http://350959853.qzone.qq.com'),)

DEFAULT_PAGINATION = 5

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
