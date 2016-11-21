# -*- encoding:utf-8 -*-

"""
File:       URLUtility.py
Author:     magerx@paxmac.org
Modify:     2016-03-18
"""

from urlparse import urlparse, urlunparse, ParseResult
import re
import os

"""
处理各种URL的函数
"""


def get_domain(url):
    """
    :url:       url
    :return:    带协议的domian
    """
    url = urlparse(url)
    return '://'.join([url.scheme, url.netloc])


class changable_urlcomp(object):
    """
    urlparse.ParseResult是tuple不可更改
    这个类就是拿过来修改用
    """

    def __init__(self, init):
        """
        复制一份urlparse.ParseResult，init即为对象
        """
        self.query = init.query
        self.params = init.params
        self.fragment = init.fragment
        self.path = init.path
        self.netloc = init.netloc
        self.scheme = init.scheme

    def to_standard(self):
        """
        返回一个标准的urlparse.ParseResult对象
        """
        return ParseResult(
            scheme=self.scheme,
            netloc=self.netloc,
            path=self.path,
            params=self.params,
            query=self.query,
            fragment=self.fragment
        )


def real_url_process(link, url):
    """
    处理多种相对路径的情况
    :link:      页面中的连接
    :url:       原始URL
    :return:    changable_urlcomp对象
    """
    # 拿到可以修改的对象
    url = changable_urlcomp(urlparse(url))
    link = changable_urlcomp(urlparse(link))

    # query跟着url走，params全部清空，fragment如果link有的话就跟着link走
    url.query = link.query
    url.params = link.params = ''

    if link.fragment:
        url.fragment = ''  # link.fragment,这里为了去重考虑，直接扔掉fragment

    # link中有域名
    if link.netloc:
        # link为自带协议的，直接返回
        if link.scheme:
            return link
        # 使用url的协议
        else:
            link.scheme = url.scheme
            return link

    # 没有路径
    if len(link.path) == 0:
        return url

    # link中路径为绝对路径
    if link.path[0] == '/':
        url.path = link.path
        return url

    # link为相对路径，同时不以'/'开头
    tmp = url.path.split('/')
    del tmp[-1]
    url.path = "{0}/{1}".format('/'.join(tmp), link.path)  # 相对路径则通过当前目录进行拼接+ '/' + link.path
    return url


def url_process(link, url):
    """
    :link:      页面中的连接
    :url:       原始URL
    :return:    合成出来的URL
    """
    u = real_url_process(link, url)

    # 处理掉url中连续//之类的路径问题
    u.path = os.path.realpath('/' + u.path)
    return urlunparse(u.to_standard())


# TODO：修改下参数抽象
def sort_query(query):
    """
    提取出参数，排序后连接，忽略具体的值，只有名字
    :query:     URL中的查询字串
    :return:    将key排序后组合成串
    """

    # 如果参数中没有"="，直接将该key置空
    query = query.split('&')
    for i in xrange(len(query)):
        querys = query[i].split('=', 1)
        query[i] = querys[0] if len(querys) == 2 else ''
    query.sort()

    # 链接成参数列表

    # 对URL进行抽象处理
    # newquery = list()

    # 没搞懂当时为什么要做参数抽象
    # for param in query:
    #     if '=' in param:
    #         tmp = param.split('=', 1)
    #         if len(tmp[1]) == 0:
    #             tmp[1] = 'null'
    #         elif tmp[1].isdigit():
    #             tmp[1] = '%d'
    #         else:
    #             tmp[1] = '%s'

    # newquery.append('='.join(tmp))
    # 去除value后重新拼装上去
    newquery = '=&'.join(query)

    return newquery  # parameters


# TODO: 重写下URL相似
def get_pattern(url):
    """
    将URL模式化，现在只是对最后一级进行模式替换，如果有需要可以替换
    有个初步的想法是前后一致，而中间的某一个打散了匹配
    :url:       目标URL
    :return:    模式化后的URL
    """
    query = ''

    parse = urlparse(url)
    path = parse.path
    dirlist = path.split('/')

    # 参数抽离
    query = sort_query(parse.query)

    # 重新封装文件名,同后缀文件名为数字的统一认为相似
    filename = os.path.splitext(dirlist[-1])
    # 为了去重考虑，将ext为空的都置为'/'
    prefix, ext = filename if filename[1] else (filename[0], '/')

    if prefix.isdigit():
        prefix = '%d'

    elif 'htm' in ext:
        if not prefix.isalpha():
            prefix = '%w'

    # 抽象目录中的数字、中文
    if len(dirlist) > 2:
        cn_pattern = re.compile(u'[\u4e00-\u9fa5]+')
        for x in range(len(dirlist) - 1):
            tmp_dir = dirlist[x]
            if tmp_dir.isdigit():
                dirlist[x] = "%d"
            elif cn_pattern.search(tmp_dir):
                dirlist[x] = "%ZH-CN"
            elif len(tmp_dir) >= 5 and not tmp_dir.isalpha():  # 解决目录中出现类似23df334这样的情况
                dirlist[x] = "{len}%$".format(len=len(tmp_dir))

    dirlist[-1] = ''

    filename = prefix + ext
    path = '/'.join(dirlist)
    path = '{0}/{1}'.format(os.path.dirname(path), filename)

    # parse.scheme,相似处理时将fragment置空,同时为了去重考虑将scheme都设置为http
    url = urlunparse(('http', parse.netloc, path, parse.params, query, '')) 

    return url


def extract_path_domain(url):
    """
    将url分成域名和目录，去掉文件名，并处理一些细枝末节的东西
    :url:       目标URL
    :return:    (path, domain)
    """
    domain = get_domain(url)
    path = urlparse(url).path

    if ';' in path:
        path = path[0:path.find(';')] + '.'

    if len(path) > 0:  # and path[-1] == '/':
        path = os.path.dirname(path)
    # elif len(path) == 0:
    else:
        path = '/'

    return path, domain


def extract_path_query(url):
    """
    将url分成路径和查询
    :url:       目标URL
    :return:    (path, query)其中query是列表形式
    """
    url, query = url.split('?', 1)

    querys = query.split('&')
    res = []
    for query in querys:
        t = query.split('=', 1)
        if len(t) != 2:
            t.append('')
        res.append(t)

    return url, res


def extract_netloc_path(url):
    """
    :url:       url
    :return:    (domain, path)
    """
    url = urlparse(url)
    return url.netloc


if __name__ == '__main__':
    print get_pattern('http://news.qq.com/a/20161104/040812.htm#p=1')
