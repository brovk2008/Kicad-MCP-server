import os
import shutil
import subprocess
import platform
from kicad_mcp.server import mcp
from kicad_mcp import errors

def _get_kicad_cli_path() -> str:
    """Locate the kicad-cli binary using PATH search, running connection, or fallbacks."""
    # 1. Search PATH
    path = shutil.which("kicad-cli")
    if path:
        return path
        
    # 2. Check running connection
    try:
        from kicad_mcp import connection
        board = connection.get_board()
        ipc_path = board._kicad.get_kicad_binary_path("kicad-cli")
        if ipc_path and os.path.exists(ipc_path):
            return ipc_path
    except Exception:
        pass
        
    # 3. Fallbacks based on OS
    syst = platform.system()
    if syst == "Windows":
        for version in ["9.0", "8.0", "10.0"]:
            p = f"C:\\Program Files\\KiCad\\{version}\\bin\\kicad-cli.exe"
            if os.path.exists(p):
                return p
    elif syst == "Darwin":  # macOS
        paths = [
            "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
            "/Applications/KiCad.app/Contents/MacOS/kicad-cli"
        ]
        for p in paths:
            if os.path.exists(p):
                return p
    elif syst == "Linux":
        paths = ["/usr/bin/kicad-cli", "/usr/local/bin/kicad-cli"]
        for p in paths:
            if os.path.exists(p):
                return p
                
    return "kicad-cli"

@mcp.tool()
@errors.wrap
def run_kicad_cli(command: str, args: list[str]) -> dict:
    """Run an arbitrary headless kicad-cli command.
    
    Example:
      command="sch", args=["erc", "project.kicad_sch"]
      command="pcb", args=["drc", "project.kicad_pcb"]
    """
    cli_path = _get_kicad_cli_path()
    cmd = [cli_path, command] + args
    
    # Run the process
    res = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    
    return errors.ok(
        exit_code=res.returncode,
        stdout=res.stdout,
        stderr=res.stderr,
        command_run=" ".join(cmd),
    )

@mcp.tool()
@errors.wrap
def run_erc(schematic_path: str, severity: str = "warning") -> dict:
    """Run Electrical Rules Check (ERC) on a schematic sheet.
    
    Returns the report and any violations detected.
    """
    abs_sch = os.path.abspath(schematic_path)
    if not os.path.exists(abs_sch):
        return errors.err(f"Schematic file not found at: {abs_sch}")
        
    cli_path = _get_kicad_cli_path()
    cmd = [cli_path, "sch", "erc", "--severity", severity, abs_sch]
    
    res = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    return errors.ok(
        exit_code=res.returncode,
        report=res.stdout,
        errors=res.stderr,
    )

@mcp.tool()
@errors.wrap
def run_drc(board_path: str, severity: str = "warning") -> dict:
    """Run Design Rules Check (DRC) on a PCB layout.
    
    Returns the report and any violations detected.
    """
    abs_board = os.path.abspath(board_path)
    if not os.path.exists(abs_board):
        return errors.err(f"Board file not found at: {abs_board}")
        
    cli_path = _get_kicad_cli_path()
    cmd = [cli_path, "pcb", "drc", "--severity", severity, abs_board]
    
    res = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    return errors.ok(
        exit_code=res.returncode,
        report=res.stdout,
        errors=res.stderr,
    )

@mcp.tool()
@errors.wrap
def export_schematic_pdf(schematic_path: str, output_path: str) -> dict:
    """Export the schematic design headlessly to a PDF file."""
    abs_sch = os.path.abspath(schematic_path)
    if not os.path.exists(abs_sch):
        return errors.err(f"Schematic file not found at: {abs_sch}")
        
    abs_out = os.path.abspath(output_path)
    
    cli_path = _get_kicad_cli_path()
    cmd = [cli_path, "sch", "export", "pdf", "-o", abs_out, abs_sch]
    
    res = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    if res.returncode == 0:
        return errors.ok(output_path=abs_out, message="Schematic PDF exported successfully.")
    else:
        return errors.err(f"Failed to export PDF: {res.stderr}\nStdout: {res.stdout}")

@mcp.tool()
@errors.wrap
def export_schematic_netlist(schematic_path: str, output_path: str, format: str = "ipc356") -> dict:
    """Export the schematic design headlessly to a netlist file (e.g. ipc356)."""
    abs_sch = os.path.abspath(schematic_path)
    if not os.path.exists(abs_sch):
        return errors.err(f"Schematic file not found at: {abs_sch}")
        
    abs_out = os.path.abspath(output_path)
    
    cli_path = _get_kicad_cli_path()
    cmd = [cli_path, "sch", "export", "netlist", "--format", format, "-o", abs_out, abs_sch]
    
    res = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    if res.returncode == 0:
        return errors.ok(output_path=abs_out, message="Schematic netlist exported successfully.")
    else:
        return errors.err(f"Failed to export netlist: {res.stderr}\nStdout: {res.stdout}")
