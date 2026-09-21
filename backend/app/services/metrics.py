"""
metrics.py — RAKSHYA VISION Phase 10 Step 10
Operational Metrics Collector & Prometheus Exposition Engine.
Provides high-performance, thread-safe metric counters, gauges, histograms,
and standardized Prometheus 0.0.4 text / JSON exports.
"""

import time
import os
import psutil
import threading
from typing import Dict, Any, List, Optional, Tuple


class MetricsCollector:
    """
    Thread-safe operational telemetry collector for RAKSHYA VISION.
    Tracks frame throughput, detections, incidents, smart alerts,
    evidence archival, and system resource utilization.
    """
    _instance: Optional["MetricsCollector"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._start_time = time.time()
        self._counters: Dict[str, Dict[Tuple[Tuple[str, str], ...], float]] = {}
        self._gauges: Dict[str, Dict[Tuple[Tuple[str, str], ...], float]] = {}
        self._metric_help: Dict[str, str] = {
            "rakshya_pipeline_frames_total": "Total video frames ingested and processed by camera workers",
            "rakshya_pipeline_dropped_frames_total": "Total video frames dropped due to queue congestion or slow inference",
            "rakshya_detections_total": "Total AI object and hazard detections categorized by class",
            "rakshya_incidents_total": "Total safety incidents created categorized by risk level and camera",
            "rakshya_alerts_total": "Total smart alerts generated categorized by severity and event type",
            "rakshya_alert_actions_total": "Total lifecycle actions taken on alerts (CREATED, ACKNOWLEDGED, RESOLVED, DISMISSED)",
            "rakshya_alert_dispatches_total": "Total external alert notifications sent categorized by provider and status",
            "rakshya_camera_workers_active": "Current count of active camera capture worker threads",
            "rakshya_evidence_storage_bytes": "Total filesystem storage consumed by visual evidence artifacts",
            "rakshya_uptime_seconds": "Total running time of RAKSHYA VISION service in seconds",
            "rakshya_process_cpu_percent": "Current process CPU utilization percentage",
            "rakshya_process_memory_rss_bytes": "Resident Set Size (RSS) memory consumption in bytes",
        }
        self._metric_types: Dict[str, str] = {
            "rakshya_pipeline_frames_total": "counter",
            "rakshya_pipeline_dropped_frames_total": "counter",
            "rakshya_detections_total": "counter",
            "rakshya_incidents_total": "counter",
            "rakshya_alerts_total": "counter",
            "rakshya_alert_actions_total": "counter",
            "rakshya_alert_dispatches_total": "counter",
            "rakshya_camera_workers_active": "gauge",
            "rakshya_evidence_storage_bytes": "gauge",
            "rakshya_uptime_seconds": "gauge",
            "rakshya_process_cpu_percent": "gauge",
            "rakshya_process_memory_rss_bytes": "gauge",
        }

    @classmethod
    def get_instance(cls) -> "MetricsCollector":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = MetricsCollector()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        with cls._lock:
            cls._instance = None

    def _normalize_labels(self, labels: Optional[Dict[str, str]]) -> Tuple[Tuple[str, str], ...]:
        if not labels:
            return ()
        return tuple(sorted(labels.items()))

    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increments a counter metric with optional dimensional labels."""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = {}
            key = self._normalize_labels(labels)
            self._counters[name][key] = self._counters[name].get(key, 0.0) + value

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Sets the current value of a gauge metric."""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = {}
            key = self._normalize_labels(labels)
            self._gauges[name][key] = float(value)

    def get_uptime_seconds(self) -> float:
        """Returns total uptime in seconds."""
        return round(time.time() - self._start_time, 2)

    def _format_label_string(self, label_tuple: Tuple[Tuple[str, str], ...]) -> str:
        if not label_tuple:
            return ""
        items = [f'{k}="{v}"' for k, v in label_tuple]
        return "{" + ",".join(items) + "}"

    def export_prometheus_text(self) -> str:
        """
        Exports all metrics in standard Prometheus text exposition format (0.0.4).
        Conforms strictly to Prometheus scraping specifications.
        """
        lines: List[str] = []

        # Refresh dynamic system gauges
        uptime = self.get_uptime_seconds()
        self.set_gauge("rakshya_uptime_seconds", uptime)

        try:
            proc = psutil.Process(os.getpid())
            self.set_gauge("rakshya_process_cpu_percent", proc.cpu_percent(interval=None))
            self.set_gauge("rakshya_process_memory_rss_bytes", proc.memory_info().rss)
        except Exception:
            pass

        # Update evidence storage gauge if service available
        try:
            from app.services.evidence_manager import EvidenceManager
            self.set_gauge("rakshya_evidence_storage_bytes", EvidenceManager.get_instance().get_total_storage_usage())
        except Exception:
            pass

        # Update active cameras gauge
        try:
            from app.camera.manager import CameraManager
            active_cams = sum(1 for s in CameraManager.get_instance().get_all_statuses() if s.state.value == "CONNECTED")
            self.set_gauge("rakshya_camera_workers_active", active_cams)
        except Exception:
            pass

        with self._lock:
            # Format counters
            for name, entries in self._counters.items():
                help_text = self._metric_help.get(name, "Rakshya Vision counter metric")
                metric_type = self._metric_types.get(name, "counter")
                lines.append(f"# HELP {name} {help_text}")
                lines.append(f"# TYPE {name} {metric_type}")
                for label_tuple, val in entries.items():
                    lbl_str = self._format_label_string(label_tuple)
                    lines.append(f"{name}{lbl_str} {val}")

            # Format gauges
            for name, entries in self._gauges.items():
                help_text = self._metric_help.get(name, "Rakshya Vision gauge metric")
                metric_type = self._metric_types.get(name, "gauge")
                lines.append(f"# HELP {name} {help_text}")
                lines.append(f"# TYPE {name} {metric_type}")
                for label_tuple, val in entries.items():
                    lbl_str = self._format_label_string(label_tuple)
                    lines.append(f"{name}{lbl_str} {val}")

        lines.append("")  # Trailing newline required by Prometheus
        return "\n".join(lines)

    def export_json_summary(self) -> Dict[str, Any]:
        """
        Exports a consolidated JSON telemetry report for dashboards and UI widgets.
        """
        uptime = self.get_uptime_seconds()
        self.set_gauge("rakshya_uptime_seconds", uptime)

        # Build counters summary
        counters_summary: Dict[str, Any] = {}
        with self._lock:
            for name, entries in self._counters.items():
                counters_summary[name] = [
                    {"labels": dict(lbl), "value": val} for lbl, val in entries.items()
                ]

            gauges_summary: Dict[str, Any] = {}
            for name, entries in self._gauges.items():
                gauges_summary[name] = [
                    {"labels": dict(lbl), "value": val} for lbl, val in entries.items()
                ]

        memory_mb = 0.0
        cpu_percent = 0.0
        try:
            proc = psutil.Process(os.getpid())
            memory_mb = round(proc.memory_info().rss / (1024 * 1024), 2)
            cpu_percent = proc.cpu_percent(interval=None)
        except Exception:
            pass

        return {
            "uptime_seconds": uptime,
            "system_resources": {
                "process_memory_mb": memory_mb,
                "process_cpu_percent": cpu_percent,
            },
            "counters": counters_summary,
            "gauges": gauges_summary,
        }
