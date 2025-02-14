import pytest
from unittest.mock import MagicMock
from similar_images.db_client import DBClient

@pytest.fixture
def live_client():
    return DBClient()

def _test_store_image_data_happy_path(live_client, tmp_path):
    # GIVEN
    file_path="requirements.in"
    origin_url = "https://example.com/image.jpg"
    out_path = tmp_path / "test_happy_path"
    # WHEN
    s3_url, image_id = live_client.upload(file_path=file_path, origin_url=origin_url)
    item = live_client.download(file_path=out_path, origin_url=origin_url)
    # THEN
    print(item)
    expected_item = {'projectName': {'S': 'unit_tests'}, 'imageUrl': {'S': origin_url}, 's3Url': {'S': s3_url}, 's3Key': {'S': image_id}}
    assert item == expected_item
    with open(out_path, "r") as f1:
        with open(file_path, "r") as f2:
            assert f1.read() == f2.read()
