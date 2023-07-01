# Worten & Telegram price updates

This script fetches the latest product updates from Worten.pt and sends them to a Telegram channel. It uses web scraping with Selenium and BeautifulSoup to extract data from the website and the Telegram API to send notifications.

## Requirements

- Telethon
- Beautifulsoup4
- Python-telegram-bot
- Selenium
- Undetected-chromedriver

## Installation

1. Clone the repository:

```python
git clone https://github.com/henriqueleote/WortenChannelBot.git
cd WortenChannelBot
```

2. Install the required dependencies:

```python
pip install -r requirements.txt

```

3. Update the `TOKEN` variable in the script with your bot credentials.

4. Update the `channel_id` variable with the ID of the channel where you want to forward the messages.

5. Update the `INTERVAL` variable to your desired interval.

6. Update the `MINIMUM_DISCOUNT` variable to your desired discount minimum.

## Usage

1. Run the script:

```python
py WortenChannelBot.py
```

2. The script will start website every `INTERVAL` seconds 

3. Everytime it monitors, if detects a new product, sends it to the Telegram channel

## Customization

- You can modify the url, `MINIMUM_DISCOUNT`, `INTERVAL` and queries to adjust to your scalp needs.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

[MIT License](LICENSE)
