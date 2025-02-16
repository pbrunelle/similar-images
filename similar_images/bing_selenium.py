import json
import logging
import time
from typing import Any
from urllib.parse import quote_plus

import pyperclip
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger()


def _is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


_JS_DROP_FILE = """
    var target = arguments[0],
        offsetX = arguments[1],
        offsetY = arguments[2],
        document = target.ownerDocument || document,
        window = document.defaultView || window;

    var input = document.createElement('INPUT');
    input.type = 'file';
    input.onchange = function () {
    var rect = target.getBoundingClientRect(),
        x = rect.left + (offsetX || (rect.width >> 1)),
        y = rect.top + (offsetY || (rect.height >> 1)),
        dataTransfer = { files: this.files };

    ['dragenter', 'dragover', 'drop'].forEach(function (name) {
        var evt = document.createEvent('MouseEvent');
        evt.initMouseEvent(name, !0, !0, window, 0, 0, 0, x, y, !1, !1, !1, !1, 0, null);
        evt.dataTransfer = dataTransfer;
        target.dispatchEvent(evt);
    });

    setTimeout(function () { document.body.removeChild(input); }, 25);
    };
    document.body.appendChild(input);
    return input;
"""


class BingSelenium:
    def __init__(
        self,
        driver: Any | None = None,
        wait_first_load: float | None = None,
        wait_between_scroll: float | None = None,
        safe_search: bool | None = None,
        headless: bool | None = None,
        user_data_dir: str | None = None,
    ):
        options = Options()
        if headless is not False:
            options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")
        if user_data_dir:
            options.add_argument(f"--user-data-dir={user_data_dir}")
        self.driver = driver if driver else webdriver.Chrome(options=options)
        self.wait_first_load = wait_first_load if wait_first_load is not None else 2
        self.wait_between_scroll = (
            wait_between_scroll if wait_between_scroll is not None else 1
        )
        self.safe_search = safe_search if safe_search is not None else False

    def search_images(self, query: str, max_images: int = -1):
        done = set()
        i = 0
        self.driver.get("https://www.bing.com")
        self.configure_safe_search()
        url = f"https://www.bing.com/images/search?q={quote_plus(query)}"
        logger.info(f"Searching {url=}")
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
            logger.debug(
                f"Search results iteration {i}: found {added} links, total {len(done)}"
            )
            if added == 0:
                break
            if max_images > 0 and len(done) >= max_images:
                break
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(self.wait_between_scroll)

    def search_similar_images(self, url_or_path: str, max_images: int = -1):
        done = set()
        i = 0
        is_url = _is_url(url_or_path)
        logger.info(f"Searching similar to {'URL' if is_url else 'path'} {url_or_path}")
        self.driver.get("https://www.bing.com/images")
        self.configure_safe_search()
        # time.sleep(self.wait_first_load)
        button = self.driver.find_element(By.ID, "sb_sbi")
        ActionChains(self.driver).move_to_element(button).click(button).perform()

        if is_url:
            text_input = self.driver.find_element(By.ID, "sb_pastepn")
            pyperclip.copy(url_or_path)
            ActionChains(self.driver).move_to_element(text_input).click(
                text_input
            ).key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()
        else:
            # https://stackoverflow.com/a/53108153
            drop_target = self.driver.find_element(By.ID, "sb_dropzone")
            file_input = drop_target.parent.execute_script(
                _JS_DROP_FILE, drop_target, 0, 0
            )
            file_input.send_keys(url_or_path)

        time.sleep(self.wait_first_load)
        while True:
            i += 1
            added = 0
            elements = self.driver.find_elements(By.CLASS_NAME, "richImgLnk")
            for element in elements:
                m = element.get_attribute("data-m")
                if m:
                    try:
                        image_data = json.loads(m)
                        url = image_data["murl"]
                        if url not in done:
                            done.add(url)
                            added += 1
                            yield url
                            ActionChains(self.driver).scroll_to_element(
                                element
                            ).perform()
                            time.sleep(0.1)
                    except json.JSONDecodeError:
                        logger.debug(f"json.JSONDecodeError")
                        pass
            logger.debug(
                f"Similar results iteration {i}: found {added} links, total {len(done)}"
            )
            if added == 0:
                break
            if max_images > 0 and len(done) >= max_images:
                break
            time.sleep(self.wait_between_scroll)

    def configure_safe_search(self) -> None:
        if not self.safe_search:
            self.driver.add_cookie(
                {
                    "name": "SRCHHPGUSR",
                    "value": "SRCHLANG=en&IG=69033305F5234C079A7886B84F432FB5&DM=0&BRW=XW&BRH=M&CW=1779&CH=918&SCW=1762&SCH=918&DPR=1.0&UTC=-300&WTS=63874663291&HV=1739066971&PRVCW=1792&PRVCH=332&ADLT=OFF&BCML=0&BCSRLANG=",
                    "domain": ".bing.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": False,
                    "expiry": 1773627172,
                }
            )

    def done(self) -> None:
        self.driver.quit()
