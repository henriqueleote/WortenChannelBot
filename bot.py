import asyncio
import time
import requests
import telegram
from telegram.error import BadRequest, RetryAfter, TimedOut, NetworkError
import worten_config
import datetime

queries = ['iphone', 'macbook', 'apple', 'samsung', 'tablet', 'consola', 'portatil', 'huawei', 'smartphone', 'drone',
           'projetor', 'imac', 'ipad', 'tv', 'exaustor', 'powerbank', 'belkin', 'sanduicheira',
           'sandwicheira', 'monitor']

bannedList = ['suport tv ', 'suporte de tv ', 'toner ', 'triciclo ', 'bebé ', 'berço ', 'cama ', 'carrinho ',
              'aquecedor ', 'capa ', 'cabo ', 'case ', 'seguro ', 'película ', 'substituição ', 'tinteiros ',
              'protector de ecrã', 'protetor de ecrã']

sku_list = {}

firstIteration = True

# bool to control if messages are sent to telegram or not
sendMessage = True

# Telegram Channel ID
channel_id = worten_config.channel_id

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
}


async def handleItem(item):
    productID = item['product']['sku']
    productName = item['product']['name']
    productQuantity = item['totalOffers']

    skip = False

    for word in bannedList:
        if word in productName.lower():
            skip = True

    if productID not in sku_list and not skip and int(productQuantity) < 5:
        if firstIteration is False:
            productImage = item['product']['image']['url']
            productGrade = item['product']['textProperties'].get('grade-recon', {})

            if not productGrade:
                productGrade = 'Últimas unidades'
            productFinalPrice = str(item['winningOffer']['pricing']['final']['value'])
            formatedProductFinalPrice = float(f"{productFinalPrice[:-2]}.{productFinalPrice[-2:]}")

            url = f'https://worten.pt{item["product"]["url"]}'

            grade_emoji_map = {
                "A+": f"\U0001F535 Grade",
                "A": f"\U0001F7E2 Grade",
                "B": f"\U0001F7E1 Grade",
                "C": f"\U0001F7E0 Grade"
            }

            emoji = grade_emoji_map.get(productGrade, "\u26AA")  # White circle emoji

            title = f'\U0001F534\u26AA Worten \u26AA\U0001F534\n'
            message = (f'{title}{productName}\n'
                       f'Price: {formatedProductFinalPrice}€\n'
                       f'Condition: {emoji} {productGrade}\n'
                       f'Quantity: {productQuantity}\n'
                       f'{url}')

            print(f'\033[92m{productID} | {formatedProductFinalPrice}€ | {productName}\033[0m')

            if sendMessage:
                try:
                    async with bot:
                        await bot.send_photo(chat_id=channel_id, photo=productImage, caption=message)
                except BadRequest as e:
                    async with bot:
                        await bot.send_photo(chat_id=channel_id, photo=productImage, caption=message)
                except RetryAfter as e:
                    time.sleep(e.retry_after)
                    async with bot:
                        await bot.send_photo(chat_id=channel_id, photo=productImage, caption=message)
                except TimedOut as e:
                    time.sleep(60)
                    async with bot:
                        await bot.send_photo(chat_id=channel_id, photo=productImage, caption=message)
                except NetworkError as e:
                    time.sleep(30)
                    async with bot:
                        await bot.send_photo(chat_id=channel_id, photo=productImage, caption=message)
                except Exception as e:
                    time.sleep(1)
                    async with bot:
                        await bot.send_photo(chat_id=channel_id, photo=productImage, caption=message)

    sku_list[productID] = {
        'state': True,
        'time': datetime.datetime.now()
    }


async def queryWebsite(query):
    page = 0

    while True:
        json_data = {
            'variables': {
                'query': 'outlet ' + query,
                'params': {
                    'pageNumber': page,
                    'pageSize': 48,
                    'filters': [
                        {
                            'key': 't_tags',
                            'virtual': False,
                            'value': [
                                'is_in_stock',
                            ],
                        },
                        {
                            'key': 'seller_id',
                            'virtual': False,
                            'value': [
                                '689dda97-efa4-4c6d-96bc-6f4bbfda8394',
                            ],
                        },
                    ],
                    'sort': {
                        'field': 'rank1',
                        'order': 'ASC',
                    },
                    'collapse': True,
                },
                'badgesParams': {
                    'contextId': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1IjoiL3NlYXJjaD9xdWVyeT1vdXRsZXQrbWFjYm9vayZmYWNldEZpbHRlcnM9dF90YWdzOmlzX2luX3N0b2NrJmZhY2V0RmlsdGVycz1zZWxsZXJfaWQ6Njg5ZGRhOTctZWZhNC00YzZkLTk2YmMtNmY0YmJmZGE4Mzk0IiwiYyI6IndvcnRlbnB0IiwicCI6e30sInNjIjoiV0VCIiwiYWIiOiJBIiwic2NvcGUiOiJjdHgiLCJhdWQiOiJuZXQud29ydGVuLmNhdGFsb2cuYmZmIiwiaXNzIjoibmV0LndvcnRlbi5jYXRhbG9nLmJmZiJ9.v2dXe1JYgR5Okt-9eRmGvxHPAv3tq15LjN7PuiFG7Ao',
                    'targets': [
                        'card_badge_winning_offer',
                        'system_badge_product_actions',
                    ],
                    'moduleId': '01G43461Q8B57C3G7XKFZQWN57',
                },
                'hasVariants': True,
                'debug': False,
            },
            'extensions': {
                'persistedQuery': {
                    'version': 1,
                    'sha256Hash': '799b33ff47d1ecd61508b2f4f02852fac19ff4f473e6f9ff1edbf69e41ad1338',
                },
            },
        }
        response = requests.post('https://www.worten.pt/_/api/graphql', headers=headers, json=json_data)
        if response.status_code == 200:
            mainSet = response.json().get('data', [])
            if mainSet:
                searchProducts = mainSet.get('searchProducts', [])
                if searchProducts:
                    hasNextPage = searchProducts.get('hasNextPage', False)
                    totalHits = searchProducts.get('totalHits', 0)
                    if int(totalHits) > 1000:
                        queries.remove(query)
                        return
                    data = searchProducts.get('hits', [])
                    if data:
                        for item in data:
                            await handleItem(item)
                    if hasNextPage:
                        page += 1
                    else:
                        break
        else:
            page = page


bot = telegram.Bot(token=worten_config.TOKEN)


async def main():
    global firstIteration
    while True:
        program_starts = time.time()
        print(f'Running worten.pt... ({datetime.datetime.now()})')
        for query in queries:
            await queryWebsite(query)

        firstIteration = False

        # remove deleted products
        handleRemovedProducts()

        print(f'{len(sku_list)} products | {time.time() - program_starts} seconds')
        async with bot:
            await bot.send_message(chat_id=worten_config.status_channel_id,
                                   text=f'Last worten product now',
                                   disable_notification=True)

        time.sleep(15)


def handleRemovedProducts():
    global sku_list

    removed = []

    for key, value in list(sku_list.items()):
        if value['state'] is False:

            time_difference = (datetime.datetime.now() - value['time']).total_seconds()

            # 5 minutes ago
            if time_difference > 300:
                sku_list.pop(key)
                removed.append(key)
        else:
            sku_list[key] = {
                'state': False,
                'time': datetime.datetime.now()
            }

    if removed:
        print(f'\033[91mProducts removed more than 5 minutes ago: {removed}\033[0m')


if __name__ == '__main__':
    asyncio.run(main())
