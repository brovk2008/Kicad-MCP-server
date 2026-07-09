from kipy.proto.common import commands
from kipy.board_types import to_concrete_board_shape
from kicad_mcp.server import mcp
from kicad_mcp import connection, errors

@mcp.tool()
@errors.wrap
def get_selection() -> dict:
    """Retrieve items in the current board editor selection."""
    board = connection.get_board()
    selection = board.get_selection()
    result = []
    for item in selection:
        # Determine human-friendly name
        concrete = to_concrete_board_shape(item) if hasattr(item, "attributes") else item
        item_type = type(concrete).__name__
        
        summary = ""
        if hasattr(concrete, "reference_field"):
            summary = f"Footprint {concrete.reference_field.text.value}"
        elif hasattr(concrete, "net") and concrete.net:
            summary = f"Net: {concrete.net.name}"
        elif hasattr(concrete, "value"):
            summary = f"Text: {concrete.value}"
            
        result.append({
            "id": str(concrete.id),
            "type": item_type,
            "summary": summary,
        })
    return errors.ok(selection=result, count=len(result))

@mcp.tool()
@errors.wrap
def get_selection_as_string() -> dict:
    """Retrieve the selection content serialized in KiCad's board file format."""
    board = connection.get_board()
    content = board.get_selection_as_string()
    return errors.ok(content=content)

@mcp.tool()
@errors.wrap
def add_to_selection(item_ids: list[str]) -> dict:
    """Add items to the active selection on the board by their IDs."""
    board = connection.get_board()
    items = board.get_items_by_id(item_ids)
    if not items:
        return errors.err("No valid items found matching the provided IDs.")
    updated = board.add_to_selection(items)
    return errors.ok(selected_count=len(updated))

@mcp.tool()
@errors.wrap
def remove_from_selection(item_ids: list[str]) -> dict:
    """Remove items from the active selection on the board by their IDs."""
    board = connection.get_board()
    items = board.get_items_by_id(item_ids)
    if not items:
        return errors.err("No valid items found matching the provided IDs.")
    updated = board.remove_from_selection(items)
    return errors.ok(selected_count=len(updated))

@mcp.tool()
@errors.wrap
def clear_selection() -> dict:
    """Clear all active selections on the board."""
    board = connection.get_board()
    board.clear_selection()
    return errors.ok()

@mcp.tool()
@errors.wrap
def select_footprints(references: list[str]) -> dict:
    """Select footprints on the board by their reference designators."""
    board = connection.get_board()
    fps = board.get_footprints()
    targets = [f for f in fps if f.reference_field.text.value.upper() in [r.upper() for r in references]]
    if not targets:
        return errors.err("No footprints found matching the provided references.")
    board.clear_selection()
    updated = board.add_to_selection(targets)
    return errors.ok(selected_count=len(updated))

@mcp.tool()
@errors.wrap
def run_action(action: str) -> dict:
    """Trigger a KiCad TOOL_ACTION in the editor.
    
    WARNING: Action names can be unstable between KiCad versions. Use with caution.
    Known actions:
      - 'pcbnew.ZoneFiller.zoneFill'
      - 'pcbnew.InteractiveRouter.DRCCheck'
      - 'pcbnew.ZoneFiller.zoneUnfill'
      - 'pcbnew.Editor.selectAll'
    """
    client = connection.get_client()
    res = client.run_action(action)
    try:
        status_name = commands.RunActionStatus.Name(res.status)
    except Exception:
        status_name = f"UNKNOWN({res.status})"
    return errors.ok(status=status_name)
