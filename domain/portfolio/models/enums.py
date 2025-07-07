from enum import Enum

class Currency(Enum):
    """Supported currencies (subset of database enum)."""
    USD = "USD"
    CAD = "CAD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    AUD = "AUD"

class Exchange(Enum):
    """Supported exchanges (subset of database enum)."""
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    LSE = "LSE"
    HKEX = "HKEX"
    EURONEXT = "EURONEXT"
    ASX = "ASX"
    JPX = "JPX"