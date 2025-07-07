"""Domain errors for the Portfolio domain."""

class PortfolioDomainError(Exception):
    """Base class for all portfolio domain errors."""
    pass

class DuplicateHoldingError(PortfolioDomainError):
    """Raised when adding a holding with a stock_id that already exists in the portfolio."""
    
    def __init__(self, portfolio_id, stock_id):
        self.portfolio_id = portfolio_id
        self.stock_id = stock_id
        super().__init__(f"Portfolio {portfolio_id} already has a holding for stock {stock_id}")

class NegativeCashBalanceError(PortfolioDomainError):
    """Raised when an operation would result in a negative cash balance."""
    
    def __init__(self, portfolio_id, attempted_balance):
        self.portfolio_id = portfolio_id
        self.attempted_balance = attempted_balance
        super().__init__(f"Portfolio {portfolio_id} cannot have negative cash balance: {attempted_balance}")

class InvalidPortfolioNameError(PortfolioDomainError):
    """Raised when creating or renaming a portfolio with an invalid name."""
    
    def __init__(self, name, reason):
        self.name = name
        self.reason = reason
        super().__init__(f"Invalid portfolio name '{name}': {reason}")

class OwnershipMismatchError(PortfolioDomainError):
    """Raised when associating holdings or activity entries whose portfolio_id does not match the aggregate."""
    
    def __init__(self, expected_portfolio_id, actual_portfolio_id):
        self.expected_portfolio_id = expected_portfolio_id
        self.actual_portfolio_id = actual_portfolio_id
        super().__init__(f"Ownership mismatch: expected {expected_portfolio_id}, got {actual_portfolio_id}")

class StockNotFoundError(PortfolioDomainError):
    """Raised when referencing a stock_id that does not exist in the Stock repository."""
    
    def __init__(self, stock_id):
        self.stock_id = stock_id
        super().__init__(f"Stock {stock_id} not found")
