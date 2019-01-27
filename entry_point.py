# !/usr/bin/env python
import scrapy
from scrapy.cmdline import execute

ret = execute(['scrapy', 'crawl', 'coursera', '-o', 'machine learning.json', '-a', 'query=machine learning', '-a', 'language=English'])
# ret = execute(['scrapy', 'crawl', 'coursera', '-o', 'machine learning.json', '-a', 'query=machine learning'])