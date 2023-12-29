import scrapy
from scrapy.http import Request
from urllib import parse
from ..items import CnblogItem
from ..utils.common import get_md5
import datetime
import re
from scrapy.loader import ItemLoader
from scrapy_redis.spiders import RedisSpider


class CnblogSpider(scrapy.Spider):
    name = "cnblog"
    allowed_domains = ["www.cnblogs.com"]
    start_urls = ["https://www.cnblogs.com/sitehome/p/1"]
    # redis_key = 'cnblog:start_urls'

    next_url = "https://www.cnblogs.com/sitehome/p/{0}"
    # headers = {
    #     "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    # }

    def parse(self, response):

        all_urls = response.css('div.post-list a::attr(href)').extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]

        for url in all_urls:
            match_obj = re.match('(.*.cnblogs.com/(.*)/p/.*.html)',url)
            if match_obj:
                request_url = match_obj.group(1)
                writer_id = match_obj.group(2)
                yield Request(url=request_url,meta={'writer_id':writer_id},callback=self.parse_detail)

        for x in range(2,100):
            yield Request(url=self.next_url.format(x), callback=self.parse)

    def parse_detail(self,response):
        item_loader = ItemLoader(item=CnblogItem(), response=response)

        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_css("title", 'span[role="heading"]::text')
        item_loader.add_css("date", "span#post-date::text")
        item_loader.add_value("writer_id", response.meta['writer_id'])
        item_loader.add_css("views_num","span#post_view_count::text")
        item_loader.add_css("comments_num", "span#post_comment_count::text")
        item_loader.add_css("main_content", "div#cnblogs_post_body")

        blog_item = item_loader.load_item()

        yield blog_item
        pass