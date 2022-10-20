import pathlib
from multiprocessing import Pool, cpu_count
from functools import partial
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import json
import time
import os


my_user_agent = 'user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
options = webdriver.ChromeOptions()
options.add_argument(f'useragent={my_user_agent}')
options.add_argument('--disable-blink-features=AutomationControlled')


def get_list_links(category_url: str):
    """
    Получает список ссылок на товары с первой страницы каталога
    :param category_url: str - ссылка на категорию товаров. Получаем прямым копированием с адресной строки выбранной
    категории
    :return: list - список ссылок на товары с первой страницы открытой категории.
    """
    page = 1
    list_of_links = []

    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    browser.get(url=f'{category_url}&p={page}')
    time.sleep(2)
    link_cards_tag = browser.find_element(by=By.CLASS_NAME, value="products-page__list")
    link_cards_block = link_cards_tag.find_elements(by=By.CLASS_NAME, value='catalog-product__name')
    list_href = []
    for link in link_cards_block:
        list_href.append(link.get_attribute('href'))
    list_of_links.extend(list_href)
    page += 1
    return list_of_links


def multiprocess_get_list_links(category_url: str, quantity_page: int) -> List[str]:
    """
    Функция принимает ссылку на категорию товаров и количество страниц, с которых необходимо парсить информацию.
    Функция работает в мушьтипроцессоном режиме и запускает функцию get_list_links
    Возвращает список со ссылками на каждый товар в отдельности.
    :param category_url: str - Ссылка на категорию товаров
    :param quantity_page: int - Количество страниц товара для парсинга
    :return: list - Список ссылок на товары.
    """
    list_of_pages = [f'{category_url}&p={page}' for page in range(1, quantity_page + 1)]
    with Pool(processes=cpu_count()) as pool:
        links = pool.map(get_list_links, list_of_pages)
    result = []
    [result.extend(link) for link in links]
    return result


def get_product(category_name: str, args: tuple) -> dict:
    """
    Функция собирает данные о конкретном продукте.
    :param category_name: str - категория товара, который в данный момент обрабатывается
    :param args: tuple - кортеж из двух элементов (ссылка на продукт, порядковый номер продукта). Порядковый номер
    продукта будет записан в имени файла его изображения с добавлением .png
    :return: dict - словарь с названием характеристики и его значением
    """

    product = {}
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    browser.get(url=args[0])
    browser.maximize_window()
    time.sleep(1)
    image = browser.find_element(by=By.CLASS_NAME, value='product-images-slider__img')
    image.click()
    time.sleep(5)
    image = browser.find_element(by=By.CLASS_NAME, value='media-viewer-image__main-img')
    image_screen = image.screenshot_as_png
    with open(f'{category_name}/{args[1]}.png', 'bw') as file:
        file.write(image_screen)
    product['image'] = f'{args[1]}.png'
    time.sleep(2)
    button_close = browser.find_element(by=By.CLASS_NAME, value='media-viewer__close')
    button_close.click()
    time.sleep(5)
    name = browser.find_element(by=By.TAG_NAME, value='h1').text
    product['name'] = name
    price_tag = browser.find_element(by=By.CLASS_NAME, value='product-buy__price')
    price = price_tag.text
    price = price.replace(' ', '')[:-1]
    product['price'] = price
    page_down = browser.find_element(by=By.TAG_NAME, value='html')
    page_down.send_keys(Keys.PAGE_DOWN)
    time.sleep(5)
    describe = browser.find_element(by=By.CLASS_NAME, value='product-card-description-text').text
    product['describe'] = describe
    category = browser.find_elements(by=By.CLASS_NAME, value='product-characteristics__spec-value')[1].text
    product['category'] = category
    button = browser.find_element(by=By.CLASS_NAME, value='product-characteristics__expand')
    button.click()
    time.sleep(5)
    characteristic_title_class = browser.find_elements(by=By.CLASS_NAME,
                                                       value='product-characteristics__spec-title')
    characteristic_value_class = browser.find_elements(by=By.CLASS_NAME,
                                                       value='product-characteristics__spec-value')
    characteristic_title = [item.text for item in characteristic_title_class]
    characteristic_value = [item.text for item in characteristic_value_class]
    features = dict(zip(characteristic_title, characteristic_value))
    product['features'] = features
    return product


def multiprocess_get_product(list_links, category_name):
    """
    Функция принимает список ссылок на товары и название категории товара. Работает в мультипроцессорном режиме,
    использует функцию get_product. Название категории используется для создания директории, куда записываются файлы
    с изображением товара. Пути к файлам
    :param list_links: list - список ссылок на товар
    :param category_name: str - название категории.
    :return:
    """
    if not os.path.exists(category_name):
        os.mkdir(category_name)
    args = [(link, num + 1, category_name) for num, link in enumerate(list_links)]
    func = partial(get_product, category_name)
    with Pool(processes=cpu_count()-1) as pool:
        product_list = pool.map(func, args)
    with open(f'{category_name}.json', 'w') as file:
        json.dump(product_list, file, indent=4)
    return product_list


def product_to_json(item):
    with open('goods.json', 'w', encoding='utf-8') as file:
        json.dump(item, file, indent=4)


if __name__ == '__main__':
    result = multiprocess_get_list_links('https://www.dns-shop.ru/catalog/17a8face16404e77/roboty-pylesosy/?order=2', 1)
    print(*result, sep='\n')
    list_product = multiprocess_get_product(result, 'robot_vacuum_cleaner')
    print(*list_product, sep='\n')

