from kipy.board_types import BoardText, BoardTextBox
from kipy.common_types import TextAttributes
from kicad_mcp.server import mcp
from kicad_mcp import connection, units, errors

def _text_to_dict(item) -> dict:
    t_type = "BoardText" if isinstance(item, BoardText) else "BoardTextBox"
    res = {
        "id": str(item.id),
        "type": t_type,
        "value": item.value,
        "layer": units.layer_name(item.layer),
        "locked": item.locked,
        "size_mm": {
            "width_mm": units.to_mm_float(item.attributes.size.x),
            "height_mm": units.to_mm_float(item.attributes.size.y),
        },
        "bold": item.attributes.bold,
        "italic": item.attributes.italic,
        "angle_deg": item.attributes.angle,
    }
    if isinstance(item, BoardText):
        res["position_mm"] = units.vec_to_dict(item.position)
    else:
        res["top_left_mm"] = units.vec_to_dict(item.top_left)
        res["bottom_right_mm"] = units.vec_to_dict(item.bottom_right)
    return res

@mcp.tool()
@errors.wrap
def list_text(layer_name: str | None = None) -> dict:
    """List free text and text box items on the board, optionally filtered by layer name."""
    board = connection.get_board()
    items = board.get_text()
    result = []
    
    layer_int = None
    if layer_name:
        layer_int = units.layer(layer_name)

    for item in items:
        if layer_int is not None and item.layer != layer_int:
            continue
        result.append(_text_to_dict(item))
    return errors.ok(texts=result, count=len(result))

@mcp.tool()
@errors.wrap
def get_text_item(text_id: str) -> dict:
    """Get details of a specific text or text box item by its ID."""
    board = connection.get_board()
    items = board.get_items_by_id([text_id])
    if not items:
        return errors.err(f"Text item with ID '{text_id}' not found.")
    return errors.ok(text=_text_to_dict(items[0]))

@mcp.tool()
@errors.wrap
def add_text(
    value: str,
    x_mm: float,
    y_mm: float,
    layer_name: str = "F.SilkS",
    size_mm: float = 1.0,
    bold: bool = False,
    italic: bool = False,
    rotation_deg: float = 0.0,
) -> dict:
    """Add a free text object to the board."""
    board = connection.get_board()
    t = BoardText()
    t.value = value
    t.position = units.vec(x_mm, y_mm)
    t.layer = units.layer(layer_name)
    t.locked = False
    
    t.attributes.size = units.vec(size_mm, size_mm)
    t.attributes.bold = bold
    t.attributes.italic = italic
    t.attributes.angle = rotation_deg
    
    created = board.create_items(t)
    return errors.ok(text_id=str(created[0].id))

@mcp.tool()
@errors.wrap
def add_text_box(
    value: str,
    x1_mm: float,
    y1_mm: float,
    x2_mm: float,
    y2_mm: float,
    layer_name: str = "F.SilkS",
    size_mm: float = 1.0,
) -> dict:
    """Add a text box to the board."""
    board = connection.get_board()
    tb = BoardTextBox()
    tb.value = value
    tb.top_left = units.vec(x1_mm, y1_mm)
    tb.bottom_right = units.vec(x2_mm, y2_mm)
    tb.layer = units.layer(layer_name)
    tb.locked = False
    
    tb.attributes.size = units.vec(size_mm, size_mm)
    
    created = board.create_items(tb)
    return errors.ok(text_id=str(created[0].id))

@mcp.tool()
@errors.wrap
def update_text_value(text_id: str, value: str) -> dict:
    """Update the text value of a text or text box item."""
    board = connection.get_board()
    items = board.get_items_by_id([text_id])
    if not items:
        return errors.err(f"Text item with ID '{text_id}' not found.")
    item = items[0]
    item.value = value
    board.update_items([item])
    return errors.ok()

@mcp.tool()
@errors.wrap
def update_text_position(text_id: str, x_mm: float, y_mm: float) -> dict:
    """Update the position of a text item (top-left for text boxes)."""
    board = connection.get_board()
    items = board.get_items_by_id([text_id])
    if not items:
        return errors.err(f"Text item with ID '{text_id}' not found.")
    item = items[0]
    
    if isinstance(item, BoardText):
        item.position = units.vec(x_mm, y_mm)
    else:
        # For TextBox, move it relative to top-left
        tl = item.top_left
        br = item.bottom_right
        delta = units.vec(x_mm, y_mm) - tl
        item.top_left = units.vec(x_mm, y_mm)
        item.bottom_right = br + delta
        
    board.update_items([item])
    return errors.ok()

@mcp.tool()
@errors.wrap
def update_text_layer(text_id: str, layer_name: str) -> dict:
    """Update the layer of a text or text box item."""
    board = connection.get_board()
    items = board.get_items_by_id([text_id])
    if not items:
        return errors.err(f"Text item with ID '{text_id}' not found.")
    item = items[0]
    item.layer = units.layer(layer_name)
    board.update_items([item])
    return errors.ok()

@mcp.tool()
@errors.wrap
def update_text_attributes(
    text_id: str,
    size_mm: float | None = None,
    bold: bool | None = None,
    italic: bool | None = None,
    rotation_deg: float | None = None,
) -> dict:
    """Update text formatting attributes."""
    board = connection.get_board()
    items = board.get_items_by_id([text_id])
    if not items:
        return errors.err(f"Text item with ID '{text_id}' not found.")
    item = items[0]
    
    if size_mm is not None:
        item.attributes.size = units.vec(size_mm, size_mm)
    if bold is not None:
        item.attributes.bold = bold
    if italic is not None:
        item.attributes.italic = italic
    if rotation_deg is not None:
        item.attributes.angle = rotation_deg
        
    board.update_items([item])
    return errors.ok()

@mcp.tool()
@errors.wrap
def lock_text(text_id: str, locked: bool) -> dict:
    """Lock or unlock a text or text box item."""
    board = connection.get_board()
    items = board.get_items_by_id([text_id])
    if not items:
        return errors.err(f"Text item with ID '{text_id}' not found.")
    item = items[0]
    item.locked = locked
    board.update_items([item])
    return errors.ok()

@mcp.tool()
@errors.wrap
def remove_text(text_id: str) -> dict:
    """Remove a text or text box item from the board."""
    board = connection.get_board()
    items = board.get_items_by_id([text_id])
    if not items:
        return errors.err(f"Text item with ID '{text_id}' not found.")
    board.remove_items(items)
    return errors.ok(removed=text_id)

@mcp.tool()
@errors.wrap
def expand_text_variables(text: str) -> dict:
    """Expand text variables in the given string based on board/project settings."""
    board = connection.get_board()
    expanded = board.expand_text_variables(text)
    return errors.ok(expanded=expanded)
