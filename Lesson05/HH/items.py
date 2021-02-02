# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class HeadHunterVacancyItem(scrapy.Item):
    _id = scrapy.Field()
    url = scrapy.Field()
    item_type = scrapy.Field()
    vacancy_title = scrapy.Field()
    vacancy_salary = scrapy.Field()
    company_name = scrapy.Field()
    company_city = scrapy.Field()
    company_link = scrapy.Field()
    vacancy_description = scrapy.Field()
    vacancy_skills = scrapy.Field()


class HeadHunterEmployerItem(scrapy.Item):
    _id = scrapy.Field()
    url = scrapy.Field()
    item_type = scrapy.Field()
    company_url = scrapy.Field()
    spheres = scrapy.Field()
    company_name = scrapy.Field()
    vacancies_link = scrapy.Field()
