from kipy.errors import ApiError

def ok(**kwargs) -> dict:
    return {"ok": True, **kwargs}

def err(message: str) -> dict:
    return {"ok": False, "error": message}

def wrap(fn):
    """Decorator: catch ApiError and generic Exception, return err() dict."""
    from functools import wraps
    @wraps(fn)
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ApiError as exc:
            return err(f"KiCad API error: {exc}")
        except Exception as exc:
            import traceback
            # Include traceback for unexpected errors to help debugging
            tb = traceback.format_exc()
            return err(f"Unexpected error: {exc}\n{tb}")
    return inner
