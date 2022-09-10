import json
import scrapy
import re
from scrapy_splash import SplashRequest
from urllib.parse import urlparse


class WidgetSpider(scrapy.Spider):
    name = 'widget'

    def start_requests(self):
        url = "https://careers.microsoft.com/us/en/search-results"
        parsed = urlparse(url)
        apply_url = f"{parsed.scheme}://{parsed.netloc}/us/en/job"
        company = "Microsoft"
        yield SplashRequest(url, 
                            callback=self.parse, 
                            cb_kwargs=dict(
                                base_url = url,
                                offset = 0,
                                company = company, 
                                apply_url = apply_url
                            ))
    
    def parse(self, response, base_url, offset, company, apply_url):
        scripts = response.xpath('//script[@type="text/javascript"]').extract()
        data_script = None
        for script in scripts:
            if "jobs" in script:
                data_script = script
        if data_script:
            data = re.findall('"data":{"jobs.*',data_script)
            data = re.findall('.*,"aggregations', data[0])
            data = data[0].replace(',"aggregations',"")
            data = data.replace('"data":{"jobs":',"")
            data = json.loads(data)
            for job in data:
                if "title" not in job or "jobSeqNo" not in job:
                    continue
                job_name = job["title"]
                job_id = job["jobSeqNo"]
                category = "N/A"
                locations = "N/A"
                if "category" in job:
                    category = job["category"]
                if "multi_location" in job:
                    locations = ":".join(job["multi_location"])
                elif "location" in job:
                    locations = job["location"]
                application_url = f"{apply_url}/{job_id}"
                yield {
                    'company' : company,
                    'job' : job_name.strip(),
                    'application' : application_url.strip(),
                    'category' : category.strip(),
                    'location': locations.strip()
                } 
            n_jobs = len(data)
            if n_jobs > 0:
                new_offset = offset + n_jobs
                new_url = f"{base_url}?from={new_offset}&s=1"
                yield scrapy.Request(new_url,
                                    callback=self.parse,
                                    cb_kwargs=dict(
                                        base_url = base_url,
                                        offset = new_offset,
                                        company = company,
                                        apply_url = apply_url
                                    ))






