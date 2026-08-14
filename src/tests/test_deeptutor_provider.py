from src.providers.llm import DeepTutorProvider


def test_deeptutor_url_from_http_base():
    provider = DeepTutorProvider("http://127.0.0.1:8002")
    assert provider.ws_url == "ws://127.0.0.1:8002/api/v1/ws"


def test_deeptutor_url_preserves_api_path():
    provider = DeepTutorProvider("https://tutor.example/api/v1/ws")
    assert provider.ws_url == "wss://tutor.example/api/v1/ws"


def test_deeptutor_token_is_only_added_to_connect_url():
    provider = DeepTutorProvider("http://127.0.0.1:8002", token="test token")
    assert provider.ws_url == "ws://127.0.0.1:8002/api/v1/ws"
    assert provider._connect_url == "ws://127.0.0.1:8002/api/v1/ws?token=test+token"


def test_deeptutor_turn_contains_history_and_system_instruction():
    provider = DeepTutorProvider("http://127.0.0.1:8002")
    payload = provider._turn_payload(
        [{"role": "user", "content": "first"}, {"role": "user", "content": "second"}],
        "teach concisely",
    )
    assert payload["type"] == "message"
    assert payload["capability"] == "chat"
    assert "[System instruction]\nteach concisely" in payload["content"]
    assert "[user]\nfirst" in payload["content"]
    assert payload["content"].endswith("[User]\nsecond")
