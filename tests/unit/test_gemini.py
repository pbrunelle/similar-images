from unittest.mock import AsyncMock

import httpx
import pytest

from similar_images.gemini import Decision, Gemini


@pytest.mark.parametrize(
    "text_before_image",
    [
        False,
        True,
    ],
)
@pytest.mark.asyncio
async def test_gemini_ok(text_before_image):
    # GIVEN
    httpx_client = AsyncMock()
    content = {
        "candidates": [
            {
                "content": {"parts": [{"text": "Goo\ngle"}], "role": "model"},
                "finishReason": "STOP",
                "avgLogprobs": -5.926936864852905e-06,
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 270,
            "candidatesTokenCount": 1,
            "totalTokenCount": 271,
            "promptTokensDetails": [
                {"modality": "IMAGE", "tokenCount": 258},
                {"modality": "TEXT", "tokenCount": 12},
            ],
            "candidatesTokensDetails": [{"modality": "TEXT", "tokenCount": 1}],
        },
        "modelVersion": "gemini-2.0-flash",
    }
    httpx_client.post = AsyncMock(
        return_value=httpx.Response(
            request=httpx.Request("POST", url="goo.gell.com"),
            status_code=200,
            json=content,
        )
    )
    model = "hello"
    gemini = Gemini(
        httpx_client=httpx_client,
        model="hello",
        max_output_tokens=10,
        text_before_image=text_before_image,
    )
    image_path = "tests/integration/data/google-logo.png"
    # WHEN
    got = await gemini.chat(
        "What does this logo represent? Answer with a single word.", [image_path]
    )
    # THEN
    assert got == Decision(
        image_path="tests/integration/data/google-logo.png",
        content=content,
        status_code=200,
        usage={
            "promptTokenCount": 270,
            "candidatesTokenCount": 1,
            "totalTokenCount": 271,
        },
        block=None,
        text="Goo\ngle",
        decision="goo gle",
    )
    b64image = (
        "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABGdBTUEAALGPC/xhBQAAAAlwSFlzAAAOwgA"
        "ADsIBFShKgAAABE9JREFUWEe9l11sFFUUx/tisCj4xJsPoiBvSJRSHrTEr0WwDyTUQmsfQKwYgjwYtSYEDS"
        "RULfKRgA8thUJMw7YaaIUKJUWkot1YJGYJaYMWUAs1s9vtBzu77u7sHP/3zuluLnd2O7WNv+RkPs7H/8y5d"
        "6bbAq/Ytj0XVplOpxsty+qFDcOSbGFxT/gQUyFiOW36oNgiFG6CQJw8gtgYco4gdyGXmTqoMxtF9qKY5ZSd"
        "OkhNocYeNFLIZb2BhCeRfJ3rTBvUCqLmAi6fHwQ+jYQQ5ypYdwfJbD5Ko+9tofBrr5DhW07Gy8UUXuujkXf"
        "fJvN4A1mDf3K0CmoaOCxhGXf4yTVxa+gOje38kIyXlpHxYlF+Q8zYxx/InPsRTeScBBwPIUAbe/x8B4VeLX"
        "EXy2Oh0hX0z8XzXCULNMRy6HtCbDiOyWCeOOZa3KuN1+3kSirQqmNZB3S0CJ0pu108uVtRYZHqCooePkjxM"
        "ycp3nEK54co8lalEjO+r5bItrmaCqRSylKgoyb2ScRmC61+TikobLhqDSWuBDhKJ9HbQ+H1pXTv0Od8JzfQ"
        "bJTiOH8EHSkfmeiBdzTxka0byR4f54jc2GaUz/IDTRNTmCPGX8n3JHZsgFKds2is5rGMuHjl0qMRjpg5oL1"
        "OjL+RryXpW7WU6npAmnlwHoVWLaX4udPsnVmgXV+AUfTytcT6xZdpQFji5HyiVIq9Mwu0A6KBYb6WpLofVR"
        "qwrlWwx50Xdkc928Xr6oNA2xANJPlakrowS2kg/fsO9rjjJpTLmn9UpEQDif+1gaZLCc5ymGggzNcSbQmC6"
        "9njjptQLmsNaBOQS6BuwqsrlQYGuxdTMj31TXjTSGsNXOrT9kDA5TX8NCN+umM+PetfQ20DXez1jr8nqTUw"
        "NKp+muVriI+Bss3t2C2KdRVSbdsztNS/Vpqv7Q0Kx0c4YnLuxW0qO2Aq4hvqY+zNAu1y0cBcjELx7u/ZlRG"
        "fsKrO92k0MfmnOIk/aTUn4oq4sBZ9/U0cHpZ/DzCKI85th7tRg0q+fl1rovSbzdR95wpH6dwYuU2b2v0QHF"
        "PExTRiCW38DVJcgCksREfKDjl7u1trYMLKvt1Ge682UeuNs/TVb+foi2Azvdm1nYr8ZdJffKyGnv/sr0wDP"
        "/Srv2uhlYTmEyzvgI72sD/Dl/3tmrhXK2reQCX7ftbefQG0PmHZLLg/G51dc0KydP5xGctR5SqSz4pbyulw"
        "sJ2rZIHGrzg8yLIqGMsCBIhfrwpDZoi2/7SflrU4I57MNn/3EfVFBjg7C2r/jcPjLOcOApa4NSEQm/N43yn"
        "a+v0uWtVeTctby+WT+to2UfWFHXIv9EducrSKEMcDPsUy+eFJBDl32qCWGHv+J78fNFGIzVKH5P/8YwC5Sb"
        "HhcOq+5l4Q00AR8R+x+HB4QsQipwG56qs2HVBsDmwdCtdDIAAzYAk2cR4QPsSUowfnCzcpBQX/AlbCfo58G"
        "EZgAAAAAElFTkSuQmCC"
    )
    text_part = {"text": "What does this logo represent? Answer with a single word."}
    image_part = {"inline_data": {"mime_type": "image/png", "data": b64image}}
    parts = [text_part, image_part] if text_before_image else [image_part, text_part]
    httpx_client.post.assert_called_once_with(
        f"https://generativelanguage.googleapis.com/v1beta/models/hello:generateContent?key={gemini._api_key}",
        json={
            "generationConfig": {"max_output_tokens": 10},
            "contents": {"parts": parts},
        },
    )


def test_decision_answer():
    # GIVEN
    decision = Decision(
        image_path="",
        content={},
        block=None,
        text=None,
        decision="Here is a description of the image. Bla bla bla. <answer>no</answer>",
        status_code=200,
        usage=None,
    )
    # WHEN
    got = decision.answer()
    # THEN
    assert got == "no"
