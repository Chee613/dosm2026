import json

import dashboard_server


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self.payload


def test_gemini_classifies_a_typo_into_a_supported_intent():
    captured = {}

    def fake_open(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": json.dumps(
                                        {
                                            "intent": "highest_priority",
                                            "islands": [],
                                            "confidence": 0.98,
                                        }
                                    )
                                }
                            ]
                        }
                    }
                ]
            }
        )

    result = dashboard_server.classify_question(
        "which island have the highest rosk rightnow",
        "Redang",
        "secret-key",
        urlopen=fake_open,
    )

    assert result == {"intent": "highest_priority", "islands": [], "confidence": 0.98}
    assert captured["timeout"] == 8
    assert captured["request"].headers["X-goog-api-key"] == "secret-key"
    assert "gemini-3.1-flash-lite:generateContent" in captured["request"].full_url
    body = json.loads(captured["request"].data)
    assert body["generationConfig"]["responseMimeType"] == "application/json"


def test_gemini_rejects_unknown_intents():
    def fake_open(_request, timeout=8, **_kwargs):
        return FakeResponse(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": '{"intent":"invent_answer","islands":[],"confidence":1}'}
                            ]
                        }
                    }
                ]
            }
        )

    try:
        dashboard_server.classify_question("hello", None, "secret-key", urlopen=fake_open)
    except ValueError as error:
        assert "Unsupported intent" in str(error)
    else:
        raise AssertionError("unknown Gemini intent was accepted")
