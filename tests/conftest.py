# conftest.py — pytest session fixture
# Pre-import requests so sys.modules["requests"] is the real module before
# test_fetch.py's _load_module() bootstrapper checks it.  Without this, the
# bootstrapper injects a bare types.ModuleType("requests") (no .get), which
# causes patch("requests.get", ...) to raise AttributeError.
import requests  # noqa: F401
