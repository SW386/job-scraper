# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from importlib import import_module

from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware

from selenium.webdriver.support.ui import WebDriverWait
from scrapy_selenium import SeleniumRequest

from stem import Signal
from stem.control import Controller


class SeleniumMiddleware:
    """Scrapy middleware handling the requests using selenium"""

    def __init__(self, driver_name, driver_executable_path, driver_arguments, browser_executable_path):
        webdriver_base_path = f'selenium.webdriver.{driver_name}'
        driver_klass_module = import_module(f'{webdriver_base_path}.webdriver')
        self.driver_klass = getattr(driver_klass_module, 'WebDriver')
        driver_options_module = import_module(f'{webdriver_base_path}.options')
        driver_options_klass = getattr(driver_options_module, 'Options')
        driver_options = driver_options_klass()
        if browser_executable_path:
            driver_options.binary_location = browser_executable_path
        for argument in driver_arguments:
            driver_options.add_argument(argument)
        self.driver_kwargs = {
            'executable_path': driver_executable_path,
            f'{driver_name}_options': driver_options
        }

    @classmethod
    def from_crawler(cls, crawler):
        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME')
        driver_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        browser_executable_path = crawler.settings.get('SELENIUM_BROWSER_EXECUTABLE_PATH')
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS')
        if not driver_name or not driver_executable_path:
            raise NotConfigured('SELENIUM_DRIVER_NAME and SELENIUM_DRIVER_EXECUTABLE_PATH must be set')
        middleware = cls(
            driver_name=driver_name,
            driver_executable_path=driver_executable_path,
            driver_arguments=driver_arguments,
            browser_executable_path=browser_executable_path
        )

        return middleware

    def process_request(self, request, spider):
        if not isinstance(request, SeleniumRequest):
            return None
        driver = self.driver_klass(**self.driver_kwargs)
        driver.get(request.url)
        for cookie_name, cookie_value in request.cookies.items():
            driver.add_cookie({
                'name': cookie_name,
                'value': cookie_value
            })
        if request.wait_until:
            WebDriverWait(driver, request.wait_time).until(request.wait_until)
        if request.screenshot:
            request.meta['screenshot'] = driver.get_screenshot_as_png()
        if request.script:
            driver.execute_script(request.script)
        body = str.encode(driver.page_source)
        request.meta.update({'driver': driver})
        return HtmlResponse(
            driver.current_url,
            body=body,
            encoding='utf-8',
            request=request
        )

class ProxyMiddleware(HttpProxyMiddleware):
    """Scrapy middleware for issuing a new IP address if necessary"""

    def __init__(self, proxy_url, proxy_pass, ban_sites):
        self.proxy_url = proxy_url
        self.proxy_pass = proxy_pass
        self.ban_sites = ban_sites
        super(ProxyMiddleware, self).__init__()

    @classmethod
    def from_crawler(cls, crawler):
        proxy_url = crawler.settings.get('PROXY_URL')
        proxy_pass = crawler.settings.get('PROXY_PASSWORD')
        ban_sites = crawler.settings.get('IP_BAN_SITES')
        if not proxy_url or not proxy_pass or not ban_sites:
            raise NotConfigured('PROXY_URL, PROXY_PASSWORD, and IP_BAN_SITES must be set')
        middleware = cls(
            proxy_url = proxy_url,
            proxy_pass = proxy_pass,
            ban_sites = ban_sites
        )
        return middleware

    def new_tor_identity(self):
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password=self.proxy_pass)
            controller.signal(Signal.NEWNYM)

    def process_request(self, request, spider):
        url = request.url
        for ban_site in self.ban_sites:
            if ban_site in url:
                self.new_tor_identity()
                request.meta['proxy'] = self.proxy_url