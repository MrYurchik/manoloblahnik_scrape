import json
import re
from bs4 import BeautifulSoup
import scrapy

RE_JSON = re.compile(r'"ecommerce":({.+}),')


class ManoloBlahnikSpider(scrapy.Spider):
    name = 'manoloblahnik'
    allowed_domains = ['manoloblahnik.com']
    start_urls = ['https://www.manoloblahnik.com/gb/']

    main_categories = ['Women', 'Men']
    ignore_categories = ['View All']

    def parse(self, response, *args):
        top_categories = response.css('.level0.level-top')
        for top_cat in top_categories:
            top_cat_name = top_cat.css('a span::text').get()
            if top_cat_name not in self.main_categories:
                continue

            for sub_cat in top_cat.css('.level1.parent.parent'):
                # sub_cat_name = sub_cat.css('h2 a span::text').get()
                for sub_sub_cat in sub_cat.css('.level1.submenu li'):
                    sub_sub_cat_url = sub_sub_cat.css('a::attr(href)').get()
                    sub_sub_cat_name = sub_sub_cat.css('a span::text').get()
                    if sub_sub_cat_name in self.ignore_categories:
                        continue
                    yield from self.get_page_with_products(sub_sub_cat_url)

    def get_page_with_products(self, url: str):
        cookies = {
            'auto_country_switcher': 'gb',
            'newsletter-holded': 'true',
            'X-Magento-Vary': 'f4779982487cd2ac4b16ccb8c340d6e66ae2d049',
        }

        headers = {
            'authority': 'www.manoloblahnik.com',
            'accept': '*/*',
            'accept-language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
            'referer': url,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        }

        yield scrapy.Request(url,
                             dont_filter=True,  # if needs to ignore scraped pages set to False
                             cookies=cookies,
                             headers=headers,
                             callback=self.parse_products,
                             errback=self.parse_error)

    def parse_products(self, response, *args):
        try:
            html_text = json.loads(response.text)["productsHtml"]
        except (ValueError, TypeError, KeyError):
            html_text = response.text

        soup = BeautifulSoup(html_text, "html.parser")

        for a in soup.select("li.product.show-me a"):
            onclick = a["onclick"]
            js = RE_JSON.search(onclick)
            if js:
                js = json.loads(js.group(1))["click"]

                pid = js["products"][0]["id"]
                url = a["href"]
                image = a.select_one("picture.photo.image-left img").get("data-isrcset", "").split(" 1x")[0]
                price = round(float(js["products"][0]["price"]), 2)
                name = js["products"][0]["name"]
                category = js["actionField"]["list"]

                item = dict(
                    id=pid,
                    url=url,
                    price=price,
                    name=name,
                    category=category,
                    image=image,
                )
                yield item

        next_page_url = (soup.select_one("li#load-more-container button#load-more") or dict()).get("data-url")
        if next_page_url:
            yield from self.get_page_with_products(next_page_url)

    def parse_error(self, response, *args):
        pass
