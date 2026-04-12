from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Iterable

DEFAULT_HISTOGRAM_BUCKETS: tuple[float, ...] = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
)


def _format_labels(labels: dict[str, str] | None) -> tuple[tuple[str, str], ...]:
    if not labels:
        return ()
    return tuple(sorted((str(k), str(v)) for k, v in labels.items() if v is not None and str(k)))


@dataclass
class _HistogramState:
    buckets: tuple[float, ...]
    bucket_counts: list[int]
    count: int = 0
    sum: float = 0.0


_LOCK = threading.Lock()
_COUNTERS: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
_HISTOGRAMS: dict[tuple[str, tuple[tuple[str, str], ...]], _HistogramState] = {}


def reset_metrics() -> None:
    with _LOCK:
        _COUNTERS.clear()
        _HISTOGRAMS.clear()


def inc_counter(name: str, *, labels: dict[str, str] | None = None, value: float = 1.0) -> None:
    key = (name, _format_labels(labels))
    with _LOCK:
        _COUNTERS[key] = float(_COUNTERS.get(key, 0.0)) + float(value)


def observe_histogram(
    name: str,
    *,
    labels: dict[str, str] | None = None,
    value: float,
    buckets: tuple[float, ...] = DEFAULT_HISTOGRAM_BUCKETS,
) -> None:
    key = (name, _format_labels(labels))
    with _LOCK:
        state = _HISTOGRAMS.get(key)
        if state is None:
            state = _HistogramState(buckets=buckets, bucket_counts=[0 for _ in buckets])
            _HISTOGRAMS[key] = state
        state.count += 1
        state.sum += float(value)
        for idx, boundary in enumerate(state.buckets):
            if value <= boundary:
                state.bucket_counts[idx] += 1


def _render_labels(labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return ""
    parts = [f'{k}="{v}"' for k, v in labels]
    return "{" + ",".join(parts) + "}"


def render_prometheus() -> str:
    lines: list[str] = []
    with _LOCK:
        for (name, labels), value in sorted(_COUNTERS.items()):
            lines.append(f"{name}{_render_labels(labels)} {value}")

        for (name, labels), state in sorted(_HISTOGRAMS.items()):
            cumulative = 0
            for boundary, bucket_count in zip(state.buckets, state.bucket_counts, strict=True):
                cumulative += bucket_count
                bucket_labels = dict(labels)
                bucket_labels["le"] = str(boundary)
                lines.append(f"{name}_bucket{_render_labels(_format_labels(bucket_labels))} {cumulative}")
            inf_labels = dict(labels)
            inf_labels["le"] = "+Inf"
            lines.append(f"{name}_bucket{_render_labels(_format_labels(inf_labels))} {state.count}")
            lines.append(f"{name}_count{_render_labels(labels)} {state.count}")
            lines.append(f"{name}_sum{_render_labels(labels)} {state.sum}")

    # Prometheus expects a trailing newline.
    return "\n".join(lines) + "\n"


class _Timer:
    def __init__(self) -> None:
        self._start = time.perf_counter()

    def seconds(self) -> float:
        return max(0.0, time.perf_counter() - self._start)


def start_timer() -> _Timer:
    return _Timer()
