from kipy.board_types import Track, ArcTrack, Net
from kipy.errors import ApiError
from kicad_mcp.server import mcp
from kicad_mcp import connection, units, errors

def _track_to_dict(t) -> dict:
    t_type = "Track" if isinstance(t, Track) else "ArcTrack"
    res = {
        "id": str(t.id),
        "type": t_type,
        "start_mm": units.vec_to_dict(t.start),
        "end_mm": units.vec_to_dict(t.end),
        "layer": units.layer_name(t.layer),
        "width_mm": units.to_mm_float(t.width),
        "net": t.net.name,
        "length_mm": units.to_mm_float(t.length()),
        "locked": t.locked,
    }
    if isinstance(t, ArcTrack):
        res["mid_mm"] = units.vec_to_dict(t.mid)
    return res

@mcp.tool()
@errors.wrap
def list_tracks(net_name: str | None = None, layer_name: str | None = None) -> dict:
    """List tracks on the board, optionally filtered by net name and/or layer name."""
    board = connection.get_board()
    tracks = board.get_tracks()
    result = []
    
    layer_int = None
    if layer_name:
        layer_int = units.layer(layer_name)

    for t in tracks:
        if net_name and t.net.name.upper() != net_name.upper():
            continue
        if layer_int is not None and t.layer != layer_int:
            continue
        result.append(_track_to_dict(t))
    return errors.ok(tracks=result, count=len(result))

@mcp.tool()
@errors.wrap
def get_track(track_id: str) -> dict:
    """Get details of a specific track by its ID."""
    board = connection.get_board()
    items = board.get_items_by_id([track_id])
    if not items:
        return errors.err(f"Track with ID '{track_id}' not found.")
    return errors.ok(track=_track_to_dict(items[0]))

@mcp.tool()
@errors.wrap
def add_track(
    start_x_mm: float,
    start_y_mm: float,
    end_x_mm: float,
    end_y_mm: float,
    layer_name: str = "F.Cu",
    width_mm: float = 0.25,
    net_name: str | None = None,
    locked: bool = False,
) -> dict:
    """Add a straight track segment to the board."""
    board = connection.get_board()
    t = Track()
    t.start = units.vec(start_x_mm, start_y_mm)
    t.end = units.vec(end_x_mm, end_y_mm)
    t.layer = units.layer(layer_name)
    t.width = units.mm(width_mm)
    if net_name:
        t.net = Net(name=net_name)
    t.locked = locked

    created = board.create_items(t)
    return errors.ok(track_id=str(created[0].id))

@mcp.tool()
@errors.wrap
def add_arc_track(
    start_x_mm: float,
    start_y_mm: float,
    mid_x_mm: float,
    mid_y_mm: float,
    end_x_mm: float,
    end_y_mm: float,
    layer_name: str = "F.Cu",
    width_mm: float = 0.25,
    net_name: str | None = None,
    locked: bool = False,
) -> dict:
    """Add an arc track segment to the board."""
    board = connection.get_board()
    t = ArcTrack()
    t.start = units.vec(start_x_mm, start_y_mm)
    t.mid = units.vec(mid_x_mm, mid_y_mm)
    t.end = units.vec(end_x_mm, end_y_mm)
    t.layer = units.layer(layer_name)
    t.width = units.mm(width_mm)
    if net_name:
        t.net = Net(name=net_name)
    t.locked = locked

    created = board.create_items(t)
    return errors.ok(track_id=str(created[0].id))

@mcp.tool()
@errors.wrap
def update_track_width(track_id: str, width_mm: float) -> dict:
    """Update the width of a track segment."""
    board = connection.get_board()
    items = board.get_items_by_id([track_id])
    if not items:
        return errors.err(f"Track with ID '{track_id}' not found.")
    t = items[0]
    t.width = units.mm(width_mm)
    board.update_items([t])
    return errors.ok()

@mcp.tool()
@errors.wrap
def update_track_net(track_id: str, net_name: str) -> dict:
    """Update the net assigned to a track."""
    board = connection.get_board()
    items = board.get_items_by_id([track_id])
    if not items:
        return errors.err(f"Track with ID '{track_id}' not found.")
    t = items[0]
    t.net = Net(name=net_name)
    board.update_items([t])
    return errors.ok()

@mcp.tool()
@errors.wrap
def move_track(track_id: str, delta_x_mm: float, delta_y_mm: float) -> dict:
    """Move a track by a relative delta (in millimeters)."""
    board = connection.get_board()
    items = board.get_items_by_id([track_id])
    if not items:
        return errors.err(f"Track with ID '{track_id}' not found.")
    t = items[0]
    offset = units.vec(delta_x_mm, delta_y_mm)
    t.start += offset
    t.end += offset
    if isinstance(t, ArcTrack):
        t.mid += offset
    board.update_items([t])
    return errors.ok()

@mcp.tool()
@errors.wrap
def lock_track(track_id: str, locked: bool) -> dict:
    """Lock or unlock a track segment."""
    board = connection.get_board()
    items = board.get_items_by_id([track_id])
    if not items:
        return errors.err(f"Track with ID '{track_id}' not found.")
    t = items[0]
    t.locked = locked
    board.update_items([t])
    return errors.ok()

@mcp.tool()
@errors.wrap
def remove_track(track_id: str) -> dict:
    """Remove a track segment from the board."""
    board = connection.get_board()
    items = board.get_items_by_id([track_id])
    if not items:
        return errors.err(f"Track with ID '{track_id}' not found.")
    board.remove_items(items)
    return errors.ok(removed=track_id)

@mcp.tool()
@errors.wrap
def remove_tracks_in_rect(
    x1_mm: float,
    y1_mm: float,
    x2_mm: float,
    y2_mm: float,
    layer_name: str | None = None,
) -> dict:
    """Remove all tracks within a bounding box, optionally filtered by layer name."""
    board = connection.get_board()
    tracks = board.get_tracks()
    
    xmin = min(x1_mm, x2_mm)
    xmax = max(x1_mm, x2_mm)
    ymin = min(y1_mm, y2_mm)
    ymax = max(y1_mm, y2_mm)
    
    layer_int = None
    if layer_name:
        layer_int = units.layer(layer_name)

    to_remove = []
    for t in tracks:
        if layer_int is not None and t.layer != layer_int:
            continue
        
        # Check if track is completely inside the rectangle
        start_x = units.to_mm_float(t.start.x)
        start_y = units.to_mm_float(t.start.y)
        end_x = units.to_mm_float(t.end.x)
        end_y = units.to_mm_float(t.end.y)
        
        in_rect = (
            xmin <= start_x <= xmax and
            ymin <= start_y <= ymax and
            xmin <= end_x <= xmax and
            ymin <= end_y <= ymax
        )
        
        if in_rect:
            to_remove.append(t)
            
    if to_remove:
        board.remove_items(to_remove)
    return errors.ok(removed_count=len(to_remove))

@mcp.tool()
@errors.wrap
def get_tracks_by_net(net_name: str) -> dict:
    """List tracks belonging to a specific net."""
    return list_tracks(net_name=net_name)

@mcp.tool()
@errors.wrap
def get_tracks_by_netclass(netclass: str) -> dict:
    """List tracks belonging to all nets in a net class."""
    board = connection.get_board()
    if not hasattr(board, "get_items_by_netclass"):
        # version gate / fallback: get project net classes and query nets
        project = board.get_project()
        net_classes = project.get_net_classes()
        nc = next((c for c in net_classes if c.name.upper() == netclass.upper()), None)
        if nc is None:
            return errors.err(f"Netclass '{netclass}' not found.")
        
        # Now query tracks on any net in the class
        tracks = board.get_tracks()
        nc_nets = set(nc.nets)
        result = [_track_to_dict(t) for t in tracks if t.net.name in nc_nets]
        return errors.ok(tracks=result, count=len(result))
    
    # If the newer board.get_items_by_netclass exists (KiCad 10+)
    # We can retrieve items directly
    items = board.get_items_by_netclass(netclass, types=["track"])
    result = [_track_to_dict(item) for item in items]
    return errors.ok(tracks=result, count=len(result))
