"""timescale_portfolio_aggregate

Revision ID: b2c4fa7a944a
Revises: 36a94e5c1c86
Create Date: 2025-07-06 15:11:58.885287

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b2c4fa7a944a'
down_revision: Union[str, Sequence[str], None] = '36a94e5c1c86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('''
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create exchange enum type
CREATE TYPE exchange_type AS ENUM ('NYSE', 'NASDAQ', 'LSE', 'HKEX', 'EURONEXT', 'ASX', 'JPX', 'BSE', 'SSE', 'SZSE', 'FRA', 'SWX', 'TSE');

-- Create currency enum type
CREATE TYPE currency_type AS ENUM ('USD', 'CAD', 'EUR', 'GBP', 'JPY', 'AUD', 'CHF', 'CNY', 'HKD', 'SGD', 'NZD', 'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'RUB', 'BRL', 'MXN', 'KRW', 'INR', 'THB', 'MYR', 'IDR', 'PHP', 'VND', 'ZAR', 'TRY', 'ILS', 'AED', 'SAR', 'QAR', 'KWD', 'BHD', 'OMR', 'JOD', 'LBP', 'EGP', 'MAD', 'TND', 'DZD', 'LYD', 'SDG', 'ETB', 'UGX', 'KES', 'TZS', 'RWF', 'XAF', 'XOF', 'GHS', 'NGN', 'SLL', 'GMD', 'LRD', 'SVC', 'GTQ', 'HNL', 'NIO', 'CRC', 'PAB', 'JMD', 'HTG', 'DOP', 'CUP', 'BBD', 'XCD', 'TTD', 'GYD', 'SRD', 'FKP', 'SHP', 'GIP', 'JEP', 'GGP', 'IMP', 'TVD', 'ANG', 'AWG', 'BMD', 'KYD', 'VUV', 'WST', 'FJD', 'TOP', 'PGK', 'SBD', 'NCF', 'XPF');

-- Portfolio table (regular table) - REMOVED cash_balance
CREATE TABLE portfolio (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

-- Equity table (regular table)
CREATE TABLE equity (
    id UUID PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL UNIQUE,
    name VARCHAR(128),
    exchange exchange_type,
    created_at TIMESTAMPTZ NOT NULL
);

-- Equity holding table (regular table)
CREATE TABLE equity_holding (
    id UUID PRIMARY KEY,
    portfolio_id UUID NOT NULL REFERENCES portfolio(id) ON DELETE CASCADE,
    equity_id UUID NOT NULL REFERENCES equity(id),
    quantity NUMERIC NOT NULL,
    cost_basis NUMERIC NOT NULL,
    current_value NUMERIC NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE(portfolio_id, equity_id) -- One holding per equity per portfolio
);

-- Cash holding table (regular table)
CREATE TABLE cash_holding (
    id UUID PRIMARY KEY,
    portfolio_id UUID NOT NULL REFERENCES portfolio(id) ON DELETE CASCADE,
    currency currency_type NOT NULL,
    balance NUMERIC NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE(portfolio_id, currency) -- One cash balance per currency per portfolio
);

-- ActivityReportEntry table (hypertable)
CREATE TABLE activity_report_entry (
    id UUID NOT NULL,
    portfolio_id UUID NOT NULL REFERENCES portfolio(id) ON DELETE CASCADE,
    equity_id UUID REFERENCES equity(id),
    activity_type VARCHAR(32) NOT NULL,
    amount NUMERIC NOT NULL,
    currency currency_type,
    date TIMESTAMPTZ NOT NULL,
    raw_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (id, date, portfolio_id)
);

-- Convert to hypertable for time series queries
SELECT create_hypertable('activity_report_entry', 'date', 'portfolio_id', 4);

-- Indexes for performance
CREATE INDEX idx_activity_report_entry_portfolio_id_date ON activity_report_entry (portfolio_id, date DESC);
CREATE INDEX idx_activity_report_entry_portfolio_id_activity_type ON activity_report_entry (portfolio_id, activity_type);
CREATE INDEX idx_activity_report_entry_portfolio_id_currency ON activity_report_entry (portfolio_id, currency);
CREATE INDEX idx_equity_holding_portfolio_id ON equity_holding (portfolio_id);
CREATE INDEX idx_cash_holding_portfolio_id ON cash_holding (portfolio_id);
CREATE INDEX idx_portfolio_tenant_id ON portfolio (tenant_id);
CREATE INDEX idx_equity_symbol ON equity (symbol);
''')
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('''
-- Drop indexes
DROP INDEX IF EXISTS idx_activity_report_entry_portfolio_id_date;
DROP INDEX IF EXISTS idx_activity_report_entry_portfolio_id_activity_type;
DROP INDEX IF EXISTS idx_activity_report_entry_portfolio_id_currency;
DROP INDEX IF EXISTS idx_equity_holding_portfolio_id;
DROP INDEX IF EXISTS idx_cash_holding_portfolio_id;
DROP INDEX IF EXISTS idx_portfolio_tenant_id;
DROP INDEX IF EXISTS idx_equity_symbol;

-- Drop tables (order matters due to foreign key constraints)
DROP TABLE IF EXISTS activity_report_entry;
DROP TABLE IF EXISTS cash_holding;
DROP TABLE IF EXISTS equity_holding;
DROP TABLE IF EXISTS equity;
DROP TABLE IF EXISTS portfolio;

-- Drop enum types
DROP TYPE IF EXISTS currency_type;
DROP TYPE IF EXISTS exchange_type;

-- Drop TimescaleDB extension (optional, may be used by other schemas)
-- DROP EXTENSION IF EXISTS timescaledb;
''')
