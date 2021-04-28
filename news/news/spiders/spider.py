import os
import scrapy
from time import sleep
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException


PRAVDA_XML_FILE_PATH = os.path.join('..', 'data', 'pravda_spider_data.xml')
TSN_XML_FILE_PATH = os.path.join('..', 'data', 'tsn_spider_data.xml')


class PravdaNewsSpider(scrapy.Spider):
    name = "pravda_spider"
    start_urls = [r"https://www.pravda.com.ua/news/"]

    def __init__(self, name=None, **kwargs):
        super(PravdaNewsSpider, self).__init__(name, **kwargs)

        self.xml_file = open(PRAVDA_XML_FILE_PATH, 'w')
        self.xml_file.write(f'<data from="pravda.com.ua">\n')

    def parse(self, response, **kwargs):
        for article_link in response.xpath('//div[@class="article_header"]/a/@href'):
            yield scrapy.Request(response.urljoin(article_link.get()), callback=self.parse_article)

        url_on_yesterdays_news = response.xpath('//a[img/@src="/images/v6/ico_arr_l.svg"]/@href')
        if url_on_yesterdays_news:
            yield scrapy.Request(
                response.urljoin(url_on_yesterdays_news[0].get()),
                callback=self.parse
            )

    def parse_article(self, response):
        self.xml_file.write(f'\t<text url="{response.url}">\n')

        for paragraph in response.xpath('//div[@class="post_text"]/p[not(script)]'):
            self.xml_file.write(f"\t\t{paragraph.get()}\n")

        for paragraph in response.xpath('//article[@class="article"]/p'):
            self.xml_file.write(f"\t\t{paragraph.get()}\n")

        for paragraph in response.xpath('//div[@class="post__text"]/p'):
            self.xml_file.write(f"\t\t{paragraph.get()}\n")

        self.xml_file.write("\t</text>\n")

    def __del__(self):
        self.xml_file.write(f"</data>\n")
        self.xml_file.close()


class TsnNewsSpider(scrapy.Spider):
    name = "tsn_spider"
    start_urls = [r"https://tsn.ua/news"]

    def __init__(self, name=None, **kwargs):
        super(TsnNewsSpider, self).__init__(name, **kwargs)

        self.xml_file = open(TSN_XML_FILE_PATH, 'w')
        self.xml_file.write(f'<data from="tsn.ua">\n')

        self.driver = webdriver.Firefox()

    def parse(self, response, **kwargs):
        self.driver.get(response.url)

        load_more_articles_button = self.driver.find_element_by_xpath(
            '//button[@class="c-nav__btn c-nav--etc i-reset--a i-load"]'
        )

        xpath_to_articles_link = '//a[@class="c-card__link"]'

        previus_article_num = 0
        while previus_article_num != len(self.driver.find_elements_by_xpath(xpath_to_articles_link)):
            previus_article_num = len(self.driver.find_elements_by_xpath(xpath_to_articles_link))
            for _ in range(10):
                self.driver.execute_script("arguments[0].click();", load_more_articles_button)
                sleep(1)

        for article_link in self.driver.find_elements_by_xpath(xpath_to_articles_link):
            yield scrapy.Request(response.urljoin(article_link.get_attribute("href")), callback=self.parse_article)

    def parse_article(self, response):
        self.xml_file.write(f'\t<text url="{response.url}">\n')

        for paragraph in response.xpath('//div[@class="c-card__box c-card__body"]/p'):
            self.xml_file.write(f"\t\t{paragraph.get()}\n")

        self.xml_file.write("\t</text>\n")

    def __del__(self):
        self.xml_file.write(f"</data>\n")
        self.xml_file.close()

        self.driver.close()
