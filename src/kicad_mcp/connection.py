import threading
import kipy
from kipy.errors import ApiError, ConnectionError as KiCadConnectionError

_lock = threading.Lock()
_client: kipy.KiCad | None = None


def get_client(timeout_ms: int = 5000) -> kipy.KiCad:
    """Return the singleton kipy.KiCad client, creating or reconnecting as needed."""
    global _client
    with _lock:
        if _client is None:
            _client = _make_client(timeout_ms)
        else:
            # Probe liveness; rebuild if dead
            try:
                _client.ping()
            except (KiCadConnectionError, OSError):
                try:
                    _client.close()
                except Exception:
                    pass
                _client = _make_client(timeout_ms)
        return _client


def _make_client(timeout_ms: int) -> kipy.KiCad:
    try:
        client = kipy.KiCad(
            client_name="kicad-mcp-server",
            timeout_ms=timeout_ms,
        )
        client.ping()
        return client
    except Exception as exc:
        raise RuntimeError(
            f"Cannot connect to KiCad IPC API. "
            f"Is KiCad 9+ running with Preferences→Plugins→Enable KiCad IPC API checked? "
            f"Original error: {exc}"
        ) from exc


def get_board():
    """Return the currently open Board, or raise a clear error."""
    client = get_client()
    try:
        board = client.get_board()
        return board
    except ApiError as exc:
        raise RuntimeError(
            "No PCB is currently open in KiCad. Open a .kicad_pcb file first."
        ) from exc


def close():
    global _client
    with _lock:
        if _client is not None:
            try:
                _client.close()
            except Exception:
                pass
            _client = None
