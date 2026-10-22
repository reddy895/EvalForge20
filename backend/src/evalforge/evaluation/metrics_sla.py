"""SLA latency boundary validator."""

def evaluate_sla_latency(latency_ms: float, max_allowed_ms: float = 2000.0) -> bool:
    """Return True if model response meets SLA threshold."""
    return 0.0 < latency_ms <= max_allowed_ms
