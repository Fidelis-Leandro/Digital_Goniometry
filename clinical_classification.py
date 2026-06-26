"""
clinical_classification.py — Hybrid clinical classification logic (TAM + Functional)
======================================================================================

Responsible for classifying patient performance across 3 layers:
    1. Articular (TAM): using the best session TAM.
    2. Functional Repetitions: valid peak detection and hit counting.
    3. Hybrid Session: fair and intelligent final classification combining 1 and 2.
"""

from typing import Any, Dict, List

# Hex colors for classifications (used in PDF and interface)
COLOR_EXCELLENT = "#22c55e"  # green
COLOR_GOOD      = "#eab308"  # yellow
COLOR_FAIR      = "#f97316"  # orange
COLOR_POOR      = "#ef4444"  # red

def classify_articular_tam(finger: str, best_tam_session: float) -> Dict[str, str]:
    """
    LAYER 1: Classic articular classification based on the best session TAM.

    Rules:
    - For INDEX, MIDDLE, RING, PINKY:
        Excellent: >= 260
        Good:      195–259
        Fair:      130–194
        Poor:      < 130
    - For THUMB:
        Excellent: > 120
        Good:      100–120
        Poor:      < 100
    """
    if finger == "THUMB":
        if best_tam_session > 120.0:
            return {"label": "Excellent", "color": COLOR_EXCELLENT, "source": "articular_tam"}
        elif best_tam_session >= 100.0:
            return {"label": "Good", "color": COLOR_GOOD, "source": "articular_tam"}
        else:
            return {"label": "Poor", "color": COLOR_POOR, "source": "articular_tam"}
    else:
        if best_tam_session >= 260.0:
            return {"label": "Excellent", "color": COLOR_EXCELLENT, "source": "articular_tam"}
        elif best_tam_session >= 195.0:
            return {"label": "Good", "color": COLOR_GOOD, "source": "articular_tam"}
        elif best_tam_session >= 130.0:
            return {"label": "Fair", "color": COLOR_FAIR, "source": "articular_tam"}
        else:
            return {"label": "Poor", "color": COLOR_POOR, "source": "articular_tam"}

def detect_valid_repetitions(
    tam_series: List[float],
    time_series: List[float],
    finger: str,
    min_peak_distance_s: float = 0.35,
    reset_ratio: float = 0.55,
) -> Dict[str, Any]:
    """
    LAYER 2: Detects valid repetitions based on the temporal TAM profile.

    Counts flexion/extension cycles. A local peak is computed and must
    'reset' (drop to a proportion of target_good) before the next peak counts.
    """
    if finger == "THUMB":
        target_good = 100.0
        target_excellent = 120.0
    else:
        target_good = 180.0
        target_excellent = 220.0

    valid_cycles = 0
    good_hits = 0
    excellent_hits = 0
    peaks_values = []

    if len(tam_series) < 3:
        return {
            "valid_cycles": 0,
            "good_hits": 0,
            "excellent_hits": 0,
            "success_rate_good": 0.0,
            "success_rate_excellent": 0.0,
            "best_peak": 0.0,
            "mean_peak": 0.0
        }

    last_peak_time = -999.0
    current_cycle_reset = True

    for i in range(1, len(tam_series) - 1):
        prev_val = tam_series[i - 1]
        curr_val = tam_series[i]
        next_val = tam_series[i + 1]
        t = time_series[i]

        if curr_val <= target_good * reset_ratio:
            current_cycle_reset = True

        if curr_val > prev_val and curr_val >= next_val:
            if current_cycle_reset and (t - last_peak_time) >= min_peak_distance_s:
                # Filter micro-movements: only count if the peak reaches a minimum
                # functional TAM (at least reset_ratio*target_good + 10) to avoid
                # counting baseline tremor as cycles.
                if curr_val > (target_good * reset_ratio) + 15.0:
                    valid_cycles += 1
                    peaks_values.append(curr_val)
                    last_peak_time = t
                    current_cycle_reset = False

                    if curr_val > target_excellent:
                        excellent_hits += 1
                        good_hits += 1
                    elif curr_val >= target_good:
                        good_hits += 1

    best_peak = max(peaks_values) if peaks_values else 0.0
    mean_peak = sum(peaks_values) / len(peaks_values) if peaks_values else 0.0

    success_rate_good = good_hits / valid_cycles if valid_cycles > 0 else 0.0
    success_rate_excellent = excellent_hits / valid_cycles if valid_cycles > 0 else 0.0

    return {
        "valid_cycles": valid_cycles,
        "good_hits": good_hits,
        "excellent_hits": excellent_hits,
        "success_rate_good": float(success_rate_good),
        "success_rate_excellent": float(success_rate_excellent),
        "best_peak": float(best_peak),
        "mean_peak": float(mean_peak)
    }

def classify_functional_session(
    finger: str,
    articular: Dict[str, str],
    repetition_stats: Dict[str, Any],
    realtime_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    LAYER 3: Functional session classification based on repetitions.
    """
    valid_cycles = repetition_stats["valid_cycles"]
    success_rate_good = repetition_stats["success_rate_good"]
    success_rate_excellent = repetition_stats["success_rate_excellent"]

    rom = realtime_metrics.get("rom", 0.0)
    mean_velocity = realtime_metrics.get("avg_velocity", 0.0)
    regularity = realtime_metrics.get("regularity", "-")

    min_req = (
        valid_cycles >= 5 and
        rom >= 40.0 and
        mean_velocity >= 20.0 and
        regularity != "Irregular" and regularity != "-"
    )

    if min_req and success_rate_excellent >= 0.80:
        label = "Excellent"
        color = COLOR_EXCELLENT
    elif min_req and success_rate_good >= 0.80:
        label = "Good"
        color = COLOR_GOOD
    elif valid_cycles >= 3 and success_rate_good >= 0.50:
        label = "Fair"
        color = COLOR_FAIR
    else:
        label = "Poor"
        color = COLOR_POOR

    return {
        "label": label,
        "color": color,
        "source": "functional_session",
        "valid_cycles": valid_cycles,
        "success_rate_good": success_rate_good,
        "success_rate_excellent": success_rate_excellent
    }

def classify_final_session_result(
    finger: str,
    articular: Dict[str, str],
    functional: Dict[str, Any],
    repetition_stats: Dict[str, Any]
) -> Dict[str, str]:
    """
    LAYER 4 (Final): Hybrid session classification for the report.
    """
    art_label = articular["label"]
    func_label = functional["label"]
    best_peak = repetition_stats["best_peak"]
    valid_cycles = repetition_stats["valid_cycles"]
    success_rate_good = repetition_stats["success_rate_good"]
    success_rate_excellent = repetition_stats["success_rate_excellent"]
    excellent_hits = repetition_stats["excellent_hits"]

    target_good = 100.0 if finger == "THUMB" else 180.0
    target_exc = 120.0 if finger == "THUMB" else 220.0

    final_label = "Poor"
    explanation = "Performance below the expected functional and articular targets during the session."

    if art_label in ["Fair", "Poor"] and func_label == "Excellent" and valid_cycles >= 5 and success_rate_excellent >= 0.80:
        final_label = "Good"
        explanation = f"achieved excellent functional peaks in {excellent_hits} of {valid_cycles} valid repetitions, demonstrating good coordination despite reduced classical TAM."
    elif art_label == "Good" and func_label == "Excellent":
        final_label = "Excellent"
        explanation = f"combined a good classical TAM with excellent functional consistency, exceeding the excellence target in {(success_rate_excellent*100):.0f}% of cycles."
    elif art_label == "Poor" and func_label == "Good" and valid_cycles >= 5 and success_rate_good >= 0.80:
        final_label = "Fair"
        explanation = f"although maximum TAM was low, maintained functional consistency with {(success_rate_good*100):.0f}% of repetitions above the target."
    else:
        ranks = {"Excellent": 4, "Good": 3, "Fair": 2, "Poor": 1}
        r_art = ranks[art_label]
        r_func = ranks[func_label]

        if r_art >= 3 and r_func >= 3:
            final_label = art_label
            explanation = "robust and consistent articular performance throughout the repetitions."
        else:
            if r_art <= r_func:
                final_label = art_label
                if r_art == 1:
                    explanation = "prominent articular limitation restricted the overall assessment, regardless of effort."
                else:
                    explanation = "the final score reflected the maximum articular capacity achieved (TAM), which acted as the limiting factor."
            else:
                final_label = func_label
                explanation = "lack of consistency or valid functional cycles limited the session score."

    # FINAL CAPS
    if final_label == "Excellent" and best_peak < target_exc:
        final_label = "Good" if best_peak >= target_good else "Fair"
        explanation += " (score capped because the absolute peak did not reach the excellence target)."

    if final_label == "Good" and best_peak < target_good:
        final_label = "Fair" if art_label == "Fair" else "Poor"
        explanation += " (score capped because the absolute peak did not reach the good target)."

    colors = {
        "Excellent": COLOR_EXCELLENT,
        "Good":      COLOR_GOOD,
        "Fair":      COLOR_FAIR,
        "Poor":      COLOR_POOR,
    }

    return {
        "label": final_label,
        "color": colors.get(final_label, COLOR_POOR),
        "source": "final_hybrid",
        "explanation": explanation
    }

def generate_clinical_observation_text(final_hybrid: Dict[str, str]) -> str:
    """Generate a short automatic observation text based on the final label."""
    lbl = final_hybrid["label"]
    if lbl == "Excellent":
        return "Consistent functional performance, with repeated flexions reaching the excellent range during the session."
    elif lbl == "Good":
        return "Good functional execution, with multiple repetitions above the expected angular target."
    elif lbl == "Fair":
        return "Functional movement present, but with lower consistency or success rate."
    else:
        return "Performance below the expected functional target during the session."
