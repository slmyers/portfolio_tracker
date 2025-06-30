from typing import Dict, Optional, List
from core.csv.base import BaseCSVParser, CsvSectionHandler

def parse_float(val):
    try:
        if val is None or val == "" or val == "--":
            return None
        return float(str(val).replace(",", ""))
    except Exception:
        return None

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
            "t_price": parse_float(row.get("t_price")),
            "c_price": parse_float(row.get("c_price")),
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

def ibkr_section_header_detector(row: List[str]) -> Optional[str]:
    if len(row) > 1 and row[1].strip().lower() == 'header':
        return row[0].strip()
    return None

class IbkrCsvParser(BaseCSVParser):

    def __init__(
        self,
        section_handlers: Optional[Dict[Optional[str], CsvSectionHandler]] = None,
        strict: bool = True,
        logger=None,
    ):
        if section_handlers is None:
            section_handlers = {
                "Trades": IbkrTradesHandler(),
                "Dividends": IbkrDividendsHandler(),
                "Open Positions": IbkrOpenPositionsHandler(),
            }
        super().__init__(
            section_handlers=section_handlers,
            strict=strict,
            section_header_detector=ibkr_section_header_detector,
        )
        self.logger = logger

    @property
    def trades(self):
        handler = self.section_handlers.get("Trades")
        return handler.trades if handler else []

    @property
    def dividends(self):
        handler = self.section_handlers.get("Dividends")
        return handler.dividends if handler else []

    @property
    def positions(self):
        handler = self.section_handlers.get("Open Positions")
        return handler.positions if handler else []


    def _parse_section_trades(self, rows, handler):
        self._parse_section_common(
            rows,
            handler,
            summary_row_check=lambda row: (row[2].strip().lower().startswith('total') or row[2].strip().lower().startswith('subtotal')) if len(row) > 2 else False,
            header_debug_label="Trades"
        )

    def _parse_section_open_positions(self, rows, handler):
        self._parse_section_common(
            rows,
            handler,
            summary_row_check=lambda row: (row[2].strip().lower().startswith('total') or row[2].strip().lower().startswith('subtotal')) if len(row) > 2 else False,
            header_debug_label="Open Positions"
        )

    def _parse_section_dividends(self, rows, handler):
        self._parse_section_common(
            rows,
            handler,
            summary_row_check=lambda row: (row[2].strip().lower().startswith('total')) if len(row) > 2 else False,
            header_debug_label="Dividends"
        )

    def _parse_section_common(self, rows, handler, summary_row_check, header_debug_label=None):
        """
        Shared parsing logic for IBKR sections. Skips summary/total rows and handles header/data mapping.
        summary_row_check: function(row) -> bool, returns True if row should be skipped as summary.
        header_debug_label: optional string for debug logging.
        """
        def normalize_field(field):
            return field.strip().lower().replace(' ', '_').replace('/', '_')
        header = None
        normalized_header = None
        for row_num, row in enumerate(rows):
            if not any(cell.strip() for cell in row):
                continue
            row_type = row[1].strip() if len(row) > 1 else None
            if row_type == 'Header':
                header = row[2:]
                normalized_header = [normalize_field(h) for h in header]
                if self.logger and header_debug_label:
                    self.logger.debug(f"[IBKR DEBUG] Detected header in {header_debug_label}: {header}")
                continue
            if row_type == 'Data':
                if not header:
                    if self.logger and header_debug_label:
                        self.logger.warning(f"[IBKR WARNING] Data row encountered before header in {header_debug_label} section.")
                    continue
                if summary_row_check(row):
                    if self.logger and header_debug_label:
                        self.logger.debug(f"[IBKR DEBUG] Skipping summary row in {header_debug_label}: {row}")
                    continue
                data_row = row[2:]
                if len(data_row) != len(header):
                    if self.logger and header_debug_label:
                        self.logger.warning(f"[IBKR WARNING] Data/header length mismatch in {header_debug_label}: {data_row} vs {header}")
                    continue
                data = dict(zip(normalized_header, data_row))
                handler.handle_row(data)

    def pretty_print(self, sections=None):
        """
        Pretty print the parsed IBKR CSV data.
        If sections is None, print all. Otherwise, print only the specified sections (list of str).
        """
        if sections is None:
            sections = ['trades', 'dividends', 'positions']
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

    def parse(self, file_path: str):
        """
        Per-section parsing for IBKR's multi-section CSV format. Each section is parsed by a dedicated method for robustness.
        """
        import csv
        with open(file_path, newline='', encoding='utf-8') as f:
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
        def normalize_field(field):
            return field.strip().lower().replace(' ', '_').replace('/', '_')
        header = None
        normalized_header = None
        for row_num, row in enumerate(rows):
            if not any(cell.strip() for cell in row):
                continue
            row_type = row[1].strip() if len(row) > 1 else None
            if row_type == 'Header':
                header = row[2:]
                normalized_header = [normalize_field(h) for h in header]
                continue
            if row_type == 'Data':
                if not header:
                    continue
                data_row = row[2:]
                if len(data_row) != len(header):
                    continue
                data = dict(zip(normalized_header, data_row))
                handler.handle_row(data)

    def _parse_section_dividends(self, rows, handler):
        """
        Custom parser for Dividends section to skip summary/total rows and handle currency changes.
        """
        def normalize_field(field):
            return field.strip().lower().replace(' ', '_').replace('/', '_')
        header = None
        normalized_header = None
        for row_num, row in enumerate(rows):
            if not any(cell.strip() for cell in row):
                continue
            row_type = row[1].strip() if len(row) > 1 else None
            if row_type == 'Header':
                header = row[2:]
                normalized_header = [normalize_field(h) for h in header]
                continue
            if row_type == 'Data':
                if not header:
                    continue
                # Skip summary/total rows (e.g., where the third column is 'Total', 'Total in CAD', etc.)
                currency_or_total = row[2].strip() if len(row) > 2 else ''
                if currency_or_total.lower().startswith('total'):
                    continue
                data_row = row[2:]
                if len(data_row) != len(header):
                    continue
                data = dict(zip(normalized_header, data_row))
                handler.handle_row(data)
