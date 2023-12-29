from scrapy.cmdline import  execute
import sys
import os


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

execute(['scrapy', 'crawl', 'cnblog'])
#因为在终端中调用的命令是：scrapy crawl 爬虫名称