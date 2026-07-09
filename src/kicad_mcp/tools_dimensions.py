from kipy.board_types import (
    Dimension,
    AlignedDimension,
    to_concrete_dimension
)
from kipy.proto.board import board_types_pb2
from kicad_mcp.server import mcp
from kicad_mcp import connection, units, errors

def _dimension_to_dict(d) -> dict:
    cd = to_concrete_dimension(d)
    d_type = type(cd).__name__
    
    try:
        unit_str = board_types_pb2.DimensionUnit.Name(cd.unit)
    except Exception:
        unit_str = "UNKNOWN"

    res = {
        "id": str(cd.id),
        "type": d_type,
        "layer": units.layer_name(cd.layer),
        "locked": cd.locked,
        "unit": unit_str,
        "override_text_enabled": cd.override_text_enabled,
        "override_text": cd.override_text,
        "prefix": cd.prefix,
        "suffix": cd.suffix,
    }
    
    if isinstance(cd, AlignedDimension):
        res["start_mm"] = units.vec_to_dict(cd.start)
        res["end_mm"] = units.vec_to_dict(cd.end)
        res["height_mm"] = units.to_mm_float(cd.height)
        res["extension_height_mm"] = units.to_mm_float(cd.extension_height)
        
    return res

@mcp.tool()
@errors.wrap
def list_dimensions(layer_name: str | None = None) -> dict:
    """List dimension annotations on the board, optionally filtered by layer name."""
    board = connection.get_board()
    dims = board.get_dimensions()
    result = []
    
    layer_int = None
    if layer_name:
        layer_int = units.layer(layer_name)

    for d in dims:
        if layer_int is not None and d.layer != layer_int:
            continue
        result.append(_dimension_to_dict(d))
    return errors.ok(dimensions=result, count=len(result))

@mcp.tool()
@errors.wrap
def get_dimension(dim_id: str) -> dict:
    """Get details of a specific dimension annotation by its ID."""
    board = connection.get_board()
    items = board.get_items_by_id([dim_id])
    if not items:
        return errors.err(f"Dimension annotation with ID '{dim_id}' not found.")
    return errors.ok(dimension=_dimension_to_dict(items[0]))

@mcp.tool()
@errors.wrap
def add_aligned_dimension(
    start_x_mm: float,
    start_y_mm: float,
    end_x_mm: float,
    end_y_mm: float,
    height_mm: float,
    layer_name: str,
) -> dict:
    """Add an aligned dimension annotation to the board."""
    board = connection.get_board()
    d = AlignedDimension()
    d.layer = units.layer(layer_name)
    d.start = units.vec(start_x_mm, start_y_mm)
    d.end = units.vec(end_x_mm, end_y_mm)
    d.height = units.mm(height_mm)
    d.extension_height = units.mm(height_mm / 2.0) # Reasonable extension default
    
    created = board.create_items(d)
    return errors.ok(dim_id=str(created[0].id))

@mcp.tool()
@errors.wrap
def remove_dimension(dim_id: str) -> dict:
    """Remove a dimension annotation from the board."""
    board = connection.get_board()
    items = board.get_items_by_id([dim_id])
    if not items:
        return errors.err(f"Dimension annotation with ID '{dim_id}' not found.")
    board.remove_items(items)
    return errors.ok(removed=dim_id)

@mcp.tool()
@errors.wrap
def update_dimension_layer(dim_id: str, layer_name: str) -> dict:
    """Change the layer of a dimension annotation."""
    board = connection.get_board()
    items = board.get_items_by_id([dim_id])
    if not items:
        return errors.err(f"Dimension annotation with ID '{dim_id}' not found.")
    d = items[0]
    d.layer = units.layer(layer_name)
    board.update_items([d])
    return errors.ok()

@mcp.tool()
@errors.wrap
def lock_dimension(dim_id: str, locked: bool) -> dict:
    """Lock or unlock a dimension annotation."""
    board = connection.get_board()
    items = board.get_items_by_id([dim_id])
    if not items:
        return errors.err(f"Dimension annotation with ID '{dim_id}' not found.")
    d = items[0]
    d.locked = locked
    board.update_items([d])
    return errors.ok()
