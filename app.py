from quart import Quart, render_template, request, jsonify
from hypercorn.config import Config
from hypercorn.asyncio import serve
from dotenv import load_dotenv
from jinja2 import Environment
from bs4 import BeautifulSoup
import datetime
import requests
import asyncio
import aiohttp
import os
import re

load_dotenv()
app = Quart(__name__)


def max(*args):
    return max(*args)


async def make_request(session, url):
    response = await session.get(url, timeout=3)
    return await response.text()

env = Environment()
env.filters['max'] = max


@app.route("/")
async def index():
    try:
        async with aiohttp.ClientSession() as session:
            endpoints = [
                (session, f"{request.url_root}api?type=anon"),
                (session, f"{request.url_root}api?type=ssl"),
                (session, f"{request.url_root}api?type=uk"),
                (session, f"{request.url_root}api?type=us"),
                (session, f"{request.url_root}api?type=latest")
            ]

            responses = await asyncio.gather(*[make_request(*endpoint) for endpoint in endpoints])

    except Exception as error:
        print(error)
        responses = ["None "] * 5

    proxies = [[proxy for proxy in response.splitlines() if proxy.strip()] for response in responses]

    anon_proxy, ssl_proxy, uk_proxy, us_proxy, latest_proxy = proxies

    return await render_template("index.html", anon_proxy=anon_proxy, ssl_proxy=ssl_proxy, uk_proxy=uk_proxy,
                                     us_proxy=us_proxy, latest_proxy=latest_proxy)




@app.route("/api")
async def scrape():
    if not request.args.get('type'):
        return jsonify({'error': ''''type' not found in request argument...''',
                        'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    else:
        if "anon" in request.args.get('type'):
            request_url = "https://free-proxy-list.net/anonymous-proxy.html"
        elif "ssl" in request.args.get('type'):
            request_url = "https://www.sslproxies.org/"
        elif "uk" in request.args.get('type'):
            request_url = "https://free-proxy-list.net/uk-proxy.html"
        elif "us" in request.args.get('type'):
            request_url = "https://www.us-proxy.org/"
        elif "latest" in request.args.get('type'):
            request_url = "https://free-proxy-list.net/"
        else:
            return jsonify({'error': 'requested proxy type not found...',
                            'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

        async with aiohttp.ClientSession() as session:
            async with session.get(request_url, verify_ssl=True, headers={'Referer': 'https://google.com.tr', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}) as response:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                proxy_list_text = soup.find('textarea').text
                proxy_list = proxy_list_text[proxy_list_text.rfind('UTC.'):]
                return proxy_list.replace("UTC.", "")

if __name__ == "__main__":
    config = Config()
    config.bind = f"{os.getenv('SERV_ADDRESS')}"
    asyncio.run(serve(app, config=config))
