import scrapy 
import pandas as pd
import time
import json
import re
from urllib.parse import urljoin, urlparse
from scrapy_selenium import SeleniumRequest
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

class WorkdaySpider(scrapy.Spider):
    name = "workday"

    def start_requests(self):
        #get workday companies
        df = pd.read_csv('boards.csv')
        greenhouse_rows = df[df['Portal'] == 'Workday']
        urls = list(greenhouse_rows["Jobs Page"])
        company_names = list(greenhouse_rows['Company'])
        self.url_to_company = dict(zip(urls, company_names))
        #construct params for api calls
        body = {
            "appliedFacets": {},
            "limit": 20,
	        "offset": 0,
	        "searchText": ""
        }
        headers = {"Content-Type" : "application/json"}
        #construct api based on company
        self.api_to_url = {}
        for url in urls:
            o = urlparse(url)
            company = o.netloc.split('.')[0]
            end = o.path.split('/')[-1]
            api = f'{o.scheme}://{o.netloc}/wday/cxs/{company}/{end}/jobs'
            self.api_to_url[api] = url
            yield scrapy.Request(api,
                                method='POST',
                                body=json.dumps(body).encode('utf-8'),
                                headers=headers,
                                callback=self.parse_initial)
    
    def parse_initial(self, response):
        data = json.loads(response.body)
        #check for categories
        if 'facets' in data:
            categories = []
            category_name = ''
            for facet in data['facets']:
                if 'jobFamily' in facet['facetParameter']:
                    categories = facet['values']
                    category_name = facet['facetParameter']
            if not categories:
                #parse entire board if categories not found
                yield scrapy.Request(response.request.url, 
                                    method='POST',
                                    body=response.request.body,
                                    headers=response.request.headers,
                                    callback=self.parse_job_board,
                                    cb_kwargs={
                                        'category': 'N/A',
                                        'limit': 20,
                                        'offset': 0,
                                        'total': data["total"]
                                    })
            else:
                #parse board split based on categories
                for category in categories:
                    body = {
                        "appliedFacets": {
                            category_name : [category["id"]]
                        },
                        "limit": 20,
	                    "offset": 0,
	                    "searchText": ''
                    }
                    yield scrapy.Request(response.request.url,
                                        method='POST',
                                        body=json.dumps(body).encode('utf-8'),
                                        headers=response.request.headers,
                                        callback=self.parse_job_board,
                                        cb_kwargs={
                                            'category': category['descriptor'],
                                            'limit': 20,
                                            'offset': 0,
                                            'total': category['count']
                                        })

    def parse_job_board(self, response, category, limit, offset, total):
        data = json.loads(response.body)
        for posting in data['jobPostings']:
            if 'externalPath' not in posting or 'title' not in posting:
                continue
            api_url = response.request.url
            original_url = self.api_to_url[api_url]
            company = self.url_to_company[original_url]
            #the api url provides location data
            #the application url is where you apply to the job
            job_api_url = response.request.url[:-5] + posting['externalPath']
            application_url = original_url + posting['externalPath']
            yield scrapy.Request(job_api_url, 
                                headers=response.request.headers,
                                callback=self.parse_job,
                                cb_kwargs={
                                    'company' : company,
                                    'job_name' : posting['title'],
                                    'application' : application_url,
                                    'category' : category
                                })
        if offset < total:
            #progress to next page in job board
            body = response.request.body
            body = json.loads(body.decode('utf-8'))
            body['offset'] += limit
            yield scrapy.Request(response.request.url, 
                                method='POST',
                                body=json.dumps(body).encode('utf-8'),
                                headers=response.request.headers,
                                callback=self.parse_job_board,
                                cb_kwargs={
                                        'category': category,
                                        'limit': limit,
                                        'offset': offset + limit,
                                        'total': total
                                })

    def parse_job(self, response, company, job_name, application, category):
        #construct location and save
        data = json.loads(response.body)['jobPostingInfo']
        location = 'N/A'
        if 'location' in data:
            location = data['location']
            if 'additionalLocations' in data and len(data['additionalLocations']) > 0:
                locations = [location] + data['additionalLocations']
                location = ':'.join(locations)
            if 'country' in data and 'descriptor' in data['country']:
                location = location + ':' + data['country']['descriptor']
        yield {
            'company': company.strip(), 
            'job': job_name.strip(),
            'application': application.strip(),
            'category': category.strip(), 
            'location': location,
        }

# class SeleniumWorkdaySpider(scrapy.Spider):
#     name = "workday"

#     custom_settings = {
#         "FEEDS" : {"jobs_workday.csv" : {"format" : "csv"}}
#     }

#     def start_requests(self):
#         df = pd.read_csv('boards.csv')
#         greenhouse_rows = df[df['Portal'] == 'Workday']
#         urls = list(greenhouse_rows["Jobs Page"])
#         company_names = list(greenhouse_rows['Company'])
#         self.url_to_company = dict(zip(urls, company_names))
#         for url in urls:
#             yield SeleniumRequest(url=url, 
#                                   callback=self.parse_board,
#                                   wait_time=10,
#                                   wait_until=EC.presence_of_element_located((By.XPATH, "//section/ul/li//a")))
    
#     def parse_board(self, response):
#         driver = response.request.meta['driver']
#         req_url = response.request.url
#         company = self.url_to_company[req_url]
#         last_page = False
#         while not last_page:
#             job_section = driver.find_element_by_xpath('//section/ul')
#             job_section_html = job_section.get_attribute('innerHTML')
#             soup = BeautifulSoup(job_section_html, 'html.parser')
#             for li in soup.find_all('li', recursive=False):
#                 title = li.find('a')
#                 subtitle = li.find_all('li')
#                 if not title or not subtitle:
#                     continue
#                 job_name = title.get_text()
#                 application = urljoin(req_url, title['href'])
#                 category = "N/A"
#                 if len(subtitle) > 1:
#                     category = subtitle[1].get_text()
#                 yield scrapy.Request(url=application,
#                                       callback=self.parse_application,
#                                       cb_kwargs= {
#                                           "company" : company,
#                                           "job_name" : job_name,
#                                           "application" : application,
#                                           "category" : category
#                                       })
#             try:
#                 next_button = driver.find_element_by_xpath('//button[@aria-label="next"]')
#                 next_button.click()
#                 time.sleep(0.2)
#             except:
#                 last_page = True
#         driver.close()

#     def parse_application(self, response, company, job_name, application, category):
#         try: 
#             script = response.xpath('//script[@type="application/ld+json"]/text()').extract_first()
#             regex = "(.+?)"
#             country = script.split('"addressCountry"')[1].split(",")[0].strip()
#             country = country.lstrip(': "').rstrip('"')
#             locality = script.split('"addressLocality"')[1].split("}")[0].strip()
#             locality = locality.lstrip(': "').rstrip('"')
#             location = locality + ":" + country
#         except:
#             location = "N/A"

#         yield {
#             "Company": company.strip(), 
#             "Job": job_name.strip(),
#             "Application": application.strip(),
#             "Category": category.strip(), 
#             "Location": location,
#         }

        

    
    

