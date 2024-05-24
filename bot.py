import asyncio
import re
import json
import time
import config



import telegram
from telegram.error import BadRequest, RetryAfter, TimedOut, NetworkError

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import TimeoutException
from bs4 import BeautifulSoup


# URL of the website you want to fetch
old_list = {}
recent_list = {}
added_products_list = {}
final_products_dict = {}
queries = []
MINIMUM_DISCOUNT = 0
toWait = False

# Local storage file
DATA_FILE = "data.json"

# Telegram Channel ID
channel_id = config.channel_id


# Load queries from a txt file
def load_queries():
    global queries
    try:
        file = open('queries.txt', 'r')
        lines = file.readlines()
        count = 0
        for line in lines:
            count += 1
            queries.append(line.strip())

    except FileNotFoundError:
        queries = []
        print('not found')


# Load products from the JSON file
def load_products():
    global old_list
    try:
        with open(DATA_FILE, 'r') as file:
            data = file.read()
            if data:
                old_list = json.loads(data)
            else:
                old_list = {}
    except FileNotFoundError:
        old_list = {}


# Save products to the JSON file
def save_products():
    global final_products_dict

    with open(DATA_FILE, 'w') as file:
        if final_products_dict:
            json.dump(final_products_dict, file)
            print("saved to file")
        else:
            file.write('')



def compareLists():
    global old_list, recent_list, added_products_list, final_products_dict

    print("comparing lists...")

    merged_product_dict = {}

    # Merge old_product_list and added_product_list
    merged_product_dict.update(old_list)
    merged_product_dict.update(added_products_list)

    # Remove products from merged_product_dict that are not in new_product_list
    for product_id in list(merged_product_dict.keys()):
        if product_id not in recent_list:
            del merged_product_dict[product_id]

    final_products_dict = merged_product_dict

    print("lists compared")

    return final_products_dict
    # Now, final_product_dict contains the merged list with the desired structure


def runWebDriver(driver, link):
    global toWait
    driver.get(link)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".listing-content__card"))
        )
    except TimeoutException:
        # Check for "no_results_for_search" class
        if driver.find_element(By.CSS_SELECTOR, ".listing-content__empty-message"):
            return "EMPTY_PAGE"
        else:
            return "CRASH"

    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")

    return soup


async def getData(soup, bot):
    global toWait
    product_count_element = soup.find('p', class_='filter-and-sortblock__product-count')

    if product_count_element is not None:
        product_count_text = product_count_element.get_text(strip=True)
        product_count = re.search(r'\d+', product_count_text).group()
        if int(product_count) >= 500:
            return 'EMPTY_PAGE'

    product_group = soup.select_one('.listing-content__list')

    if product_group is not None:

        # Find all li elements inside ul_element, excluding those with hidden="hidden"
        product_list = product_group.select('li:not([hidden])')

        # Process the li elements as needed
        for product_li in product_list:

            product_link_anchor = product_li.findAll('a')
            product_link_element = product_link_anchor[0]
            product_link = f'https://worten.pt' + product_link_element.get('href', '')
            parts = product_link.split('-')
            product_id = parts[-1]

            product_info = {
                'key': product_id
            }

            if product_id not in old_list and product_id not in added_products_list:

                # Find product HTML Elements
                product_discount = product_li.select_one('div.discount-flag--percent').text if  product_li.select_one('div.discount-flag--percent') is not None else ""
                product_name = product_li.select_one('span.produc-card__name__link').text.strip()
                product_price = product_li.select_one('span.price__numbers').select_one('span.value').text.strip()
                img_src = product_li.select_one('img.product-card__image')['src']

                grade_string = re.search(r"Grade (A\+?|B|C)", product_name)

                grade_emoji_map = {
                    "Grade A+": "\U0001F535",
                    "Grade A": "\U0001F7E2",
                    "Grade B": "\U0001F7E1",
                    "Grade C": "\U0001F7E0"
                }

                grade = grade_string.group(0) if grade_string else "Outro"
                emoji = grade_emoji_map.get(grade, "\u26AA")  # White circle emoji

                lowercase_string = product_name.lower()
                if "grade" in lowercase_string or "reuse" in lowercase_string or "recondicionado" in lowercase_string or "caixa aberta" in lowercase_string:
                    if product_discount != "":
                        product_discount = re.sub("[^0-9]", "", product_discount)

                    if product_discount != "" and int(product_discount) >= MINIMUM_DISCOUNT:
                        # Check if doesn't exist anywhere
                        print('new product -> ' + product_name)
                        added_products_list[product_id] = product_info

                        # Send message to telegram
                        title = f'\U0001F534\u26AA Worten \u26AA\U0001F534\n'
                        message = f'{title}{product_name}\nPrice: {product_price}€\nCondition: {emoji} {grade} \nDiscount: {product_discount}%\n{product_link}'
                        try:
                            async with bot:
                                await bot.send_photo(chat_id=channel_id, photo=img_src, caption=message)
                        except BadRequest as e:
                            async with bot:
                                await bot.send_photo(chat_id=channel_id, photo=img_src, caption=message)
                        except RetryAfter as e:
                            time.sleep(e.retry_after)
                            async with bot:
                                await bot.send_photo(chat_id=channel_id, photo=img_src, caption=message)
                        except TimedOut as e:
                            time.sleep(60)
                            async with bot:
                                await bot.send_photo(chat_id=channel_id, photo=img_src, caption=message)
                        except NetworkError as e:
                            time.sleep(30)
                            async with bot:
                                await bot.send_photo(chat_id=channel_id, photo=img_src, caption=message)
                        except Exception as e:
                            time.sleep(1)
                            async with bot:
                                await bot.send_photo(chat_id=channel_id, photo=img_src, caption=message)


            recent_list[product_id] = product_info

        toWait = False
        return("NEXT_PAGE")
    else:

        p_element = soup.find('p', {'class': 'filter-and-sortblock__product-count'})

        if p_element is None:
            toWait = True
            return "ACCESS_ERROR"

        else:
            return ('EMPTY_PAGE')


bot = telegram.Bot(token=config.TOKEN)


async def main():

    #async with bot:
    #    await bot.send_message(text="Running worten bot...", chat_id=channel_id, disable_notification=True)

    load_queries()
    load_products()

    # Always running script
    while True:

        options = webdriver.ChromeOptions()
        options.add_argument("--log-level=3") # removes chrome logs from cmd bash
        options.add_argument("--headless") # NO GUI browser
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        s = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=s, options=options)

        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )

        # For all types of product in file queries.txt
        for query in queries:
            result = ""
            page = 1
            while True:
                print(f'fetching all "{query}" - page {page}')
                link = f'https://www.worten.pt/search?query=outlet%20{query}&sort_by=price&order_by=asc&facetFilters=seller_id%3A689dda97-efa4-4c6d-96bc-6f4bbfda8394&facetFilters=t_tags%3Ais_in_stock&page={page}'
                soup = runWebDriver(driver, link)
                if soup == "EMPTY_PAGE":
                    print("moving to the next item")
                    break  # Exit the loop if an empty page is encountered

                if soup == "CRASH":
                    await application.bot.send_message(chat_id=channel_id, text='Worted crashed due to failed link', disable_notification=True)
                    print("Script didn't load correctly this link: \n" + link)
                    return


                result = await getData(soup, bot)  # Call getData function for each page
                if result == "EMPTY_PAGE":
                    print("moving to the next item")
                    break  # Exit the loop if an empty page is encountered
                if result == "ACCESS_ERROR":
                    # Retry accessing the page
                    print("access problem, trying to access again")
                    continue  # Continue to the next iteration of the loop
                # Process the data or perform any other necessary actions
                if result == "NEXT_PAGE":
                    print("moving to the next page")
                    page += 1  # Move to the next page
        compareLists()
        save_products()

        #async with bot:
        #    await bot.send_message(text="Worten bot is over.", chat_id=channel_id, disable_notification=True)

        # Close driver
        driver.quit()

        time.sleep(1800)

if __name__ == '__main__':
    asyncio.run(main())