import pathlib
from multiprocessing import Pool, cpu_count
from functools import partial
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import json

# from fake_useragent import UserAgent
import time
import os

my_user_agent = 'user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
# useragent = UserAgent()
options = webdriver.ChromeOptions()
options.add_argument(f'useragent={my_user_agent}')
options.add_argument('--disable-blink-features=AutomationControlled')


def get_list_links(category_url: str):
    """
    get a list of links to products of the required quantity
    :param quantity:
    :param category_url:
    :param file_name:
    :return: list
    """
    page = 1
    list_of_links = []

    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    browser.get(url=f'{category_url}&p={page}')
    time.sleep(5)
    link_cards_tag = browser.find_element(by=By.CLASS_NAME, value="products-page__list")
    link_cards_block = link_cards_tag.find_elements(by=By.CLASS_NAME, value='catalog-product__name')
    list_href = []
    for link in link_cards_block:
        list_href.append(link.get_attribute('href'))
    list_of_links.extend(list_href)
    page += 1
    return list_of_links


def multiprocess_map(category_url, quantity_page):
    list_of_pages = [f'{category_url}&p={page}' for page in range(1, quantity_page + 1)]
    with Pool(processes=cpu_count()) as pool:
        links = pool.map(get_list_links, list_of_pages)
    result = []
    [result.extend(link) for link in links]
    return result


def get_list_link_for_product(file_name):
    with open(file_name, 'r') as file:
        list_link_for_product = file.readlines()
    return list_link_for_product


def get_product(category_name: str, args: tuple) -> dict:
    product = {}
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    browser.get(url=args[0])
    browser.maximize_window()
    time.sleep(5)
    image = browser.find_element(by=By.CLASS_NAME, value='product-images-slider__img')
    image.click()
    time.sleep(5)
    image = browser.find_element(by=By.CLASS_NAME, value='media-viewer-image__main-img')
    with open(f'{category_name}/{args[1]}.png', 'bw') as file:
        image_screen = image.screenshot_as_png
        file.write(image_screen)
        product['image'] = f'{args[1]}.png'
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
    args = [(link, num + 1, category_name) for num, link in enumerate(list_links)]
    func = partial(get_product, category_name)
    with Pool(processes=cpu_count()) as pool:
        product_list = pool.map(func, args)
    return product_list


def product_to_json(item):
    with open('goods.json', 'w', encoding='utf-8') as file:
        json.dump(item, file, indent=4)


if __name__ == '__main__':

    result = multiprocess_map('https://www.dns-shop.ru/catalog/17a89aab16404e77/videokarty/?order=2&p=2', 2)
    print(*result, sep='\n')
    list_product = multiprocess_get_product(result, 'videocard')
    print(*list_product, sep='\n')
