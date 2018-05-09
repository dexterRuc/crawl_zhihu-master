# coding: utf-8
import requests
import pymongo
from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr
import time
import poplib


class MainHandler(object):
    # 输入邮件地址, 口令和POP3服务器地址:
    email = 'getproxy@163.com'
    password = 'crawlzhihu666'
    pop3_server = 'pop.163.com'

    test_url = 'https://www.zhihu.com/api/v4/members/yi-shi-hua-hua/followees?include=data%5B*%5D.answer_count,articles_count,gender,follower_count,is_followed,is_following,badge%5B?(type=best_answerer)%5D.topics&offset=0&limit=20'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
    }
    mongo_uri = '183.174.228.25:38018'
    mongodb = 'zhihu'
    collection_name = 'proxy'
    client = pymongo.MongoClient(mongo_uri)
    db = client[mongodb]


    def test_proxies(self):
        print('Test Proxies')
        items = list(self.db[self.collection_name].find()) #把返回的游标变成List
        for item in items:
            self.test_proxy(item)

    def test_proxy(self, item):
        proxy = item.get('proxy') #(proxy_host, proxy_port) = tuple(proxy.split(':'))
        name = item.get('name')
        print(name+' '+proxy)
        proxies = {
            'http' : 'http://'+proxy,
            'https': 'https://'+proxy
        }
        try:
            requests.get(url=self.test_url,
                         headers=self.headers,
                         proxies=proxies,
                         timeout=30)
            print('Valid Proxy', proxy)
        except :
            print('Invalid Proxy', proxy)
            self.db[self.collection_name].remove({'name': name}) #从数据库中删除

    def guess_charset(self, msg):
        charset = msg.get_charset()
        if charset is None:
            content_type = msg.get('Content-Type', '').lower()
            pos = content_type.find('charset=')
            if pos >= 0:
                charset = content_type[pos + 8:].strip()
        return charset

    def decode_str(self, s):
        value, charset = decode_header(s)[0]
        if charset:
            value = value.decode(charset)
        return value

    def get_ip_from_email(self, msg):
        content_type = msg.get_content_type()
        if content_type == 'text/plain' or content_type == 'text/html':
            content = msg.get_payload(decode=True)
            charset = self.guess_charset(msg)
            if charset:
                content = content.decode(charset)
                name = content.split(' ')[0]
                proxy = content.split(' ')[1]
                return name,proxy

    def fetch_eamil(self):
        # 连接到POP3服务器:
        server = poplib.POP3(self.pop3_server)
        # 可以打开或关闭调试信息:
        server.set_debuglevel(0)
        # 可选:打印POP3服务器的欢迎文字:
        # print(server.getwelcome().decode('utf-8'))
        # 身份认证:
        server.user(self.email)
        server.pass_(self.password)
        # stat()返回邮件数量和占用空间:
        # print('Messages: %s. Size: %s' % server.stat())
        # list()返回所有邮件的编号:
        resp, mails, octets = server.list()
        # 可以查看返回的列表类似[b'1 82923', b'2 2184', ...]
        # print(mails)
        # 获取最新一封邮件, 注意索引号从1开始:
        index = len(mails)
        if index == 0:
            print('no email!')
            return

        resp, lines, octets = server.retr(index)
        # lines存储了邮件的原始文本的每一行,
        # 可以获得整个邮件的原始文本:
        msg_content = b'\r\n'.join(lines).decode('utf-8')
        # 稍后解析出邮件:
        msg = Parser().parsestr(msg_content)
        parts = msg.get_payload()
        name,proxy = self.get_ip_from_email(parts[0])
        item = {
            'name': name,
            'proxy': proxy
        }
        self.db[self.collection_name].update({'name': item['name']}, item, True)
        self.test_proxies()
        # 可以根据邮件索引号直接从服务器删除邮件:
        server.dele(index)
        # 关闭连接:
        server.quit()

def run():
    b = MainHandler()
    while True:
        b.fetch_eamil()
        time.sleep(10*60)

run()

