from typing import Dict, Any, Optional, Callable, IO, List
import csv

class CsvSectionHandler:
    """
    Base class for section handlers. Subclass and override handle_row for custom logic.
    """
    def handle_row(self, row: dict):
        raise NotImplementedError

class BaseCSVParser:
    def __init__(
        self,
        section_handlers: Dict[Optional[str], CsvSectionHandler],
        strict: bool = True,
        section_header_detector: Optional[Callable[[List[str]], Optional[str]]] = None,
    ):
        """
        section_handlers: Dict mapping section name (or None for single-section) to handler
        strict: If True, raise on errors; if False, collect errors and continue
        section_header_detector: Optional function to detect section headers from a row
        """
        self.section_handlers = section_handlers
        self.strict = strict
        self.section_header_detector = section_header_detector
        self.errors = []

    def parse(self, file_path: str):
        current_section = None
        handler = None
        header = None
        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row_num, row in enumerate(reader):
                if not any(cell.strip() for cell in row):
                    continue  # skip blank lines
                # Section header detection
                section = self._detect_section(row)
                if section is not None:
                    current_section = section
                    handler = self.section_handlers.get(current_section)
                    header = None
                    continue
                # Header row detection (first non-empty row after section header)
                if header is None:
                    header = row
                    continue
                # Data row
                if handler is None:
                    handler = self.section_handlers.get(None)
                if handler is None:
                    self._handle_error(f"No handler for section '{current_section}' at row {row_num+1}")
                    continue
                try:
                    data = dict(zip(header, row))
                    handler.handle_row(data)
                except Exception as e:
                    self._handle_error(f"Error in section '{current_section}' at row {row_num+1}: {e}")
        if self.errors and self.strict:
            raise RuntimeError(f"Parsing failed with errors: {self.errors}")
        return self

    def _detect_section(self, row: List[str]) -> Optional[str]:
        if self.section_header_detector:
            return self.section_header_detector(row)
        # Default: treat rows with 'Header' in second column as section header
        if len(row) > 1 and row[1].strip().lower() == 'header':
            return row[0].strip()
        return None

    def _handle_error(self, msg: str):
        if self.strict:
            raise RuntimeError(msg)
        else:
            self.errors.append(msg)

    def get_errors(self) -> List[str]:
        return self.errors
