import scrapy
from scrapy.http import Request
from urllib import parse
from ..items import ArticlespiderItem
from ..utils.common import get_md5
import datetime
import re
# from scrapy.loader import ItemLoader
from scrapy_redis.spiders import RedisSpider

class ArticleSpider(RedisSpider):
    name = "article"
    allowed_domains = ["column.chinadaily.com.cn"]
    start_urls = ["https://column.chinadaily.com.cn/allarticle/page_1.html"]
    #redis_key = 'article:start_urls'
    next_url = "https://column.chinadaily.com.cn/allarticle/page_{0}.html"

    def parse(self, response):

        all_urls = response.css('div.left-two a::attr(href)').extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]

        for url in all_urls:
            match_obj = re.match('(.*column.chinadaily.com.cn/a/.*.html)',url)
            if match_obj:
                request_url = match_obj.group(1)

                yield Request(url=request_url,callback=self.parse_detail)

        # final_url = response.css('a[stytle="text-decoration:none"]::attr(href)').extract()
        # i = int(re.findall('.*_(\d+).html',final_url)[0])

        for x in range(2,126):
                yield Request(url=self.next_url.format(x), callback=self.parse)


    def parse_detail(self,response):
        # image_url = response.css("figure img::attr(src)").extract()[0]
        title = response.css("div.dabiaoti::text").extract()[0]
        date = response.css("div.xinf-le::text").extract()[0].strip()
        writer = response.css("div.xinf-le-r::text").extract()[0].strip()
        main_content = response.css("div.article").extract()[0]
        #把date的格式转换为datetime
        date = datetime.datetime.strptime(str(date),'%Y年%m月%d日').date()  #格式为：year-month-day

        #实例化item方法
        article_item = ArticlespiderItem()

        #把值传入到items中
        article_item['url'] = response.url
        article_item['title'] = title
        article_item['date'] = date
        article_item['writer'] = writer
        article_item['main_content'] = main_content
        # article_item['image_url'] = [image_url]
        #注意：image_path的指向在pipeline中完成
        article_item['url_object_id'] = get_md5(response.url)

        # ##通过item loader加载item
        # item_loader = ItemLoader(item=ArticlespiderItem(), response=response)
        # item_loader.add_css("title", "div.dabiaoti::text")  #第一个参数就是items.py中添加的field的名称
        # item_loader.add_value("url",response.url)
        # item_loader.add_value("url_object_id",get_md5(response.url))
        # item_loader.add_css("date", "div.xinf-le::text")
        # item_loader.add_css("writer", "div.xinf-le-r::text")
        # item_loader.add_css("main_content", "div.article")
        #
        # #调用配置好的item
        # article_item = item_loader.load_item()

        #article_item传入到pipeline中
        yield article_item


