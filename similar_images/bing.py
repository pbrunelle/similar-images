import requests
import  bs4
import json
from urllib.parse import quote_plus

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


class Bing:

    def __init__(self, user_agent: str = DEFAULT_USER_AGENT):
        self.user_agent = user_agent

    def search_images(self, query: str, start: int = 1) -> list[str]:
        url = f"https://www.bing.com/images/search?q={quote_plus(query)}&first={start}&safeSearch=Off"
        print(f"{url=}")
        headers = {'User-Agent': self.user_agent}
        response = requests.get(url, headers=headers)
        print(f"{response=}")
        # print(f"{response.content}")
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.content, 'html.parser')
        links = []
        for link in soup.find_all('a', class_='iusc'):
            m = link.get('m')
            if m:
                try:
                    image_data = json.loads(m)
                    url = image_data["murl"]
                    links.append(url)
                except json.JSONDecodeError:
                    pass
        # print(f"{links=}")
        return links