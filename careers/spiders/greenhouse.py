import scrapy 
import pandas as pd
from careers.items import JobsItem

class GreenhouseSpider(scrapy.Spider):
    name = "greenhouse"

    def start_requests(self):
        df = pd.read_csv('boards.csv')
        greenhouse_rows = df[df['Portal'] == 'Greenhouse']
        urls = list(greenhouse_rows["Jobs Page"])
        company_names = list(greenhouse_rows['Company'])
        self.url_to_company = dict(zip(urls, company_names))
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        req_url = response.request.url
        company = self.url_to_company[req_url]
        for section in response.xpath('//section'):
            header_selector = '*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]'
            section_title = section.xpath(f'./{header_selector}/text()').extract_first()
            if not section_title:
                section_title = "N/A"
            for opening in section.xpath('./div[@class="opening"]'):
                job_name = opening.xpath('./a/text()').extract_first()
                job_application_url = opening.xpath('./a/@href').extract_first()
                job_application_url = response.urljoin(job_application_url)
                location = opening.xpath('./span[@class="location"]/text()').extract_first()
                yield {
                    'company' : company.strip(),
                    'job' : job_name.strip(),
                    'application' : job_application_url.strip(),
                    'category' : section_title.strip(),
                    'location': location.strip()
                }








