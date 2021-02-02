from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose
from .items import HeadHunterVacancyItem, HeadHunterEmployerItem
from urllib.parse import urljoin


def clear_garbage_symbols(value):
    value = value.replace("\u2009", "")
    value = value.replace("\xa0", "")
    return value.strip()


def clear_empty_items(values):
    return [value for value in values if value != '']


def join_str(values):
    return (' '.join(values)).strip()


class HeadHunterVacancyLoader(ItemLoader):
    default_item_class = HeadHunterVacancyItem
    url_out = TakeFirst()
    vacancy_title_out = TakeFirst()
    vacancy_salary_in = MapCompose(clear_garbage_symbols, "".join)
    vacancy_salary_out = TakeFirst()
    company_name_in = "".join
    company_name_out = TakeFirst()
    company_city_out = TakeFirst()
    company_link_in = MapCompose(lambda url: urljoin('https://hh.ru', url))
    company_link_out = TakeFirst()
    vacancy_description_in = "".join
    vacancy_description_out = TakeFirst()
    item_type_out = TakeFirst()


class HeadHunterEmployerLoader(ItemLoader):
    default_item_class = HeadHunterEmployerItem
    item_type_out = TakeFirst()
    company_url_out = TakeFirst()
    company_name_in = MapCompose(''.join, clear_garbage_symbols)
    company_name_out = join_str
    spheres_out = clear_empty_items
    url = TakeFirst()
    vacancies_link_out = TakeFirst()
