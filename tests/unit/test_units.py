import pytest
from kicad_mcp import units

def test_mm_to_nm():
    assert units.mm(1.0) == 1000000
    assert units.mm(0.0) == 0
    assert units.mm(-2.5) == -2500000

def test_nm_to_mm():
    assert units.to_mm_float(1000000) == 1.0
    assert units.to_mm_float(0) == 0.0
    assert units.to_mm_float(-2500000) == -2.5

def test_vec_conversion():
    v = units.vec(1.2, -3.4)
    assert v.x == 1200000
    assert v.y == -3400000
    
    d = units.vec_to_dict(v)
    assert d == {"x_mm": 1.2, "y_mm": -3.4}

def test_angle_conversion():
    a = units.angle(90)
    assert units.angle_to_degrees(a) == 90.0

def test_layer_name_conversion():
    # F.Cu is BoardLayer.BL_F_Cu
    f_cu_int = units.layer("F.Cu")
    assert f_cu_int > 0
    assert units.layer_name(f_cu_int) == "F.Cu"

    with pytest.raises(ValueError):
        units.layer("NonExistentLayerNameXYZ")
