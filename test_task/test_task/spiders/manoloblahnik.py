import pdb

import scrapy
from urllib.parse import urlparse

class ManoloblahnikSpider(scrapy.Spider):
    main_category = ['Women', 'Men']
    name = 'manoloblahnik'
    allowed_domains = ['manoloblahnik.com']
    start_urls = ['https://www.manoloblahnik.com/gb']

    def parse(self, response):
        print('ABIBA')
        top_lvl = response.css('.level0.level-top')
        for par in top_lvl:
            cat_name = par.css('a span::text').get()
            if cat_name not in self.main_category:
                continue
            cat_url = par.css('a::attr(href)').get()
            print('START PARSE lvl0')
            cat_id = scrapy.Request(cat_url, callback=self.parse_cat_id)
####################
            print(f"Cat name {cat_name}, Cat url {cat_url}, Cat id {cat_id}")
            yield self.parse_lvl1_cat(par)

    def parse_lvl1_cat(self, par):
        print('START PARSE lvl1')
        for sub_cat in par.css('.level1.parent.parent'):
            print('next level')
            cat_name = sub_cat.css('h2 a span::text').get()
            cat_url = sub_cat.css('h2 a::attr(href)').get()
            cat_id = scrapy.Request(cat_url, callback=self.parse_cat_id)
            print(f"Cat name {cat_name}, Cat url {cat_url}, Cat id {cat_id}")

            print('NEXT_NEXT LVL')
            for sub_sub_cat in sub_cat.css('.level1.submenu li'):
                sub_cat_url = sub_sub_cat.css('a::attr(href)').get()
                sub_cat_name = sub_sub_cat.css('a span').get()
                sub_cat_id = scrapy.Request(sub_cat_url, callback=self.parse_cat_id)
                print(f"SUB_Cat name {sub_cat_name}, Cat url {sub_cat_url}, Cat id {sub_cat_id}")


    def parse_cat_id(self, response):
        cat_id = urlparse(response.css('#load-more::attr(data-url)').get()).query.split('id=')[-1]
        print(cat_id)
        response.meta['id'] = cat_id
        return response.meta['id']


    def get_prod_url(self, cat_id):
        return f"https://www.manoloblahnik.com/gb/category/index/index?p=2&id={cat_id}"

    def get_product(self):
        pass