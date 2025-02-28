import os
import random
import tempfile

import exrex
import httpx

from similar_images.bing_selenium import BingSelenium
from similar_images.types import RunConfiguration
from similar_images.utils import get_urls_or_files


class ImageSource:
    """Return URLs or paths to images."""

    def get_client(self):
        return httpx.AsyncClient(follow_redirects=True, timeout=30)

    async def batches(self):
        raise NotImplementedError()

    async def images(self, batch: str) -> str:
        raise NotImplementedError()


class BrowserQuerySource(ImageSource):
    """Returns URLs to images based on search query terms."""

    def __init__(self, browser: BingSelenium, queries: str, random: bool = False):
        self._browser = browser
        self._queries = queries
        self._random = random

    async def batches(self):
        queries = exrex.generate(self._queries)
        if self._random:
            queries = list(queries)
            random.shuffle(queries)
        for query in queries:
            query = query.strip()
            yield query

    async def images(self, batch: str):
        async for url in self._browser.search_images(batch):
            yield url


class BrowserImageSource(ImageSource):
    """Returns URLs to images using the 'Search using an image' functionality."""

    def __init__(
        self, browser: BingSelenium, urls_or_paths: list[str], random: bool = False
    ):
        self._browser = browser
        self._urls_or_paths = urls_or_paths
        self._random = random

    async def batches(self):
        urls_or_paths = get_urls_or_files(self._urls_or_paths)
        if self._random:
            urls_or_paths = list(urls_or_paths)
            random.shuffle(urls_or_paths)
        for path in urls_or_paths:
            yield path

    async def images(self, batch: str):
        async for url in self._browser.search_similar_images(batch):
            yield url


class FakeClient:
    async def get(self, url: str, *args, **kwargs):
        with open(url, "rb") as f:
            return httpx.Response(
                status_code=200,
                content=f.read(),
                request=httpx.Request(method="GET", url=f"file://{url}"),
            )


class LocalFileImageSource(ImageSource):
    """Returns paths to the local file system.

    Useful for evaluation.
    """

    def __init__(self, local_paths: list[str], random: bool = False):
        self._local_paths = local_paths
        self._random = random

    def get_client(self):
        return FakeClient()

    async def batches(self):
        paths = self._local_paths
        if self._random:
            paths = list(paths)
            random.shuffle(paths)
        for path in paths:
            yield path

    async def images(self, batch: str):
        files_or_urls = get_urls_or_files([batch])
        if self._random:
            files_or_urls = list(files_or_urls)
            random.shuffle(files_or_urls)
        for path in files_or_urls:
            yield path


def get_browser(image_source: str, config: RunConfiguration) -> BingSelenium:
    assert config.bing_selenium, (
        f"{image_source}: need to specify bing_selenium configuration"
    )
    home_tmp_dir = tempfile.mkdtemp(dir=os.environ["HOME"])
    bs = config.bing_selenium
    return BingSelenium(
        wait_first_load=bs.wait_first_load,
        wait_between_scroll=bs.wait_between_scroll,
        safe_search=bs.safe_search,
        headless=bs.headless,
        user_data_dir=home_tmp_dir,
    )


def get_image_sources(config: RunConfiguration) -> list[ImageSource]:
    if not config.image_sources:
        return []
    ret = []
    for image_source in config.image_sources:
        for source_name, source_config in image_source.items():
            match source_name:
                case "BrowserQuerySource":
                    ret.append(
                        BrowserQuerySource(
                            browser=get_browser(source_name, config), **source_config
                        )
                    )
                case "BrowserImageSource":
                    ret.append(
                        BrowserImageSource(
                            browser=get_browser(source_name, config), **source_config
                        )
                    )
                case "LocalFileImageSource":
                    ret.append(LocalFileImageSource(**source_config))
    return ret
