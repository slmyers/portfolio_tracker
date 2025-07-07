# ADR-002: Adopt TimescaleDB for Portfolio Tracker Time Series Data

## Status
Accepted

## Context
The Portfolio Tracker application requires efficient storage, querying, and analysis of time series data, including portfolio values, holdings snapshots, and high-volume activity logs. Our domain model (see `docs/domain/portfolio.md`) emphasizes scalability, on-demand access, and advanced analytics. While standard PostgreSQL is robust, it lacks native time series optimizations for large-scale, high-ingest workloads and advanced time-based queries.

## Decision
We will use TimescaleDB as our primary database for time series data in the Portfolio Tracker. TimescaleDB is a PostgreSQL extension purpose-built for time series workloads, offering:
- Hypertables for automatic partitioning and efficient time-based queries
- Continuous aggregates (materialized views) for fast analytics
- Native compression and retention policies
- Full compatibility with PostgreSQL, allowing use of standard SQL, ORMs, and JSONB fields

This decision enables us to:
- Efficiently store and query large volumes of activity entries and portfolio value history
- Support advanced analytics (e.g., rolling returns, time-windowed performance)
- Scale to support many tenants and high-frequency data

## Consequences
- Our Docker/Postgres containers will be replaced with TimescaleDB containers for local and CI environments
- Production deployments will use managed TimescaleDB (e.g., Timescale Cloud) or self-managed on cloud VMs
- Schema and migrations will use TimescaleDB features (hypertables, continuous aggregates)
- Application code and repository interfaces remain PostgreSQL-compatible, but can leverage TimescaleDB optimizations

---

## Initial Migrations (SQL)

Below are example migrations for the core domain tables, using TimescaleDB features:

```sql
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Portfolio table (regular table)
CREATE TABLE portfolio (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    cash_balance NUMERIC NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

-- Stock table (regular table)
CREATE TABLE stock (
    id UUID PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL UNIQUE,
    name VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL
);

-- Holding table (regular table)
CREATE TABLE holding (
    id UUID PRIMARY KEY,
    portfolio_id UUID NOT NULL REFERENCES portfolio(id) ON DELETE CASCADE,
    stock_id UUID NOT NULL REFERENCES stock(id),
    quantity NUMERIC NOT NULL,
    cost_basis NUMERIC NOT NULL,
    current_value NUMERIC NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

-- ActivityReportEntry table (hypertable)
CREATE TABLE activity_report_entry (
    id UUID PRIMARY KEY,
    portfolio_id UUID NOT NULL REFERENCES portfolio(id) ON DELETE CASCADE,
    stock_id UUID REFERENCES stock(id),
    activity_type VARCHAR(32) NOT NULL,
    amount NUMERIC NOT NULL,
    date TIMESTAMPTZ NOT NULL,
    raw_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

-- Convert to hypertable for time series queries
SELECT create_hypertable('activity_report_entry', 'date');

-- Indexes for performance
CREATE INDEX idx_activity_report_entry_portfolio_id_date ON activity_report_entry (portfolio_id, date DESC);
CREATE INDEX idx_holding_portfolio_id ON holding (portfolio_id);
```

---

## Example TimescaleDB Queries

### Incremental and Materialized Calculations in TimescaleDB

TimescaleDB enables efficient incremental and materialized calculations, which are essential for time series analytics in the portfolio domain:

- **Incremental (Rolling Window) Calculations:**
  - Use SQL window functions to compute rolling sums, averages, and other metrics over time. These calculations are performed incrementally as new data arrives, without rescanning the entire dataset.
  - Example: Rolling 30-day net activity (see Query 3 below).

- **Continuous Aggregates (Materialized Views):**
  - TimescaleDB's continuous aggregates automatically and incrementally maintain materialized views of aggregated data (e.g., daily portfolio value), updating only the new or changed data.
  - This provides fast, up-to-date analytics without the overhead of recomputing large aggregates on every query.
  - Example: Daily portfolio value materialized view (see Query 2 below).

These features are a key reason for adopting TimescaleDB, as they directly support the scalability and analytics requirements of the portfolio tracker.

### 1. Portfolio Value Over Time (Daily)
```sql
SELECT date_trunc('day', date) AS day, SUM(amount) AS net_activity
FROM activity_report_entry
WHERE portfolio_id = $1
GROUP BY day
ORDER BY day;
```

### 2. Continuous Aggregate: Daily Portfolio Value
```sql
CREATE MATERIALIZED VIEW daily_portfolio_value
WITH (timescaledb.continuous) AS
SELECT
    portfolio_id,
    date_trunc('day', date) AS day,
    SUM(amount) AS net_activity
FROM activity_report_entry
GROUP BY portfolio_id, day;
```

### 3. Rolling 30-Day Net Activity
```sql
SELECT
    date,
    SUM(amount) OVER (PARTITION BY portfolio_id ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS rolling_30d_net
FROM activity_report_entry
WHERE portfolio_id = $1
ORDER BY date;
```

### 4. Top N Most Active Stocks in a Portfolio (by activity count)
```sql
SELECT stock_id, COUNT(*) AS activity_count
FROM activity_report_entry
WHERE portfolio_id = $1
GROUP BY stock_id
ORDER BY activity_count DESC
LIMIT 10;
```

---

## References
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [Portfolio Domain Model](./portfolio.md)

---

_Last updated: 2025-07-05_
