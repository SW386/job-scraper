import scrapy 
import json
from urllib.parse import urlencode

class BloombergSpider(scrapy.Spider):

    name = 'bloomberg'

    api_url = 'https://careers.bloomberg.com/job_search/search_query'
    base_url = 'https://careers.bloomberg.com/job/detail/'


    def start_requests(self):
        headers = {
            'X-Requested-With' : 'XMLHttpRequest'
        }
        query = {
            'jobStartIndex' : 0,
            'jobBatchSize' : 5000
        }
        params = urlencode(query)
        url = f'{self.api_url}?{params}'
        yield scrapy.Request(url, 
                            headers=headers,
                            callback = self.parse)
    
    def parse(self, response):
        data = json.loads(response.body)
        jobs = data['jobData']
        for job in jobs:
            job_id = job['JobReqNbr']
            job_name = job['JobTitle']
            job_category = job['Specialty']['Value']
            job_city = job['Office']['City']
            job_state = job['Office']['State']
            job_country = job['Office']['Country']
            if job_state:
                location = f'{job_city},{job_state},{job_country}'
            else:
                location = f'{job_city},{job_country}'
            application_url = self.base_url + job_id
            yield {
                'company': 'Bloomberg',
                'job': job_name,
                'application' : application_url,
                'category': job_category,
                'location': location
            }



