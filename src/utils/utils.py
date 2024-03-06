
def fix_coordinate(value: int) -> int:
    """Fixes the coordinates when calculating for multi-monitor setups."""
    if value > 2**15:
        return value - 2**16
    return value