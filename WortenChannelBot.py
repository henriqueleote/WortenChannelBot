import re

from selenium.webdriver.common.by import By
from undetected_chromedriver import Chrome, ChromeOptions
# pip install -U git+https://github.com/ultrafunkamsterdam/undetected-chromedriver@fix-multiple-instance
# Bot.send_message' was never awaited, Enable tracemalloc to get the object allocation traceback - pip install python-telegram-bot==13.13
import json
import time
from bs4 import BeautifulSoup
import telegram

# URL of the website you want to fetch
PRODUCT_URL = f'https://worten.pt'
old_product_list = {}
new_product_list = {}
added_product_list = {}
final_product_dict = {}
queries = []


# Local storage file
DATA_FILE = "data.json"

# Telegram Bot Token
TOKEN = '5849084397:AAGWlLjZIdO3Ize5Myl_gG5k7N3FV0PURmM'

# Telegram Channel ID
channel_id = "-1001921638321"


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
    global old_product_list
    try:
        with open(DATA_FILE, 'r') as file:
            data = file.read()
            if data:
                old_product_list = json.loads(data)
            else:
                old_product_list = {}
    except FileNotFoundError:
        old_product_list = {}


# Save products to the JSON file
def save_products():
    global final_product_dict

    print("saving lists")

    with open(DATA_FILE, 'w') as file:
        if final_product_dict:
            json.dump(final_product_dict, file)
        else:
            file.write('')


def compareLists():
    global old_product_list, new_product_list, added_product_list, final_product_dict

    print("comparing lists")

    for query, old_query_products in old_product_list.items():
        new_query_products = new_product_list.get(query, {})
        added_query_products = added_product_list.get(query, {})

        for product_id in list(old_query_products.keys()):
            if product_id not in new_query_products:
                del old_query_products[product_id]

        old_query_products.update(added_query_products)
        final_product_dict[query] = old_query_products

    return final_product_dict
    # Now, final_product_list contains the merged list with the desired criteria


def runWebDriver(link):
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = Chrome(options=options)
    driver.get(link)

    # Retrive source code
    html_content = driver.page_source

    # Close driver
    driver.quit()

    # Parse and return HTML code
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup


def getData(query, soup, bot):

    # <ul data-v-04484ba1="" class="listing-content__list listing-content__list--grid"> i want to get this element with soup
    product_group = soup.select_one('.listing-content__list')

    if product_group is not None:

        # Find all li elements inside ul_element, excluding those with hidden="hidden"
        product_list = product_group.find_all('li', attrs={'hidden': None})

        # Process the li elements as needed
        for product_li in product_list:
            # Find product HTML Elements
            img_src = ""
            grade = ""
            product_name_span = product_li.findAll('span', {'class': 'produc-card__name__link'})
            product_link_anchor = product_li.findAll('a')
            product_price_euro = product_li.findAll('span', {'class': 'integer'})
            product_price_cent = product_li.findAll('span', {'class': 'decimal'})
            img_element = product_li.findAll('img', {'class': 'product-card__image'})
            gradePattern = r"Grade (A\+?|B|C)"

            # Get product data
            product_name = product_name_span[0].text.strip()
            product_link = PRODUCT_URL + product_link_anchor[0]['href']
            product_price = f'{product_price_euro[0].text},{product_price_cent[0].text}'
            grade_string = re.search(gradePattern, product_name)
            img_src = img_element[0].get("src")
            if grade_string is not None:
                grade = grade_string.group(1)

            if grade == "A+":
                emoji = "\U0001F535"
            elif grade == "A":
                emoji = "\U0001F7E2"
            elif grade == "B":
                emoji = "\U0001F7E1"
            elif grade == "C":
                emoji = "\U0001F7E0"
            else:
                grade = "Outro"
                emoji = "\u26AA"  # White circle emoji

            # Emoji
            red_circle = "\U0001F534"
            white_circle = "\u26AA"

            parts = product_link.split('-')
            product_id = parts[-1]

            product_info = {
                'key': product_id,
                'name': product_name,
                'price': product_price,
                'link': product_link,
                'query': query,
                'grade': grade
            }

            # Check if already exists in the existing list
            if product_id not in old_product_list[query]:
                print('new product -> ' + product_name)
                added_product_list[query][product_id] = product_info

                # Send message to telegram
                title = f'{red_circle}{white_circle} Worten {white_circle}{red_circle}\n'
                message = f'{title}{product_name}\nPrice: {product_price}\nCondition: Grade {grade} {emoji}\n{product_link}'
                if (img_src != ''):
                    bot.send_photo(chat_id=channel_id, photo=img_src, caption=message)
                else:
                    bot.send_message(chat_id=channel_id, text=message)


            new_product_list[query][product_id] = product_info

        return("NEXT_PAGE")
    else:

        p_element = soup.find('p', {'class': 'filter-and-sortblock__product-count'})

        if p_element is None:
            return "ACCESS_ERROR"

        else:
            return ('EMPTY_PAGE')


# Start Bot with defined TOKEN
bot = telegram.Bot(token=TOKEN)

# Send a start-up message to the Chat
bot.send_message(chat_id=channel_id, text='Now getting updates from Worten')

load_queries()
load_products()

# Always running script
while True:
    # For all types of product in file queries.txt
    for query in queries:
        result = ""
        page = 1
        while True:
            print(f'fetching all "{query}" - page {page}')
            soup = runWebDriver(f'https://www.worten.pt/search?query=outlet%20{query}&sort_by=price&order_by=asc&facetFilters=seller_id%3A689dda97-efa4-4c6d-96bc-6f4bbfda8394&facetFilters=t_tags%3Ais_in_stock&page={page}')
            old_product_list.setdefault(query, {})
            new_product_list.setdefault(query, {})
            added_product_list.setdefault(query, {})
            result = getData(query, soup, bot)  # Call getData function for each page
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
    time.sleep(3600)