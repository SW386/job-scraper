import scrapy 
import pandas as pd

class LeverSpider(scrapy.Spider):
    name = "lever"

    def start_requests(self):
        df = pd.read_csv('boards.csv')
        greenhouse_rows = df[df['Portal'] == 'Lever']
        urls = list(greenhouse_rows["Jobs Page"])
        company_names = list(greenhouse_rows['Company'])
        self.url_to_company = dict(zip(urls, company_names))
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        req_url = response.request.url
        company = self.url_to_company[req_url]
        for posting in response.xpath('//div[@class="posting"]'):
            job_name = posting.xpath('./a/h5/text()').extract_first()
            job_application_url = posting.xpath('./a/@href').extract_first()
            if not job_name or not job_application_url:
                continue
            job_application_url = response.urljoin(job_application_url)
            location = posting.xpath('.//span[contains(@class, "sort-by-location")]/text()').extract_first()
            category = posting.xpath('.//span[contains(@class, "sort-by-team")]/text()').extract_first()
            if not location:
                location = 'N/A'
            if not category:
                category = 'N/A'
            yield {
                'company' : company.strip(),
                'job' : job_name.strip(),
                'application' : job_application_url.strip(),
                'category' : category.strip(),
                'location': location.strip()
            }


