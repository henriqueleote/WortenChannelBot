import re
from selenium.webdriver.common.by import By
from telegram.error import BadRequest, RetryAfter, TimedOut, Unauthorized, NetworkError
from undetected_chromedriver import Chrome, ChromeOptions
import json
import time
from bs4 import BeautifulSoup
import telegram
import config

# URL of the website you want to fetch
PRODUCT_URL = f'https://worten.pt'
old_list = {}
recent_list = {}
added_products_list = {}
final_products_dict = {}
queries = []
INTERVAL = 1800
MINIMUM_DISCOUNT = 0
toWait = False

# Local storage file
DATA_FILE = "data.json"

# Telegram Bot Token
TOKEN = config.TOKEN

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

    # Parse and return HTML code
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Wait until a specific element loads
    #while soup.find('p', class_='filter-and-sortblock__product-count') is None:
        #time.sleep(1)  # Wait for 1 second before checking again
        #soup = BeautifulSoup(driver.page_source, "html.parser")

    #if toWait:
     #   while soup.find('p', class_='filter-and-sortblock__product-count') is None:
      #      time.sleep(1)  # Wait for 1 second before checking again
       #     soup = BeautifulSoup(driver.page_source, "html.parser")

    return soup


def getData(soup, bot):
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
            product_link = PRODUCT_URL + product_link_element.get('href', '')
            parts = product_link.split('-')
            product_id = parts[-1]

            product_info = {
                'key': product_id
            }

            if product_id not in old_list and product_id not in added_products_list:

                # Find product HTML Elements
                img_src = ""
                grade = ""
                product_discount = ""
                product_name_span = product_li.findAll('span', {'class': 'produc-card__name__link'})
                product_price_euro = product_li.findAll('span', {'class': 'integer'})
                product_price_cent = product_li.findAll('span', {'class': 'decimal'})
                img_element = product_li.findAll('img', {'class': 'product-card__image'})
                gradePattern = r"Grade (A\+?|B|C)"

                # Get product data
                product_name = product_name_span[0].text.strip()

                product_price = f'{product_price_euro[0].text},{product_price_cent[0].text}'
                grade_string = re.search(gradePattern, product_name)
                img_src = img_element[0].get("src")

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
                    product_discount_span = product_li.findAll('span', {'class': 'bold'})
                    if (product_discount_span):
                        product_discount = re.sub("[^0-9]", "", product_discount_span[0].text.strip())

                    if product_discount and int(product_discount) >= MINIMUM_DISCOUNT:
                        # Check if doesn't exist anywhere
                        print('new product -> ' + product_name)
                        added_products_list[product_id] = product_info

                        # Send message to telegram
                        title = f'\U0001F534\u26AA Worten \u26AA\U0001F534\n'
                        message = f'{title}{product_name}\nPrice: {product_price}€\nCondition: {emoji} {grade} \nDiscount: {product_discount}%\n{product_link}'

                        try:
                            bot.send_photo(chat_id=channel_id, photo=img_src, caption=message)
                        except BadRequest as e:
                            bot.send_photo(chat_id=channel_id, photo=img_src, caption=message)
                        except RetryAfter as e:
                            time.sleep(e.retry_after)
                            bot.send_photo(chat_id=channel_id, photo=img_src, caption=message)
                        except TimedOut as e:
                            time.sleep(60)
                            bot.send_photo(chat_id=channel_id, photo=img_src, caption=message)
                        except Unauthorized as e:
                            time.sleep(0.25)
                        except NetworkError as e:
                            time.sleep(30)
                            bot.send_photo(chat_id=channel_id, photo=img_src, caption=message)
                        except Exception as e:
                            time.sleep(1)
                            bot.send_photo(chat_id=channel_id, photo=img_src, caption=message)


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


# Start Bot with defined TOKEN
bot = telegram.Bot(token=TOKEN)

load_queries()
load_products()

# Always running script
while True:

    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    # Start driver
    driver = Chrome(options=options)

    bot.send_message(chat_id=channel_id, message="Running worten bot...", disable_notification=True)

    # For all types of product in file queries.txt
    for query in queries:
        result = ""
        page = 1
        while True:
            print(f'fetching all "{query}" - page {page}')
            soup = runWebDriver(driver, f'https://www.worten.pt/search?query=outlet%20{query}&sort_by=price&order_by=asc&facetFilters=seller_id%3A689dda97-efa4-4c6d-96bc-6f4bbfda8394&facetFilters=t_tags%3Ais_in_stock&page={page}')
            result = getData(soup, bot)  # Call getData function for each page
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
    bot.send_message(chat_id=channel_id, message="Worten bot is over...", disable_notification=True)

    # Close driver
    driver.quit()

    time.sleep(INTERVAL)

