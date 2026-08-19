def format_tokens(num: float) -> str:
    """Format token count into compact human readable string (e.g. 40.7M, 74.9K, 123)."""
    val = float(num)
    if val >= 1_000_000_000:
        return f"{val / 1_000_000_000:.1f}B"
    elif val >= 1_000_000:
        return f"{val / 1_000_000:.1f}M"
    elif val >= 1_000:
        return f"{val / 1_000:.1f}K"
    else:
        if val.is_integer():
            return str(int(val))
        return f"{val:.1f}"

def format_progress_bar(current: int, total: int, width: int = 20) -> str:
    """Renders a progress bar string."""
    if total <= 0:
        pct = 0.0
    else:
        pct = min(1.0, max(0.0, current / float(total)))
    filled_len = int(round(width * pct))
    bar = "█" * filled_len + "░" * (width - filled_len)
    return f"[{bar}] {pct * 100:.1f}%"
