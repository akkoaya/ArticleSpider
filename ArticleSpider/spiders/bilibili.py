import scrapy
from scrapy.http import Request
from ..items import BiliItem
import re
from scrapy.loader import ItemLoader
import json

class BilibiliSpider(scrapy.Spider):
    name = "bilibili"
    allowed_domains = ["bilibili.com"]
    start_urls = ["https://api.bilibili.com/x/article/recommends?cid={0}&pn=1&ps=10000"]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Encoding":"gzip"
    }

    def start_requests(self):
        for x in range(1,28):
            yield scrapy.Request(url=self.start_urls[0].format(x), headers=self.headers, dont_filter=True)


    def parse(self, response):
        data = json.loads(response.text)
        pass
        for re in data['data']:
            url = re['view_url']
            title = re['title']
            date = re['publish_time']
            writer = re['author']['name']
            cv_number = 'cv'+str(re['id'])
            main_content =re['summary']
            yield Request(url=re['view_url'], meta={'url':url,'title':title,'date':date,'writer':writer,'cv_number':cv_number,'main_content':main_content},callback=self.parse_detail,
                          headers=self.headers)


    def parse_detail(self, response):
        item_loader = ItemLoader(item=BiliItem(), response=response)

        views_num = re.findall(r'\"view\":(\d+),', response.text)
        like_num = re.findall(r'\"like\":(\d+),', response.text)
        comments_num = re.findall(r'\"reply\":(\d+),', response.text)
        item_loader.add_value("url", response.meta['url'])
        item_loader.add_value("title", response.meta['title'])
        item_loader.add_value("date", response.meta['date'])
        item_loader.add_value("writer", response.meta['writer'])
        if 'article-tags' in response.text:
            item_loader.add_css("tags", "div.article-tags a::text")
        else:
            item_loader.add_value("tags", '无')
        item_loader.add_value("cv_number", response.meta['cv_number'])
        item_loader.add_value("views_num",views_num)
        item_loader.add_value("likes_num",like_num)
        item_loader.add_value("comments_num",comments_num)
        item_loader.add_value("main_content", response.meta['main_content'])
        bili_item = item_loader.load_item()

        yield bili_item


