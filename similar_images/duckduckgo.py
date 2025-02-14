from urllib.parse import quote_plus

import bs4
import requests

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


class DuckDuckGo:
    def __init__(self, user_agent: str = DEFAULT_USER_AGENT):
        self.user_agent = user_agent

    def search_images(self, query: str) -> list[str]:
        url = f"https://duckduckgo.com/?q={quote_plus(query)}&iar=images&iax=images&ia=images"
        print(f"{url=}")
        headers = {"User-Agent": self.user_agent}
        response = requests.get(url, headers=headers)
        print(f"{response=}")
        print(f"{response.content}")
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.content, "html.parser")
        links = []
        for link in soup.find_all("img", class_="tile__media__img"):
            if "src" in link.attrs:
                links.append("https:" + link["src"])
        print(f"{links=}")
        return links
