"""
Render the Alice (short answer) vs Bob (long answer) eviction example
as a single PNG for slide 22.5.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import rcParams
from matplotlib import font_manager

# Register the Noto Sans CJK font file directly so matplotlib can find it
# regardless of the system font cache state.
NOTO_TTC = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
font_manager.fontManager.addfont(NOTO_TTC)
rcParams["font.family"] = "Noto Sans CJK JP"  # first face in the TTC; covers Hangul
rcParams["axes.unicode_minus"] = False

OUT = "/home/pdaejun/bidaw/figures/example_alice_bob.png"

# ─── Data ──────────────────────────────────────────────────────────────────
# Bucket labels and reuse-distance centers
bucket_labels = ["small\n(<200)", "P1\n200–240", "P2\n240–280", "P3\n280–320",
                 "P4\n320–360", "P5\n360–400", "P6\n400–440", "extreme\n(>440)"]
bucket_centers = [100, 220, 260, 300, 340, 380, 420, 480]

# Initial probability distribution (shared by both Alice and Bob)
prob_init = [0.40, 0.20, 0.15, 0.10, 0.05, 0.04, 0.03, 0.03]

# Ghost-cache measured hit rates for each bucket
hit_rates  = [1.00, 0.95, 0.85, 0.55, 0.25, 0.15, 0.05, 0.00]

# Alice: short answer (20 tokens) → lower bound 80 GB → no truncation
alice_lb = 80
alice_prob = prob_init.copy()
alice_potential = sum(p * h for p, h in zip(alice_prob, hit_rates))

# Bob: long answer (180 tokens) → lower bound 360 GB → truncate everything
# strictly below the bucket containing 360 GB
bob_lb = 360
bob_prob = []
for c, p in zip(bucket_centers, prob_init):
    # Keep only buckets that intersect or sit above the lower bound 360
    # Promising buckets are [200,240), [240,280), ..., [400,440)
    # Bucket center 380 -> bucket [360,400) which contains 360 (right on boundary)
    if c < bob_lb:
        bob_prob.append(0.0)
    else:
        bob_prob.append(p)
total = sum(bob_prob)
bob_prob = [p / total for p in bob_prob]
bob_potential = sum(p * h for p, h in zip(bob_prob, hit_rates))

# ─── Figure ────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(
    1, 2, figsize=(13.0, 4.8),
    gridspec_kw={"wspace": 0.20},
)

GREY    = "#9CA3AF"
BLUE    = "#3B82F6"
RED     = "#DC2626"
GREEN   = "#16A34A"
LIGHT   = "#E5E7EB"
DARK    = "#1F2937"

for ax, prob, lb, label, name, potential, surv_color in [
    (axes[0], alice_prob, alice_lb, "사용자 A",
     "짧은 답변 (20 토큰)", alice_potential, BLUE),
    (axes[1], bob_prob, bob_lb, "사용자 B",
     "긴 답변 (180 토큰)", bob_potential, RED),
]:
    x = list(range(len(bucket_labels)))

    # Original probability (faint grey) for reference on Bob's chart
    if name == "긴 답변 (180 토큰)":
        ax.bar(x, prob_init, color=LIGHT, edgecolor="none", width=0.78,
               label="원래 분포")

    # Active (truncated/normalized) probability bars
    colors = [GREY if p == 0 else surv_color for p in prob]
    ax.bar(x, prob, color=colors, edgecolor=DARK, linewidth=0.6,
           width=0.78, label="적용 분포")

    # Mark the bucket containing the lower bound with a red dashed line
    # x position of lower bound based on bucket boundaries
    boundaries = [0, 200, 240, 280, 320, 360, 400, 440, 600]
    lb_x = None
    for i in range(len(boundaries) - 1):
        if boundaries[i] <= lb < boundaries[i + 1]:
            # interpolate within bar i
            frac = (lb - boundaries[i]) / (boundaries[i + 1] - boundaries[i])
            lb_x = i - 0.5 + frac
            break
    if lb_x is not None:
        ax.axvline(lb_x, color=RED, linestyle=(0, (5, 3)), linewidth=2.0,
                   alpha=0.9, zorder=5)
        ax.text(lb_x, 0.46, f" 하한 {lb} GB", color=RED,
                fontsize=10, fontweight="bold", va="top", ha="left")

    # X-axis
    ax.set_xticks(x)
    ax.set_xticklabels(bucket_labels, fontsize=8.5)
    ax.set_xlabel("Weighted reuse distance bucket (GB)", fontsize=10)

    # Y-axis
    ax.set_ylim(0, 0.55)
    ax.set_ylabel("Probability", fontsize=10)
    ax.tick_params(axis="y", labelsize=9)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    # Title with potential
    color_potential = GREEN if potential > 0.5 else RED
    decision = "유지 (perf layer)" if potential > 0.5 else "Evict 후보 (capacity)"
    ax.set_title(
        f"{label} — {name}\n"
        f"Potential = {potential:.2f}   →   {decision}",
        fontsize=11.5, fontweight="bold", color=color_potential, pad=10,
    )

# Suptitle
fig.suptitle(
    "답변 길이 → 하한 → bucket truncate → potential — 두 사용자 비교",
    fontsize=13, fontweight="bold", y=1.02,
)

plt.savefig(OUT, dpi=180, bbox_inches="tight", facecolor="white")
print(f"Saved: {OUT}")
