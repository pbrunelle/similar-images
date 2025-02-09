from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from typing import Any
from urllib.parse import quote_plus
import json
import time


class BingSelenium:
    def __init__(
            self,
            driver: Any | None = None,
            wait_first_load: float = 2,
            wait_between_scroll: float = 1,
            safe_search: bool = False,
            headless: bool = True,
        ):
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument("--start-maximized")
        self.driver = driver if driver else webdriver.Chrome(options=options)
        self.wait_first_load = wait_first_load
        self.wait_between_scroll = wait_between_scroll
        self.safe_search = safe_search

    def search_images(self, query: str, max_images: int = -1):
        done = set()
        i = 0
        self.driver.get("https://www.bing.com")
        if not self.safe_search:
            self.driver.add_cookie({
                "name": "SRCHHPGUSR",
                "value": "SRCHLANG=en&IG=69033305F5234C079A7886B84F432FB5&DM=0&BRW=XW&BRH=M&CW=1779&CH=918&SCW=1762&SCH=918&DPR=1.0&UTC=-300&WTS=63874663291&HV=1739066971&PRVCW=1792&PRVCH=332&ADLT=OFF&BCML=0&BCSRLANG=",
                "domain": ".bing.com",
                "path": "/",
                "secure": True,
                "httpOnly": False,
                "expiry": 1773627172,
            })
        url = f"https://www.bing.com/images/search?q={quote_plus(query)}"
        print(f"{url=}")
        self.driver.get(url)
        time.sleep(self.wait_first_load)  # wait for images to load
        while True:
            i += 1
            added = 0
            elements = self.driver.find_elements(By.CLASS_NAME, "iusc")
            for element in elements:
                m = element.get_attribute("m")
                if m:
                    try:
                        image_data = json.loads(m)
                        url = image_data["murl"]
                        if url not in done:
                            done.add(url)
                            added += 1
                            yield url
                    except json.JSONDecodeError:
                        pass
            print(f"{i=}: {added=} {len(done)=}")
            if added == 0:
                break
            if max_images > 0 and len(done) >= max_images:
                break
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.wait_between_scroll)
