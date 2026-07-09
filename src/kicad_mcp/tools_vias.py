from kipy.board_types import Via, Net
from kipy.proto.board.board_types_pb2 import ViaType
from kipy.proto.board import board_types_pb2
from kicad_mcp.server import mcp
from kicad_mcp import connection, units, errors

VIA_TYPE_MAP = {
    "through": ViaType.VT_THROUGH,
    "blind_buried": ViaType.VT_BLIND_BURIED,
    "blind": ViaType.VT_BLIND_BURIED,
    "buried": ViaType.VT_BLIND_BURIED,
    "micro": ViaType.VT_MICRO,
    "microvia": ViaType.VT_MICRO,
}

def _via_to_dict(via) -> dict:
    try:
        v_type = board_types_pb2.ViaType.Name(via.type)
    except Exception:
        v_type = "UNKNOWN"
    return {
        "id": str(via.id),
        "position_mm": units.vec_to_dict(via.position),
        "diameter_mm": units.to_mm_float(via.diameter),
        "drill_mm": units.to_mm_float(via.drill_diameter),
        "net": via.net.name,
        "type": v_type,
        "locked": via.locked,
    }

@mcp.tool()
@errors.wrap
def list_vias(net_name: str | None = None) -> dict:
    """List vias on the board, optionally filtered by net name."""
    board = connection.get_board()
    vias = board.get_vias()
    result = []
    for v in vias:
        if net_name and v.net.name.upper() != net_name.upper():
            continue
        result.append(_via_to_dict(v))
    return errors.ok(vias=result, count=len(result))

@mcp.tool()
@errors.wrap
def get_via(via_id: str) -> dict:
    """Get details of a specific via by its ID."""
    board = connection.get_board()
    items = board.get_items_by_id([via_id])
    if not items:
        return errors.err(f"Via with ID '{via_id}' not found.")
    return errors.ok(via=_via_to_dict(items[0]))

@mcp.tool()
@errors.wrap
def add_via(
    x_mm: float,
    y_mm: float,
    diameter_mm: float = 0.6,
    drill_mm: float = 0.3,
    net_name: str | None = None,
    via_type: str = "through",
    locked: bool = False,
) -> dict:
    """Add a via to the board."""
    board = connection.get_board()
    via = Via()
    via.position = units.vec(x_mm, y_mm)
    via.diameter = units.mm(diameter_mm)
    via.drill_diameter = units.mm(drill_mm)
    
    if net_name:
        via.net = Net(name=net_name)
    
    via.locked = locked
    
    vt = VIA_TYPE_MAP.get(via_type.lower(), ViaType.VT_THROUGH)
    via.type = vt

    created = board.create_items(via)
    return errors.ok(via_id=str(created[0].id))

@mcp.tool()
@errors.wrap
def update_via_size(via_id: str, diameter_mm: float | None = None, drill_mm: float | None = None) -> dict:
    """Update the diameter and/or drill size of a via."""
    board = connection.get_board()
    items = board.get_items_by_id([via_id])
    if not items:
        return errors.err(f"Via with ID '{via_id}' not found.")
    via = items[0]
    
    if diameter_mm is not None:
        via.diameter = units.mm(diameter_mm)
    if drill_mm is not None:
        via.drill_diameter = units.mm(drill_mm)
        
    board.update_items([via])
    return errors.ok()

@mcp.tool()
@errors.wrap
def update_via_net(via_id: str, net_name: str) -> dict:
    """Update the net assigned to a via."""
    board = connection.get_board()
    items = board.get_items_by_id([via_id])
    if not items:
        return errors.err(f"Via with ID '{via_id}' not found.")
    via = items[0]
    via.net = Net(name=net_name)
    board.update_items([via])
    return errors.ok()

@mcp.tool()
@errors.wrap
def lock_via(via_id: str, locked: bool) -> dict:
    """Lock or unlock a via."""
    board = connection.get_board()
    items = board.get_items_by_id([via_id])
    if not items:
        return errors.err(f"Via with ID '{via_id}' not found.")
    via = items[0]
    via.locked = locked
    board.update_items([via])
    return errors.ok()

@mcp.tool()
@errors.wrap
def remove_via(via_id: str) -> dict:
    """Remove a via from the board."""
    board = connection.get_board()
    items = board.get_items_by_id([via_id])
    if not items:
        return errors.err(f"Via with ID '{via_id}' not found.")
    board.remove_items(items)
    return errors.ok(removed=via_id)
