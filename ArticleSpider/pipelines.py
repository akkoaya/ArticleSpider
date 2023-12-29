# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# useful for handling different item types with a single interface


from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
import codecs    #这个包与open的最大区别就是，可以不用管编码问题
import json
import MySQLdb
import datetime
from twisted.enterprise import adbapi
import MySQLdb.cursors

# class ArticlespiderPipeline:
#     def process_item(self, item, spider):
#         #这个item就可以存放到数据库中，或者其他介质作为存储
#         return item

#中文日报网
#处理date和datetime格式的数据无法储存到json的问题
class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        # 处理返回数据中有date类型的数据
        if isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        # 处理返回数据中有datetime类型的数据
        elif isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return json.JSONEncoder.default(self, obj)


#导入到json文件
class JsonPipeline(object):
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):
        #将item转换为string的格式
        lines = json.dumps(dict(item), ensure_ascii=False,cls=DateEncoder) + '\n'  #ensure_ascii=False保证了写入中文不会出现问题
        #cls=DateEncoder，后面的是引用的上面的类，确保日期格式可以写入json
        #写入到json文件中
        self.file.write(lines)
        return item

    def spider_closed(self,spider):
        self.file.close()


#导入到mysql数据库
#同步的操作
class MysqlPipeline(object):
    def __init__(self):
        self.connect = MySQLdb.connect(host="localhost",user="root",password="123456",port=3306,db="article_spider",charset="utf8mb3",use_unicode=True)
        self.cursor = self.connect.cursor()

    def process_item(self, item, spider):
        #设置sql语句
        insert_sql = """
            insert into article(title,date,url,url_object_id,writer,main_content)
            VALUES (%s,%s,%s,%s,%s,%s)
        """
        self.cursor.execute(insert_sql,(item['title'],item['date'],item['url'],item['url_object_id'],item['writer'],item['main_content']))
        self.connect.commit()
        return item



#异步的操作
class MysqlTwistedPipline1(object):
    def __init__(self,dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls,settings): #这个cls就是MysqlTwistedPipline类
        #MYSQL的基本信息可以事先填入setings.py中，在这里再调用
        dbparms = dict(
            #这些左边的名称都要和MySQLdb.connect模块里connections的内置参数一样
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWORD'],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )
        #dbpool是一个容器
        dbpool = adbapi.ConnectionPool("MySQLdb",**dbparms)  #实际上用的还是MySQLdb这个模块,只不过twisted提供了异步的一个api
        #双星号（**）将参数以字典的形式导入
        return cls(dbpool) #实例化这个参数

    def process_item(self, item, spider):
        #使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert,item)
        #错误处理
        query.addErrback(self.handle_error,item,spider)

    def handle_error(self, failure, item, spider):
        #处理异步插入的异常
        print(failure)

    def do_insert(self,cursor,item):
        #执行具体的插入
        # 设置sql语句
        insert_sql = """
                    insert into article(title,date,url,url_object_id,writer,main_content)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """
        cursor.execute(insert_sql, (
        item['title'], item['date'], item['url'], item['url_object_id'], item['writer'], item['main_content']))
        return item



# class ArticelImagePipeline(ImagesPipeline):
#     def item_completed(self, results, item, info):
#         for ok, value in results:
#             image_path = value['path']
#         item['image_path'] = image_path
#         #这样就完成了items.py中的image_path的指向
#         return item





# 异步入Mysql库
class MysqlTwistedPipline(object):
    #尽量用一个pipeline解决所有网站的爬取，因为pipeline里是连接到mysql的，如果有大量网站，每个网站用一个pipeline，那就要连接非常多次数据库
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        # 登录参数在settings中
        dbparms = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWORD'],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=False,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)
        return cls(dbpool)

    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)
        #要在下面得知具体的错误位置，这里带上item和spider参数
    def handle_error(self, failure, item, spider):
        #这里引用item和spider参数可以得知具体的错误位置
        #这个地方太有用了，debug超好用
        return failure  #在这里打断点

    def do_insert(self, cursor, item):
        #因为question和answer的处理不一致，所以在items里分别设置
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)  # 执行数据库语句,将数据存入SQL数据库中
        return item



from models.es_types import ArticlePost
from w3lib.html import remove_tags  #去除content里面的html tag
#写入数据到ES
class ElasticsearchPipeline(object):
    def process_item(self,item,spider):
        item.save_to_es()

        return item