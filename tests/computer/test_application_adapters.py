"""
Unit tests for Phase 17 Application Adapters (VS Code, Explorer, Excel, PowerPoint, Generic Fallback).
"""

from pathlib import Path
import pytest
from core.computer.adapters import (
    create_default_adapter_registry,
    VSCodeAdapter,
    ExplorerAdapter,
    ExcelAdapter,
    PowerPointAdapter,
    GenericApplicationFallback,
)
from core.computer.models import ApplicationContext


@pytest.mark.asyncio
async def test_adapter_registry_resolution():
    registry = create_default_adapter_registry()

    vscode_adapter = registry.resolve_adapter("code.exe", "VS Code - Project")
    assert isinstance(vscode_adapter, VSCodeAdapter)

    explorer_adapter = registry.resolve_adapter("explorer.exe", "File Explorer")
    assert isinstance(explorer_adapter, ExplorerAdapter)

    unknown_adapter = registry.resolve_adapter("custom_game.exe", "MyGame 3D")
    assert isinstance(unknown_adapter, GenericApplicationFallback)


@pytest.mark.asyncio
async def test_vscode_adapter_actions():
    adapter = VSCodeAdapter()
    ctx = ApplicationContext(app_name="VSCode")

    res = await adapter.execute_action("open_file", {"filename": "main.py"}, ctx)
    assert res["success"] is True
    assert len(res["sequence"]) == 3
    assert res["sequence"][0]["keys"] == ["ctrl", "p"]


@pytest.mark.asyncio
async def test_explorer_organization_preview(tmp_path: Path):
    adapter = ExplorerAdapter()
    ctx = ApplicationContext(app_name="Explorer")

    # Create dummy files
    (tmp_path / "doc1.pdf").write_text("dummy")
    (tmp_path / "image1.png").write_text("dummy")
    (tmp_path / "archive1.zip").write_text("dummy")

    # Propose organization
    res = await adapter.execute_action("propose_organization", {"directory": str(tmp_path)}, ctx)
    assert res["success"] is True
    assert res["preview_required"] is True
    assert res["total_files"] == 3
    assert "Documents" in res["planned_directories"]
    assert "Images" in res["planned_directories"]
    assert "Archives" in res["planned_directories"]


@pytest.mark.asyncio
async def test_excel_adapter_chart_generation(tmp_path: Path):
    adapter = ExcelAdapter()
    ctx = ApplicationContext(app_name="Excel")

    csv_file = tmp_path / "sales.csv"
    csv_file.write_text("Month,Sales\nJan,1000\nFeb,1500\nMar,2000\n")
    output_excel = tmp_path / "sales_chart.xlsx"

    res = await adapter.execute_action(
        "insert_chart_from_csv",
        {"csv_path": str(csv_file), "output_excel": str(output_excel), "chart_title": "Q1 Sales"},
        ctx,
    )
    assert res["success"] is True
    assert res["verified"] is True
    assert output_excel.exists()
