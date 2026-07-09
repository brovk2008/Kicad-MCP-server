# KiCad MCP Server 🔌📐

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![KiCad: 9.0+](https://img.shields.io/badge/KiCad-9.0+-green.svg)](https://kicad.org/)

An implementation of the **Model Context Protocol (MCP)** server for **KiCad 9.0+**, enabling Large Language Models (LLMs) like Claude to inspect, edit, analyze, and render PCB layouts in real-time.

It leverages the official `kicad-python` API to communicate with running KiCad instances over local Unix domain sockets or Windows named pipes.

---

## 🚀 Key Features

This server exposes 14 specialized modules providing comprehensive control over the board layout:

| Module | Description | Key Tools |
| :--- | :--- | :--- |
| 🎛️ **Board** | Inspect/update PCB configurations, units, and canvas settings | `get_board_info`, `get_board_stackup`, `set_active_layer`, `undo_transaction` |
| 🧩 **Footprints** | Manage component properties, placements, and pads | `get_footprints`, `move_footprint`, `set_footprint_property`, `delete_footprints` |
| ⚡ **Tracks & Vias**| List, route, resize, and remove traces and vias | `get_tracks`, `create_track`, `get_vias`, `create_via`, `delete_tracks_in_rect` |
| 🗺️ **Zones** | Control copper pours, fill/unfill, and rule boundaries | `get_zones`, `create_zone`, `refill_zones` |
| 🌐 **Nets** | Import netlists, manage classes, and trace connectivity | `get_nets`, `get_net_classes`, `import_netlist` |
| 🔤 **Text** | Add and style free-standing board text labels and textboxes | `get_text`, `create_text`, `create_textbox`, `delete_text` |
| 🎨 **Shapes** | Draw graphic segments, rects, circles, and polygons on user layers | `get_shapes`, `create_shape` |
| 📏 **Dimensions** | Place precise dimension and measurement markings | `get_dimensions`, `create_dimension` |
| 👥 **Groups** | Read structural component groupings (KiCad 10+) | `get_groups` |
| 🎯 **Selection** | Read active selection, select footprints, and invoke actions | `get_selection`, `select_footprints`, `run_action` |
| 👁️ **Appearance** | Adjust layer visibility, contrast modes, ratsnest lines, and flip view | `get_editor_appearance`, `set_board_flip`, `set_inactive_layer_display` |
| 📦 **Exports** | Export manufacturing files (Gerbers, drills, position, ODB++, PDF, STEP) | `export_gerbers`, `export_drill`, `export_position`, `export_3d`, `export_pdf` |
| 📸 **Screenshots**| Render visual PNG screenshots of the board or specific selection | `get_board_screenshot`, `get_selection_screenshot` |
| 💻 **CLI Wrapper** | Headless CLI automation for schematics, ERC, DRC, and more | `run_kicad_cli`, `run_erc`, `run_drc`, `export_schematic_pdf`, `export_schematic_netlist` |

---

## 📋 Prerequisites

1. **KiCad 9.0 or higher** must be installed and running.
2. **Enable the IPC API** inside KiCad:
   - Go to **Preferences** ➔ **Preferences...**
   - Navigate to **Plugins**
   - Check the **Enable KiCad IPC API** box.
3. **Python 3.10+** (tested on Python 3.10 through 3.14).

---

## ⚙️ Installation & Setup

We recommend using [`uv`](https://github.com/astral-sh/uv) for fast and isolated environment setup.

### 1. Clone the Repository
```bash
git clone https://github.com/brovk2008/Kicad-MCP-server.git
cd Kicad-MCP-server
```

### 2. Set Up the Virtual Environment
```bash
# Using uv (recommended)
uv venv
uv pip install -e .

# Or using standard pip
python -m venv .venv
source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows
pip install -e .
```

*Note: The project automatically applies a dynamic Protobuf descriptor pool patch to ensure compatibility with `kicad-python 0.7.1` on Python 3.14.*

---

## 🛠️ MCP Configuration

To use this server with **Claude Desktop**, add the configuration snippet below to your Claude configuration file:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS/Linux**: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Configuration Snippet

```json
{
  "mcpServers": {
    "kicad-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--package",
        "kicad-mcp",
        "kicad-mcp"
      ],
      "cwd": "C:/Users/techp/Downloads/more projects/Kicad mcp",
      "env": {
        "KICAD_API_SOCKET": "ipc:///tmp/kicad/api.sock"
      }
    }
  }
}
```
*(Adjust the `cwd` directory to point to your local installation path. For Windows, the socket path defaults to `ipc://%TEMP%\\kicad\\api.sock` if not explicitly set).*

---

## 🧪 Running Tests

A test suite is included to verify unit conversions, coordinate mappings, and error wrappers:

```bash
# Activate your virtual environment and run:
pytest tests/unit/
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
