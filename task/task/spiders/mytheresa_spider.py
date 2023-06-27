import scrapy
import json


class MyTheresaSpider(scrapy.Spider):
    name = "mytheresa"
    start_urls = ["https://www.mytheresa.com/int/en/men/shoes?rdr_src=mag"]
    counter = 0 

    def parse(self, response):
        product_urls_type1 = response.css(
            'div.list__container div.item.item--sale a.item__link::attr(href)').getall()
        product_urls_type2 = response.css(
            'div.list__container div.item.item a.item__link::attr(href)').getall()
        product_urls = product_urls_type1 + product_urls_type2

        for index, url in enumerate(product_urls):
            yield response.follow(url, self.parse_product, priority=index)

        # Check if the counter has reached the limit
        if self.counter < 1000:
            next_page_url = response.css(
                'div.list__pagination div.pagination__item[data-label="nextPage"]::attr(data-index)').get()
            if next_page_url:
                next_page_url = response.urljoin(f'?page={next_page_url}')
                yield scrapy.Request(next_page_url, callback=self.parse)

    def parse_product(self, response):
        def clean_data(value):
            if value:
                value = value.strip()
                value = value.replace("Item number: ", "")
                value = value.replace("<span class=\"pricing__prices__price\"> <!-- -->\u20ac", "€")
                value = value.replace("</span>", "")
            return value


        data = {
            "breadcrumb": [breadcrumb.strip() for breadcrumb in response.xpath('//div[@class="breadcrumb"]//a/text()').getall()],
            "image_url": response.xpath('//img[@class="product__gallery__carousel__image"]/@src').get(),
            "brand": clean_data(response.xpath('//div[contains(@class, "productinfo__designer")]/text()').get()),
            "product_name": clean_data(response.xpath('//div[@class="productinfo__name"]/text()').get()),
            "listing_price": clean_data(response.xpath('//span[@class="pricing__prices__original"]/span[@class="pricing__prices__price"]').get()),
            "offer_price": clean_data(response.xpath('//span[@class="pricing__prices__discount"]/span[@class="pricing__prices__price"]').get()),
            "discount": clean_data(response.xpath('//span[@class="pricing__info__percentage"]/text()').get()),
            "product_id_text": clean_data(response.xpath('//div[@class="accordion__body__content"]//li[last()]/text()').get()),
            "sizes": [size.strip() for size in response.xpath('//span[contains(@class, "sizeitem__label")]/text()').getall()],
            "description": clean_data(response.xpath('//div[@class="accordion__body__content"]//p/text()').get()),
            "other_images": response.xpath('//div[@class="item__images"]//img/@src').getall(),
        }


        if self.counter < 1000:
            yield data

            self.save_to_json(data)

            self.counter += 1
            if self.counter >= 1000:
                self.log("Reached the response limit of 1000. Stopping the spider")

    def save_to_json(self, data):
        filename = "output.json"
        with open(filename, "a") as file:
            json.dump(data, file,ensure_ascii=False)
            file.write("\n")