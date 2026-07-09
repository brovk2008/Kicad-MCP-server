from kipy.util.units import from_mm, to_mm
from kipy.util.board_layer import layer_from_canonical_name, canonical_name
from kipy.geometry import Vector2, Angle

# ---------- length ----------

def mm(value_mm: float) -> int:
    """Convert millimeters to KiCad internal units (nanometers)."""
    return from_mm(value_mm)

def to_mm_float(value_nm: int) -> float:
    """Convert KiCad internal units (nanometers) to millimeters."""
    return to_mm(value_nm)

def vec(x_mm: float, y_mm: float) -> Vector2:
    """Create a Vector2 from mm coordinates."""
    return Vector2.from_xy(from_mm(x_mm), from_mm(y_mm))

def vec_to_dict(v: Vector2) -> dict:
    """Serialize a Vector2 to a plain dict with mm values."""
    return {"x_mm": round(to_mm(v.x), 6), "y_mm": round(to_mm(v.y), 6)}

# ---------- angles ----------

def angle(degrees: float) -> Angle:
    return Angle.from_degrees(degrees)

def angle_to_degrees(a: Angle) -> float:
    return round(a.degrees, 6)

# ---------- layers ----------

def layer(name: str) -> int:
    """Convert a canonical layer name (e.g. 'F.Cu') to a BoardLayer enum int."""
    try:
        val = layer_from_canonical_name(name)
        if val <= 0:
            raise ValueError()
        return val
    except Exception:
        raise ValueError(
            f"Unknown layer name '{name}'. "
            f"Use canonical names like 'F.Cu', 'B.Cu', 'F.SilkS', 'B.SilkS', "
            f"'F.Mask', 'B.Mask', 'F.Fab', 'B.Fab', 'Edge.Cuts', 'Dwgs.User', etc."
        )

def layer_name(layer_int: int) -> str:
    """Convert a BoardLayer enum int back to a canonical name string."""
    try:
        return canonical_name(layer_int)
    except Exception:
        return f"UnknownLayer({layer_int})"
