## Scrapy分布式爬虫项目

### 项目介绍
- 1.中文日报网文章爬取


- 2.bilibili专栏爬取  


- 3.cnblog博客爬取  


- 4.zhihu问答爬取  



### 项目实现的功能
 - 1.通过异步io实现全量快速爬取


 - 2.通过scrapy_redis实现分布式爬取


 - 3.使用redis调度器，实现爬虫的暂停和恢复


 - 4.集成selenlium实现模拟登录，并获取动态网页


 - 5.搭建cookie池并储存到reids，定时检查cookies池的有效性，并使用线程池管理


 - 6.通过中间件实现随机获取url请求头


 - 7.爬取免费ip代理网站搭建ip代理池，并集成到scrapy中实现随机获取ip代理


 - 8.通过bloomfilter方法对bitmap方法进行改进，多重hash函数降低冲突，节省内存的同时，实现url去重


 - 9.通过scrapy_redis优先级队列实现增量抓取


 - 10.scrapy对接mysql，实现数据存储

## 相关项目
- [CookieService](https://github.com/akkoaya/CookieService)

- [LcvSearch](https://github.com/akkoaya/LcvSearch)
