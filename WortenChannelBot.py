from undetected_chromedriver import Chrome, ChromeOptions
#pip install -U git+https://github.com/ultrafunkamsterdam/undetected-chromedriver@fix-multiple-instance
import json
import time
from bs4 import BeautifulSoup
import telegram

# URL of the website you want to fetch
search_category = 'tablet'
URL = f'https://www.worten.pt/search?query=outlet%20{search_category}&sort_by=price&order_by=asc&facetFilters=seller_id%3A689dda97-efa4-4c6d-96bc-6f4bbfda8394&facetFilters=t_tags%3Ais_in_stock'

# Variables
most_recent = None
history_product_count = 0

# Local storage file
SETTINGS_FILE = "settings.json"
settings = None

# Telegram Bot Token
TOKEN = '6201495078:AAGmPD9vEI_dIT1D4uAMbF2_9Rx3dOzc1Bg'

# Telegram Channel ID
channel_id = "-1001921638321"

# Load settings from the JSON file
def load_settings():
    global settings
    try:
        with open(SETTINGS_FILE, 'r') as file:
            data = file.read()
            if data:
                settings = json.loads(data)
            else:
                settings = {}
    except FileNotFoundError:
        settings = {}


# Save settings to the JSON file
def save_settings():
    with open(SETTINGS_FILE, 'w') as file:
        if settings:
            json.dump(settings, file)
        else:
            file.write('')

def runWebDriver(category):
    global search_category
    search_category = category

    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = Chrome(options=options)

    driver.get(URL)

    # Retrive source code
    html_content = driver.page_source

    # Close driver
    driver.quit()

    # Parse and return HTML code
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup

def getData(bot):
    print('running...')

    #Get internet code
    soup = runWebDriver('tablet')

    p_element = soup.find('p', {'class': 'filter-and-sortblock__product-count'})

    span_element = p_element.find('span')

    product_count = span_element.contents[0]

    if (int(product_count) > 0):

        #<ul data-v-04484ba1="" class="listing-content__list listing-content__list--grid"> i want to get this element with soup
        ul_element = soup.select_one('.listing-content__list')

        # Find all li elements inside ul_element, excluding those with hidden="hidden"
        li_elements = ul_element.find_all('li', attrs={'hidden': None})

        def getData(bot):
            print('running...')

            # Get internet code
            soup = runWebDriver('tablet')

            # Find the ul element with class "listing-content__list"
            ul_element = soup.select_one('.listing-content__list')

            # Find all li elements inside ul_element, excluding those with hidden="hidden"
            li_elements = ul_element.find_all('li', attrs={'hidden': None})

            # Process the li elements as needed
            for li in li_elements:
                # Find the span element with class "product-card__name__link" inside each li
                product_name_span = li.find('span', class_='product-card__name__link')

                # Extract the text inside the span element
                product_name = product_name_span.get_text(strip=True)

                # Do something with the product name
                print(product_name)

            # Rest of the code...

        # Process the li elements as needed
        for li in li_elements:
            # Do something with each li element
            print(f'{li}\n')


# Start Bot with defined TOKEN
bot = telegram.Bot(token=TOKEN)

# Send a start-up message to the Chat
#bot.send_message(chat_id=channel_id, text='Now getting updates from Worten')

load_settings()

while (True):
    getData(bot)
    time.sleep(180)