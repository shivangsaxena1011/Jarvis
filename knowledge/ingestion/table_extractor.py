"""
SHIVANI Tabular Data Extractor
Extracts and structures tables from Markdown, CSV, and TSV sources,
preserving relational rows, columns, and metric alignment.
"""

import csv
import io
import re
from typing import Any, Dict, List, Optional


class TableExtractor:
    """Detects and extracts structured tabular data from text."""

    @classmethod
    def extract_markdown_tables(cls, text: str) -> List[Dict[str, Any]]:
        """
        Extracts markdown pipe tables.
        Returns list of dicts with headers, rows, and raw markdown representation.
        """
        tables: List[Dict[str, Any]] = []
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Check if line looks like markdown table header
            if "|" in line and i + 1 < len(lines) and re.match(r"^\|?[\s\-:|]+\|?$", lines[i + 1].strip()):
                start_line = i + 1
                header_raw = [c.strip() for c in line.strip("|").split("|")]
                headers = [h for h in header_raw if h]
                
                rows: List[List[str]] = []
                table_lines = [lines[i], lines[i + 1]]
                i += 2
                while i < len(lines) and "|" in lines[i].strip():
                    cur_line = lines[i].strip()
                    row_cells = [c.strip() for c in cur_line.strip("|").split("|")]
                    rows.append(row_cells)
                    table_lines.append(lines[i])
                    i += 1
                
                end_line = i
                tables.append({
                    "headers": headers,
                    "rows": rows,
                    "line_start": start_line,
                    "line_end": end_line,
                    "markdown": "\n".join(table_lines),
                })
            else:
                i += 1
        return tables

    @classmethod
    def parse_csv_to_markdown(cls, csv_content: str, delimiter: str = ",") -> str:
        """Converts raw CSV or TSV text into standard Markdown table format."""
        try:
            reader = csv.reader(io.StringIO(csv_content.strip()), delimiter=delimiter)
            rows = list(reader)
            if not rows:
                return ""
            
            headers = [h.strip() for h in rows[0]]
            md_lines = ["| " + " | ".join(headers) + " |"]
            md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
            
            for row in rows[1:]:
                cells = [c.strip().replace("\n", " ") for c in row]
                # Pad cells if necessary
                while len(cells) < len(headers):
                    cells.append("")
                md_lines.append("| " + " | ".join(cells[:len(headers)]) + " |")
            
            return "\n".join(md_lines)
        except Exception:
            return csv_content
