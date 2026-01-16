# -----------------------------
# 🎨 Global Color Configuration
# -----------------------------

# Base pastel palette
PALETTE = {
    "blue":  "#DCEAFB",
    "green": "#E6F4EA",
    "teal":  "#E8F5FA",
    "peach": "#FFF5E6",
    "purple": "#EFEAFF",
    "pink":  "#FDE7E7",
}

# Metric display names used in the CHART (from long_df["metric_display"])
CHART_METRIC_COLORS = {
    "Max Level Reached": PALETTE["blue"],
    "Number of Sessions": PALETTE["green"],
    "Total Play Time (min)": PALETTE["teal"],
    "Avg Session Length (min)": PALETTE["peach"],
    "Active Span (days)": PALETTE["purple"],
    "Days to RA": PALETTE["pink"],
}

# Engagement metric names used in TILES (from get_engagement_metrics_for_cohort)
TILE_METRIC_COLORS = {
    "Avg Level Reached": PALETTE["blue"],
    "Avg # Sessions / User": PALETTE["green"],
    "Avg Total Play Time / User": PALETTE["teal"],
    "Avg Session Length / User": PALETTE["peach"],
    "Active Span / User": PALETTE["purple"],
    "Avg Days to RA": PALETTE["pink"],
}
TILE_METRIC_COLORS.update({
    "Eligible users": PALETTE["blue"],
    "Book readers (language-mapped)": PALETTE["green"],
    "Uptake": PALETTE["peach"],
    "Book readers (unmapped)": PALETTE["pink"],
})