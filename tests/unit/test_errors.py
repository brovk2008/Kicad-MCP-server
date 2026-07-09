from kicad_mcp import errors
from kipy.errors import ApiError

def test_ok():
    res = errors.ok(test_val="hello", num=42)
    assert res == {"ok": True, "test_val": "hello", "num": 42}

def test_err():
    res = errors.err("something failed")
    assert res == {"ok": False, "error": "something failed"}

def test_wrap_decorator_success():
    @errors.wrap
    def success_fn():
        return errors.ok(data="yay")
        
    res = success_fn()
    assert res == {"ok": True, "data": "yay"}

def test_wrap_decorator_api_error():
    @errors.wrap
    def api_fail_fn():
        raise ApiError("KiCad crashed")
        
    res = api_fail_fn()
    assert res["ok"] is False
    assert "KiCad API error" in res["error"]

def test_wrap_decorator_unexpected_error():
    @errors.wrap
    def crash_fn():
        raise RuntimeError("Unexpected exception")
        
    res = crash_fn()
    assert res["ok"] is False
    assert "Unexpected error" in res["error"]
