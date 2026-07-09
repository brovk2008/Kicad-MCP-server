import os
import tempfile
import base64
import io
from PIL import Image

from kipy.proto.board import board_jobs_pb2
from kipy.proto.common.types import jobs_pb2
from kicad_mcp.server import mcp
from kicad_mcp import connection, units, errors

@mcp.tool()
@errors.wrap
def get_board_screenshot(width_px: int = 1600, layers: list[str] | None = None) -> dict:
    """Take a visual screenshot of the board and return it as a base64 PNG."""
    board = connection.get_board()

    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        tmp_svg = f.name
    try:
        cmd = board_jobs_pb2.RunBoardJobExportSvg()
        cmd.job_settings.document.CopyFrom(board._doc)
        cmd.job_settings.output_path = os.path.abspath(tmp_svg)
        cmd.fit_page_to_board = True
        
        if layers:
            cmd.plot_settings.layers.extend([units.layer(lay) for lay in layers])
        else:
            cmd.plot_settings.layers.extend(board.get_enabled_layers())
            
        res = board._kicad.send(cmd, jobs_pb2.RunJobResponse)
        if res.status != jobs_pb2.JS_SUCCESS:
            return errors.err(f"Failed to export SVG for screenshot: {res.message}")

        # Render SVG to PNG
        try:
            import cairosvg
            png_bytes = cairosvg.svg2png(url=tmp_svg, output_width=width_px)
            b64 = base64.b64encode(png_bytes).decode()
            return errors.ok(
                base64_png=b64,
                format="png",
                width_px=width_px,
                instructions="Decode the base64_png field to display the image.",
            )
        except (ImportError, OSError) as exc:
            # Graceful fallback: return SVG text instead of PNG
            with open(tmp_svg, "r", encoding="utf-8") as f:
                svg_text = f.read()
            return errors.ok(
                svg_text=svg_text,
                format="svg",
                note=(
                    f"cairosvg or system libcairo library is not installed/configured. "
                    f"Returned raw SVG instead. Error: {exc}"
                ),
            )
    finally:
        if os.path.exists(tmp_svg):
            try:
                os.unlink(tmp_svg)
            except Exception:
                pass

@mcp.tool()
@errors.wrap
def get_board_screenshot_svg(layers: list[str] | None = None) -> dict:
    """Retrieve the board visual layout as raw SVG text."""
    board = connection.get_board()

    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        tmp_svg = f.name
    try:
        cmd = board_jobs_pb2.RunBoardJobExportSvg()
        cmd.job_settings.document.CopyFrom(board._doc)
        cmd.job_settings.output_path = os.path.abspath(tmp_svg)
        cmd.fit_page_to_board = True
        
        if layers:
            cmd.plot_settings.layers.extend([units.layer(lay) for lay in layers])
        else:
            cmd.plot_settings.layers.extend(board.get_enabled_layers())
            
        res = board._kicad.send(cmd, jobs_pb2.RunJobResponse)
        if res.status != jobs_pb2.JS_SUCCESS:
            return errors.err(f"Failed to export SVG: {res.message}")

        with open(tmp_svg, "r", encoding="utf-8") as f:
            svg_text = f.read()
            
        return errors.ok(svg_text=svg_text)
    finally:
        if os.path.exists(tmp_svg):
            try:
                os.unlink(tmp_svg)
            except Exception:
                pass

@mcp.tool()
@errors.wrap
def get_selection_screenshot(width_px: int = 1200) -> dict:
    """Take a visual screenshot of only the selected items and return as base64 PNG."""
    try:
        import cairosvg
    except (ImportError, OSError) as exc:
        return errors.err(
            f"cairosvg or system libcairo library is not installed/configured. "
            f"Selection screenshot requires image rendering support. Error: {exc}"
        )

    board = connection.get_board()
    selection = board.get_selection()
    if not selection:
        return errors.err("No items are currently selected.")

    # Calculate selection bounding box
    sel_bbox = board.get_item_bounding_box(selection, include_text=True)
    if sel_bbox is None:
        return errors.err("Could not determine bounding box of selection.")

    # Get bounding box of the whole board (using tracks + footprints + shapes)
    all_items = list(board.get_tracks()) + list(board.get_footprints()) + list(board.get_shapes())
    if not all_items:
        return errors.err("Board is empty.")
    board_bbox = board.get_item_bounding_box(all_items, include_text=True)
    if board_bbox is None:
        return errors.err("Could not determine bounding box of board.")

    # We export the whole board with fit_page_to_board=True to a temp SVG
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        tmp_svg = f.name
    try:
        cmd = board_jobs_pb2.RunBoardJobExportSvg()
        cmd.job_settings.document.CopyFrom(board._doc)
        cmd.job_settings.output_path = os.path.abspath(tmp_svg)
        cmd.fit_page_to_board = True
        cmd.plot_settings.layers.extend(board.get_enabled_layers())
            
        res = board._kicad.send(cmd, jobs_pb2.RunJobResponse)
        if res.status != jobs_pb2.JS_SUCCESS:
            return errors.err(f"Failed to export SVG: {res.message}")

        # Render full PNG first
        png_bytes = cairosvg.svg2png(url=tmp_svg, output_width=width_px)
        
        # Crop to selection relative to the board bounds
        img = Image.open(io.BytesIO(png_bytes))
        w, h = img.size
        
        bw = board_bbox.size.x
        bh = board_bbox.size.y
        if bw == 0:
            bw = 1
        if bh == 0:
            bh = 1

        x_pct = (sel_bbox.pos.x - board_bbox.pos.x) / bw
        y_pct = (sel_bbox.pos.y - board_bbox.pos.y) / bh
        w_pct = sel_bbox.size.x / bw
        h_pct = sel_bbox.size.y / bh
        
        left = int(x_pct * w)
        top = int(y_pct * h)
        right = int((x_pct + w_pct) * w)
        bottom = int((y_pct + h_pct) * h)
        
        # Clamp bounds
        left = max(0, min(left, w))
        top = max(0, min(top, h))
        right = max(0, min(right, w))
        bottom = max(0, min(bottom, h))
        
        if (right - left) > 0 and (bottom - top) > 0:
            img = img.crop((left, top, right, bottom))
            
        out_bytes = io.BytesIO()
        img.save(out_bytes, format="PNG")
        cropped_png_bytes = out_bytes.getvalue()
        
        b64 = base64.b64encode(cropped_png_bytes).decode()
        return errors.ok(
            base64_png=b64,
            format="png",
            width_px=img.size[0],
            height_px=img.size[1],
        )
    finally:
        if os.path.exists(tmp_svg):
            try:
                os.unlink(tmp_svg)
            except Exception:
                pass
