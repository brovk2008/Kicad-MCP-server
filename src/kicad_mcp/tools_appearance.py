from kipy.proto.board import board_commands_pb2
from kicad_mcp.server import mcp
from kicad_mcp import connection, errors

@mcp.tool()
@errors.wrap
def get_editor_appearance() -> dict:
    """Retrieve current visual settings for the PCB editor."""
    board = connection.get_board()
    settings = board.get_editor_appearance_settings()
    
    try:
        inactive_mode = board_commands_pb2.InactiveLayerDisplayMode.Name(settings.inactive_layer_display)
    except Exception:
        inactive_mode = "UNKNOWN"
        
    try:
        net_color_mode = board_commands_pb2.NetColorDisplayMode.Name(settings.net_color_display)
    except Exception:
        net_color_mode = "UNKNOWN"
        
    try:
        board_flip = board_commands_pb2.BoardFlipMode.Name(settings.board_flip)
    except Exception:
        board_flip = "UNKNOWN"
        
    try:
        ratsnest_mode = board_commands_pb2.RatsnestDisplayMode.Name(settings.ratsnest_display)
    except Exception:
        ratsnest_mode = "UNKNOWN"

    return errors.ok(
        inactive_layer_display=inactive_mode,
        net_color_display=net_color_mode,
        board_flip=board_flip,
        ratsnest_display=ratsnest_mode,
    )

@mcp.tool()
@errors.wrap
def set_board_flip(flipped: bool) -> dict:
    """Flip the editor board view (view from back)."""
    board = connection.get_board()
    settings = board.get_editor_appearance_settings()
    settings.board_flip = (
        board_commands_pb2.BoardFlipMode.BFM_FLIPPED_X if flipped 
        else board_commands_pb2.BoardFlipMode.BFM_NORMAL
    )
    board.set_editor_appearance_settings(settings)
    return errors.ok()

@mcp.tool()
@errors.wrap
def set_inactive_layer_display(mode: str) -> dict:
    """Set the display mode of inactive layers.
    
    Choose: 'normal', 'dimmed', or 'hidden'
    """
    board = connection.get_board()
    settings = board.get_editor_appearance_settings()
    
    m_lower = mode.lower()
    if m_lower == "normal":
        settings.inactive_layer_display = board_commands_pb2.InactiveLayerDisplayMode.ILDM_NORMAL
    elif m_lower == "dimmed":
        settings.inactive_layer_display = board_commands_pb2.InactiveLayerDisplayMode.ILDM_DIMMED
    elif m_lower == "hidden":
        settings.inactive_layer_display = board_commands_pb2.InactiveLayerDisplayMode.ILDM_HIDDEN
    else:
        return errors.err(f"Invalid mode: '{mode}'. Choose 'normal', 'dimmed', or 'hidden'.")
        
    board.set_editor_appearance_settings(settings)
    return errors.ok()

@mcp.tool()
@errors.wrap
def set_ratsnest_display(mode: str) -> dict:
    """Set the display mode of ratsnest lines.
    
    Choose: 'all' (all layers) or 'visible' (visible layers only)
    """
    board = connection.get_board()
    settings = board.get_editor_appearance_settings()
    
    m_lower = mode.lower()
    if m_lower == "all" or m_lower == "all_layers":
        settings.ratsnest_display = board_commands_pb2.RatsnestDisplayMode.RDM_ALL_LAYERS
    elif m_lower == "visible" or m_lower == "visible_layers":
        settings.ratsnest_display = board_commands_pb2.RatsnestDisplayMode.RDM_VISIBLE_LAYERS
    else:
        return errors.err(f"Invalid mode: '{mode}'. Choose 'all' or 'visible'.")
        
    board.set_editor_appearance_settings(settings)
    return errors.ok()

@mcp.tool()
@errors.wrap
def set_net_color_display(mode: str) -> dict:
    """Set the display mode of net and netclass colors.
    
    Choose: 'all', 'ratsnest', or 'off'
    """
    board = connection.get_board()
    settings = board.get_editor_appearance_settings()
    
    m_lower = mode.lower()
    if m_lower == "all":
        settings.net_color_display = board_commands_pb2.NetColorDisplayMode.NCDM_ALL
    elif m_lower == "ratsnest":
        settings.net_color_display = board_commands_pb2.NetColorDisplayMode.NCDM_RATSNEST
    elif m_lower == "off":
        settings.net_color_display = board_commands_pb2.NetColorDisplayMode.NCDM_OFF
    else:
        return errors.err(f"Invalid mode: '{mode}'. Choose 'all', 'ratsnest', or 'off'.")
        
    board.set_editor_appearance_settings(settings)
    return errors.ok()
