# !/usr/bin/env python
import scrapy
# from scrapy.cmdline import execute
#
# ret = execute(['scrapy', 'crawl', 'coursera', '-o', 'machine learning.json', '-a', 'query=machine learning', '-a', 'language=English'])
# ret = execute(['scrapy', 'crawl', 'coursera', '-o', 'machine learning.json', '-a', 'query=machine learning'])

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from urllib.parse import quote
import json

results = {}


def crawler_results(item, response, spider):
    for key in item:
        results[key] = item[key]


class CourseraSpider(scrapy.Spider):
    name = "coursera"
    page = 1

    def __init__(self, query=None, language=None, *args, **kwargs):
        super(CourseraSpider, self).__init__(*args, **kwargs)

        if language is not None:
            self.start_urls = [
                'https://www.coursera.org/courses?query={0}&{1}={2}'.format(quote(query), quote('indices[test_all_products][refinementList][language][0]'), quote(language))
            ]
        else:
            self.start_urls = [
                'https://www.coursera.org/courses?query={0}'.format(quote(query))
            ]

    def parse(self, response):
        # follow links to author pages
        ret = {}
        with open('result.html', 'wb') as f:
            f.write(response.body)

        for course in response.css('li.ais-InfiniteHits-item'):
            badge = course.css('div.card-info div::text')
            if len(badge) < 1 or badge.extract_first().lower() != 'course':
                continue

            href = course.css('a')[0]
            yield response.follow(href, self.parse_course)

        # follow pagination links
        nav = response.css('nav')
        if 0 < len(nav):
            li = nav.css('ul li')
            self.last_page = int(li[len(li)-2].css('span::text').extract_first())
            if self.page < self.last_page:
                self.page += 1
                next_list_url = '{0}&{1}={2}'.format(self.start_urls[0], quote('indices[test_all_products][page]'), self.page)
                print(next_list_url)
                yield response.follow(next_list_url, self.parse)

    def parse_course(self, response):
        def extract_with_css(query, index=0):
            return response.css(query)[index].extract().strip()

        def extract_with_css_attribute(query, attribute, index=0):
            return response.css(query)[index].xpath('@{0}'.format(attribute)).extract_first()

        def extract_instructors():
            instructors = []
            for instructor in response.css('div.Instructors h3 a::text'):
                name = instructor.extract()
                if name.find(' - ') != -1:
                    name = name.split(' - ')[1]
                instructors.append(name)

            return instructors

        def extract_organization():
            partner_banner = response.css('.partnerBanner_10e5gws-o_O-Box_120drhm-o_O-displayflex_poyjc')
            # organization = partner_banner.css('img.rectangularXl_ltk00o')
            organization = partner_banner.css('img')
            if 0 < len(organization):
                return organization[0].xpath('@alt').extract_first()

            organization = partner_banner.css('img.rectangular_1ljyelh')
            if 0 < len(organization):
                return organization[0].xpath('@alt').extract_first()

            organization = partner_banner.css('span::text')
            return organization.extract_first()

        def extract_rating():
            about_course = response.css('.AboutCourse span::text')
            for course in about_course:
                if course.extract().find('ratings') != -1:
                    return about_course[1].extract()

            return ''

        def extract_syllabus():
            syllabus = []
            for week in response.css('.Syllabus .SyllabusWeek'):
                modules = []
                for modu in week.css('.SyllabusModule'):
                    module = {}
                    module["title"] = modu.css('h2::text').extract_first()

                    description = []
                    for desc in modu.css('span::text'):
                        if "..." == desc.extract():
                            break

                        description.append(desc.extract())

                    module["description"] = description
                    modules.append(module)

                syllabus.append(modules)

            return syllabus

        def extract_glance():
            glace = []
            for div in response.css('.ProductGlance')[0].xpath('div'):
                title = div.xpath('div')[1].css('h4 span::text')
                if len(title) < 1:
                    title = div.xpath('div')[1].css('h4::text')

                contents = div.xpath('div')[1].css('div a span::text')
                if len(contents) < 1:
                    contents = div.xpath('div')[1].css('div::text')

                if len(contents) < 1:
                    contents = div.xpath('div')[1].css('div span::text')

                content_txt = ''
                for content in contents:
                    if content.extract() == '...':
                        break

                    content_txt = '{0} {1} '.format(content_txt, content.extract())

                glace.append({
                    "title": title.extract_first(),
                    "content": content_txt,
                })

            return glace

        return {
            response.url: {
                'title': extract_with_css('h1::text'),
                'instructor': extract_instructors(),
                'organization': extract_organization(),
                'description': extract_with_css('div.content .content-inner::text'),
                'rating': extract_rating(),
                'syllabus': extract_syllabus(),
                'glace': extract_glance()
            }
        }


process = CrawlerProcess(get_project_settings())
process.crawl(CourseraSpider, query='machine learning', language='English')
for p in process.crawlers:
    p.signals.connect(crawler_results, signal=scrapy.signals.item_scraped)
process.start()

with open('machine learning.json', 'w') as f:
    f.write(json.dumps(results))
