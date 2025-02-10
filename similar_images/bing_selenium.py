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
            wait_between_scroll: float = 1):
        options = Options()
        self.driver = driver if driver else webdriver.Chrome(options=options)
        self.wait_first_load = wait_first_load
        self.wait_between_scroll = wait_between_scroll

    def search_images(self, query: str, max_images: int = -1):
        done = set()
        i = 0
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


"""
SCROLL_PAUSE_TIME = 0.5

# Get scroll height
last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    # Scroll down to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Wait to load page
    time.sleep(SCROLL_PAUSE_TIME)

    # Calculate new scroll height and compare with last scroll height
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height
"""
