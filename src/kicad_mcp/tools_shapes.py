from kipy.board_types import (
    BoardShape,
    BoardSegment,
    BoardRectangle,
    BoardCircle,
    BoardArc,
    BoardPolygon,
    to_concrete_board_shape
)
from kipy.geometry import PolyLine, PolyLineNode, PolygonWithHoles, Vector2, Angle
from kicad_mcp.server import mcp
from kicad_mcp import connection, units, errors

def _shape_to_dict(shape) -> dict:
    c_shape = to_concrete_board_shape(shape)
    s_type = type(c_shape).__name__
    
    # Bounding box
    bbox_dict = None
    try:
        # Bbox is a method or property?
        if hasattr(c_shape, "bounding_box"):
            bbox = c_shape.bounding_box()
            if hasattr(bbox, "pos"):
                bbox_dict = {
                    "x_mm": units.to_mm_float(bbox.pos.x),
                    "y_mm": units.to_mm_float(bbox.pos.y),
                    "w_mm": units.to_mm_float(bbox.size.x),
                    "h_mm": units.to_mm_float(bbox.size.y),
                }
    except Exception:
        pass

    res = {
        "id": str(c_shape.id),
        "type": s_type,
        "layer": units.layer_name(c_shape.layer),
        "locked": c_shape.locked,
        "width_mm": units.to_mm_float(c_shape.attributes.stroke.width),
        "filled": c_shape.attributes.fill.filled,
        "bounding_box": bbox_dict,
    }
    
    # Geometry serialization
    if isinstance(c_shape, BoardSegment):
        res["start_mm"] = units.vec_to_dict(c_shape.start)
        res["end_mm"] = units.vec_to_dict(c_shape.end)
    elif isinstance(c_shape, BoardRectangle):
        res["top_left_mm"] = units.vec_to_dict(c_shape.top_left)
        res["bottom_right_mm"] = units.vec_to_dict(c_shape.bottom_right)
    elif isinstance(c_shape, BoardCircle):
        res["center_mm"] = units.vec_to_dict(c_shape.center)
        res["radius_mm"] = units.to_mm_float(c_shape.radius())
    elif isinstance(c_shape, BoardArc):
        res["start_mm"] = units.vec_to_dict(c_shape.start)
        res["mid_mm"] = units.vec_to_dict(c_shape.mid)
        res["end_mm"] = units.vec_to_dict(c_shape.end)
    elif isinstance(c_shape, BoardPolygon):
        poly_list = []
        for poly in c_shape.polygons:
            pts = []
            for node in poly.outline.nodes:
                if node.has_point:
                    pts.append(units.vec_to_dict(node.point))
            poly_list.append(pts)
        res["points_mm"] = poly_list
        
    return res

@mcp.tool()
@errors.wrap
def list_shapes(layer_name: str | None = None) -> dict:
    """List graphic shapes on the board, optionally filtered by layer name."""
    board = connection.get_board()
    shapes = board.get_shapes()
    result = []
    
    layer_int = None
    if layer_name:
        layer_int = units.layer(layer_name)

    for s in shapes:
        if layer_int is not None and s.layer != layer_int:
            continue
        result.append(_shape_to_dict(s))
    return errors.ok(shapes=result, count=len(result))

@mcp.tool()
@errors.wrap
def get_shape(shape_id: str) -> dict:
    """Get details of a specific graphic shape by its ID."""
    board = connection.get_board()
    items = board.get_items_by_id([shape_id])
    if not items:
        return errors.err(f"Shape with ID '{shape_id}' not found.")
    return errors.ok(shape=_shape_to_dict(items[0]))

@mcp.tool()
@errors.wrap
def add_segment(
    x1_mm: float,
    y1_mm: float,
    x2_mm: float,
    y2_mm: float,
    layer_name: str,
    width_mm: float = 0.1,
) -> dict:
    """Add a straight graphic segment (line) to the board."""
    board = connection.get_board()
    s = BoardSegment()
    s.layer = units.layer(layer_name)
    s.start = units.vec(x1_mm, y1_mm)
    s.end = units.vec(x2_mm, y2_mm)
    s.attributes.stroke.width = units.mm(width_mm)
    
    created = board.create_items(s)
    return errors.ok(shape_id=str(created[0].id))

@mcp.tool()
@errors.wrap
def add_rectangle(
    x1_mm: float,
    y1_mm: float,
    x2_mm: float,
    y2_mm: float,
    layer_name: str,
    width_mm: float = 0.1,
    filled: bool = False,
) -> dict:
    """Add a graphic rectangle to the board."""
    board = connection.get_board()
    r = BoardRectangle()
    r.layer = units.layer(layer_name)
    r.top_left = units.vec(x1_mm, y1_mm)
    r.bottom_right = units.vec(x2_mm, y2_mm)
    r.attributes.stroke.width = units.mm(width_mm)
    r.attributes.fill.filled = filled
    
    created = board.create_items(r)
    return errors.ok(shape_id=str(created[0].id))

@mcp.tool()
@errors.wrap
def add_circle(
    center_x_mm: float,
    center_y_mm: float,
    radius_mm: float,
    layer_name: str,
    width_mm: float = 0.1,
    filled: bool = False,
) -> dict:
    """Add a graphic circle to the board."""
    board = connection.get_board()
    c = BoardCircle()
    c.layer = units.layer(layer_name)
    c.center = units.vec(center_x_mm, center_y_mm)
    c.radius_point = units.vec(center_x_mm + radius_mm, center_y_mm)
    c.attributes.stroke.width = units.mm(width_mm)
    c.attributes.fill.filled = filled
    
    created = board.create_items(c)
    return errors.ok(shape_id=str(created[0].id))

@mcp.tool()
@errors.wrap
def add_arc(
    start_x_mm: float,
    start_y_mm: float,
    mid_x_mm: float,
    mid_y_mm: float,
    end_x_mm: float,
    end_y_mm: float,
    layer_name: str,
    width_mm: float = 0.1,
) -> dict:
    """Add a graphic arc to the board."""
    board = connection.get_board()
    a = BoardArc()
    a.layer = units.layer(layer_name)
    a.start = units.vec(start_x_mm, start_y_mm)
    a.mid = units.vec(mid_x_mm, mid_y_mm)
    a.end = units.vec(end_x_mm, end_y_mm)
    a.attributes.stroke.width = units.mm(width_mm)
    
    created = board.create_items(a)
    return errors.ok(shape_id=str(created[0].id))

@mcp.tool()
@errors.wrap
def add_polygon(
    points_mm: list[dict],
    layer_name: str,
    width_mm: float = 0.1,
    filled: bool = True,
) -> dict:
    """Add a graphic polygon to the board.
    
    points_mm should be a list like [{"x_mm": 0, "y_mm": 0}, ...]
    """
    board = connection.get_board()
    p = BoardPolygon()
    p.layer = units.layer(layer_name)
    p.attributes.stroke.width = units.mm(width_mm)
    p.attributes.fill.filled = filled
    
    poly_with_holes = PolygonWithHoles()
    outline = PolyLine()
    outline.closed = True
    for pt in points_mm:
        node = PolyLineNode()
        node.point = units.vec(pt["x_mm"], pt["y_mm"])
        outline.append(node)
        
    poly_with_holes.outline = outline
    p.polygons.append(poly_with_holes)
    
    created = board.create_items(p)
    return errors.ok(shape_id=str(created[0].id))

@mcp.tool()
@errors.wrap
def move_shape(shape_id: str, delta_x_mm: float, delta_y_mm: float) -> dict:
    """Move a shape by a relative offset (in millimeters)."""
    board = connection.get_board()
    items = board.get_items_by_id([shape_id])
    if not items:
        return errors.err(f"Shape with ID '{shape_id}' not found.")
    shape = to_concrete_board_shape(items[0])
    shape.move(units.vec(delta_x_mm, delta_y_mm))
    board.update_items([shape])
    return errors.ok()

@mcp.tool()
@errors.wrap
def rotate_shape(shape_id: str, angle_deg: float, center_x_mm: float, center_y_mm: float) -> dict:
    """Rotate a shape by an angle around a center point (in degrees)."""
    board = connection.get_board()
    items = board.get_items_by_id([shape_id])
    if not items:
        return errors.err(f"Shape with ID '{shape_id}' not found.")
    shape = to_concrete_board_shape(items[0])
    
    # We might need to convert rect to polygon first if rotation is not a multiple of 90
    if isinstance(shape, BoardRectangle) and angle_deg % 90 != 0:
        # Convert to BoardPolygon first, then delete rectangle and create polygon
        poly = BoardPolygon.from_rectangle(shape)
        board.remove_items([shape])
        poly.rotate(Angle.from_degrees(angle_deg), units.vec(center_x_mm, center_y_mm))
        created = board.create_items(poly)
        return errors.ok(shape_converted_to_polygon=True, new_shape_id=str(created[0].id))
        
    shape.rotate(Angle.from_degrees(angle_deg), units.vec(center_x_mm, center_y_mm))
    board.update_items([shape])
    return errors.ok()

@mcp.tool()
@errors.wrap
def update_shape_layer(shape_id: str, layer_name: str) -> dict:
    """Change the layer of a shape."""
    board = connection.get_board()
    items = board.get_items_by_id([shape_id])
    if not items:
        return errors.err(f"Shape with ID '{shape_id}' not found.")
    shape = items[0]
    shape.layer = units.layer(layer_name)
    board.update_items([shape])
    return errors.ok()

@mcp.tool()
@errors.wrap
def update_shape_width(shape_id: str, width_mm: float) -> dict:
    """Update the stroke line width of a shape."""
    board = connection.get_board()
    items = board.get_items_by_id([shape_id])
    if not items:
        return errors.err(f"Shape with ID '{shape_id}' not found.")
    shape = to_concrete_board_shape(items[0])
    shape.attributes.stroke.width = units.mm(width_mm)
    board.update_items([shape])
    return errors.ok()

@mcp.tool()
@errors.wrap
def lock_shape(shape_id: str, locked: bool) -> dict:
    """Lock or unlock a shape."""
    board = connection.get_board()
    items = board.get_items_by_id([shape_id])
    if not items:
        return errors.err(f"Shape with ID '{shape_id}' not found.")
    shape = items[0]
    shape.locked = locked
    board.update_items([shape])
    return errors.ok()

@mcp.tool()
@errors.wrap
def remove_shape(shape_id: str) -> dict:
    """Remove a shape from the board."""
    board = connection.get_board()
    items = board.get_items_by_id([shape_id])
    if not items:
        return errors.err(f"Shape with ID '{shape_id}' not found.")
    board.remove_items(items)
    return errors.ok(removed=shape_id)
