def normalize_field(field: str) -> str:
    """
    Normalize a field name by stripping whitespace, converting to lowercase,
    and replacing spaces and slashes with underscores.
    """
    return field.strip().lower().replace(' ', '_').replace('/', '_')

def is_summary_row(row: list, summary_keywords: list = ["total", "subtotal"]) -> bool:
    """
    Check if a row is a summary row based on keywords.
    """
    if len(row) > 2:
        return any(row[2].strip().lower().startswith(keyword) for keyword in summary_keywords)
    return False
