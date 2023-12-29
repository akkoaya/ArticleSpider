from elasticsearch_dsl import Document, Date, Nested, Boolean,analyzer, InnerDoc, Completion, Keyword, Text,Integer
from elasticsearch_dsl.connections import connections #对ES进行连接

connections.create_connection(hosts=['http://localhost:9200/'])


class ArticlePost(Document):
    #中文日报网文章数据类型

    # 后面的类型和kibana里面的类型一致，可以自己看要求定义
    url =  Keyword()
    url_object_id = Keyword()
    title = Text(analyzer='ik_max_word')
    date = Date()
    writer = Text(analyzer='ik_smart')
    main_content = Text(analyzer='ik_max_word')

    class Index:
        #新建一个index
        name = "article"

# if __name__ == "__main__":
#      ArticlePost.init() #这个方法就会直接根据定义的这个类生成对应的mapping


from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}
ik_max_word = CustomAnalyzer("ik_max_word", filter=["lowercase"])

class CnblogPost(Document):
    #csdn博客网数据类型
    suggest = Completion(analyzer=ik_max_word) #lowercase表示大小写转换
    url = Keyword()
    url_object_id = Keyword()
    title = Text(analyzer='ik_max_word')
    date = Date() #这个根据自己的需求填格式
    writer_id = Keyword()
    views_num = Integer()
    comments_num = Integer()
    main_content = Text(analyzer='ik_max_word')

    class Index:
        name = "cnblog"

if __name__ == "__main__":
     CnblogPost.init()


class BiliPost(Document):
    #b站数据类型
    url = Keyword()
    url_object_id = Keyword()
    title = Text(analyzer='ik_max_word')
    date = Date()
    writer_id = Keyword()
    cv_number = Keyword()
    views_num = Integer()
    comments_num = Integer()
    main_content = Text(analyzer='ik_max_word')

    class Index:
        name = "bilibili"

# if __name__ == "__main__":
#      BiliPost.init()
