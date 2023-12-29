# 连接数据库来执行启动爬虫脚本
import redis
import json

rd = redis.Redis("localhost",decode_responses=True)

rd.lpush('cnblog:start_urls','https://www.cnblogs.com/sitehome/p/1')

urls = [('https://www.cnblogs.com/zhujiqian/p/17934369.html',3),
        ('https://www.cnblogs.com/cosimo/p/17934648.html',5),
        ('https://www.cnblogs.com/luohenyueji/p/17934693.html',8),
        ('https://www.cnblogs.com/yx-study/p/17935635.html',20)]

for url in urls:
    rd.rpush("cnblog:new_urls",json.dumps(url))
    #这里用rpush和scheduler的lpop达成一个先进先出的效果
