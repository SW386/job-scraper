import scrapy 
import json

class AppleSpider(scrapy.Spider):

    name = 'apple'

    csrf_url = 'https://jobs.apple.com/api/csrfToken'
    api_url = 'https://jobs.apple.com/api/role/search'
    base_url = 'https://jobs.apple.com/en-us/details/'

    def start_requests(self):
        yield scrapy.Request(self.csrf_url,
                             callback=self.get_csrf,
                             dont_filter=True,
                             cb_kwargs = dict(
                                 page = 1
                             ))

    def get_csrf(self, response, page):
        csrf = response.headers['X-Apple-Csrf-Token']
        headers = {
            'x-apple-csrf-token' : csrf,
            'Content-Type' : 'application/json'
        }
        body = {	
	        'query':'',
	        'filters':{
                'range':{
			        'standardWeeklyHours':{
				        'start': None,
				    'end': None
			        }
		        }
	        },
	        'page':page,
	        'locale':'en-us',
	        'sort':''
        }   
        yield scrapy.Request(self.api_url, 
                            method='POST',
                            headers=headers,
                            body=json.dumps(body).encode('utf-8'),
                            callback = self.get_data,
                            dont_filter=True,
                            cb_kwargs=dict(
                                page = page
                            ))

    def get_data(self, response, page):
        data = json.loads(response.body)
        if "searchResults" in data:
            results = data["searchResults"]
            for result in results:
                num_id = result["id"].split("-")[1]
                application_link = self.base_url + num_id
                job_name = result["postingTitle"]
                category = result["team"]["teamName"]
                locations = []
                for location in result["locations"]:
                    city = location["city"]
                    state = location["stateProvince"]
                    countryName = location["countryName"]
                    combined = [city, state, countryName]
                    combined = [i for i in combined if i != ""]
                    loc = ",".join(combined)
                    locations.append(loc)
                locations = ":".join(locations)
                yield {
                    "company": "Apple",
                    "job": job_name,
                    "application": application_link,
                    "category": category,
                    "location": locations
                }
            yield scrapy.Request(self.csrf_url,
                                callback=self.get_csrf,
                                dont_filter=True,
                                cb_kwargs = dict(
                                    page = page+1
                                ))


