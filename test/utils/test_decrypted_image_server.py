from types import SimpleNamespace

from modules.utils.decrypted_image_server import get_request_base_url


class DummyRequest:
    def __init__(self, headers=None, root_path="", scheme="http"):
        self.headers = headers or {}
        self.request = SimpleNamespace(
            scope={"root_path": root_path},
            url=SimpleNamespace(scheme=scheme),
        )


def test_get_request_base_url_preserves_reverse_proxy_prefix_from_referer():
    request = DummyRequest(
        headers={"referer": "https://example.test/proxy/7860/?__theme=dark"}
    )

    assert get_request_base_url(request) == "https://example.test/proxy/7860"


def test_get_request_base_url_prefers_forwarded_prefix_over_referer_path():
    request = DummyRequest(
        headers={
            "referer": "https://example.test/",
            "x-forwarded-prefix": "/app/sdcpp/",
        }
    )

    assert get_request_base_url(request) == "https://example.test/app/sdcpp"


def test_get_request_base_url_uses_root_path_without_referer():
    request = DummyRequest(
        headers={"host": "127.0.0.1:7860"},
        root_path="/proxy/7860",
        scheme="https",
    )

    assert get_request_base_url(request) == "https://127.0.0.1:7860/proxy/7860"
