# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from urllib import parse

import scrapy
import datetime
from utils.common import get_nums,deal_nums
from models.es_types import ArticlePost,CnblogPost
from w3lib.html import remove_tags  #去除content里面的html tag
import redis

redis_cli = redis.Redis(host='localhost')
class ArticlespiderItem(scrapy.Item):
    #items.py中只有一种类型：Field类型
    url =  scrapy.Field()
    url_object_id = scrapy.Field()  #把url存为固定长度，md5
    title = scrapy.Field()
    date = scrapy.Field()
    writer = scrapy.Field()
    main_content = scrapy.Field()
    # image_url = scrapy.Field()
    # image_path = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                        insert into article(title,date,url,url_object_id,writer,main_content,)
                        values (%s,%s,%s,%s,%s,%s)
                        """
        params = (self['title'], self['date'], self['url'], self['url_object_id'], self['writer'], self['main_content'])
        return insert_sql, params

    def save_to_es(self):
        #将item转换为ES的数据
        article = ArticlePost()
        article.url = self['url']
        article.meta.id = self['url_object_id'] #用url_object_id取代ES里index的id
        article.title =  self['title']
        article.date = self['date']
        article.writer = self['writer']
        article.main_content = remove_tags(self['main_content']) #去除里面的html tag
        article.save() #保存
        return


class ZhihuQuestionItem(scrapy.Item):
    # 知乎的问题 item
    question_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    # content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    subscriber_num = scrapy.Field()
    view_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into zhihu_question(question_id,topics,url,title,answer_num,
                                        comments_num,subscriber_num,view_num,crawl_time,)
            values(%s,%s,%s,%s,%s,%s,%s,%s,%s) 
             
        """
        # ON DUPLICATE KEY UPDATE answer_num = VALUES(answer_num)
        # 上面这一行是mysql的更新语句，防止主键重复而报错，如果已经存在就更新内容，title=VALUES(title)的话，更新的内容就是title，可以添加其他更新字段
        # 因为爬取的时候是有可能会爬到同一个question的，所以主键可能会重复
        # 必须添加在values()之后

        question_id = self["question_id"][0]
        topics = ",".join(self["topics"])
        url = self["url"][0]
        title = "".join(self["title"])
        # content = "".join(self["content"])
        #utils目录下的common.py写一个专门提取数字的方法get_nums，然后给这里调用
        answer_num = get_nums(self['answer_num'][0])
        comments_num = get_nums(self['comments_num'][0])
        subscriber_num = get_nums(self['subscriber_num'][0])
        view_num = get_nums(self['view_num'][1])
        #strftime()可以把datetime格式转为str类型,后面跟自定义的格式，可以在settings.py中配置好，名称为SQL_DATETIME_FORMAT以及SQL_DATE_FORMAT
        crawl_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        params = (
        question_id, topics, url, title, answer_num, comments_num, subscriber_num, view_num, crawl_time)
        #注意这里一定要和上面的sql语句里的顺序一致
        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):
    # 知乎的回答 item
    answer_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_name = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        # 插入知乎question表的sql语句
        insert_sql = """
        insert into zhihu_answer(answer_id,url,question_id,author_name,content,praise_num,
                                    comments_num,create_time,update_time,crawl_time,)
        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
        
        """
        # ON DUPLICATE KEY UPDATE content = VALUES(content) praise_num = VALUES(praise_num)
        # 上面这一行是mysql的更新语句，防止主键重复而报错，如果已经存在就更新内容，answer_id=VALUES(answer_id)的话，更新的内容就是answer_id，可以添加其他更新字段
        # 因为爬取的时候是有可能会爬到同一个answer的，所以主键可能会重复
        # 必须添加在values()之后

        #因为create_time和update_time在原来的json里是一个int的字段，datetime.datetime.fromtimestamp()方法可以解析为datetime格式
        create_time = datetime.datetime.fromtimestamp(self['create_time']).strftime("%Y-%m-%d %H:%M:%S")
        update_time = datetime.datetime.fromtimestamp(self['update_time']).strftime("%Y-%m-%d %H:%M:%S")
        crawl_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        params = (
            self["answer_id"], self["url"], self['question_id'],
            self['author_name'], self['content'], self['praise_num'],
            self['comments_num'], create_time, update_time, crawl_time
        )
        return insert_sql, params



from elasticsearch_dsl.connections import connections #对ES进行连接

def get_suggests(index,info_tuple):  #用tuple是因为它有顺序，而且可以传递多个值
    #根据字符串生成搜索建议数组
    used_words = set() #用于去重，因为不同的字段下可能都会出现同一个关键词，而不同字段设置的权重不一样，不能把之前的覆盖了
    suggests = []
    es = connections.get_connection() #获得之前在es_types对ES进行的连接
    for text,weight in info_tuple: #引用get_suggest函数就要放入index，和(text以及weight)
        if text:
            #调用es的anlayze接口分析字符串
            #首先获取es的连接,放在全局
            #然后对anlayze进行配置
            words = es.indices.analyze(index=index, body={'analyzer':"ik_max_word",'text':text})
            pass
            analyzed_words = set([r["token"] for r in words["tokens"] if len(r["token"]) > 1]) #过滤掉单个字的关键词，并且放入set中
            new_words = analyzed_words - used_words #去除原来的词
        else:
            new_words = set()
        if new_words:
            suggests.append({"input":list(new_words),"weight":weight})

    return suggests



class CnblogItem(scrapy.Item):
    url =  scrapy.Field()
    url_object_id = scrapy.Field()
    title = scrapy.Field()
    date = scrapy.Field()
    writer_id = scrapy.Field()
    views_num = scrapy.Field()
    comments_num = scrapy.Field()
    main_content = scrapy.Field()

    def save_to_es(self):
        cnblog = CnblogPost()

        cnblog.url = self['url'][0]
        cnblog.meta.id = self['url_object_id'][0] #设置index的id为url_object_id
        cnblog.title = self['title'][0]
        cnblog.date = self['date'][0]
        cnblog.writer_id = self['writer_id'][0]
        cnblog.views_num = self['views_num'][0]
        cnblog.comments_num = self['comments_num'][0]
        cnblog.main_content = remove_tags(self['main_content'][0])
        cnblog.suggest = get_suggests("cnblog",((cnblog.title, 10),)) #注意set里面只有一个元素的时候必须加个逗号，不然不计算该元素

        cnblog.save() #保存
        redis_cli.incr('cnblog_nums')
        return

    def get_insert_sql(self):

        insert_sql = """
        insert into cnblog(url_object_id,url,title,date,writer_id,views_num,comments_num,main_content,)
        values(%s,%s,%s,%s,%s,%s,%s,%s) 

        """
        params = (
            self["url_object_id"][0], self["url"][0], self['title'][0],
            self['date'][0], self['writer_id'][0], self['views_num'][0],
            self['comments_num'][0],self['main_content'][0]
        )
        return insert_sql, params





class BiliItem(scrapy.Item):
    url =  scrapy.Field()
    title = scrapy.Field()
    date = scrapy.Field()
    writer = scrapy.Field()
    tags = scrapy.Field()
    cv_number = scrapy.Field()
    views_num = scrapy.Field()
    likes_num = scrapy.Field()
    comments_num = scrapy.Field()
    main_content = scrapy.Field()
    def get_insert_sql(self):
        insert_sql = """
            insert into bilibili(url,title,date,writer,tags,cv_number,
                                views_num,likes_num,comments_num,main_content,)
            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 

        """

        url = self['url'][0]
        title = self['title'][0]
        date = datetime.datetime.fromtimestamp(self["date"][0])
        writer = self["writer"][0]
        tags = ','.join([x.strip() for x in self["tags"]])
        cv_number = self["cv_number"][0]
        views_num = deal_nums(self["views_num"][0])
        likes_num = deal_nums(self["likes_num"][0])
        comments_num = deal_nums(self["comments_num"][0])
        main_content = self['main_content'][0]

        params = (url,title,date,writer,tags,cv_number,
                  views_num,likes_num,comments_num,main_content)
        # 注意这里一定要和上面的sql语句里的顺序一致
        return insert_sql,params