import json
import pdb
from bs4 import BeautifulSoup
import scrapy
from urllib.parse import urlparse


class ManoloblahnikSpider(scrapy.Spider):
    main_category = ['Women', 'Men']
    name = 'manoloblahnik'
    allowed_domains = ['manoloblahnik.com']
    start_urls = ['https://www.manoloblahnik.com/gb']
    cookies = {
        'auto_country_switcher': 'gb',
        'newsletter-holded': 'true',
        'X-Magento-Vary': 'f4779982487cd2ac4b16ccb8c340d6e66ae2d049',
    }

    headers = {
        'authority': 'www.manoloblahnik.com',
        'accept': '*/*',
        'accept-language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
        'referer': 'https://www.manoloblahnik.com/gb/women/edits/newarrivals.html',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    }

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
            pdb.set_trace()
            yield cat_id
            print(f"Cat name {cat_name}, Cat url {cat_url}, Cat id {cat_id}")
            yield from self.parse_lvl1_cat(par)

    def parse_lvl1_cat(self, par):
        print('START PARSE lvl1')
        for sub_cat in par.css('.level1.parent.parent'):
            print('next level')
            cat_name = sub_cat.css('h2 a span::text').get()
            cat_url = sub_cat.css('h2 a::attr(href)').get()
            cat_id = scrapy.Request(cat_url, callback=self.parse_cat_id)
            yield cat_id
            if not cat_id:
                yield from scrapy.Request(cat_url, callback=self.one_page_cat)
            print(f"Cat name {cat_name}, Cat url {cat_url}, Cat id {cat_id}")

            print('NEXT_NEXT LVL')
            for sub_sub_cat in sub_cat.css('.level1.submenu li'):
                sub_cat_url = sub_sub_cat.css('a::attr(href)').get()
                sub_cat_name = sub_sub_cat.css('a span').get()
                sub_cat_id = scrapy.Request(sub_cat_url, callback=self.parse_cat_id)
                sub_cat_id.meta['cat_id'] = 1
                yield sub_cat_id
                if not sub_cat_id:
                    yield from scrapy.Request(sub_cat_url, callback=self.one_page_cat)
                else:
                    yield scrapy.Request(self.get_prod_url(cat_id=sub_cat_id), callback=self.one_page_cat,
                                         cookies=self.cookies, headers=self.headers)
                print(f"SUB_Cat name {sub_cat_name}, Cat url {sub_cat_url}, Cat id {sub_cat_id}")
        return

    @staticmethod
    def parse_cat_id(response):
        load_more = response.css('#load-more::attr(data-url)').get()
        if not load_more:
            return None
        cat_id = urlparse(response.css('#load-more::attr(data-url)').get()).query.split('id=')[-1]
        # category = response.meta
        # category['cat_id'] = cat_id
        # yield category
        return cat_id

    def get_prod_url(self, cat_id, start=2):
        pdb.set_trace()
        return f"https://www.manoloblahnik.com/gb/category/index/index?p={start}&id={cat_id}"

    def one_page_cat(self, response):
        self.logger.info("Visited %s", response.url)
        print('start_scrap_product')
        product_list = []
        product_pool = json.loads(response.text)['productsHtml']
        soup = BeautifulSoup(product_pool, 'html.parser')
        product_pool = soup.select('.product.show-me')
        for product in product_pool:
            product_url = product.select_one('a')['href']
            product_info = product.select_one('a')['onclick']
            product_info = json.loads(product_info[product_info.rfind('{"name"'):product_info.rfind('"}]}') + 2])
            product_name = product_info['name']
            product_id = product_info['id']
            product_price = product_info['price']
            product_category = product_info['category']
            product_img = product.select_one('.photo.image-hover source[type="image/jpeg"]')['data-isrcset']
            print(
                f'Name {product_name} Url:{product_url}, Id {product_id}, price {product_price}, Category {product_category}, img {product_img}')
            product_list.append({'name': product_name, 'url': product_url, 'id': product_id, 'price': product_price,
                                 'category': product_category, 'img': product_img})
        return product_list
