from kipy.proto.board import board_types_pb2
from kipy.proto.board.board_types_pb2 import BoardLayer
from kicad_mcp.server import mcp
from kicad_mcp import connection, units, errors

def _fp_to_dict(fp) -> dict:
    return {
        "reference": fp.reference_field.text.value,
        "value": fp.value_field.text.value,
        "lib_id": str(fp.definition.id),
        "position_mm": units.vec_to_dict(fp.position),
        "rotation_deg": units.angle_to_degrees(fp.orientation),
        "layer": units.layer_name(fp.layer),
        "locked": fp.locked,
        "dnp": fp.attributes.do_not_populate,
        "bom_excluded": fp.attributes.exclude_from_bill_of_materials,
    }

@mcp.tool()
@errors.wrap
def list_footprints(ref_filter: str | None = None) -> dict:
    """List footprints on the board, optionally filtered by reference designator substring."""
    board = connection.get_board()
    fps = board.get_footprints()
    result = []
    for fp in fps:
        ref = fp.reference_field.text.value
        if ref_filter and ref_filter.upper() not in ref.upper():
            continue
        result.append(_fp_to_dict(fp))
    return errors.ok(footprints=result, count=len(result))

@mcp.tool()
@errors.wrap
def get_footprint(reference: str) -> dict:
    """Retrieve detailed information about a specific footprint by its reference designator."""
    board = connection.get_board()
    fps = board.get_footprints()
    fp = next((f for f in fps if f.reference_field.text.value.upper() == reference.upper()), None)
    if fp is None:
        return errors.err(f"Footprint '{reference}' not found.")

    # Serialize fields
    fields_list = []
    # fields include custom and default ones
    for item in fp.texts_and_fields:
        if hasattr(item, "name") and hasattr(item, "text"):
            fields_list.append({
                "name": item.name,
                "value": item.text.value,
                "visible": item.visible if hasattr(item, "visible") else True,
                "position_mm": units.vec_to_dict(item.text.position),
            })

    # Serialize pads
    pads_list = []
    for pad in fp.definition.pads:
        padstack_layers = [units.layer_name(lay) for lay in pad.padstack.layers]
        drill_diameter = 0.0
        try:
            drill_diameter = units.to_mm_float(pad.padstack.drill.diameter.x)
        except Exception:
            pass

        # Find copper layer size
        size_mm = {"width_mm": 0.0, "height_mm": 0.0}
        shape_name = "UNKNOWN"
        if pad.padstack.copper_layers:
            # use first copper layer for representative size
            lay = pad.padstack.copper_layers[0]
            size_mm = {"width_mm": units.to_mm_float(lay.size.x), "height_mm": units.to_mm_float(lay.size.y)}
            shape_name = board_types_pb2.PadStackShape.Name(lay.shape)

        pads_list.append({
            "number": pad.number,
            "net": pad.net.name,
            "type": board_types_pb2.PadType.Name(pad.pad_type),
            "position_mm": units.vec_to_dict(pad.position),
            "size_mm": size_mm,
            "shape": shape_name,
            "drill_mm": drill_diameter,
            "layers": padstack_layers,
        })

    # Serialize 3D models
    models_list = []
    try:
        for model in fp.definition.models:
            models_list.append({
                "filename": model.filename,
                "visible": model.visible,
                "opacity": model.opacity,
            })
    except Exception:
        pass

    detail = _fp_to_dict(fp)
    detail.update({
        "fields": fields_list,
        "pads": pads_list,
        "models": models_list,
    })
    return errors.ok(footprint=detail)

@mcp.tool()
@errors.wrap
def get_footprint_bounding_box(reference: str) -> dict:
    """Get the bounding box of a footprint (in millimeters)."""
    board = connection.get_board()
    fps = board.get_footprints()
    fp = next((f for f in fps if f.reference_field.text.value.upper() == reference.upper()), None)
    if fp is None:
        return errors.err(f"Footprint '{reference}' not found.")

    bbox = board.get_item_bounding_box(fp, include_text=True)
    if bbox is None:
        return errors.err(f"Could not compute bounding box for footprint '{reference}'.")

    return errors.ok(
        x_mm=units.to_mm_float(bbox.pos.x),
        y_mm=units.to_mm_float(bbox.pos.y),
        w_mm=units.to_mm_float(bbox.size.x),
        h_mm=units.to_mm_float(bbox.size.y),
    )

@mcp.tool()
@errors.wrap
def move_footprint(reference: str, x_mm: float, y_mm: float) -> dict:
    """Move a footprint to absolute coordinates (in millimeters)."""
    board = connection.get_board()
    fps = board.get_footprints()
    fp = next((f for f in fps if f.reference_field.text.value.upper() == reference.upper()), None)
    if fp is None:
        return errors.err(f"Footprint '{reference}' not found.")

    fp.position = units.vec(x_mm, y_mm)
    board.update_items([fp])
    return errors.ok(reference=reference, position=units.vec_to_dict(fp.position))

@mcp.tool()
@errors.wrap
def rotate_footprint(reference: str, rotation_deg: float) -> dict:
    """Rotate a footprint to a specific absolute angle (in degrees)."""
    board = connection.get_board()
    fps = board.get_footprints()
    fp = next((f for f in fps if f.reference_field.text.value.upper() == reference.upper()), None)
    if fp is None:
        return errors.err(f"Footprint '{reference}' not found.")

    fp.orientation = units.angle(rotation_deg)
    board.update_items([fp])
    return errors.ok(reference=reference, rotation_deg=rotation_deg)

@mcp.tool()
@errors.wrap
def move_and_rotate_footprint(reference: str, x_mm: float, y_mm: float, rotation_deg: float) -> dict:
    """Move and rotate a footprint in one operation."""
    board = connection.get_board()
    fps = board.get_footprints()
    fp = next((f for f in fps if f.reference_field.text.value.upper() == reference.upper()), None)
    if fp is None:
        return errors.err(f"Footprint '{reference}' not found.")

    fp.position = units.vec(x_mm, y_mm)
    fp.orientation = units.angle(rotation_deg)
    board.update_items([fp])
    return errors.ok(reference=reference, position=units.vec_to_dict(fp.position), rotation_deg=rotation_deg)

@mcp.tool()
@errors.wrap
def flip_footprint(reference: str) -> dict:
    """Flip a footprint to the opposite side of the board (F.Cu <=> B.Cu)."""
    board = connection.get_board()
    fps = board.get_footprints()
    fp = next((f for f in fps if f.reference_field.text.value.upper() == reference.upper()), None)
    if fp is None:
        return errors.err(f"Footprint '{reference}' not found.")

    new_layer = (BoardLayer.BL_B_Cu if fp.layer == BoardLayer.BL_F_Cu else BoardLayer.BL_F_Cu)
    fp.layer = new_layer
    board.update_items([fp])
    return errors.ok(reference=reference, new_layer=units.layer_name(fp.layer))

@mcp.tool()
@errors.wrap
def lock_footprint(reference: str, locked: bool) -> dict:
    """Lock or unlock a footprint to prevent accidental movement."""
    board = connection.get_board()
    fps = board.get_footprints()
    fp = next((f for f in fps if f.reference_field.text.value.upper() == reference.upper()), None)
    if fp is None:
        return errors.err(f"Footprint '{reference}' not found.")

    fp.locked = locked
    board.update_items([fp])
    return errors.ok(reference=reference, locked=locked)

@mcp.tool()
@errors.wrap
def set_footprint_dnp(reference: str, dnp: bool) -> dict:
    """Set the Do Not Populate (DNP) flag on a footprint."""
    board = connection.get_board()
    fps = board.get_footprints()
    fp = next((f for f in fps if f.reference_field.text.value.upper() == reference.upper()), None)
    if fp is None:
        return errors.err(f"Footprint '{reference}' not found.")

    fp.attributes.do_not_populate = dnp
    board.update_items([fp])
    return errors.ok(reference=reference, dnp=dnp)

@mcp.tool()
@errors.wrap
def set_footprint_bom_excluded(reference: str, excluded: bool) -> dict:
    """Set whether a footprint is excluded from the Bill of Materials (BOM)."""
    board = connection.get_board()
    fps = board.get_footprints()
    fp = next((f for f in fps if f.reference_field.text.value.upper() == reference.upper()), None)
    if fp is None:
        return errors.err(f"Footprint '{reference}' not found.")

    fp.attributes.exclude_from_bill_of_materials = excluded
    board.update_items([fp])
    return errors.ok(reference=reference, bom_excluded=excluded)

@mcp.tool()
@errors.wrap
def set_footprint_field(reference: str, field_name: str, value: str, visible: bool | None = None) -> dict:
    """Update or add a field on a footprint (e.g. Reference, Value, custom fields)."""
    board = connection.get_board()
    fps = board.get_footprints()
    fp = next((f for f in fps if f.reference_field.text.value.upper() == reference.upper()), None)
    if fp is None:
        return errors.err(f"Footprint '{reference}' not found.")

    # Match common fields or text/fields
    updated = False
    if field_name.lower() == "reference":
        fp.reference_field.text.value = value
        if visible is not None:
            fp.reference_field.visible = visible
        updated = True
    elif field_name.lower() == "value":
        fp.value_field.text.value = value
        if visible is not None:
            fp.value_field.visible = visible
        updated = True
    elif field_name.lower() == "datasheet":
        fp.datasheet_field.text.value = value
        if visible is not None:
            fp.datasheet_field.visible = visible
        updated = True
    elif field_name.lower() == "description":
        fp.description_field.text.value = value
        if visible is not None:
            fp.description_field.visible = visible
        updated = True
    else:
        # Check texts_and_fields
        for item in fp.texts_and_fields:
            if hasattr(item, "name") and item.name.lower() == field_name.lower():
                item.text.value = value
                if visible is not None and hasattr(item, "visible"):
                    item.visible = visible
                updated = True
                break

    if not updated:
        return errors.err(f"Field '{field_name}' not found on footprint '{reference}'.")

    board.update_items([fp])
    return errors.ok(reference=reference, field=field_name, value=value)

@mcp.tool()
@errors.wrap
def remove_footprint(reference: str) -> dict:
    """Remove a footprint from the board."""
    board = connection.get_board()
    fps = board.get_footprints()
    fp = next((f for f in fps if f.reference_field.text.value.upper() == reference.upper()), None)
    if fp is None:
        return errors.err(f"Footprint '{reference}' not found.")

    board.remove_items([fp])
    return errors.ok(reference=reference, removed=True)

@mcp.tool()
@errors.wrap
def list_pads(reference: str) -> dict:
    """List all pads of a footprint."""
    board = connection.get_board()
    fps = board.get_footprints()
    fp = next((f for f in fps if f.reference_field.text.value.upper() == reference.upper()), None)
    if fp is None:
        return errors.err(f"Footprint '{reference}' not found.")

    pads_list = []
    for pad in fp.definition.pads:
        drill_diameter = 0.0
        try:
            drill_diameter = units.to_mm_float(pad.padstack.drill.diameter.x)
        except Exception:
            pass

        size_mm = {"width_mm": 0.0, "height_mm": 0.0}
        shape_name = "UNKNOWN"
        if pad.padstack.copper_layers:
            lay = pad.padstack.copper_layers[0]
            size_mm = {"width_mm": units.to_mm_float(lay.size.x), "height_mm": units.to_mm_float(lay.size.y)}
            shape_name = board_types_pb2.PadStackShape.Name(lay.shape)

        pads_list.append({
            "number": pad.number,
            "net": pad.net.name,
            "type": board_types_pb2.PadType.Name(pad.pad_type),
            "position_mm": units.vec_to_dict(pad.position),
            "size_mm": size_mm,
            "shape": shape_name,
            "drill_mm": drill_diameter,
        })
    return errors.ok(reference=reference, pads=pads_list, count=len(pads_list))

@mcp.tool()
@errors.wrap
def get_pad(reference: str, pad_number: str) -> dict:
    """Get detailed information for a single pad of a footprint."""
    board = connection.get_board()
    fps = board.get_footprints()
    fp = next((f for f in fps if f.reference_field.text.value.upper() == reference.upper()), None)
    if fp is None:
        return errors.err(f"Footprint '{reference}' not found.")

    pad = next((p for p in fp.definition.pads if p.number == pad_number), None)
    if pad is None:
        return errors.err(f"Pad '{pad_number}' not found on footprint '{reference}'.")

    drill_diameter = 0.0
    try:
        drill_diameter = units.to_mm_float(pad.padstack.drill.diameter.x)
    except Exception:
        pass

    copper_layers = []
    for lay in pad.padstack.copper_layers:
        copper_layers.append({
            "layer": units.layer_name(lay.layer),
            "shape": board_types_pb2.PadStackShape.Name(lay.shape),
            "size_mm": {"width_mm": units.to_mm_float(lay.size.x), "height_mm": units.to_mm_float(lay.size.y)},
            "offset_mm": units.vec_to_dict(lay.offset),
        })

    return errors.ok(
        number=pad.number,
        net=pad.net.name,
        type=board_types_pb2.PadType.Name(pad.pad_type),
        position_mm=units.vec_to_dict(pad.position),
        drill_mm=drill_diameter,
        copper_layers=copper_layers,
    )

@mcp.tool()
@errors.wrap
def get_connected_items(reference: str, pad_number: str) -> dict:
    """Retrieve items connected to a specific pad."""
    board = connection.get_board()
    fps = board.get_footprints()
    fp = next((f for f in fps if f.reference_field.text.value.upper() == reference.upper()), None)
    if fp is None:
        return errors.err(f"Footprint '{reference}' not found.")

    pad = next((p for p in fp.definition.pads if p.number == pad_number), None)
    if pad is None:
        return errors.err(f"Pad '{pad_number}' not found on footprint '{reference}'.")

    connected = board.get_connected_items(pad)
    items_list = []
    for item in connected:
        items_list.append({
            "id": str(item.id),
            "type": type(item).__name__,
        })
    return errors.ok(connected_items=items_list)

@mcp.tool()
@errors.wrap
def interactive_move_footprint(reference: str) -> dict:
    """Initiates an interactive move in the GUI. Returns immediately but blocks further API calls until complete."""
    board = connection.get_board()
    fps = board.get_footprints()
    fp = next((f for f in fps if f.reference_field.text.value.upper() == reference.upper()), None)
    if fp is None:
        return errors.err(f"Footprint '{reference}' not found.")

    board.interactive_move(fp.id)
    return errors.ok(message="Interactive move initiated in KiCad GUI.")
