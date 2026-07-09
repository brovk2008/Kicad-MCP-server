from kipy.board_types import Net, Track, ArcTrack, Via, Pad
from kicad_mcp.server import mcp
from kicad_mcp import connection, units, errors

def _netclass_to_dict(nc) -> dict:
    return {
        "name": nc.name,
        "priority": nc.priority,
        "clearance_mm": units.to_mm_float(nc.clearance) if nc.clearance is not None else None,
        "track_width_mm": units.to_mm_float(nc.track_width) if nc.track_width is not None else None,
        "via_diameter_mm": units.to_mm_float(nc.via_diameter) if nc.via_diameter is not None else None,
        "via_drill_mm": units.to_mm_float(nc.via_drill) if nc.via_drill is not None else None,
        "microvia_diameter_mm": units.to_mm_float(nc.microvia_diameter) if nc.microvia_diameter is not None else None,
        "microvia_drill_mm": units.to_mm_float(nc.microvia_drill) if nc.microvia_drill is not None else None,
    }

@mcp.tool()
@errors.wrap
def list_nets(netclass_filter: str | None = None) -> dict:
    """List nets on the board, optionally filtered by netclass name."""
    board = connection.get_board()
    nets = board.get_nets(netclass_filter=netclass_filter)
    result = [{"name": n.name} for n in nets]
    return errors.ok(nets=result, count=len(result))

@mcp.tool()
@errors.wrap
def get_net_items(net_name: str, item_types: list[str] | None = None) -> dict:
    """Retrieve all board items associated with a specific net."""
    board = connection.get_board()
    
    # Normalize types filter
    types_filter = [t.lower() for t in item_types] if item_types else ["track", "via", "pad", "zone"]
    
    # Fallback/query approach for maximum compatibility (works on KiCad 9 and 10)
    items_list = []
    
    if "track" in types_filter:
        for t in board.get_tracks():
            if t.net.name.upper() == net_name.upper():
                t_type = "Track" if isinstance(t, Track) else "ArcTrack"
                items_list.append({
                    "id": str(t.id),
                    "type": t_type,
                    "layer": units.layer_name(t.layer),
                })
                
    if "via" in types_filter:
        for v in board.get_vias():
            if v.net.name.upper() == net_name.upper():
                items_list.append({
                    "id": str(v.id),
                    "type": "Via",
                })
                
    if "pad" in types_filter:
        for p in board.get_pads():
            if p.net.name.upper() == net_name.upper():
                items_list.append({
                    "id": str(p.id),
                    "type": "Pad",
                    "number": p.number,
                })
                
    if "zone" in types_filter:
        for z in board.get_zones():
            if not z.is_rule_area() and z.net and z.net.name.upper() == net_name.upper():
                items_list.append({
                    "id": str(z.id),
                    "type": "Zone",
                    "name": z.name,
                })

    return errors.ok(net=net_name, items=items_list, count=len(items_list))

@mcp.tool()
@errors.wrap
def get_items_by_netclass(netclass: str, item_types: list[str] | None = None) -> dict:
    """Retrieve all board items associated with nets in a specific netclass."""
    board = connection.get_board()
    project = board.get_project()
    
    # Find all nets in this netclass
    net_classes = project.get_net_classes()
    nc = next((c for c in net_classes if c.name.upper() == netclass.upper()), None)
    if nc is None:
        return errors.err(f"Netclass '{netclass}' not found.")
        
    # Get nets belonging to this class
    nets = board.get_nets(netclass_filter=netclass)
    net_names = {n.name.upper() for n in nets}
    
    # Normalized types
    types_filter = [t.lower() for t in item_types] if item_types else ["track", "via", "pad", "zone"]
    items_list = []
    
    if "track" in types_filter:
        for t in board.get_tracks():
            if t.net.name.upper() in net_names:
                t_type = "Track" if isinstance(t, Track) else "ArcTrack"
                items_list.append({
                    "id": str(t.id),
                    "type": t_type,
                    "net": t.net.name,
                })
                
    if "via" in types_filter:
        for v in board.get_vias():
            if v.net.name.upper() in net_names:
                items_list.append({
                    "id": str(v.id),
                    "type": "Via",
                    "net": v.net.name,
                })
                
    if "pad" in types_filter:
        for p in board.get_pads():
            if p.net.name.upper() in net_names:
                items_list.append({
                    "id": str(p.id),
                    "type": "Pad",
                    "number": p.number,
                    "net": p.net.name,
                })
                
    if "zone" in types_filter:
        for z in board.get_zones():
            if not z.is_rule_area() and z.net and z.net.name.upper() in net_names:
                items_list.append({
                    "id": str(z.id),
                    "type": "Zone",
                    "name": z.name,
                    "net": z.net.name,
                })

    return errors.ok(netclass=netclass, items=items_list, count=len(items_list))

@mcp.tool()
@errors.wrap
def get_netclass_for_net(net_name: str) -> dict:
    """Retrieve netclass settings for a given net."""
    board = connection.get_board()
    class_map = board.get_netclass_for_nets(Net(name=net_name))
    nc = class_map.get(net_name)
    if nc is None:
        return errors.err(f"No netclass found for net '{net_name}'.")
    return errors.ok(netclass=_netclass_to_dict(nc))

@mcp.tool()
@errors.wrap
def import_netlist(
    netlist_path: str,
    dry_run: bool = False,
    delete_extra: bool = True,
    update_footprints: bool = True,
    override_locks: bool = False,
) -> dict:
    """Import a netlist file into the board. (Requires newer KiCad/kipy API)."""
    board = connection.get_board()
    if not hasattr(board, "import_netlist"):
        return errors.err("import_netlist is not supported on this KiCad/kipy version.")
    
    # Invoke the native method if it exists
    result = board.import_netlist(
        netlist_path=netlist_path,
        dry_run=dry_run,
        delete_extra_footprints=delete_extra,
        update_footprints=update_footprints,
        override_locks=override_locks,
    )
    return errors.ok(
        new_footprint_count=result.new_footprint_count,
        warning_count=result.warning_count,
        error_count=result.error_count,
        report=result.report,
    )
