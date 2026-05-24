from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "paper" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COLORS = {
    "yieldos": "#2563eb",
    "distserve": "#16a34a",
    "sarathi": "#f97316",
    "continuous": "#64748b",
    "v01": "#7c93d6",
    "red": "#dc2626",
}


def load_summary(run: str) -> dict[str, dict]:
    rows = json.loads((ROOT / "runs" / run / "summary.json").read_text())
    return {row["policy"]: row for row in rows}


def save(fig: plt.Figure, filename: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG_DIR / filename, bbox_inches="tight")
    plt.close(fig)


def style_axes(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)


def bar_chart(filename: str, title: str, labels: list[str], values: list[float], colors: list[str], ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    bars = ax.bar(labels, values, color=colors, edgecolor="#1f2937", linewidth=0.5)
    ax.set_title(title, pad=12, weight="bold")
    ax.set_ylabel(ylabel)
    style_axes(ax)
    ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=9)
    ax.margins(y=0.14)
    save(fig, filename)


def gain_chart(filename: str, title: str, labels: list[str], gains: list[float]) -> None:
    colors = [COLORS["yieldos"] if gain >= 0 else COLORS["red"] for gain in gains]
    bar_chart(filename, title, labels, gains, colors, "gain over DistServe (%)")


def architecture() -> None:
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.set_title("YieldOS-Lite: slow-path governance, fast-path dispatch", weight="bold", pad=12)

    boxes = {
        "Intake": (0.45, 4.15),
        "Soft Shape\nForecast": (2.35, 4.15),
        "SLO Notary": (4.55, 4.75),
        "KV Treasury": (4.55, 3.55),
        "Policy\nSnapshot": (6.75, 4.15),
        "Fast Dispatch\nLoop": (6.75, 2.45),
        "Serving\nEngine": (4.55, 1.2),
        "Trace\nArchive": (2.35, 1.2),
    }

    for label, (x, y) in boxes.items():
        box = FancyBboxPatch(
            (x, y),
            1.55,
            0.65,
            boxstyle="round,pad=0.04,rounding_size=0.04",
            facecolor="#eff6ff",
            edgecolor=COLORS["yieldos"],
            linewidth=1.3,
        )
        ax.add_patch(box)
        ax.text(x + 0.775, y + 0.325, label, ha="center", va="center", fontsize=9)

    arrows = [
        ((2.0, 4.48), (2.35, 4.48)),
        ((3.9, 4.48), (4.55, 5.05)),
        ((3.9, 4.48), (4.55, 3.88)),
        ((6.1, 5.05), (6.75, 4.5)),
        ((6.1, 3.88), (6.75, 4.5)),
        ((7.52, 4.15), (7.52, 3.1)),
        ((6.75, 2.6), (6.1, 1.65)),
        ((4.55, 1.55), (3.9, 1.55)),
        ((2.35, 1.55), (1.2, 4.15)),
    ]
    for start, end in arrows:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12, linewidth=1.2, color="#374151"))

    ax.text(
        5.0,
        3.05,
        "Shape forecasts are evidence;\nSLO/KV governance sets urgency and value.",
        ha="center",
        va="center",
        fontsize=9,
        color="#4b5563",
    )
    save(fig, "yieldos_architecture.pdf")


def baseline_goodput() -> None:
    rows = load_summary("final_compare_800")
    bar_chart(
        "baseline_goodput.pdf",
        "MVP baseline comparison",
        ["YieldOS", "DistServe", "Sarathi", "Continuous"],
        [
            rows["yieldos_lite"]["governed_goodput"],
            rows["distserve_disaggregated"]["governed_goodput"],
            rows["sarathi_chunked_prefill"]["governed_goodput"],
            rows["continuous_batching"]["governed_goodput"],
        ],
        [COLORS["yieldos"], COLORS["distserve"], COLORS["sarathi"], COLORS["continuous"]],
        "governed goodput",
    )


def main_goodput() -> None:
    rows = load_summary("next_policy_compare_800_v2")
    bar_chart(
        "yieldos_goodput.pdf",
        "Ablation-refined YieldOS-Lite comparison",
        ["YieldOS-Lite", "Initial", "DistServe", "Sarathi", "Continuous"],
        [
            rows["yieldos_lite_v02_tick_50ms"]["governed_goodput"],
            rows["yieldos_lite"]["governed_goodput"],
            rows["distserve_disaggregated"]["governed_goodput"],
            rows["sarathi_chunked_prefill"]["governed_goodput"],
            rows["continuous_batching"]["governed_goodput"],
        ],
        [COLORS["yieldos"], COLORS["v01"], COLORS["distserve"], COLORS["sarathi"], COLORS["continuous"]],
        "governed goodput",
    )


def load_sweep() -> None:
    rows = load_summary("further_load_sweep_800")
    labels = ["50%", "70%", "90%", "110%", "130%", "150%"]
    gains = []
    for key in ["0.50", "0.70", "0.90", "1.10", "1.30", "1.50"]:
        y = rows[f"yieldos_v02_load_{key}"]["governed_goodput"]
        d = rows[f"distserve_disaggregated_load_{key}"]["governed_goodput"]
        gains.append((y - d) / d * 100.0)
    gain_chart("load_sweep_gains.pdf", "Load sweep: YieldOS gain over DistServe", labels, gains)


def slo_tightness() -> None:
    rows = load_summary("further_slo_tightness_sweep_800")
    labels = ["Loose", "Normal", "Tight", "Impossible"]
    gains = []
    for key in ["loose", "normal", "tight", "impossible"]:
        y = rows[f"yieldos_v02_slo_{key}"]["governed_goodput"]
        n = rows[f"yieldos_v02_no_slo_notary_slo_{key}"]["governed_goodput"]
        gains.append((y - n) / n * 100.0)
    gain_chart("slo_tightness_gain.pdf", "SLO Notary gain by SLO tightness", labels, gains)


def profile_gains() -> None:
    rows = load_summary("trace_workload_suite_800_v2")
    labels = ["chat", "RAG", "code", "batch", "mixed"]
    keys = ["chat_heavy", "rag_heavy", "code_heavy", "batch_summary_heavy", "mixed_enterprise"]
    gains = []
    for key in keys:
        y = rows[f"yieldos_v02_{key}"]["governed_goodput"]
        d = rows[f"distserve_disaggregated_{key}"]["governed_goodput"]
        gains.append((y - d) / d * 100.0)
    gain_chart("profile_gains.pdf", "Profile suite: YieldOS gain over DistServe", labels, gains)


def burstgpt_boundary() -> None:
    scale100 = load_summary("burstgpt_sample_800_scale100")
    scale200 = load_summary("burstgpt_sample_800_scale200")
    labels = ["100x", "200x"]
    dist = [
        scale100["distserve_disaggregated_burstgpt"]["governed_goodput"],
        scale200["distserve_disaggregated_burstgpt"]["governed_goodput"],
    ]
    yld = [
        scale100["yieldos_v02_burstgpt"]["governed_goodput"],
        scale200["yieldos_v02_burstgpt"]["governed_goodput"],
    ]
    x = range(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    ax.bar([i - width / 2 for i in x], dist, width, label="DistServe-style", color=COLORS["distserve"], edgecolor="#1f2937", linewidth=0.5)
    ax.bar([i + width / 2 for i in x], yld, width, label="YieldOS-Lite", color=COLORS["yieldos"], edgecolor="#1f2937", linewidth=0.5)
    ax.set_xticks(list(x), labels)
    ax.set_ylabel("governed goodput")
    ax.set_title("BurstGPT boundary condition", weight="bold", pad=12)
    ax.legend(frameon=False)
    style_axes(ax)
    save(fig, "burstgpt_boundary.pdf")


def ohi_scatter() -> None:
    points = []
    with (ROOT / "runs" / "ohi_gain_analysis" / "ohi_gain.csv").open() as f:
        for row in csv.DictReader(f):
            label = row["workload"].replace("_heavy", "").replace("_enterprise", "").replace("burstgpt_100x", "BurstGPT")
            points.append((label, float(row["ohi"]), float(row["yieldos_gain_pct"])))
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for label, ohi, gain in points:
        color = COLORS["red"] if gain < 0 else COLORS["yieldos"]
        ax.scatter([ohi], [gain], s=58, color=color, edgecolor="#111827", linewidth=0.5)
        ax.annotate(label, (ohi, gain), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.axhline(0, color="#6b7280", linewidth=0.8)
    ax.set_xlabel("Obligation Heterogeneity Index")
    ax.set_ylabel("YieldOS gain over DistServe (%)")
    ax.set_title("OHI vs YieldOS advantage", weight="bold", pad=12)
    style_axes(ax)
    save(fig, "ohi_gain_scatter.pdf")


def main() -> None:
    architecture()
    baseline_goodput()
    main_goodput()
    load_sweep()
    slo_tightness()
    profile_gains()
    burstgpt_boundary()
    ohi_scatter()
    print(f"wrote figures to {FIG_DIR}")


if __name__ == "__main__":
    main()
