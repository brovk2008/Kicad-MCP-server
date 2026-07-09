import os
from kipy.proto.board import board_jobs_pb2
from kipy.proto.common.types import jobs_pb2
from kicad_mcp.server import mcp
from kicad_mcp import connection, units, errors

def _run_export_job(cmd, output_path: str, board) -> dict:
    cmd.job_settings.document.CopyFrom(board._doc)
    
    # Resolve absolute path for output
    abs_path = os.path.abspath(output_path)
    cmd.job_settings.output_path = abs_path
    
    res = board._kicad.send(cmd, jobs_pb2.RunJobResponse)
    if res.status == jobs_pb2.JS_SUCCESS:
        return errors.ok(output_path=abs_path, message=res.message)
    else:
        return errors.err(f"Export failed: {res.message}")

@mcp.tool()
@errors.wrap
def export_svg(
    output_path: str,
    layers: list[str] | None = None,
    fit_page_to_board: bool = True,
    precision: int = 4,
) -> dict:
    """Export the board to an SVG file."""
    board = connection.get_board()
    cmd = board_jobs_pb2.RunBoardJobExportSvg()
    
    if layers:
        cmd.plot_settings.layers.extend([units.layer(lay) for lay in layers])
    else:
        cmd.plot_settings.layers.extend(board.get_enabled_layers())
        
    cmd.fit_page_to_board = fit_page_to_board
    cmd.precision = precision
    
    return _run_export_job(cmd, output_path, board)

@mcp.tool()
@errors.wrap
def export_pdf(
    output_path: str,
    layers: list[str] | None = None,
    single_document: bool = True,
) -> dict:
    """Export the board to a PDF document."""
    board = connection.get_board()
    cmd = board_jobs_pb2.RunBoardJobExportPdf()
    
    if layers:
        cmd.plot_settings.layers.extend([units.layer(lay) for lay in layers])
    else:
        cmd.plot_settings.layers.extend(board.get_enabled_layers())
        
    cmd.single_document = single_document
    cmd.page_mode = board_jobs_pb2.BoardJobPaginationMode.BJPM_ALL_LAYERS_ONE_PAGE if single_document else board_jobs_pb2.BoardJobPaginationMode.BJPM_EACH_LAYER_OWN_PAGE
    
    return _run_export_job(cmd, output_path, board)

@mcp.tool()
@errors.wrap
def export_dxf(
    output_path: str,
    layers: list[str] | None = None,
    polygon_mode: bool = False,
) -> dict:
    """Export the board layout to a DXF file."""
    board = connection.get_board()
    cmd = board_jobs_pb2.RunBoardJobExportDxf()
    
    if layers:
        cmd.plot_settings.layers.extend([units.layer(lay) for lay in layers])
    else:
        cmd.plot_settings.layers.extend(board.get_enabled_layers())
        
    cmd.polygon_mode = polygon_mode
    
    return _run_export_job(cmd, output_path, board)

@mcp.tool()
@errors.wrap
def export_gerbers(output_dir: str, layers: list[str] | None = None) -> dict:
    """Export the board layout to Gerber files in the specified output directory."""
    board = connection.get_board()
    cmd = board_jobs_pb2.RunBoardJobExportGerbers()
    
    if layers:
        cmd.layers.extend([units.layer(lay) for lay in layers])
    else:
        cmd.layers.extend(board.get_enabled_layers())
        
    return _run_export_job(cmd, output_dir, board)

@mcp.tool()
@errors.wrap
def export_drill(output_path: str, format: str = "excellon") -> dict:
    """Export CNC drill files for manufacturing."""
    board = connection.get_board()
    cmd = board_jobs_pb2.RunBoardJobExportDrill()
    
    f_lower = format.lower()
    if f_lower == "excellon":
        cmd.format = board_jobs_pb2.DrillFormat.DF_EXCELLON
    elif f_lower == "gerber":
        cmd.format = board_jobs_pb2.DrillFormat.DF_GERBER
    else:
        return errors.err(f"Invalid format: '{format}'. Choose 'excellon' or 'gerber'.")
        
    return _run_export_job(cmd, output_path, board)

@mcp.tool()
@errors.wrap
def export_position(output_path: str, format: str = "csv", side: str = "both") -> dict:
    """Export footprint component placement position files for assembly."""
    board = connection.get_board()
    cmd = board_jobs_pb2.RunBoardJobExportPosition()
    
    f_lower = format.lower()
    if f_lower == "csv":
        cmd.format = board_jobs_pb2.PositionFormat.PF_CSV
    elif f_lower == "ascii":
        cmd.format = board_jobs_pb2.PositionFormat.PF_ASCII
    elif f_lower == "gerber":
        cmd.format = board_jobs_pb2.PositionFormat.PF_GERBER
    else:
        return errors.err(f"Invalid format: '{format}'. Choose 'csv', 'ascii', or 'gerber'.")
        
    s_lower = side.lower()
    if s_lower == "front":
        cmd.side = board_jobs_pb2.PositionSide.PS_FRONT
    elif s_lower == "back":
        cmd.side = board_jobs_pb2.PositionSide.PS_BACK
    else:
        cmd.side = board_jobs_pb2.PositionSide.PS_BOTH
        
    return _run_export_job(cmd, output_path, board)

@mcp.tool()
@errors.wrap
def export_3d(output_path: str) -> dict:
    """Export the 3D STEP model of the board."""
    board = connection.get_board()
    cmd = board_jobs_pb2.RunBoardJobExport3D()
    cmd.format = board_jobs_pb2.Board3DFormat.B3D_STEP
    
    return _run_export_job(cmd, output_path, board)

@mcp.tool()
@errors.wrap
def export_render(output_path: str, width_px: int = 1920, height_px: int = 1080) -> dict:
    """Render the 3D raytrace view of the board to an image file."""
    board = connection.get_board()
    cmd = board_jobs_pb2.RunBoardJobExportRender()
    cmd.width = width_px
    cmd.height = height_px
    cmd.format = board_jobs_pb2.RenderFormat.RF_PNG
    
    return _run_export_job(cmd, output_path, board)

@mcp.tool()
@errors.wrap
def export_ipc2581(output_path: str) -> dict:
    """Export the board in IPC-2581 assembly/manufacturing format."""
    board = connection.get_board()
    cmd = board_jobs_pb2.RunBoardJobExportIpc2581()
    
    return _run_export_job(cmd, output_path, board)

@mcp.tool()
@errors.wrap
def export_odb(output_path: str) -> dict:
    """Export the board in ODB++ manufacturing format."""
    board = connection.get_board()
    cmd = board_jobs_pb2.RunBoardJobExportODB()
    
    return _run_export_job(cmd, output_path, board)

@mcp.tool()
@errors.wrap
def export_gencad(output_path: str) -> dict:
    """Export the board layout in GenCAD format."""
    board = connection.get_board()
    cmd = board_jobs_pb2.RunBoardJobExportGencad()
    
    return _run_export_job(cmd, output_path, board)

@mcp.tool()
@errors.wrap
def export_ps(output_path: str, force_a4: bool = False) -> dict:
    """Export the board layout to PostScript files."""
    board = connection.get_board()
    cmd = board_jobs_pb2.RunBoardJobExportPs()
    cmd.force_a4 = force_a4
    
    return _run_export_job(cmd, output_path, board)

@mcp.tool()
@errors.wrap
def export_ipc_d356(output_path: str) -> dict:
    """Export netlist test data in IPC-D-356 format."""
    board = connection.get_board()
    cmd = board_jobs_pb2.RunBoardJobExportIpcD356()
    
    return _run_export_job(cmd, output_path, board)

@mcp.tool()
@errors.wrap
def export_stats(output_path: str) -> dict:
    """Export board statistics report."""
    board = connection.get_board()
    cmd = board_jobs_pb2.RunBoardJobExportStats()
    cmd.format = board_jobs_pb2.StatsOutputFormat.SOF_REPORT
    
    return _run_export_job(cmd, output_path, board)
