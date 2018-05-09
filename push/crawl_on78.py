# coding: utf-8
import requests
import json
import time
import pymongo
import os
import random
import linecache
import threading

class CrawlThread(threading.Thread):

    def __init__(self,func,args=()):
        super(CrawlThread,self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result  # 如果子线程不使用join方法，此处可能会报没有self.result的错误
        except Exception:
            return ''

def get_random_ua():
    file_path = os.path.abspath('.') + '/utils/user_agent.txt'
    line_num = len(open(file_path, 'r').readlines())
    index = random.randint(0,line_num)
    random_ua = linecache.getline(file_path,index)[:-1]
    return random_ua

# def get_random_ip():
#     file_path = os.path.abspath('.') + '/utils/proxies.txt'
#     line_num = len(open(file_path, 'r').readlines())
#     index = random.randint(0,line_num)
#     random_ip = linecache.getline(file_path,index)[:-1]
#     return random_ip

def get_random_ip(): # 从mongo数据库中
    mongo_uri = '183.174.228.25:38018'
    mongodb = 'zhihu'
    collection_name = 'proxy'
    client = pymongo.MongoClient(mongo_uri)
    db = client[mongodb][collection_name]
    items = list(db.find())[0]
    proxy = items.get('proxy')
    client.close()
    return proxy

def get_auth():
    file_path = os.path.abspath('.') + '/utils/auth.txt'
    line_num = len(open(file_path, 'r').readlines())
    index = random.randint(0, line_num)
    random_auth = linecache.getline(file_path, index)[:-1]
    return random_auth

def judge_crawl(url_token):
    mongo_uri = '183.174.228.25:38018'
    mongodb = 'zhihu'
    collection_name = 'users_info'
    client = pymongo.MongoClient(mongo_uri)
    db = client[mongodb][collection_name]
    items = list(db.find({'url_token': url_token}))
    if len(items) == 0: #在数据库中未找到
        return True
    else:
        return False

def get_uncrawl_user():
    mongo_uri = '183.174.228.25:38018'
    mongodb = 'zhihu'
    uncrawl_collection = 'un_crawl_users_78' # 78的备份 只有url_token
    uncrawl_client = pymongo.MongoClient(mongo_uri)
    uncrawl_db = uncrawl_client[mongodb][uncrawl_collection]
    item = uncrawl_db.find_one() # find_one() 取第一个数据 返回是一个dict
    url_token = item.get('url_token')
    follower_count = item.get('follower_count')
    while True:
        print(url_token)
        if url_token[0] < 'n': #88爬取 > 'n'
            uncrawl_db.remove({'url_token': url_token})
            item = uncrawl_db.find_one()  # findOne() 取第一个数据
            url_token = item.get('url_token')
            follower_count = item.get('follower_count')
            continue
        if judge_crawl(url_token) and follower_count < 10000: #详细信息数据中还没有
            if crawl_user(url_token): #抓取完成
                uncrawl_db.remove({'url_token': url_token})
                item = uncrawl_db.find_one()  # findOne() 取第一个数据
                url_token = item.get('url_token')
                follower_count = item.get('follower_count')
        else:
            uncrawl_db.remove({'url_token': url_token})
            item = uncrawl_db.find_one()  # findOne() 取第一个数据
            url_token = item.get('url_token')
            follower_count = item.get('follower_count')


def crawl_user(user):
    print('crawl '+user)
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    user_query = 'locations,employments,gender,educations,business,voteup_count,thanked_Count,follower_count,following_count,cover_url,following_topic_count,following_question_count,following_favlists_count,following_columns_count,columns_count,answer_count,articles_count,pins_count,question_count,commercial_question_count,favorite_count,favorited_count,logs_count,marked_answers_count,marked_answers_text,message_thread_token,account_status,is_active,is_force_renamed,is_bind_sina,sina_weibo_url,sina_weibo_name,show_sina_weibo,is_blocking,is_blocked,is_following,is_followed,mutual_followees_count,vote_to_count,vote_from_count,thank_to_count,thank_from_count,thanked_count,description,hosted_live_count,participated_live_count,allow_message,industry_category,org_name,org_homepage,badge[?(type=best_answerer)].topics'
    first_activities_url = "https://www.zhihu.com/api/v4/members/{user}/activities?limit={limit}"
    activities_url = "https://www.zhihu.com/api/v4/members/{user}/activities?limit={limit}&after_id={after_id}&desktop=True"
    # "https://www.zhihu.com/answer/{id}"
    answers_url = "https://www.zhihu.com/api/v4/members/{user}/answers?offset={offset}&limit={limit}&sort_by=created"
    # "https://www.zhihu.com/question/{id}"
    questions_url = "https://www.zhihu.com/api/v4/members/{user}/questions?limit={limit}&offset={offset}"
    # "https://zhuanlan.zhihu.com/p/{id}"
    articles_url = "https://www.zhihu.com/api/v4/members/{user}/articles?limit={limit}&offset={offset}"
    # ['data']['columns']['id'] "https://www.zhihu.com/columns/{id}"
    columns_url = "https://www.zhihu.com/api/v4/members/{user}/column-contributions?offset={offset}&limit={limit}"
    # https://www.zhihu.com/pin/{id}
    pins_url = "https://www.zhihu.com/api/v4/members/{user}/pins?offset={offset}&limit={limit}"
    favlists_url = "https://www.zhihu.com/api/v4/members/{user}/favlists?offset={offset}&limit={limit}"
    # ['data']['url_token'] https://www.zhihu.com/people/{url_token}
    followee_url =  "https://www.zhihu.com/api/v4/members/{user}/followees?offset={offset}&limit={limit}"
    follower_url = "https://www.zhihu.com/api/v4/members/{user}/followers?offset={offset}&limit={limit}"
    # ['data']['topic']['id'] str https://www.zhihu.com/topic/{id}
    following_topics_url = "https://www.zhihu.com/api/v4/members/{user}/following-topic-contributions?offset={offset}&limit={limit}"
    # "https://www.zhihu.com/columns/{id}"
    following_columns_url = "https://www.zhihu.com/api/v4/members/{user}/following-columns?offset={offset}&limit={limit}"
    following_questions_url = "https://www.zhihu.com/api/v4/members/{user}/following-questions?offset={offset}&limit={limit}"
    following_favlists_url = "https://www.zhihu.com/api/v4/members/{user}/following-favlists?offset={offset}&limit={limit}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20'
    }

    item = {
        'id': '',
        'name': '',
        'avatar_url': '',
        'headline': '',
        'description': '',
        'url' : '',
        'url_token' : '',
        'gender': '',
        'cover_url': '',
        'type': '',
        'badge': '',
        'answer_count': 0,
        'articles_count': 0,
        'commercial_question_count': 0,
        'favorite_count': 0,
        'favorited_count': 0,
        'follower_count': 0,
        'following_columns_count': 0,
        'following_count': 0,
        'pins_count': 0,
        'question_count': 0,
        'thank_from_count': 0,
        'thank_to_count': 0,
        'thanked_count': 0,
        'vote_from_count': 0,
        'vote_to_count': 0,
        'voteup_count': 0,
        'following_favlists_count': 0,
        'following_question_count': 0,
        'following_topic_count': 0,
        'marked_answers_count': 0,
        'mutual_followees_count': 0,
        'hosted_live_count': 0,
        'participated_live_count': 0,

        'columns_count':0,

        'locations': '',
        'educations': '',
        'employments': '',
        # 获取
        'activities': '',
        'answers': '',
        'questions': '',
        'articles': '',
        'columns': '',
        'pins': '',
        'favlists': '',
        'followees': '',
        'followers': '',
        'following_topic': '',
        'following_columns': '',
        'following_question': '',
        'following_favlists': ''
    }

    retry_count = 0
    while retry_count < 5:
        proxy = get_random_ip()
        proxies = { 'https': 'https://' + proxy,
                    'http': 'http://' + proxy}
        try: #尝试获取页面
            response = requests.get(url=user_url.format(user=user, include=user_query),
                                    headers=headers,
                                    #proxies=proxies,
                                    )
            response.encoding = "utf-8"
            if response.status_code == 404 or response.status_code == 401:  # 404 账号被删除了来到了知识荒原
                                                                            # 401 账号被永久封禁
                return True  # 就当作爬过了 不然会死循环
            try: #尝试加载返回结果
                result = json.loads(response.content)
                for key in item.keys():
                    if key in result.keys():
                        item[key] = result.get(key)
                # item['activities'] = get_user_activity(user, first_activities_url, activities_url)
                item['answers'] = get_user_details(user, answers_url, item['answer_count'])
                item['questions'] = get_user_details(user, questions_url, item['question_count'])
                item['articles'] = get_user_details(user, articles_url, item['articles_count'])
                item['columns'] = get_user_details(user, columns_url, item['columns_count'])
                item['pins'] = get_user_details(user, pins_url, item['pins_count'])
                item['favlists'] = get_user_details(user, favlists_url, item['favorite_count'])
                item['followees'] = get_user_details(user, followee_url, item['following_count'])
                item['followers'] = get_user_details(user, follower_url, item['follower_count'])
                item['following_topic'] = get_user_details(user, following_topics_url,item['following_topic_count'])
                item['following_columns'] = get_user_details(user, following_columns_url,item['following_columns_count'])
                item['following_question'] = get_user_details(user, following_questions_url,item['following_question_count'])
                item['following_favlists'] = get_user_details(user, following_favlists_url,item['following_favlists_count'])

                insert_to_mongodb(item)
                return True
            except: #失败因为状态码非200
                print(response.status_code)

        except:
            retry_count += 1
    return False

def insert_to_mongodb(item):
    mongo_uri = '183.174.228.25:38018'
    mongodb = 'zhihu'
    collection_name = 'users_info'

    client = pymongo.MongoClient(mongo_uri)
    db = client[mongodb]
    db[collection_name].update({'url_token': item['url_token']}, item, True)
    print(item['url_token'])
    client.close()


# def get_user_details(user, details_url): # 未使用多线程
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
#         'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20'
#     }
#     #headers = self.headers
#     details = []
#     offset = 0
#     limit = 20
#     is_end = False
#     next_url = details_url.format(user=user, offset=offset, limit=limit)
#     while is_end == False:
#
#         while True :
#             headers['User-Agent'] = get_random_ua()
#             proxy = get_random_ip()
#             protocol = 'https' if 'https' in proxy else 'http'
#             proxies = {protocol: proxy}
#
#             response = requests.get(url=next_url,
#                                     # cookies=self.cookies,
#                                     proxies=proxies,
#                                     headers=headers
#                                     )
#             if response.status_code == 200:
#                 break
#         #time.sleep(2)
#         response.encoding = "utf-8"
#         results = json.loads(response.text)
#         is_end = results["paging"]["is_end"]
#         next_url = details_url.format(user=user, offset=offset, limit=limit)
#         offset += 20
#         for data in results['data']:
#             if 'id' in data.keys():
#                 if isinstance(data['id'], int):
#                     details.append(str(data['id']))
#                 else:
#                     details.append(data['id'])
#             elif 'column' in data.keys(): # 专栏特殊处理
#                 details.append(data['column']['id'])
#             elif 'topic' in data.keys(): # 话题特殊处理
#                 details.append(data['topic']['id'])
#
#     detail = ','.join(details)
#     return detail
def get_user_details(user, details_url, num):

    n = num//20 + 1 # 需要发送多少请求
    thread_list = []

    for i in range(n):
        url = details_url.format(user=user,offset=i*20,limit=20)
        thread = CrawlThread(func=get_user_details_thread,args=(url,))
        thread_list.append(thread)
        thread.start()

    details = ''
    for thread in thread_list:
        thread.join()
        details += thread.get_result()

    return details

def get_user_details_thread(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
    }
    retry_count = 0
    while retry_count < 5:
        proxy = get_random_ip()
        proxies = {'https': 'https://' + proxy,
                   'http': 'http://' + proxy}
        try:
            response = requests.get(url=url,
                                    #proxies=proxies,
                                    headers=headers
                                    )
            response.encoding = "utf-8"
            details = []
            try:
                results = json.loads(response.text)
                for data in results['data']:
                    if 'id' in data.keys():
                        if isinstance(data['id'], int):
                            details.append(str(data['id']))
                        else:
                            details.append(data['id'])
                    elif 'column' in data.keys():  # 专栏特殊处理
                        details.append(data['column']['id'])
                    elif 'topic' in data.keys():  # 话题特殊处理
                        details.append(data['topic']['id'])

                detail = ','.join(details)
                return detail
            except:
                print(response.status_code)
            break #成功得到页面即可返回
        except:
            retry_count += 1
    return url #实在某个线程未完成暂且存下url


def get_user_activity(user, first_activities_url, activities_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
    }

    activities = {}
    is_end = False
    next_url = first_activities_url.format(user=user, limit=10)
    time_format = '%Y-%m-%d %H:%M:%S'
    end_time = '2018-04-05 00:00:00' # 以来的行为
    trans_time = int(time.mktime(time.strptime(end_time, time_format)))
    while is_end == False:

        while True :
            headers['User-Agent'] = get_random_ua()
            proxy = get_random_ip()
            protocol = 'https' if 'https' in proxy else 'http'
            proxies = {protocol: proxy}

            response = requests.get(url=next_url,
                                    # cookies=self.cookies,
                                    proxies=proxies,
                                    headers=headers
                                    )
            if response.status_code == 200:
                break
        #time.sleep(2)
        response.encoding = "utf-8"
        results = json.loads(response.text)
        is_end = results['paging']['is_end']
        after_id = results['data'][-1]['id']
        next_url = activities_url.format(user=user, after_id=after_id, limit=20)
        for data in results['data']:
            activities[data['target']['id']] = data['verb']
        now_process = time.localtime(float(after_id))
        #print(time.strftime(time_format, now_process))
        if int(after_id) <= trans_time:  # 超过时限内的行为
            break
    activity = json.dumps(activities, ensure_ascii=False)
    return activity


def get_user_activity_thread(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20'
    }

    activities = {}

    headers['User-Agent'] = get_random_ua()
    proxy = get_random_ip()
    protocol = 'https' if 'https' in proxy else 'http'
    proxies = {protocol: proxy}

    response = requests.get(url=url,
                            proxies=proxies,
                            headers=headers
                            )

        #time.sleep(2)
    response.encoding = "utf-8"
    results = json.loads(response.text)
    is_end = results['paging']['is_end']
    after_id = results['data'][-1]['id']
    for data in results['data']:
        activities[data['target']['id']] = data['verb']
    now_process = time.localtime(float(after_id))
    #print(time.strftime(time_format, now_process))
    activity = json.dumps(activities, ensure_ascii=False)
    return activity



get_uncrawl_user()