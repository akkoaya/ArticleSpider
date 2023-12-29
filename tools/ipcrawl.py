#爬取网站ip代理池
import requests
from scrapy.selector import Selector
import MySQLdb

conn = MySQLdb.connect(host="localhost", user="root", passwd="123456", port=3306, db="article_spider",
                       charset="utf8mb3")
cursor = conn.cursor()
class IPCrawl():
    def url_get(self,i):
        #爬取快代理
        headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        re = requests.get(f"https://www.kuaidaili.com/free/intr/{i}/", headers = headers)
        print(f"正在爬取第{i}页")
        html = re.text
        return html

    def crawl_ips(self,html):
        selector = Selector(text=html)
        all_tr = selector.css('tbody tr')

        ip_list=[]
        for tr in all_tr:
            type = tr.css('td[data-title="类型"]::text').extract()[0]
            ip = tr.css('td[data-title="IP"]::text').extract()[0]
            port = tr.css('td[data-title="PORT"]::text').extract()[0]
            speed = tr.css('td[data-title="响应速度"]::text').extract()[0]
            ip_list.append([type,ip,port,speed])

        return ip_list
    def download_ip(self,ip_list):

        for ip_info in ip_list:

            cursor.execute('''
                insert proxy_pool(type,ip,port,speed) VALUES('{0}','{1}','{2}','{3}') 
                '''.format(ip_info[0],ip_info[1],ip_info[2],ip_info[3])
            )
            conn.commit()


    def run(self):
        for i in range(1, 1000):
            html =  self.url_get(i)
            ip_list = self.crawl_ips(html)
            self.download_ip(ip_list)

class GetIP(object):
    def get_random_ip(self):
        #从数据库中随机取出一个ip
        random_sql = '''
            SELECT ip,port FROM proxy_pool
            ORDER BY RAND()
            LIMIT 1
        '''
        result = cursor.execute(random_sql)
        for ip_info in cursor.fetchall():  #因为result的值无法直接获取
            ip = ip_info[0]
            port = ip_info[1]

        re = self.select_ip(ip,port)
        if re:
            return "http://{0}:{1}".format(ip, port)
        else:
            return self.get_random_ip()

    def select_ip(self,ip,port):
        #判断ip是否可用
        http_url = "http://www.baidu.com"
        proxy_url = f"http://{ip}:{port}"
        try:
            proxy_dict = {
                "http":proxy_url
            }
            response = requests.get(http_url,proxies=proxy_dict)
        except Exception as e:
            print("invalid ip:"+ip)
            self.delete_ip(ip)
            return False
        else:
            code = response.status_code
            if code >=200 and code <300:
                print("effective ip")
                return True
            else:
                print("invalid ip:"+ip)
                self.delete_ip(ip)
                return False

    def delete_ip(self,ip):
        delete_sql = f"DELETE FROM proxy_pool WHERE ip='{ip}'"
        cursor.execute(delete_sql)
        conn.commit()
        return True

    def run(self):
        self.get_random_ip()

if __name__ == "__main__": #如果不这么写，在其他模块import这个模块的时候，会直接执行下面的命令
    # spider = IPCrawl()
    # spider.run()

    select = GetIP()
    select.run()

