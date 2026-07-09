from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="kicad-mcp",
    instructions=(
        "Full control of a running KiCad 9+ instance via the IPC API: "
        "inspect and edit PCBs, manage components, tracks, vias, zones, nets, "
        "run exports, take screenshots. Requires KiCad to be running with "
        "Preferences → Plugins → Enable KiCad IPC API checked."
    ),
)

# Import all tool modules — the @mcp.tool() decorators register tools at import time
# Circular imports are avoided by importing after the mcp instance is created.
from kicad_mcp import (    # noqa: F401
    tools_board,
    tools_footprints,
    tools_tracks,
    tools_vias,
    tools_zones,
    tools_nets,
    tools_text,
    tools_shapes,
    tools_dimensions,
    tools_groups,
    tools_selection,
    tools_appearance,
    tools_export,
    tools_screenshot,
    tools_cli,
)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
