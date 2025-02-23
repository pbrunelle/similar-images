import httpx
import pytest

from similar_images.gemini import Gemini


@pytest.mark.parametrize(
    "model",
    [
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite-preview-02-05",
        "gemini-2.0-pro-exp-02-05",
    ],
)
@pytest.mark.asyncio
async def test_gemini_ok(model):
    # GIVEN
    httpx_client = httpx.AsyncClient()
    gemini = Gemini(
        httpx_client=httpx_client,
        model=model,
        max_output_tokens=10,
    )
    image_path = "tests/integration/data/google-logo.png"
    # WHEN
    got = await gemini.chat(
        "What does this logo represent? Answer with a single word.", [image_path]
    )
    print(got)
    assert got.text.strip().lower() == "google"
    assert got.block is None
    assert got.decision == "google"
    assert got.usage["promptTokenCount"] == 270
    assert got.usage["candidatesTokenCount"] in (1, 2)
    assert got.status_code == 200
