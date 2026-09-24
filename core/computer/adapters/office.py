"""
SHIVANI Microsoft Office Application Adapters (Phase 17).
Provides safe automation and semantic analysis for Excel, Word, and PowerPoint.
"""

from __future__ import annotations
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.computer.adapters.base import ApplicationAdapter
from core.computer.models import ApplicationContext


class ExcelAdapter(ApplicationAdapter):
    """Specialized adapter for Microsoft Excel and spreadsheet analysis."""

    @property
    def name(self) -> str:
        return "Microsoft Excel Adapter"

    @property
    def supported_processes(self) -> List[str]:
        return ["excel.exe", "excel"]

    async def get_available_actions(self) -> List[str]:
        return [
            "save_workbook",
            "insert_chart_from_csv",
            "analyze_spreadsheet",
        ]

    async def execute_action(
        self, action_name: str, parameters: Dict[str, Any], context: ApplicationContext
    ) -> Dict[str, Any]:
        if action_name == "save_workbook":
            return {"success": True, "hotkey": ["ctrl", "s"], "action": action_name}

        if action_name == "insert_chart_from_csv":
            csv_path = Path(parameters.get("csv_path", ""))
            output_excel = Path(parameters.get("output_excel", "chart_output.xlsx"))
            if not csv_path.exists():
                return {"success": False, "error": f"CSV file '{csv_path}' not found"}

            try:
                import xlsxwriter

                # Read CSV
                rows = []
                with open(csv_path, mode="r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for r in reader:
                        rows.append(r)

                if not rows:
                    return {"success": False, "error": "CSV file is empty"}

                # Create workbook and chart
                workbook = xlsxwriter.Workbook(str(output_excel))
                worksheet = workbook.add_worksheet("Data")

                for row_idx, row in enumerate(rows):
                    for col_idx, cell in enumerate(row):
                        try:
                            val = float(cell)
                            worksheet.write_number(row_idx, col_idx, val)
                        except ValueError:
                            worksheet.write_string(row_idx, col_idx, cell)

                # Add a bar chart
                chart = workbook.add_chart({"type": "column"})
                chart.add_series({
                    "name": f"=Data!$B$1",
                    "categories": f"=Data!$A$2:$A${len(rows)}",
                    "values": f"=Data!$B$2:$B${len(rows)}",
                })
                chart.set_title({"name": parameters.get("chart_title", "Sales Chart")})
                worksheet.insert_chart("D2", chart)
                workbook.close()

                return {
                    "success": True,
                    "action": action_name,
                    "output_file": str(output_excel),
                    "rows_processed": len(rows),
                    "verified": output_excel.exists(),
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": f"Unknown Excel action '{action_name}'"}


class PowerPointAdapter(ApplicationAdapter):
    """Specialized adapter for Microsoft PowerPoint and slide review."""

    @property
    def name(self) -> str:
        return "Microsoft PowerPoint Adapter"

    @property
    def supported_processes(self) -> List[str]:
        return ["powerpnt.exe", "powerpoint"]

    async def get_available_actions(self) -> List[str]:
        return ["review_presentation", "save_presentation", "next_slide"]

    async def execute_action(
        self, action_name: str, parameters: Dict[str, Any], context: ApplicationContext
    ) -> Dict[str, Any]:
        if action_name == "save_presentation":
            return {"success": True, "hotkey": ["ctrl", "s"], "action": action_name}

        if action_name == "next_slide":
            return {"success": True, "hotkey": ["pagedown"], "action": action_name}

        if action_name == "review_presentation":
            pptx_path = Path(parameters.get("presentation_path", ""))
            if not pptx_path.exists():
                return {"success": False, "error": f"Presentation '{pptx_path}' not found"}

            try:
                from pptx import Presentation

                prs = Presentation(str(pptx_path))
                issues: List[Dict[str, Any]] = []

                for idx, slide in enumerate(prs.slides, start=1):
                    shapes = list(slide.shapes)
                    texts = [s.text.strip() for s in shapes if hasattr(s, "text") and s.text.strip()]

                    # Check 1: Slide without title or text
                    if not texts:
                        issues.append({
                            "slide_number": idx,
                            "type": "EMPTY_SLIDE",
                            "message": f"Slide {idx} appears completely blank.",
                        })

                    # Check 2: Potential overlapping text shapes
                    if len(shapes) > 15:
                        issues.append({
                            "slide_number": idx,
                            "type": "CLUTTERED_LAYOUT",
                            "message": f"Slide {idx} contains {len(shapes)} shapes; high visual clutter.",
                        })

                return {
                    "success": True,
                    "action": action_name,
                    "slide_count": len(prs.slides),
                    "issues_found": len(issues),
                    "issues": issues,
                    "verified": True,
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": f"Unknown PowerPoint action '{action_name}'"}


class WordAdapter(ApplicationAdapter):
    """Specialized adapter for Microsoft Word."""

    @property
    def name(self) -> str:
        return "Microsoft Word Adapter"

    @property
    def supported_processes(self) -> List[str]:
        return ["winword.exe", "word"]

    async def get_available_actions(self) -> List[str]:
        return ["save_document", "print_document", "select_all"]

    async def execute_action(
        self, action_name: str, parameters: Dict[str, Any], context: ApplicationContext
    ) -> Dict[str, Any]:
        if action_name == "save_document":
            return {"success": True, "hotkey": ["ctrl", "s"], "action": action_name}
        if action_name == "select_all":
            return {"success": True, "hotkey": ["ctrl", "a"], "action": action_name}
        return {"success": False, "error": f"Unknown Word action '{action_name}'"}
