import scrapy
import json
from copy import deepcopy
from urllib.parse import urlencode

class AmazonSpider(scrapy.Spider):

    name = 'amazon'

    api_url = 'https://www.amazon.jobs/en/search.json'
    base_url = 'https://www.amazon.jobs'
    subdivisions = {
        "Amazon Retail": "retail",
        "Amazon Web Services": "amazon-web-services",
        "Amazon Operations Technology": "operations-technology",
        "Amazon Devices": "amazon-devices",
        "Amazon Alexa": "alexa",
        "Amazon Financial & Global Business Services": "finance",
        "Amazon Advertising": "advertising",
        "Amazon Human Resources": "humanresources",
        "Amazon Fulfillment & Operations": "fulfillment-operations",
        "Amazon Entertainment": "amazon-entertainment",
        "Amazon eCommerce Foundation": "ecommerce-platform",
        "Amazon Transportation": "transport",
        "Amazon Marketplace": "seller-services",
        "Amazon Customer Trust & Partner Support": "customer-trust-and-partner-support",
        "Amazon Consumer Payments": "consumer-payments",
        "Amazon Subsidiaries": "subsidiaries",
        "Amazon Go": "amazongo",
        "Amazon Consumer Engagement": "consumerengagement",
        "Amazon Kindlle Content": "kindle-content",
        "Amazonian Experience & Technology": "amazonian-experience-and-technology",
        "Amazon Selling Partner Services": "selling-partner-services",
        "Amazon Fresh": "amazonfresh",
        "Amazon Business & Corporate Development": "business-corporate-development",
        "Amazon Legal": "legal-team",
        "Amazon Student Programs": "student-programs",
        "Amazon Global Corporate Affairs": "gca",
        "Amazon Customer Service": "amazon-customer-service",
        "Amazon Customer Experience & Business Trends": "customer-experience-business-trends",
        "Amazon Care": "amazon-care",
        "Amazon XCM (Cross-Channel, Cross-Category Marketing)": "cross-channel-cross-category-marketing",
        "Amazon Health Storefront & Tech": "HSST",
    }
    categories = {
        "Software Development": "software-development",
        "Solutions Architect": "solutions-architect",
        "Operations, IT, & Support Engineering": "operations-it-support-engineering",
        "Project/Program/Product Management-- Technical": "project-program-product-management-technical",
        "Project/Program/Product Management-- Non Technical": "project-program-product-management-non-tech",
        "Sales, Advertising, & Account Management": "sales-advertising-account-management",
        "Human Resources": "human-resources",
        "Systems, Quality, & Security Engineering":  "systems-quality-security-engineering",
        "Finance, Accounting, & Global Business Services": "finance-accounting",
        "Business Intelligence": "business-intelligence",
        "Business & Merchant Development": "business-merchant-development",
        "Marketing": "marketing-pr",
        "Machine Learning Science": "machine-learning-science",
        "Fulfillment & Operations Management": "fulfillment-operations-management",
        "Amazon Design": "design",
        "Editorial, Writing, & Content Management": "editorial-writing-content-management",
        "Buying, Planning, & Instock Management": "buying-planning-instock-management",
        "Customer Service": "customer-service",
        "Facilities, Maintenance, & Real Estate": "facilities-maintenance-real-estate",
        "Hardware Development": "hardware-development",
        "Data Science": "data-science",
        "Supply Chain/Transportation Management": "supply-chain-transportation-management",
        "Medical, Health, & Safety": "medical-health-safety",
        "Administrative Support": "administrative-support",
        "Investigation & Loss Prevention": "investigation-loss-prevention",
        "Research Science": "research-science",
        "Leadership Development & Training": "leadership-development-training",
        "Legal": "legal",
        "Public Relations & Communications": "public-relations",
        "Audio/Video/Photography Production": "audio-video-photography-production",
        "Database Administration": "database-administration",
        "Public Policy": "public-policy",
        "Economics": "economics",
        "Fulfillment Associate": "fulfillment-warehouse-associate"
    }

    def start_requests(self):
        for company, key in self.subdivisions.items():
            params = {
                "sort": "recent",
                "business_category[]": key,
                "offset": 0,
                "result_limit": 100,
            }
            urlparams = urlencode(params)
            url = self.api_url + '?' + urlparams
            yield scrapy.Request(url, 
                                callback=self.parse, 
                                cb_kwargs=dict(
                                    params=params,
                                    company=company
                                ))



    def parse(self, response, params, company):
        data = json.loads(response.body)
        if data['hits'] > 9999 and 'category[]' not in params:
            for category, key in self.categories.items():
                new_params = deepcopy(params)
                new_params['category[]'] = category
                urlparams = urlencode(new_params)
                url = self.api_url + '?' + urlparams
                yield scrapy.Request(url, 
                                    callback=self.parse,
                                    cb_kwargs=dict(
                                        params=new_params,
                                        company=company
                                    ))
        elif data['jobs']:
            for job in data['jobs']:
                job_name = job['title']
                category = job['job_category']
                location = job['normalized_location']
                path = job['job_path']
                application_link = self.base_url + path
                yield {
                    "company": company,
                    "job": job_name,
                    "application": application_link,
                    "category": category,
                    "location": location
                }
            if params['offset'] < data['hits']:
                params['offset'] += 100
                urlparams = urlencode(params)
                url = self.api_url + '?' + urlparams
                yield scrapy.Request(url, 
                                    callback=self.parse,
                                    cb_kwargs=dict(
                                        params=params,
                                        company=company
                                    ))
            

