import scrapy
from ..loaders import HeadHunterVacancyLoader, HeadHunterEmployerLoader


class HeadHunterSpider(scrapy.Spider):
    main_url = 'https://hh.ru'

    name = 'head_hunter'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']

    xpath_query = {
        "vacancy_list": "//div[contains(@class, 'vacancy-serp-item__info')]//a/@href",
        "pagination": "//div[contains(@class, 'bloko-gap')]//a[contains(@class, 'HH-Pager-Control')]/@href"
    }

    vacancy_list_query = {
        'vacancy_title': "//div[@class='vacancy-title']//h1[@data-qa='vacancy-title']/text()",
        'vacancy_salary': "//div[@class='vacancy-title']/p[@class='vacancy-salary']/span/text()",
        'company_name': "//div[@class='vacancy-company__details']/a/span/text()",
        'company_city': "//div[@data-qa='vacancy-company']/p[@data-qa = 'vacancy-view-location']/text()",
        'company_link': "//div[@class='vacancy-company__details']/a/@href",
        'vacancy_description': "//div[@class='vacancy-section']//text()",
        'vacancy_skills': "//div[contains(@data-qa,'skills-element')]/text()"
    }

    employer_query = {
        'company_name': "//div[@class='company-header']//h1//span[@class='company-header-title-name']/text()",
        'company_url': "//div[@class='employer-sidebar-content']//a[@data-qa='sidebar-company-site']/@href",
        'spheres': "//div[@class='employer-sidebar-block']/div[@class='bloko-text-emphasis']/..//p/text()",
        'vacancies_link': "//div[@class='employer-sidebar-block']/a[contains(@data-qa,'employer-vacancies-link')]/@href"
    }

    @staticmethod
    def gen_tasks(response, link_list, callback):
        for link in link_list:
            yield response.follow(link, callback=callback)

    def urls_prepare(self, response, xpath_query_key):
        return response.xpath(self.xpath_query[xpath_query_key]).getall()

    def vacancy_list_parse(self, response):
        yield from self.gen_tasks(
            response, self.urls_prepare(response, "pagination"), self.vacancy_list_parse
        )
        yield from self.gen_tasks(
            response, self.urls_prepare(response, "vacancy_list"), self.vacancy_parse
        )

    def parse(self, response):
        yield from self.gen_tasks(
            response, self.urls_prepare(response, "pagination"), callback=self.vacancy_list_parse
        )

    def vacancy_parse(self, response):
        loader = HeadHunterVacancyLoader(response=response)
        loader.add_value("url", response.url)
        loader.add_value("item_type", 'vacancy')

        for key, xpath_query in self.vacancy_list_query.items():
            loader.add_xpath(key, xpath_query)

        data = loader.load_item()
        yield data
        try:
            yield response.follow(
                response.xpath(self.vacancy_list_query['company_link']).get(), callback=self.employer_parse)
        except ValueError:
            print('---------------------------------------------------------------------')
            print(data)
            print('---------------------------------------------------------------------')

    def employer_parse(self, response):
        loader = HeadHunterEmployerLoader(response=response)
        loader.add_value("url", response.url)

        loader.add_value("item_type", 'employer')
        loader.add_value('company_name', '')
        loader.add_value('company_url', '')
        loader.add_value('spheres', '')

        for key, xpath_query in self.employer_query.items():
            loader.add_xpath(key, xpath_query)

        result = loader.load_item()
        if len(result['company_name']) > 1 and len(result['url']) > 1 and len(result['url']) > 1:
            yield result

        vacancies_link_url = response.xpath(self.employer_query['vacancies_link']).get()
        if vacancies_link_url is not None:
            yield response.follow(vacancies_link_url, callback=self.vacancy_list_parse)

