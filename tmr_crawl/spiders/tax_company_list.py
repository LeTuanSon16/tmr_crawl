import scrapy
from scrapy.crawler import CrawlerProcess
from urllib.parse import urljoin


class TaxCompanyListSpider(scrapy.Spider):
    name = 'tax_company_list'
    start_urls = [
        "https://www.gdt.gov.vn/wps/portal/!ut/p/z1/tZNfT4MwFMU_jY_kXqAU9ghMB4ouG-4PfVkYIFRH2bBh-u1lcya-MDTL-tCmybm_c3J7CwyWwETc8DyWvBLxpr1HjK6QDPzAmodjhwYO2mE49P3wTsMJgcVR4I5sj5gBokVGiD5xxk-eO1HR14H9pR47lo199XNgwBIht7KAqIhFxW_wncus3WMlFXWdNPIg2SY8hYiaVmaq61RJEDWFGDRVLBKnijagKR1oqqoa-k-kbk92PvHi4PebMDWG5Eh4cJ05hmNyEpzrWp9J1IY0u0MasGh4toeZqOqyfcfwnz3w-hwoXujQg9eui1evi9cvxN8DyzfV-vsD8tfdjtntlFdCZh8Sll1jvi1ns9LSP5W3qbV_finycvV4qxunY5N_AexGVMM!/dz/d5/L2dBISEvZ0FBIS9nQSEh/"]

    custom_settings = {
        'FEEDS': {'tax_company_data.csv': {'format': 'csv', 'encoding': 'utf-8-sig', 'overwrite': True}},
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 1,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_links = 100
        self.visited_links = 0
        self.visited_urls = set()

    def parse(self, response):
        # Xử lý bảng dữ liệu
        rows = response.css('table.ta_border tr')
        for row in rows:
            if row.css('th'): continue

            cells = row.css('td')
            if len(cells) < 5: continue

            yield {
                'ngay_quyet_dinh': cells[0].css('::text').get('').strip(),
                'so_quyet_dinh': cells[1].css('::text').get('').strip(),
                'co_quan_ban_hanh': cells[2].css('::text').get('').strip(),
                'quyet_dinh': urljoin(response.url, cells[3].css('a::attr(href)').get('') or ''),
                'danh_sach_doanh_nghiep': urljoin(response.url, cells[4].css('a::attr(href)').get('') or '')
            }

        if self.visited_links >= self.max_links:
            return

        self.visited_urls.add(response.url)
        pagination_links = response.css('div.page a[title^="Link to page"]::attr(href)').getall()

        for link in pagination_links:
            abs_url = urljoin(response.url, link)
            if abs_url not in self.visited_urls and self.visited_links < self.max_links:
                self.visited_links += 1
                yield scrapy.Request(url=abs_url, callback=self.parse)


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(TaxCompanyListSpider)
    process.start()