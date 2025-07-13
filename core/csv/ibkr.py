from typing import Dict, Optional, List
from core.csv.base import BaseCSVParser, CsvSectionHandler
from datetime import datetime
from core.csv.utils import normalize_field, is_summary_row
from core.csv.state_machine import CsvStateMachine
from enum import Enum

def parse_float(val):
    try:
        if val is None or val == "" or val == "--":
            return None
        return float(str(val).replace(",", ""))
    except Exception:
        return None
    
class IbkrStatementHandler(CsvSectionHandler):
    def __init__(self):
        self.statement_metadata = {}

    def handle_row(self, row: dict):
        # Accepts a dict with keys like 'field_name' and 'field_value' from generic parsing
        field = row.get('field_name')
        value = row.get('field_value')
        if field:
            self.statement_metadata[field] = value

class IbkrTradesHandler(CsvSectionHandler):
    def __init__(self):
        self.trades: List[dict] = []

    def handle_row(self, row: dict):
        # Only process rows with a symbol and datetime (skip SubTotal/Total)
        if not row.get("symbol") or not row.get("date_time"):
            return
        trade = {
            "data_discriminator": row.get("datadiscriminator"),
            "asset_category": row.get("asset_category"),
            "currency": row.get("currency"),
            "symbol": row.get("symbol"),
            "datetime": row.get("date_time"),
            "quantity": parse_float(row.get("quantity")),
            "t_price": parse_float(row.get("t._price")),  # Handle normalized field name
            "c_price": parse_float(row.get("c._price")),  # Handle normalized field name
            "proceeds": parse_float(row.get("proceeds")),
            "commission": parse_float(row.get("comm_fee")) or parse_float(row.get("comm_in_cad")),
            "basis": parse_float(row.get("basis")),
            "realized_pl": parse_float(row.get("realized_p_l")),
            "mtm_pl": parse_float(row.get("mtm_p_l")) or parse_float(row.get("mtm_in_cad")),
            "code": row.get("code"),
        }
        self.trades.append(trade)

class IbkrDividendsHandler(CsvSectionHandler):
    def __init__(self):
        self.dividends: List[dict] = []

    def handle_row(self, row: dict):
        # Only process rows with a date and description (skip Total rows)
        if not row.get("date") or not row.get("description"):
            return
        dividend = {
            "currency": row.get("currency"),
            "date": row.get("date"),
            "description": row.get("description"),
            "amount": parse_float(row.get("amount")),
        }
        self.dividends.append(dividend)

class IbkrOpenPositionsHandler(CsvSectionHandler):
    def __init__(self):
        self.positions: List[dict] = []

    def handle_row(self, row: dict):
        # Only process rows with a symbol and quantity (skip Total rows)
        if not row.get("symbol") or not row.get("quantity"):
            return
        position = {
            "data_discriminator": row.get("datadiscriminator"),
            "asset_category": row.get("asset_category"),
            "currency": row.get("currency"),
            "symbol": row.get("symbol"),
            "quantity": parse_float(row.get("quantity")),
            "mult": parse_float(row.get("mult")),
            "cost_price": parse_float(row.get("cost_price")),
            "cost_basis": parse_float(row.get("cost_basis")),
            "close_price": parse_float(row.get("close_price")),
            "value": parse_float(row.get("value")),
            "unrealized_pl": parse_float(row.get("unrealized_p_l")),
            "code": row.get("code"),
        }
        self.positions.append(position)

class IbkrForexBalancesHandler(CsvSectionHandler):
    def __init__(self):
        self.forex_balances: List[dict] = []

    def handle_row(self, row: dict):
        # Only process rows with currency and quantity (skip Total rows)
        if not row.get("currency") or not row.get("quantity") or row.get("currency") == "":
            return
        
        # In IBKR forex balances, the 'description' field contains the actual currency
        # while 'currency' field shows the base currency (usually CAD)
        actual_currency = row.get("description") or row.get("currency")
        
        forex_balance = {
            "asset_category": row.get("asset_category"),
            "currency": actual_currency,  # Use description as the actual currency
            "base_currency": row.get("currency"),  # The original currency column
            "description": row.get("description"),
            "quantity": parse_float(row.get("quantity")),
            "cost_price": parse_float(row.get("cost_price")),
            "cost_basis_in_cad": parse_float(row.get("cost_basis_in_cad")),
            "close_price": parse_float(row.get("close_price")),
            "value_in_cad": parse_float(row.get("value_in_cad")),
            "unrealized_pl_in_cad": parse_float(row.get("unrealized_p_l_in_cad")),
            "code": row.get("code"),
        }
        self.forex_balances.append(forex_balance)

def ibkr_section_header_detector(row: List[str]) -> Optional[str]:
    if len(row) > 1 and row[1].strip().lower() == 'header':
        return row[0].strip()
    return None

class SectionNames(Enum):
    TRADES = "Trades"
    DIVIDENDS = "Dividends"
    OPEN_POSITIONS = "Open Positions"
    STATEMENT = "Statement"
    FOREX_BALANCES = "Forex Balances"

class IbkrCsvParser(BaseCSVParser):
    def __init__(
        self,
        section_handlers: Optional[Dict[Optional[str], CsvSectionHandler]] = None,
        strict: bool = True,
        logger=None,
    ):
        if section_handlers is None:
            section_handlers = {
                SectionNames.TRADES.value: IbkrTradesHandler(),
                SectionNames.DIVIDENDS.value: IbkrDividendsHandler(),
                SectionNames.OPEN_POSITIONS.value: IbkrOpenPositionsHandler(),
                SectionNames.STATEMENT.value: IbkrStatementHandler(),
                SectionNames.FOREX_BALANCES.value: IbkrForexBalancesHandler(),
            }
        super().__init__(
            section_handlers=section_handlers,
            strict=strict,
            section_header_detector=ibkr_section_header_detector,
            logger=logger,
        )
        if logger is None:
            self.logger = {
                "info": print,
                "debug": print,
                "error": print,
                "warning": print,
            }
        else:
            self.logger = logger
        
        # Initialize state machine
        self.state_machine = CsvStateMachine(self.logger)

    @property
    def trades(self):
        handler = self.section_handlers.get(SectionNames.TRADES.value)
        return handler.trades if handler else []

    @property
    def dividends(self):
        handler = self.section_handlers.get(SectionNames.DIVIDENDS.value)
        return handler.dividends if handler else []

    @property
    def positions(self):
        handler = self.section_handlers.get(SectionNames.OPEN_POSITIONS.value)
        return handler.positions if handler else []
    
    @property
    def meta(self):
        handler = self.section_handlers.get(SectionNames.STATEMENT.value)
        return handler.statement_metadata if handler else {}

    @property
    def forex_balances(self):
        handler = self.section_handlers.get(SectionNames.FOREX_BALANCES.value)
        return handler.forex_balances if handler else []
    
    def _parse_section_trades(self, rows, handler):
        self.state_machine.transition_to_section(SectionNames.TRADES.value)
        self.state_machine.process_section(rows, handler)

    def _parse_section_open_positions(self, rows, handler):
        self.state_machine.transition_to_section(SectionNames.OPEN_POSITIONS.value)
        self.state_machine.process_section(rows, handler)

    def _parse_section_dividends(self, rows, handler):
        self.state_machine.transition_to_section(SectionNames.DIVIDENDS.value)
        self.state_machine.process_section(rows, handler)

    def _parse_section_statement(self, rows, handler=None):
        self.state_machine.transition_to_section(SectionNames.STATEMENT.value)
        self.state_machine.process_section(rows, handler)
        
        # Post-process statement metadata
        self._process_statement_metadata(handler)

    def _process_statement_metadata(self, handler):
        """Process and enhance statement metadata after parsing."""
        if not handler:
            return
            
        meta = handler.statement_metadata
        if self.logger:
            self.logger.debug(f"[IBKR DEBUG] Extracted statement_info: {meta}")
        
        # Parse period
        self._parse_period(meta)
        
        # Parse generated date
        self._parse_generated_date(meta)
        
        if self.logger:
            self.logger.debug(f"[IBKR DEBUG] Final statement_metadata: {meta}")

    def _parse_period(self, meta):
        """Parse period information from statement metadata."""
        period = meta.get("Period", "")
        if " - " in period:
            period_start, period_end = [d.strip().replace('"', '') for d in period.split(" - ")]
            try:
                meta["PeriodStart"] = datetime.strptime(period_start, "%B %d, %Y").date()
                meta["PeriodEnd"] = datetime.strptime(period_end, "%B %d, %Y").date()
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"[IBKR DEBUG] Failed to parse period: {e}")
                meta["PeriodStart"] = period_start
                meta["PeriodEnd"] = period_end

    def _parse_generated_date(self, meta):
        """Parse generated date from statement metadata."""
        when_generated = meta.get("WhenGenerated", "").replace('"', '').split(",")[0]
        try:
            meta["GeneratedAt"] = datetime.strptime(when_generated, "%Y-%m-%d")
        except Exception as e:
            if self.logger:
                self.logger.debug(f"[IBKR DEBUG] Failed to parse generated date: {e}")
            meta["GeneratedAt"] = when_generated

    def _parse_section_forex_balances(self, rows, handler):
        self.state_machine.transition_to_section(SectionNames.FOREX_BALANCES.value)
        self.state_machine.process_section(rows, handler)

    def pretty_print(self, sections=None):
        """
        Pretty print the parsed IBKR CSV data.
        If sections is None, print all. Otherwise, print only the specified sections (list of str).
        """
        if sections is None:
            sections = ['statement', 'trades', 'dividends', 'positions']
        if 'statement' in sections or 'meta' in sections:
            self.logger.info("=== Statement Metadata ===")
            meta = self.meta
            if meta:
                for k, v in meta.items():
                    self.logger.info(f"{k}: {v}")
            else:
                self.logger.info("No statement metadata found.")
        if 'trades' in sections:
            self.logger.info("=== Trades ===")
            if self.trades:
                for t in self.trades:
                    self.logger.info(f"{t['datetime']} {t['symbol']} {t['quantity']} @ {t['t_price']} {t['currency']} | Proceeds: {t['proceeds']} | Comm: {t['commission']} | Realized P/L: {t['realized_pl']}")
            else:
                self.logger.info("No trades found.")
        if 'dividends' in sections:
            self.logger.info("=== Dividends ===")
            if self.dividends:
                for d in self.dividends:
                    self.logger.info(f"{d['date']} {d.get('description', '')} {d['amount']} {d['currency']}")
            else:
                self.logger.info("No dividends found.")
        if 'positions' in sections:
            self.logger.info("=== Open Positions ===")
            if self.positions:
                for p in self.positions:
                    self.logger.info(f"{p['symbol']} {p['quantity']} {p['currency']} @ {p['cost_price']} (Cost Basis: {p['cost_basis']}) | Close: {p['close_price']} | Value: {p['value']} | UPL: {p['unrealized_pl']}")
            else:
                self.logger.info("No open positions found.")
        if 'forex_balances' in sections:
            self.logger.info("=== Forex Balances ===")
            if self.forex_balances:
                for f in self.forex_balances:
                    self.logger.info(f"{f['currency']} {f['quantity']} @ {f['cost_price']} (Cost Basis in CAD: {f['cost_basis_in_cad']}) | Close: {f['close_price']} | Value in CAD: {f['value_in_cad']} | UPL in CAD: {f['unrealized_pl_in_cad']}")
            else:
                self.logger.info("No forex balances found.")

    def parse(self, file_path: str):
        """
        Per-section parsing for IBKR's multi-section CSV format. Each section is parsed by a dedicated method for robustness.
        """
        import csv
        with open(file_path, newline='', encoding='utf-8-sig') as f:
            reader = list(csv.reader(f))
        # Find all section start indices
        section_indices = []
        for idx, row in enumerate(reader):
            if len(row) > 1 and row[1].strip().lower() == 'header':
                section_indices.append(idx)
        section_indices.append(len(reader))  # Sentinel for last section

        for i in range(len(section_indices) - 1):
            start = section_indices[i]
            end = section_indices[i+1]
            section_row = reader[start]
            section_name = section_row[0].strip()
            if section_name in self.section_handlers:
                parse_method = getattr(self, f'_parse_section_{section_name.lower().replace(" ", "_")}', None)
                if parse_method:
                    self.logger.debug(f"[IBKR DEBUG] Using custom parser for section '{section_name}'")
                    parse_method(reader[start:end], self.section_handlers[section_name])
                else:
                    self.logger.debug(f"[IBKR DEBUG] Using generic parser for section '{section_name}'")
                    self._parse_section_generic(reader[start:end], self.section_handlers[section_name])
        if self.errors and self.strict:
            raise RuntimeError(f"Parsing failed with errors: {self.errors}")
        return self

    def _parse_section_generic(self, rows, handler):
        """Generic section parsing using state machine."""
        # Use the current section name if available, or fallback to generic
        section_name = getattr(self.state_machine, 'current_section_name', 'Generic')
        self.state_machine.transition_to_section(section_name)
        self.state_machine.process_section(rows, handler)
