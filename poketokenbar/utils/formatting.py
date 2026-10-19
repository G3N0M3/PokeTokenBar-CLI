from decimal import Decimal, InvalidOperation


def format_tokens(num: float) -> str:
    """Format token count into compact human readable string (e.g. 40.7M, 74.9K, 123) without rounding up."""
    if isinstance(num, int) and not isinstance(num, bool):
        sign = "-" if num < 0 else ""
        abs_int = abs(num)
        if abs_int >= 1_000_000_000_000_000:
            truncated = (abs_int // 100_000_000_000_000) / 10.0
            return f"{sign}{truncated:.1f}Q"
        elif abs_int >= 1_000_000_000_000:
            truncated = (abs_int // 100_000_000_000) / 10.0
            return f"{sign}{truncated:.1f}T"
        elif abs_int >= 1_000_000_000:
            truncated = (abs_int // 100_000_000) / 10.0
            return f"{sign}{truncated:.1f}B"
        elif abs_int >= 1_000_000:
            truncated = (abs_int // 100_000) / 10.0
            return f"{sign}{truncated:.1f}M"
        elif abs_int >= 1_000:
            truncated = (abs_int // 100) / 10.0
            return f"{sign}{truncated:.1f}K"
        else:
            return f"{sign}{abs_int}"

    val = float(num)
    sign = "-" if val < 0 else ""
    abs_val = abs(val)
    if abs_val >= 1_000_000_000_000_000:
        truncated = int(abs_val / 100_000_000_000_000) / 10.0
        return f"{sign}{truncated:.1f}Q"
    elif abs_val >= 1_000_000_000_000:
        truncated = int(abs_val / 100_000_000_000) / 10.0
        return f"{sign}{truncated:.1f}T"
    elif abs_val >= 1_000_000_000:
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
    multipliers = {
        "q": 1_000_000_000_000_000,
        "t": 1_000_000_000_000,
        "b": 1_000_000_000,
        "m": 1_000_000,
        "k": 1_000,
    }
    try:
        suffix = clean_str[-1]
        if suffix in multipliers:
            num_part = clean_str[:-1].strip()
            d_val = Decimal(num_part)
            if not d_val.is_finite():
                return -1
            return int(d_val * multipliers[suffix])
        else:
            return int(clean_str)
    except (ValueError, OverflowError, InvalidOperation):
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
