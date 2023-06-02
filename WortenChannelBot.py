from selenium.webdriver.common.by import By
from undetected_chromedriver import Chrome, ChromeOptions
# pip install -U git+https://github.com/ultrafunkamsterdam/undetected-chromedriver@fix-multiple-instance
import json
import time
from bs4 import BeautifulSoup
import telegram

# URL of the website you want to fetch
PRODUCT_URL = f'https://worten.pt'
product_dict = {}
queries = []

# Local storage file
DATA_FILE = "data.json"

# Telegram Bot Token
TOKEN = '6201495078:AAGmPD9vEI_dIT1D4uAMbF2_9Rx3dOzc1Bg'

# Telegram Channel ID
channel_id = "-1001921638321"


# Load queries from a txt file
def load_queries():
    global queries
    try:
        with open(DATA_FILE, 'r') as file:
            data = file.read()
            file = open('queries.txt', 'r')
            lines = file.readlines()
            count = 0
            for line in lines:
                count += 1
                queries.append(line.strip())
    except FileNotFoundError:
        queries = []


# Load products from the JSON file
def load_products():
    global product_dict
    try:
        with open(DATA_FILE, 'r') as file:
            data = file.read()
            if data:
                product_dict = json.loads(data)
            else:
                product_dict = {}
    except FileNotFoundError:
        product_dict = {}


# Save products to the JSON file
def save_products():
    global product_dict
    with open(DATA_FILE, 'w') as file:
        if product_dict:
            json.dump(product_dict, file)
        else:
            file.write('')


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

    p_element = soup.find('p', {'class': 'filter-and-sortblock__product-count'})

    if p_element is not None:
        span_element = p_element.find('span')

        product_count = span_element.contents[0]

        if int(product_count) > 0:

            # <ul data-v-04484ba1="" class="listing-content__list listing-content__list--grid"> i want to get this element with soup
            product_group = soup.select_one('.listing-content__list')

            # Find all li elements inside ul_element, excluding those with hidden="hidden"
            product_list = product_group.find_all('li', attrs={'hidden': None})

            # print(li_elements)

            product_total = len(product_list)

            # Process the li elements as needed
            for li in product_list:

                # Find product HTML Elements
                product_name_span = li.findAll('span', {'class': 'produc-card__name__link'})
                product_link_anchor = li.findAll('a')
                product_price_euro = li.findAll('span', {'class': 'integer'})
                product_price_cent = li.findAll('span', {'class': 'decimal'})

                # Get product data
                product_name = product_name_span[0].text.strip()
                product_link = PRODUCT_URL + product_link_anchor[0]['href']
                product_price = f'{product_price_euro[0].text},{product_price_cent[0].text}'

                parts = product_link.split('-')
                product_id = parts[-1]

                product_info = {
                    'key': product_id,
                    'name': product_name,
                    'price': product_price,
                    'link': product_link
                }

                product_dict[query][product_id] = product_info

            save_products()
    else:
        print("ACCESS_ERROR")
        return "ACCESS_ERROR"


print("start")

# Start Bot with defined TOKEN
bot = telegram.Bot(token=TOKEN)

# Send a start-up message to the Chat
# bot.send_message(chat_id=channel_id, text='Now getting updates from Worten')

load_queries()
#load_products()
print(queries)

for query in queries:
    # Worten sometimes has a problem with cookies, this loop tries to access it until gets what's needed
    while True:
        print(query)
        soup = runWebDriver(
            f'https://www.worten.pt/search?query=outlet%20{query}&sort_by=price&order_by=asc&facetFilters=seller_id%3A689dda97-efa4-4c6d-96bc-6f4bbfda8394&facetFilters=t_tags%3Ais_in_stock')
        if soup != "ACCESS_ERROR":
            break
    product_dict.setdefault(query, {})
    getData(query, soup, bot)
    #time.sleep(10)

# Always running script
#while True:
    # For all types of product in file queries.txt

    #for query code here

    #time.sleep(300)
