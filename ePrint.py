import copy
import os
import random
import sys
import threading
import time
import urllib.parse
import urllib.request
import urllib.error
from html.parser import HTMLParser
from typing import List

ePrint_URL = 'https://eprint.iacr.org/'

CATEGORY_APPLICATIONS = 'APPLICATIONS'
CATEGORY_PROTOCOLS = 'PROTOCOLS'
CATEGORY_FOUNDATIONS = 'FOUNDATIONS'
CATEGORY_IMPLEMENTATION = 'IMPLEMENTATION'
CATEGORY_SECRETKEY = 'SECRETKEY'
CATEGORY_PUBLICKEY = 'PUBLICKEY'
CATEGORY_ATTACKS = 'ATTACKS'


def ePrint_payload(q='', title='', authors='', category='',
                   submittedafter='',
                   submittedbefore='',
                   revisedafter='',
                   revisedbefore='') -> dict:
    """
    :param q:               Match anything
    :param title:           Match title
    :param authors:         Match title
    :param category:        Category
    :param submittedafter:  Submitted after
    :param submittedbefore: Submitted before
    :param revisedafter:    Revised after
    :param revisedbefore:   Revised before
    :return: payload Dict
    """
    return dict(
        q=q, title=title, authors=authors, category=category, submittedafter=submittedafter,
        submittedbefore=submittedbefore, revisedafter=revisedafter, revisedbefore=revisedbefore
    )


class PaperItem:
    """论文信息"""

    def __init__(self, name: str = '', url: str = '', update_date: str = '', title: str = '', authors: str = '',
                 category: str = ''):
        self.name, self.url, self.update_date, self.title, self.authors, self.category = \
            name, url, update_date, title, authors, category


class _EPrintHTMLParser(HTMLParser):
    # 匹配状态
    STATE_HANDLE_RUN = 0
    STATE_HANDLE_URL = 1
    STATE_HANDLE_UPDATE_DATE = 2
    STATE_HANDLE_TITLE = 3
    STATE_HANDLE_AUTHORS = 4
    STATE_HANDLE_CATEGORY = 5
    STATE_HANDLE_STOP = -1

    def __init__(self):
        super().__init__()
        self._state = self.STATE_HANDLE_STOP  # 初始状态
        self.paper_list: List[PaperItem] = []  # 论文数据结果
        # 当前检索到的论文数据
        self._cur_paper = PaperItem()

    def handle_starttag(self, tag, attrs):
        # 处于STOP状态，等待相应的html标签
        # 每篇论文的信息数据均以 <div class="mb-4"> 开始
        if self._state == self.STATE_HANDLE_STOP:
            if tag == 'div' and ('class', 'mb-4') in attrs:
                self._state = self.STATE_HANDLE_RUN
            return

        if self._state == self.STATE_HANDLE_RUN:
            # 论文url
            if tag == 'a' and ('class', 'paperlink') in attrs:
                self._state = self.STATE_HANDLE_URL
            # 更新时间
            elif tag == 'small' and ('class', 'ms-auto') in attrs:
                self._state = self.STATE_HANDLE_UPDATE_DATE
            # 标题
            elif tag == 'strong':
                self._state = self.STATE_HANDLE_TITLE
            # 作者
            elif tag == 'span' and ('class', 'fst-italic') in attrs:
                self._state = self.STATE_HANDLE_AUTHORS
            # 类别
            elif tag == 'small':
                self._state = self.STATE_HANDLE_CATEGORY

    def handle_data(self, data: str):
        # 将获取到的数据保存
        # ePrint每篇论文的html对应的信息顺序依次为
        # URL, UPDATE_DATE, TITLE, AUTHORS, CATEGORY
        # 读取完 CATEGORY 数据后即可进入STOP状态，等待下一论文的开启
        if self._state == self.STATE_HANDLE_URL:
            self._cur_paper.name = data.replace('/', '-') + '.pdf'
            self._cur_paper.url = ePrint_URL + data + '.pdf'
        elif self._state == self.STATE_HANDLE_UPDATE_DATE:
            self._cur_paper.update_date = data
        elif self._state == self.STATE_HANDLE_TITLE:
            self._cur_paper.title = data
        elif self._state == self.STATE_HANDLE_AUTHORS:
            self._cur_paper.authors = data
        elif self._state == self.STATE_HANDLE_CATEGORY:
            self._cur_paper.category = data
            self.paper_list.append(copy.deepcopy(self._cur_paper))

        if self._state != self.STATE_HANDLE_STOP:
            if self._state != self.STATE_HANDLE_CATEGORY:
                self._state = self.STATE_HANDLE_RUN
            else:
                self._state = self.STATE_HANDLE_STOP


def _request(url: str) -> bytes:
    """
    :param url: request url
    :return: data
    """
    UA_LIST = [
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 '
        'Safari/535.11',
        'User-Agent:Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
        'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)',
        'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 '
        'Safari/534.50',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0',
        ' Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1',
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1',
        ' Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
    ]
    headers = {'User-Agent': random.choice(UA_LIST)}
    try:
        req = urllib.request.Request(url=url, headers=headers)
        res = urllib.request.urlopen(req)
        data = res.read()
    except urllib.error.HTTPError:  # 发生错误
        sys.stderr.write('[Error]: {}\n'.format(url))
        data = bytes()
    time.sleep(0.5)  # 休眠0.5s
    return data


def _download_job(target_dir: str, items: List[PaperItem]) -> None:
    """
    :param target_dir:  目标目录
    :param items:       论文数据
    """
    for item in items:
        data = _request(item.url)  # 获取数据
        with open(os.path.join(target_dir, item.name), 'wb') as fp:
            fp.write(data)
        print('[ePrint Download]: {}, {}'.format(item.title, item.url))


def ePrint_download(target_dir: str, payload: dict, j: int = 6) -> None:
    """
    :param target_dir:  目标目录
    :param payload:     ePrint 检索payload
    :param j:           线程数
    """
    ePRINT_OFFSET_NUM = 100  # ePrint 论文查询以100为分页单位
    offset = 0
    while True:
        # 获取html页面
        url = ePrint_URL + 'search?' + urllib.parse.urlencode(payload) + '&offset=' + str(offset)
        data = _request(url).decode('utf-8')
        # 截取与paper信息相关的html
        pos1 = data.find('<div class="col-12 col-lg-8" style="min-height:80vh">')
        pos2 = data.find('<script>')
        data = data[pos1:pos2]
        # 解析html
        parser = _EPrintHTMLParser()
        parser.feed(data)
        parser.close()
        # 下载pdf文件
        print('================================================================')
        print('[ePrint fetch papers]: {} results'.format(len(parser.paper_list)))
        job_list: List[threading.Thread] = []
        for jid in range(j):
            job = threading.Thread(target=_download_job, args=(target_dir, parser.paper_list[jid::j]))
            job_list.append(job)
            job.start()  # 开启线程
        for job in job_list:
            job.join()  # 等待线程结束
        # 终止条件
        if len(parser.paper_list) != ePRINT_OFFSET_NUM:
            break
        # 更新offset
        offset += ePRINT_OFFSET_NUM
