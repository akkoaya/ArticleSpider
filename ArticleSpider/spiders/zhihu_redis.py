import scrapy
import re
from urllib import parse
from scrapy.loader import ItemLoader
import json
from ..items import ZhihuQuestionItem
from ..items import ZhihuAnswerItem
import redis
from scrapy_redis.spiders import RedisSpider

class ZhihuSpider(RedisSpider):
    name = "zhihu"
    # allowed_domains = ["www.zhihu.com"]
    # start_urls = ["https://www.zhihu.com"]
    redis_key = "zhihu:start_urls"
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer':'https://www.zhihu.com/',
    }

    #需要把`feeds?`后面的`cursor`的内容手动过滤掉，到`include`为止；然后把最后的`session_id`的内容也过滤掉
    #然后在`question/`,`limit=`,`offset=`后面，一一加上占位符
    #因为offset的值实际上就是请求添加的回答数量
    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/feeds?include=&limit={1}&offset={2}&order=default&platform=desktop'

    def __init__(self, name=None, **kwargs): #一定要和scrapy.Spider这个父类里的使用方法一样
        super().__init__(name, **kwargs) #然后用super()方法把这个父类里的__init__方法执行一次
        self.redis_cli = redis.Redis(host="localhost")

    def start_requests(self):
        cookie_str = self.redis_cli.srandmember("zhihu_cookies") #随机获取cookie
        cookie_dict = json.loads(cookie_str) #转为dict格式

        return [scrapy.Request(url=self.start_urls[0],headers = self.headers, dont_filter=True, cookies=cookie_dict)]

    def parse(self, response):
        # 获取所有页面内的url，并完整化
        all_urls = response.css('a::attr(href)').extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        #进一步过滤掉不是url的内容
        all_urls = filter(lambda x: True if x.startswith('https') else False, all_urls)
        # 提取知乎问题的url
        for url in all_urls:
            match_obj = re.match('(.*zhihu.com/question/(\d+))(/|$).*',url) #`$`表示结尾符

            if match_obj:
                request_url = match_obj.group(1)
                question_id = match_obj.group(2)
                #如果满足re.match的要求，则下载页面，并交给parse_question函数处理
                yield scrapy.Request(url=request_url,meta={'question_id':question_id} ,headers=self.headers, callback=self.parse_question)
                #break 这里break出去方便调试，就不会有源源不断的请求过来
            else:
                #如果不满足，则进一步跟踪
                yield scrapy.Request(url=url,headers=self.headers, callback=self.parse)  #调试的时候也可以把这个注释掉
                #pass


    def parse_question(self, response):
        #处理question
        item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)

        item_loader.add_value("question_id", response.meta['question_id'])
        item_loader.add_css("topics", ".QuestionHeader-topics .css-1gomreu::text")
        item_loader.add_value("url", response.url)
        item_loader.add_css("title", "h1.QuestionHeader-title::text")
        # item_loader.add_css("content", 'div.css-eew49z')
        item_loader.add_css("answer_num", "h4.List-headerText span::text")
        item_loader.add_css("comments_num", "div.QuestionHeader-Comment button::text")
        item_loader.add_css("subscriber_num", "strong.NumberBoard-itemValue::text")
        item_loader.add_css("view_num", "strong.NumberBoard-itemValue::text")

        question_item = item_loader.load_item()

        yield question_item   #调试answer_item的时候可以把这个注释掉，方便看结果
        pass
        yield scrapy.Request(url=self.start_answer_url.format(response.meta['question_id'],20,0),headers=self.headers, callback=self.parse_answer)
        #这里start_answer_url记得加self调用

    #加载回答的时候是用的api接口，一个接口里面存放了5个回答的数据，而接口里面有下一个接口的链接，所以必须要先模拟一个api请求以获取第一个`下一接口链接`
    #所以先定义一个全局变量`start_answer_url`,存放第一个api的链接，可以从浏览器知乎回答页面，f12向下滑动页面，获取一个`feeds?cursor`开头的请求，这个就是qpi接口，预览里可以看到有五条回答
    def parse_answer(self, response):
        answer_data = json.loads(response.text)
        pass
        #分析这个请求网页可以看出paging下有一个is_end节点，返回一个布尔值，确认是否加载完所有的回答
        is_end = answer_data['paging']['is_end']
        #next_url是下一页回答的api请求
        next_url = answer_data['paging']['next']

        #提取answer内容
        for answer in answer_data['data']:
            #实例化item
            answer_item = ZhihuAnswerItem()

            answer_item["answer_id"] = answer['target']['id']
            answer_item["url"] = answer['target']['url']
            answer_item["question_id"] = answer['target']['question']['id']
            answer_item["author_name"] = answer['target']['author']['name'] if 'name' in answer['target']['author'] else None
            answer_item["content"] = answer['target']['content'] if 'content' in answer['target'] else answer['target']['excerpt']
            answer_item["praise_num"] = answer['target']['voteup_count']
            answer_item["comments_num"]= answer['target']['comment_count']
            answer_item["create_time"] = answer['target']['created_time']
            answer_item["update_time"] = answer['target']['updated_time']
            # answer_item["crawl_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            yield answer_item
            pass
        if is_end is False:
            yield scrapy.Request(url=next_url,headers=self.headers, callback=self.parse_answer)