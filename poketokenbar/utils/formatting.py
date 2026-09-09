def format_tokens(num: float) -> str:
    """Format token count into compact human readable string (e.g. 40.7M, 74.9K, 123) without rounding up."""
    val = float(num)
    sign = "-" if val < 0 else ""
    abs_val = abs(val)
    if abs_val >= 1_000_000_000:
        truncated = int(abs_val / 100_000_000) / 10.0
        return f"{sign}{truncated:.1f}B"
    elif abs_val >= 1_000_000:
        truncated = int(abs_val / 100_000) / 10.0
        return f"{sign}{truncated:.1f}M"
    elif abs_val >= 1_000:
        truncated = int(abs_val / 100) / 10.0
        return f"{sign}{truncated:.1f}K"
    else:
        if abs_val.is_integer():
            return f"{sign}{int(abs_val)}"
        return f"{sign}{abs_val:.1f}"

def parse_tokens(amount_str: str) -> int:
    clean_str = str(amount_str).lower().strip()
    if not clean_str:
        return 0
    try:
        if clean_str.endswith("b"):
            return int(float(clean_str[:-1]) * 1_000_000_000)
        elif clean_str.endswith("m"):
            return int(float(clean_str[:-1]) * 1_000_000)
        elif clean_str.endswith("k"):
            return int(float(clean_str[:-1]) * 1_000)
        else:
            return int(clean_str)
    except ValueError:
        return -1

def format_progress_bar(current: int, total: int, width: int = 20) -> str:
    """Renders a progress bar string."""
    if total <= 0:
        pct = 0.0
    else:
        pct = min(1.0, max(0.0, current / float(total)))
    filled_len = int(round(width * pct))
    bar = "█" * filled_len + "░" * (width - filled_len)
    return f"[{bar}] {pct * 100:.1f}%"
