"""Unit tests for HardwareConstraintAnalyzer."""

from src.evalforge.core.hardware import HardwareConstraintAnalyzer


def test_hardware_estimate_7b_q4() -> None:
    est = HardwareConstraintAnalyzer.estimate_ram(7.0, "Q4_K_M", 8192)
    assert est.weights_ram_gb > 3.0 and est.weights_ram_gb < 5.0
    assert est.fits_in_8gb is True
    assert est.fits_in_16gb is True
    assert est.warning is None

def test_hardware_estimate_70b_q4() -> None:
    est = HardwareConstraintAnalyzer.estimate_ram(70.0, "Q4_K_M", 8192)
    assert est.recommended_min_ram_gb > 35.0
    assert est.fits_in_8gb is False
    assert est.fits_in_16gb is False
    assert est.fits_in_32gb is False
    assert est.warning is not None
    assert "64GB" in est.warning

def test_hardware_estimate_quantization_comparison() -> None:
    q4 = HardwareConstraintAnalyzer.estimate_ram(14.0, "Q4_K_M")
    fp16 = HardwareConstraintAnalyzer.estimate_ram(14.0, "FP16")
    assert fp16.weights_ram_gb > q4.weights_ram_gb * 3


def test_hardware_analyze_context_scaling() -> None:
    steps = [2048, 8192, 32768]
    scaling = HardwareConstraintAnalyzer.analyze_context_scaling(7.0, "Q4_K_M", steps)
    assert len(scaling) == 3
    # Memory increases strictly with larger context length
    assert scaling[0]["context_length"] == 2048
    assert scaling[2]["context_length"] == 32768
    assert scaling[2]["context_overhead_gb"] > scaling[0]["context_overhead_gb"]
    assert scaling[2]["recommended_min_ram_gb"] > scaling[0]["recommended_min_ram_gb"]

