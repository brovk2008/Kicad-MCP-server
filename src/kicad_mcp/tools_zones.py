import time
from kipy.board_types import Zone, Net
from kipy.geometry import PolyLine, PolyLineNode, PolygonWithHoles
from kipy.proto.board.board_types_pb2 import ZoneType
from kipy.proto.board import board_types_pb2
from kicad_mcp.server import mcp
from kicad_mcp import connection, units, errors

def _zone_to_dict(zone) -> dict:
    try:
        z_type = board_types_pb2.ZoneType.Name(zone.type)
    except Exception:
        z_type = "UNKNOWN"

    layers_list = [units.layer_name(lay) for lay in zone.layers]
    
    # Outer outline
    outline_points = []
    try:
        for node in zone.outline.outline.nodes:
            if node.has_point:
                outline_points.append(units.vec_to_dict(node.point))
    except Exception:
        pass

    # Holes
    holes_list = []
    try:
        for hole in zone.outline.holes:
            hole_pts = []
            for node in hole.nodes:
                if node.has_point:
                    hole_pts.append(units.vec_to_dict(node.point))
            holes_list.append(hole_pts)
    except Exception:
        pass

    net_name = None
    if not zone.is_rule_area() and zone.net:
        net_name = zone.net.name

    clearance = None
    if not zone.is_rule_area() and zone.clearance is not None:
        clearance = units.to_mm_float(zone.clearance)

    min_thickness = None
    if not zone.is_rule_area() and zone.min_thickness is not None:
        min_thickness = units.to_mm_float(zone.min_thickness)

    # Bounding box
    bbox_dict = None
    try:
        bbox = zone.bounding_box()
        bbox_dict = {
            "x_mm": units.to_mm_float(bbox.pos.x),
            "y_mm": units.to_mm_float(bbox.pos.y),
            "w_mm": units.to_mm_float(bbox.size.x),
            "h_mm": units.to_mm_float(bbox.size.y),
        }
    except Exception:
        pass

    return {
        "id": str(zone.id),
        "name": zone.name,
        "type": z_type,
        "net": net_name,
        "layers": layers_list,
        "is_rule_area": zone.is_rule_area(),
        "filled": zone.filled,
        "priority": zone.priority,
        "clearance_mm": clearance,
        "min_thickness_mm": min_thickness,
        "outline": outline_points,
        "holes": holes_list,
        "bounding_box": bbox_dict,
    }

@mcp.tool()
@errors.wrap
def list_zones(net_name: str | None = None, layer_name: str | None = None) -> dict:
    """List zones on the board, optionally filtered by net and/or layer."""
    board = connection.get_board()
    zones = board.get_zones()
    result = []
    
    layer_int = None
    if layer_name:
        layer_int = units.layer(layer_name)

    for z in zones:
        if net_name and not z.is_rule_area() and z.net and z.net.name.upper() != net_name.upper():
            continue
        if layer_int is not None and layer_int not in z.layers:
            continue
        result.append(_zone_to_dict(z))
    return errors.ok(zones=result, count=len(result))

@mcp.tool()
@errors.wrap
def get_zone(zone_id: str) -> dict:
    """Get details of a specific zone by its ID."""
    board = connection.get_board()
    items = board.get_items_by_id([zone_id])
    if not items:
        return errors.err(f"Zone with ID '{zone_id}' not found.")
    return errors.ok(zone=_zone_to_dict(items[0]))

def _build_rect_polygon(x1_mm: float, y1_mm: float, x2_mm: float, y2_mm: float) -> PolygonWithHoles:
    x1, y1 = units.mm(x1_mm), units.mm(y1_mm)
    x2, y2 = units.mm(x2_mm), units.mm(y2_mm)
    
    # Ensure ordered bounds
    xmin, xmax = min(x1, x2), max(x1, x2)
    ymin, ymax = min(y1, y2), max(y1, y2)
    
    outline = PolyLine()
    outline.closed = True
    
    for px, py in [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]:
        node = PolyLineNode()
        node.point = units.Vector2.from_xy(px, py)
        outline.append(node)
        
    p_with_h = PolygonWithHoles()
    p_with_h.outline = outline
    return p_with_h

@mcp.tool()
@errors.wrap
def add_rect_copper_zone(
    x1_mm: float,
    y1_mm: float,
    x2_mm: float,
    y2_mm: float,
    layer_name: str,
    net_name: str | None = None,
    name: str = "",
    clearance_mm: float | None = None,
    min_thickness_mm: float | None = None,
    priority: int = 0,
) -> dict:
    """Add a rectangular copper pour zone to the board."""
    board = connection.get_board()
    zone = Zone()
    zone.type = ZoneType.ZT_COPPER
    zone.layers = [units.layer(layer_name)]
    zone.name = name
    zone.priority = priority
    
    if net_name:
        zone.net = Net(name=net_name)
    if clearance_mm is not None:
        zone.clearance = units.mm(clearance_mm)
    if min_thickness_mm is not None:
        zone.min_thickness = units.mm(min_thickness_mm)

    zone.outline = _build_rect_polygon(x1_mm, y1_mm, x2_mm, y2_mm)
    created = board.create_items(zone)
    return errors.ok(zone_id=str(created[0].id))

@mcp.tool()
@errors.wrap
def add_polygon_copper_zone(
    points_mm: list[dict],
    layer_name: str,
    net_name: str | None = None,
    name: str = "",
    priority: int = 0,
) -> dict:
    """Add a polygonal copper pour zone to the board. 
    
    points_mm should be a list of dicts like [{"x_mm": 0, "y_mm": 0}, ...]
    """
    board = connection.get_board()
    zone = Zone()
    zone.type = ZoneType.ZT_COPPER
    zone.layers = [units.layer(layer_name)]
    zone.name = name
    zone.priority = priority
    
    if net_name:
        zone.net = Net(name=net_name)
        
    outline = PolyLine()
    outline.closed = True
    for pt in points_mm:
        node = PolyLineNode()
        node.point = units.vec(pt["x_mm"], pt["y_mm"])
        outline.append(node)
        
    p_with_h = PolygonWithHoles()
    p_with_h.outline = outline
    zone.outline = p_with_h
    
    created = board.create_items(zone)
    return errors.ok(zone_id=str(created[0].id))

@mcp.tool()
@errors.wrap
def add_rect_rule_area(
    x1_mm: float,
    y1_mm: float,
    x2_mm: float,
    y2_mm: float,
    layer_name: str,
    name: str = "",
) -> dict:
    """Add a keep-out / rule area zone (non-copper) to the board."""
    board = connection.get_board()
    zone = Zone()
    zone.type = ZoneType.ZT_RULE_AREA
    zone.layers = [units.layer(layer_name)]
    zone.name = name
    
    zone.outline = _build_rect_polygon(x1_mm, y1_mm, x2_mm, y2_mm)
    created = board.create_items(zone)
    return errors.ok(zone_id=str(created[0].id))

@mcp.tool()
@errors.wrap
def update_zone_net(zone_id: str, net_name: str) -> dict:
    """Change the net assigned to a copper zone."""
    board = connection.get_board()
    items = board.get_items_by_id([zone_id])
    if not items:
        return errors.err(f"Zone with ID '{zone_id}' not found.")
    zone = items[0]
    if zone.is_rule_area():
        return errors.err("Cannot assign a net to a keep-out / rule area zone.")
    zone.net = Net(name=net_name)
    board.update_items([zone])
    return errors.ok()

@mcp.tool()
@errors.wrap
def update_zone_priority(zone_id: str, priority: int) -> dict:
    """Change the priority level of a zone."""
    board = connection.get_board()
    items = board.get_items_by_id([zone_id])
    if not items:
        return errors.err(f"Zone with ID '{zone_id}' not found.")
    zone = items[0]
    zone.priority = priority
    board.update_items([zone])
    return errors.ok()

@mcp.tool()
@errors.wrap
def update_zone_clearance(zone_id: str, clearance_mm: float) -> dict:
    """Update the clearance setting of a copper zone."""
    board = connection.get_board()
    items = board.get_items_by_id([zone_id])
    if not items:
        return errors.err(f"Zone with ID '{zone_id}' not found.")
    zone = items[0]
    if zone.is_rule_area():
        return errors.err("Clearance settings do not apply to keep-out / rule area zones.")
    zone.clearance = units.mm(clearance_mm)
    board.update_items([zone])
    return errors.ok()

@mcp.tool()
@errors.wrap
def move_zone(zone_id: str, delta_x_mm: float, delta_y_mm: float) -> dict:
    """Shift a zone by a relative delta (in millimeters)."""
    board = connection.get_board()
    items = board.get_items_by_id([zone_id])
    if not items:
        return errors.err(f"Zone with ID '{zone_id}' not found.")
    zone = items[0]
    zone.move(units.vec(delta_x_mm, delta_y_mm))
    board.update_items([zone])
    return errors.ok()

@mcp.tool()
@errors.wrap
def lock_zone(zone_id: str, locked: bool) -> dict:
    """Lock or unlock a zone."""
    board = connection.get_board()
    items = board.get_items_by_id([zone_id])
    if not items:
        return errors.err(f"Zone with ID '{zone_id}' not found.")
    zone = items[0]
    zone.locked = locked
    board.update_items([zone])
    return errors.ok()

@mcp.tool()
@errors.wrap
def remove_zone(zone_id: str) -> dict:
    """Remove a zone from the board."""
    board = connection.get_board()
    items = board.get_items_by_id([zone_id])
    if not items:
        return errors.err(f"Zone with ID '{zone_id}' not found.")
    board.remove_items(items)
    return errors.ok(removed=zone_id)

@mcp.tool()
@errors.wrap
def refill_zones(block: bool = True, timeout_s: float = 60.0) -> dict:
    """Trigger refilling of all zones on the board."""
    board = connection.get_board()
    t0 = time.time()
    board.refill_zones(block=block, max_poll_seconds=timeout_s)
    return errors.ok(elapsed_s=round(time.time() - t0, 2))
