# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TmrCrawlItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class TaxCompanyListItem(scrapy.Item):
    ngay_quyet_dinh = scrapy.Field()
    so_quyet_dinh = scrapy.Field()
    co_quan_ban_hanh = scrapy.Field()
    quyet_dinh = scrapy.Field()
    danh_sach_doanh_nghiep = scrapy.Field()
    pass
