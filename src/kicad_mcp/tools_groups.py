from kicad_mcp.server import mcp
from kicad_mcp import connection, errors

@mcp.tool()
@errors.wrap
def list_groups() -> dict:
    """List structural groups of items defined on the board (KiCad 10+)."""
    board = connection.get_board()
    if not hasattr(board, "get_groups"):
        return errors.err("Groups are not supported on this KiCad/kipy version (requires KiCad 10+).")
        
    groups = board.get_groups()
    result = []
    for g in groups:
        result.append({
            "id": str(g.id),
            "name": g.name,
            "item_count": len(g.items),
        })
    return errors.ok(groups=result, count=len(result))

@mcp.tool()
@errors.wrap
def get_group(group_id: str) -> dict:
    """Retrieve detailed information about a group and its member items by ID (KiCad 10+)."""
    board = connection.get_board()
    if not hasattr(board, "get_groups"):
        return errors.err("Groups are not supported on this KiCad/kipy version (requires KiCad 10+).")
        
    groups = board.get_groups()
    g = next((group for group in groups if str(group.id) == group_id), None)
    if g is None:
        return errors.err(f"Group with ID '{group_id}' not found.")
        
    member_items = []
    for item in g.items:
        member_items.append({
            "id": str(item.id),
            "type": type(item).__name__,
        })
        
    return errors.ok(
        id=str(g.id),
        name=g.name,
        items=member_items,
        count=len(member_items),
    )
