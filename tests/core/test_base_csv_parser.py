import os
import pytest
from core.csv.base import BaseCSVParser, CsvSectionHandler

TEST_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

class SimpleHandler(CsvSectionHandler):
    def __init__(self):
        self.rows = []
    def handle_row(self, row: dict):
        self.rows.append(row)

class ListLogger:
    def __init__(self):
        self.records = []
    def debug(self, msg, *a, **kw):
        self.records.append(str(msg))
    def info(self, msg, *a, **kw):
        self.records.append(str(msg))
    def warning(self, msg, *a, **kw):
        self.records.append(str(msg))

def test_single_section_csv():
    handler = SimpleHandler()
    logger = ListLogger()
    parser = BaseCSVParser(section_handlers={None: handler}, logger=logger)
    parser.parse(os.path.join(TEST_DIR, 'simple.csv'))
    assert len(handler.rows) == 2
    assert handler.rows[0]['Date'] == '2025-01-01'
    assert handler.rows[0]['Symbol'] == 'AAPL'
    assert handler.rows[0]['Quantity'] == '10'
    assert handler.rows[1]['Symbol'] == 'GOOG'

def test_multisection_csv():
    class SectionHandler(CsvSectionHandler):
        def __init__(self):
            self.rows = []
        def handle_row(self, row: dict):
            self.rows.append(row)
    h1 = SectionHandler()
    h2 = SectionHandler()
    logger = ListLogger()
    parser = BaseCSVParser(section_handlers={
        'Section1': h1,
        'Section2': h2,
    }, logger=logger)
    parser.parse(os.path.join(TEST_DIR, 'multisection.csv'))
    assert len(h1.rows) == 2
    assert h1.rows[0]['ColA'] == 'foo'
    assert h2.rows[1]['ColY'] == '4'

def test_malformed_csv_strict():
    class StrictHandler(CsvSectionHandler):
        def handle_row(self, row: dict):
            # Try to cast Quantity to int, will fail for 'notanumber'
            int(row['Quantity'])
    handler = StrictHandler()
    logger = ListLogger()
    parser = BaseCSVParser(section_handlers={None: handler}, strict=True, logger=logger)
    with pytest.raises(RuntimeError):
        parser.parse(os.path.join(TEST_DIR, 'malformed.csv'))

def test_malformed_csv_lenient():
    class LenientHandler(CsvSectionHandler):
        def __init__(self):
            self.rows = []
        def handle_row(self, row: dict):
            int(row['Quantity'])  # Let errors propagate to parser
            self.rows.append(row)
    handler = LenientHandler()
    logger = ListLogger()
    parser = BaseCSVParser(section_handlers={None: handler}, strict=False, logger=logger)
    parser.parse(os.path.join(TEST_DIR, 'malformed.csv'))
    assert len(parser.get_errors()) > 0
    assert len(handler.rows) == 2

def test_edgecase_csv():
    handler = SimpleHandler()
    logger = ListLogger()
    parser = BaseCSVParser(section_handlers={None: handler}, logger=logger)
    parser.parse(os.path.join(TEST_DIR, 'edgecase.csv'))
    assert handler.rows[0]['Symbol'] == 'EMPTY'
    assert handler.rows[1]['Quantity'] == '-10'
    assert handler.rows[2]['Quantity'] == '0'
    assert handler.rows[3]['Quantity'] == '1000000000'

def test_bad_row_length_strict():
    class Handler(CsvSectionHandler):
        def __init__(self):
            self.rows = []
        def handle_row(self, row: dict):
            self.rows.append(row)
    handler = Handler()
    logger = ListLogger()
    parser = BaseCSVParser(section_handlers={None: handler}, strict=True, logger=logger)
    with pytest.raises(RuntimeError) as excinfo:
        parser.parse(os.path.join(TEST_DIR, 'bad_row_length.csv'))
    assert "Row length" in str(excinfo.value)

def test_bad_row_length_lenient():
    class Handler(CsvSectionHandler):
        def __init__(self):
            self.rows = []
        def handle_row(self, row: dict):
            self.rows.append(row)
    handler = Handler()
    logger = ListLogger()
    parser = BaseCSVParser(section_handlers={None: handler}, strict=False, logger=logger)
    parser.parse(os.path.join(TEST_DIR, 'bad_row_length.csv'))
    errors = parser.get_errors()
    assert any("Row length" in e for e in errors)
    # Only valid rows should be appended
    assert len(handler.rows) == 2  # Only the first and last rows are valid
