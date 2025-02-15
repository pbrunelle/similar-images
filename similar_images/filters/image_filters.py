from PIL import Image

from similar_images.filters.filter import Filter, FilterResult, FilterStage


class ImageFilter(Filter):
    def __init__(self, min_size: tuple[int, int], min_area: int) -> None:
        assert len(min_size) == 2
        assert min_area > 0
        self._min_size = tuple(sorted(min_size))
        self._min_area = min_area

    def stage(self) -> FilterStage:
        return "contents"

    def stat_name(self) -> str:
        return "small"

    async def filter(self, url: str, img: Image, **kwargs) -> FilterResult:
        size = sorted(img.size)
        area = size[0] * size[1]
        if (
            size[0] < self._min_size[0]
            or size[1] < self._min_size[1]
            or area < self._min_area
        ):
            explanation = f"Too small: {url}: {img.size}"
            return FilterResult(keep=False, explanation=explanation)
        else:
            return FilterResult(keep=True)
