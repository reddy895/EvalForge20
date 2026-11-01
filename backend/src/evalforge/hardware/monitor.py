"""Hardware resource monitoring and system telemetry for local inference evaluation."""

import os
import platform
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class HardwareSnapshot:
    timestamp: float
    cpu_percent: float | None
    ram_used_gb: float | None
    ram_total_gb: float | None
    ram_percent: float | None
    gpu_available: bool
    gpu_utilization_percent: float | None
    vram_used_gb: float | None
    vram_total_gb: float | None
    gpu_model: str | None
    os_name: str
    cpu_model: str
    cpu_cores: int


class HardwareMonitor:
    """Monitors system CPU, memory, and GPU telemetry during model evaluation runs."""

    def __init__(self) -> None:
        self.os_name = f"{platform.system()} {platform.release()}"
        self.cpu_cores = os.cpu_count() or 1
        self.cpu_model = platform.processor() or "Unknown CPU"
        self._has_nvidia_smi = shutil.which("nvidia-smi") is not None

    def get_system_specs(self) -> dict[str, Any]:
        """Return static system hardware specifications."""
        ram_total = self._get_total_ram_gb()
        return {
            "os": self.os_name,
            "architecture": platform.machine(),
            "cpu_model": self.cpu_model,
            "cpu_cores": self.cpu_cores,
            "ram_total_gb": ram_total,
            "gpu_detected": self._has_nvidia_smi,
        }

    def capture_snapshot(self) -> dict[str, Any]:
        """Capture an instant hardware utilization snapshot."""
        ram_info = self._get_ram_info()
        cpu_percent = self._get_cpu_percent()
        gpu_info = self._get_gpu_info()

        snapshot = HardwareSnapshot(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            ram_used_gb=ram_info.get("used_gb"),
            ram_total_gb=ram_info.get("total_gb"),
            ram_percent=ram_info.get("percent"),
            gpu_available=gpu_info["available"],
            gpu_utilization_percent=gpu_info.get("gpu_utilization_percent"),
            vram_used_gb=gpu_info.get("vram_used_gb"),
            vram_total_gb=gpu_info.get("vram_total_gb"),
            gpu_model=gpu_info.get("gpu_model"),
            os_name=self.os_name,
            cpu_model=self.cpu_model,
            cpu_cores=self.cpu_cores,
        )
        return asdict(snapshot)

    def _get_cpu_percent(self) -> float | None:
        """Read load average or cpu percentage on Linux."""
        try:
            if hasattr(os, "getloadavg"):
                load1, _, _ = os.getloadavg()
                # Normalize 1-minute load against core count
                return round(min(100.0, (load1 / self.cpu_cores) * 100.0), 1)
        except Exception:
            pass
        return None

    def _get_total_ram_gb(self) -> float | None:
        ram_info = self._get_ram_info()
        return ram_info.get("total_gb")

    def _get_ram_info(self) -> dict[str, float | None]:
        """Read system memory information from /proc/meminfo on Linux or fallback."""
        try:
            if os.path.exists("/proc/meminfo"):
                meminfo: dict[str, int] = {}
                with open("/proc/meminfo", encoding="utf-8") as f:
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            val = parts[1].strip().split()[0]
                            meminfo[parts[0].strip()] = int(val)
                total_kb = meminfo.get("MemTotal", 0)
                available_kb = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
                used_kb = max(0, total_kb - available_kb)
                total_gb = round(total_kb / (1024 * 1024), 2)
                used_gb = round(used_kb / (1024 * 1024), 2)
                percent = round((used_kb / total_kb) * 100.0, 1) if total_kb > 0 else None
                return {"total_gb": total_gb, "used_gb": used_gb, "percent": percent}
        except Exception:
            pass
        return {"total_gb": None, "used_gb": None, "percent": None}

    def _get_gpu_info(self) -> dict[str, Any]:
        """Query NVIDIA GPU telemetry if nvidia-smi is available."""
        if not self._has_nvidia_smi:
            return {
                "available": False,
                "gpu_utilization_percent": None,
                "vram_used_gb": None,
                "vram_total_gb": None,
                "gpu_model": None,
                "message": "NVIDIA GPU or nvidia-smi not available on system",
            }

        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2.0)
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                first = lines[0].split(",")
                if len(first) >= 4:
                    name = first[0].strip()
                    util = float(first[1].strip())
                    used_mb = float(first[2].strip())
                    total_mb = float(first[3].strip())
                    return {
                        "available": True,
                        "gpu_model": name,
                        "gpu_utilization_percent": util,
                        "vram_used_gb": round(used_mb / 1024.0, 2),
                        "vram_total_gb": round(total_mb / 1024.0, 2),
                    }
        except Exception:
            pass

        return {
            "available": False,
            "gpu_utilization_percent": None,
            "vram_used_gb": None,
            "vram_total_gb": None,
            "gpu_model": None,
            "message": "Unable to query GPU statistics",
        }


_global_monitor: HardwareMonitor | None = None


def get_hardware_monitor() -> HardwareMonitor:
    """Return singleton HardwareMonitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = HardwareMonitor()
    return _global_monitor
