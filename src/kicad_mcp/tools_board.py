import uuid
from kipy.common_types import TitleBlockInfo
from kipy.proto.board import board_commands_pb2
from kicad_mcp.server import mcp
from kicad_mcp import connection, units, errors

_commits = {}

@mcp.tool()
@errors.wrap
def kicad_ping() -> dict:
    """Check connection to KiCad and return version info."""
    client = connection.get_client()
    version = client.get_version()
    return errors.ok(
        connected=True,
        version=str(version),
        note="KiCad IPC API is reachable.",
    )

@mcp.tool()
@errors.wrap
def kicad_check_version() -> dict:
    """Check if the connected KiCad version matches the kipy library version."""
    client = connection.get_client()
    try:
        match = client.check_version()
        return errors.ok(match=match, message="KiCad version matches.")
    except Exception as exc:
        return errors.ok(match=False, message=str(exc))

@mcp.tool()
@errors.wrap
def get_board_info() -> dict:
    """Get high-level information about the currently open board."""
    board = connection.get_board()
    enabled = board.get_enabled_layers()
    enabled_names = [units.layer_name(lay) for lay in enabled]
    return errors.ok(
        name=board.name,
        copper_layers=board.get_copper_layer_count(),
        enabled_layers=enabled_names,
    )

@mcp.tool()
@errors.wrap
def get_title_block() -> dict:
    """Get the board title block info."""
    board = connection.get_board()
    tb = board.get_title_block_info()
    return errors.ok(
        title=tb.title,
        revision=tb.revision,
        date=tb.date,
        company=tb.company,
        comments={str(k): v for k, v in tb.comments.items()},
    )

@mcp.tool()
@errors.wrap
def set_title_block(
    title: str | None = None,
    revision: str | None = None,
    date: str | None = None,
    company: str | None = None,
    comments: dict[str, str] | None = None,
) -> dict:
    """Update title block information for the board.

    All parameters are optional. Values not specified will remain unchanged.
    """
    board = connection.get_board()
    tb = board.get_title_block_info()

    if title is not None:
        tb.title = title
    if revision is not None:
        tb.revision = revision
    if date is not None:
        tb.date = date
    if company is not None:
        tb.company = company
    if comments is not None:
        current = tb.comments
        for k, v in comments.items():
            try:
                ki = int(k)
                if 1 <= ki <= 9:
                    current[ki] = v
            except ValueError:
                pass
        tb.comments = current

    board.set_title_block_info(tb)
    return errors.ok()

@mcp.tool()
@errors.wrap
def get_stackup() -> dict:
    """Get stackup layers, thickness, material, and electrical properties."""
    board = connection.get_board()
    stackup = board.get_stackup()
    layers_list = []
    for lay in stackup.layers:
        dielectric_info = []
        try:
            for d_prop in lay.dielectric.layers:
                dielectric_info.append({
                    "material": d_prop.material_name,
                    "thickness_mm": units.to_mm_float(d_prop.thickness),
                    "epsilon_r": d_prop.epsilon_r,
                    "loss_tangent": d_prop.loss_tangent,
                })
        except Exception:
            pass

        layer_name_str = "Dielectric"
        if lay.layer != 0: # BL_UNDEFINED is usually 0 or -1, check units.layer_name
            layer_name_str = units.layer_name(lay.layer)

        layers_list.append({
            "name": layer_name_str,
            "user_name": lay.user_name,
            "thickness_mm": units.to_mm_float(lay.thickness),
            "material": lay.material_name,
            "enabled": lay.enabled,
            "dielectric_details": dielectric_info,
        })
    return errors.ok(layers=layers_list)

@mcp.tool()
@errors.wrap
def get_design_rules() -> dict:
    """Get raw design rules (KiCad 11+)."""
    board = connection.get_board()
    if not hasattr(board, "get_design_rules"):
        return errors.err("get_design_rules is not supported on this KiCad/kipy version (requires KiCad 11).")
    rules = board.get_design_rules()
    return errors.ok(rules=rules)

@mcp.tool()
@errors.wrap
def get_custom_design_rules() -> dict:
    """Get custom design rules text and any parsing errors (KiCad 11+)."""
    board = connection.get_board()
    if not hasattr(board, "get_custom_design_rules"):
        return errors.err("get_custom_design_rules is not supported on this KiCad/kipy version (requires KiCad 11).")
    rules_text, errors_list = board.get_custom_design_rules()
    return errors.ok(rules_text=rules_text, errors=errors_list)

@mcp.tool()
@errors.wrap
def set_custom_design_rules(rules_text: str) -> dict:
    """Set custom design rules text (KiCad 11+)."""
    board = connection.get_board()
    if not hasattr(board, "set_custom_design_rules"):
        return errors.err("set_custom_design_rules is not supported on this KiCad/kipy version (requires KiCad 11).")
    errors_list = board.set_custom_design_rules(rules_text)
    return errors.ok(errors=errors_list)

@mcp.tool()
@errors.wrap
def get_enabled_layers() -> dict:
    """Get list of currently enabled board layers."""
    board = connection.get_board()
    layers = board.get_enabled_layers()
    return errors.ok(layers=[units.layer_name(l) for l in layers])

@mcp.tool()
@errors.wrap
def get_visible_layers() -> dict:
    """Get list of visible board layers."""
    board = connection.get_board()
    layers = board.get_visible_layers()
    return errors.ok(layers=[units.layer_name(l) for l in layers])

@mcp.tool()
@errors.wrap
def set_visible_layers(layer_names: list[str]) -> dict:
    """Set the list of visible board layers."""
    board = connection.get_board()
    layer_ints = [units.layer(name) for name in layer_names]
    board.set_visible_layers(layer_ints)
    return errors.ok()

@mcp.tool()
@errors.wrap
def get_active_layer() -> dict:
    """Get current active board layer name."""
    board = connection.get_board()
    layer_int = board.get_active_layer()
    return errors.ok(layer_name=units.layer_name(layer_int))

@mcp.tool()
@errors.wrap
def set_active_layer(layer_name: str) -> dict:
    """Set the active board layer."""
    board = connection.get_board()
    board.set_active_layer(units.layer(layer_name))
    return errors.ok()

ORIGIN_TYPE_MAP = {
    "grid": board_commands_pb2.BoardOriginType.BOT_GRID,
    "drill": board_commands_pb2.BoardOriginType.BOT_DRILL,
    "drill_place": board_commands_pb2.BoardOriginType.BOT_DRILL,
}

@mcp.tool()
@errors.wrap
def get_board_origin(origin_type: str = "grid") -> dict:
    """Get board origin coordinates (grid or drill)."""
    board = connection.get_board()
    ot = ORIGIN_TYPE_MAP.get(origin_type.lower())
    if ot is None:
        return errors.err(f"Invalid origin_type: {origin_type}. Choose 'grid' or 'drill'.")
    vec = board.get_origin(ot)
    return errors.ok(**units.vec_to_dict(vec))

@mcp.tool()
@errors.wrap
def set_board_origin(origin_type: str, x_mm: float, y_mm: float) -> dict:
    """Set board origin coordinates (grid or drill)."""
    board = connection.get_board()
    ot = ORIGIN_TYPE_MAP.get(origin_type.lower())
    if ot is None:
        return errors.err(f"Invalid origin_type: {origin_type}. Choose 'grid' or 'drill'.")
    board.set_origin(ot, units.vec(x_mm, y_mm))
    return errors.ok()

@mcp.tool()
@errors.wrap
def get_board_as_string() -> dict:
    """Retrieve the entire board (.kicad_pcb) content as text."""
    board = connection.get_board()
    content = board.get_as_string()
    return errors.ok(content=content)

@mcp.tool()
@errors.wrap
def save_board() -> dict:
    """Save the board changes to file."""
    board = connection.get_board()
    board.save()
    return errors.ok()

@mcp.tool()
@errors.wrap
def save_board_as(path: str, overwrite: bool = False, include_project: bool = True) -> dict:
    """Save the board as a new file."""
    board = connection.get_board()
    board.save_as(path, overwrite=overwrite, include_project=include_project)
    return errors.ok()

@mcp.tool()
@errors.wrap
def revert_board() -> dict:
    """Revert board to the last saved state on disk."""
    board = connection.get_board()
    board.revert()
    return errors.ok()

@mcp.tool()
@errors.wrap
def begin_commit() -> dict:
    """Begin an edit transaction for batching multiple operations into a single Undo step."""
    board = connection.get_board()
    commit = board.begin_commit()
    cid = str(uuid.uuid4())
    _commits[cid] = commit
    return errors.ok(commit_id=cid)

@mcp.tool()
@errors.wrap
def push_commit(commit_id: str, message: str = "") -> dict:
    """Push/apply the active transaction and close the commit."""
    if commit_id not in _commits:
        return errors.err(f"Unknown commit_id '{commit_id}'")
    board = connection.get_board()
    board.push_commit(_commits.pop(commit_id), message)
    return errors.ok()

@mcp.tool()
@errors.wrap
def drop_commit(commit_id: str) -> dict:
    """Drop/cancel the active transaction and discard changes."""
    if commit_id not in _commits:
        return errors.err(f"Unknown commit_id '{commit_id}'")
    board = connection.get_board()
    board.drop_commit(_commits.pop(commit_id))
    return errors.ok()
