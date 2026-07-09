import os
import platform
from unittest.mock import patch, MagicMock
from kicad_mcp import tools_cli

def test_get_kicad_cli_path_env_search():
    # If shutil.which finds it, return that
    with patch("shutil.which", return_value="/mocked/path/kicad-cli"):
        path = tools_cli._get_kicad_cli_path()
        assert path == "/mocked/path/kicad-cli"

def test_get_kicad_cli_path_fallback():
    # If shutil.which doesn't find it, verify it falls back to os specific or default
    with patch("shutil.which", return_value=None), \
         patch("kicad_mcp.connection.get_board", side_effect=Exception("No running board")), \
         patch("os.path.exists", return_value=False):
        path = tools_cli._get_kicad_cli_path()
        assert path == "kicad-cli"
