import scrapy 

class FacebookSpider(scrapy.Spider):

    name = "facebook"

    start_urls = ["https://www.metacareers.com/jobs?page=1&results_per_page=100#search_result"]

    def parse(self, response):
        for job_opening in response.xpath('//a[@class="_8sef"]'):
            relative_link = job_opening.xpath('./@href').extract_first()
            application_link = response.urljoin(relative_link)
            job_name = job_opening.xpath('.//div[@class="_8sel"]/text()').extract_first()
            location_div = job_opening.xpath('.//div[@class="_8sen"]')
            location_div_specific = location_div.xpath('.//div[@class="_8see"]')
            if location_div_specific:
                locations = self.extract_subtitle(location_div_specific[0])
            else: 
                locations = "N/A"
            category_div = job_opening.xpath('.//div[@class="_8seh"]')
            category_div_specific = category_div.xpath('.//div[@class="_8see"]')
            if len(category_div_specific) > 0:
                categories = []
                for div in category_div_specific:
                    category = self.extract_subtitle(div)
                    categories.append(category)
                categories = ":".join(categories)
            else: 
                categories = "N/A"
            yield {
                'company' : 'Facebook',
                'job' : job_name.strip(),
                'application' : application_link.strip(),
                'category' : categories.strip(),
                'location': locations.strip()
            }
        buttons = response.xpath('//a[@role="button"]')
        for button in buttons:
            text = button.xpath('./text()').extract_first()
            if text == "Next":
                next_page_link = button.xpath('./@href').extract_first()
                next_page_url = response.urljoin(next_page_link)
                yield scrapy.Request(url=next_page_url, callback=self.parse)

    def extract_subtitle(self, subtitle_selector):
        primary_text = subtitle_selector.xpath('./text()').extract_first()
        supplemental = subtitle_selector.xpath('./div[@class="_9o36"]')
        if supplemental:
            supplemental_texts = supplemental.xpath('./@data-tooltip-content').extract_first()
            supplemental_texts = supplemental_texts.split('\n')
            supplemental_texts = [t.strip() for t in supplemental_texts]
            combined_texts = [primary_text] + supplemental_texts
            combined_texts = ":".join(combined_texts)
            return combined_texts
        return primary_text



            

