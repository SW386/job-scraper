import scrapy 
import json
import math

class GoogleSpider(scrapy.Spider):

    name = "google"

    base_url = "https://careers.google.com/results/"

    def start_requests(self):
        company_urls = {
            "Fitbit (Google)": ["https://careers.google.com/api/v3/search/?company=Fitbit&page_size=100&sort_by=date"],
            "Google Fiber": ["https://careers.google.com/api/v3/search/?company=Google%20Fiber&page_size=100&sort_by=date"],
            "Loon (Google)": ["https://careers.google.com/api/v3/search/?company=Loon&page_size=100&sort_by=date"],
            "Youtube (Google)": ["https://careers.google.com/api/v3/search/?company=Youtube&page_size=100&sort_by=date"],
            "Wing (Google)": ["https://careers.google.com/api/v3/search/?company=Wing&page_size=100&sort_by=date"],
            "Google": ["https://careers.google.com/api/v3/search/?company=Google&page_size=100&sort_by=date&degree=ASSOCIATE",
                       "https://careers.google.com/api/v3/search/?company=Google&page_size=100&sort_by=date&degree=BACHELORS",
                       "https://careers.google.com/api/v3/search/?company=Google&page_size=100&sort_by=date&degree=DOCTORATE",
                       "https://careers.google.com/api/v3/search/?company=Google&page_size=100&sort_by=date&degree=MASTERS",
                       "https://careers.google.com/api/v3/search/?company=Google&page_size=100&sort_by=date&degree=ENTRY_LEVEL"],
            "Waymo (Google)": ["https://careers.google.com/api/v3/search/?company=Waymo&page_size=100&sort_by=date"],
            "Verily Life Sciences (Google)": ["https://careers.google.com/api/v3/search/?company=Verily%20Life%20Sciences&page_size=100&sort_by=date"]
        }
        for company, urls in company_urls.items():
            for url in urls:
                yield scrapy.Request(url,
                                    callback=self.parse,
                                    cb_kwargs=dict(
                                        base_url = url,
                                        company = company
                                    ))

    def parse(self, response, base_url, company):
        data = json.loads(response.body)
        count = data['count']
        next_page = data['next_page']
        for job in data['jobs']:
            categories = job['categories']
            locations = job['locations']
            id = job['id'].split('/')[1]
            for i, category in enumerate(categories):
                category = category.lower()
                categories[i] = category
            categories = ":".join(categories)
            for i, location in enumerate(locations):
                locations[i] = location["display"]
            locations = ":".join(locations)
            job_application_url = self.base_url + id
            yield {
                'company' : company, 
                'job' : job['title'],
                'application' : job_application_url,
                'category' : categories,
                'location': locations
            }
        if len(data['jobs']) > 0:
            new_url = base_url + f"&page={next_page}"
            yield scrapy.Request(url=new_url, 
                                callback=self.parse,
                                cb_kwargs=dict(
                                    base_url = base_url,
                                    company = company
                                ))

    

        
        
        

        



        

