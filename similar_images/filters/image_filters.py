from PIL import Image
from similar_images.filters.filter import FilterResult, FilterStage, Filter

class ImageFilter(Filter):

    def __init__(self, min_size: tuple[int, int], min_area: int) -> None:
        self._min_size = sorted(min_size)
        self._min_area = min_area

    def stage(self) -> FilterStage:
        return "image"
        
    def stat_name(self) -> str:
        return "small"

    def filter(self, img: Image, **kwargs) -> FilterResult:
        size = sorted(img.size)
        area = size[0] * size[1]
        if size[0] < self._min_size[0] or size[1] < self._min_size[1] or area < self._min_area:
            return FilterResult(keep=False, explanation=f"{img.size}")
        else:
            return FilterResult(keep=True)
            