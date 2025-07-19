#!/usr/bin/env python3

import unittest
from uuid import uuid4
from decimal import Decimal

from domain.portfolio.holdings_management_service import HoldingsManagementService
from domain.portfolio.portfolio_errors import DuplicateHoldingError
from domain.portfolio.models.portfolio import Portfolio, PortfolioName
from domain.portfolio.models.enums import Currency
from domain.portfolio.models.holding import CashHolding
from tests.repositories.portfolio import InMemoryPortfolioRepository
from tests.repositories.equity import InMemoryEquityRepository
from tests.repositories.holdings import InMemoryEquityHoldingRepository, InMemoryCashHoldingRepository


class HoldingsManagementServiceTest(unittest.TestCase):
    """Test the specialized HoldingsManagementService."""

    def setUp(self):
        """Set up test dependencies."""
        self.cash_holding_repo = InMemoryCashHoldingRepository()
        self.portfolio_repo = InMemoryPortfolioRepository(self.cash_holding_repo)
        self.equity_repo = InMemoryEquityRepository()
        self.equity_holding_repo = InMemoryEquityHoldingRepository()
        
        self.service = HoldingsManagementService(
            portfolio_repo=self.portfolio_repo,
            equity_repo=self.equity_repo,
            equity_holding_repo=self.equity_holding_repo,
            cash_holding_repo=self.cash_holding_repo
        )
        
        self.tenant_id = uuid4()
        
        # Create a test portfolio using the repository directly        
        self.portfolio = Portfolio(
            id=uuid4(),
            tenant_id=self.tenant_id,
            name=PortfolioName("Test Portfolio")
        )
        self.portfolio_repo.save(self.portfolio)
        
        # Create initial CAD cash holding
        cash_holding = CashHolding(
            id=uuid4(),
            portfolio_id=self.portfolio.id,
            currency=Currency.CAD,
            balance=Decimal('0')
        )
        self.cash_holding_repo.save(cash_holding)

    def test_add_equity_holding_new_stock(self):
        """Test adding an equity holding with a new stock."""
        holding = self.service.add_equity_holding(
            self.portfolio.id, 
            "AAPL", 
            Decimal('100'), 
            Decimal('1000.00')
        )
        
        self.assertIsNotNone(holding)
        self.assertEqual(holding.quantity, Decimal('100'))
        self.assertEqual(holding.cost_basis, Decimal('1000.00'))
        
        # Verify stock was created
        stock = self.equity_repo.find_by_symbol("AAPL", "NASDAQ")
        self.assertIsNotNone(stock)
        self.assertEqual(stock.symbol, "AAPL")
        
        # Verify holding was saved
        saved_holding = self.equity_holding_repo.get(holding.id)
        self.assertIsNotNone(saved_holding)

    def test_add_equity_holding_existing_stock(self):
        """Test adding holdings for existing stocks in different portfolios."""
        
        # Create second portfolio
        portfolio2 = Portfolio(
            id=uuid4(),
            tenant_id=self.tenant_id,
            name=PortfolioName("Portfolio 2")
        )
        self.portfolio_repo.save(portfolio2)
        
        # Now add holding for same stock in different portfolio
        holding2 = self.service.add_equity_holding(
            portfolio2.id, 
            "AAPL", 
            Decimal('75'), 
            Decimal('750.00')
        )
        
        self.assertIsNotNone(holding2)
        
        # Verify only one stock exists
        all_holdings = (self.equity_holding_repo.find_by_portfolio_id(self.portfolio.id) + 
                       self.equity_holding_repo.find_by_portfolio_id(portfolio2.id))
        stock_ids = {h.equity_id for h in all_holdings}
        self.assertEqual(len(stock_ids), 1)  # Same stock used

    def test_add_duplicate_holding_raises_error(self):
        """Test that adding duplicate holdings raises an error."""
        self.service.add_equity_holding(self.portfolio.id, "AAPL", Decimal('100'), Decimal('1000.00'))
        
        with self.assertRaises(DuplicateHoldingError):
            self.service.add_equity_holding(self.portfolio.id, "AAPL", Decimal('50'), Decimal('500.00'))

    def test_add_holding_nonexistent_portfolio(self):
        """Test adding holding to nonexistent portfolio returns None."""
        result = self.service.add_equity_holding(uuid4(), "AAPL", Decimal('100'), Decimal('1000.00'))
        self.assertIsNone(result)

    def test_update_equity_holding(self):
        """Test updating an equity holding."""
        holding = self.service.add_equity_holding(self.portfolio.id, "AAPL", Decimal('100'), Decimal('1000.00'))
        
        success = self.service.update_equity_holding(
            holding.id,
            quantity=Decimal('150'),
            cost_basis=Decimal('1500.00')
        )
        
        self.assertTrue(success)
        
        # Verify the holding was updated
        updated_holding = self.equity_holding_repo.get(holding.id)
        self.assertEqual(updated_holding.quantity, Decimal('150'))
        self.assertEqual(updated_holding.cost_basis, Decimal('1500.00'))

    def test_update_nonexistent_holding(self):
        """Test updating nonexistent holding returns False."""
        success = self.service.update_equity_holding(uuid4(), quantity=Decimal('100'))
        self.assertFalse(success)

    def test_get_equity_holdings(self):
        """Test getting equity holdings for a portfolio."""
        # Add multiple holdings
        self.service.add_equity_holding(self.portfolio.id, "AAPL", Decimal('100'), Decimal('1000.00'))
        self.service.add_equity_holding(self.portfolio.id, "GOOGL", Decimal('50'), Decimal('500.00'))
        
        holdings = self.service.get_equity_holdings(self.portfolio.id)
        self.assertEqual(len(holdings), 2)
        
        symbols = []
        for holding in holdings:
            stock = self.equity_repo.get(holding.equity_id)
            symbols.append(stock.symbol)
        
        self.assertIn("AAPL", symbols)
        self.assertIn("GOOGL", symbols)

    def test_update_cash_balance(self):
        """Test updating cash balance."""        
        success = self.service.update_cash_balance(
            self.portfolio.id, 
            Decimal('500.00'), 
            'deposit'
        )
        self.assertTrue(success)
        
        # Verify cash holding was updated
        cash_holdings = self.service.get_cash_holdings(self.portfolio.id)
        usd_holding = next((h for h in cash_holdings if h.currency == Currency.USD), None)
        self.assertIsNotNone(usd_holding)
        self.assertEqual(usd_holding.balance, Decimal('500.00'))

    def test_update_cash_balance_with_currency(self):
        """Test updating cash balance with specific currency."""        
        success = self.service.update_cash_balance(
            self.portfolio.id, 
            Currency.CAD,
            Decimal('750.00'), 
            'deposit'
        )
        self.assertTrue(success)
        
        # Verify CAD cash holding was updated
        cash_holdings = self.service.get_cash_holdings(self.portfolio.id)
        cad_holding = next((h for h in cash_holdings if h.currency == Currency.CAD), None)
        self.assertIsNotNone(cad_holding)
        self.assertEqual(cad_holding.balance, Decimal('750.00'))

    def test_update_cash_balance_nonexistent_portfolio(self):
        """Test updating cash balance for nonexistent portfolio returns False."""
        success = self.service.update_cash_balance(
            uuid4(), 
            Decimal('500.00'), 
            'deposit'
        )
        self.assertFalse(success)

    def test_get_cash_holdings(self):
        """Test getting cash holdings for a portfolio."""
        # Portfolio should have initial CAD holding
        cash_holdings = self.service.get_cash_holdings(self.portfolio.id)
        self.assertEqual(len(cash_holdings), 1)
        
        # Add USD holding
        self.service.update_cash_balance(self.portfolio.id, Decimal('1000.00'), 'deposit')
        
        # Should now have both CAD and USD
        cash_holdings = self.service.get_cash_holdings(self.portfolio.id)
        self.assertEqual(len(cash_holdings), 2)
        
        currencies = {h.currency.value for h in cash_holdings}
        self.assertIn('CAD', currencies)
        self.assertIn('USD', currencies)


if __name__ == '__main__':
    unittest.main()
