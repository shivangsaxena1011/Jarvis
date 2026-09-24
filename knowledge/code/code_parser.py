"""
SHIVANI AST Code Parser
Extracts semantic code symbols (Classes, Functions, Methods, Calls, Imports)
using Python's standard library `ast` and pattern recognition for other languages.
"""

import ast
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

from knowledge.models import CodeSymbol, CodeSymbolType


class CodeParser:
    """Parses source code into semantic CodeSymbol definitions."""

    def parse_file(self, file_path: str, project_id: Optional[str] = None) -> List[CodeSymbol]:
        """Parses a code file and returns its symbols."""
        p = Path(file_path).resolve()
        if not p.is_file():
            return []

        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        ext = p.suffix.lower()
        if ext == ".py":
            return self.parse_python(content, str(p), project_id=project_id)
        elif ext in (".js", ".ts", ".jsx", ".tsx"):
            return self.parse_javascript_typescript(content, str(p), project_id=project_id)
        elif ext in (".java", ".kt"):
            return self.parse_jvm_languages(content, str(p), project_id=project_id)
        else:
            return []

    def parse_python(
        self,
        source_code: str,
        file_path: str,
        project_id: Optional[str] = None,
    ) -> List[CodeSymbol]:
        """Uses Python's native AST module to extract deep code symbols."""
        symbols: List[CodeSymbol] = []
        try:
            tree = ast.parse(source_code, filename=file_path)
        except Exception:
            # Fall back to regex if file has Python syntax errors
            return self._parse_python_regex_fallback(source_code, file_path, project_id)

        # Global imports in file
        file_imports: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    file_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    file_imports.append(f"{mod}.{alias.name}" if mod else alias.name)

        # Top-level module symbol
        symbols.append(
            CodeSymbol(
                project_id=project_id,
                file_path=file_path,
                name=Path(file_path).stem,
                symbol_type=CodeSymbolType.MODULE,
                signature=f"module {Path(file_path).name}",
                docstring=ast.get_docstring(tree) or "",
                line_start=1,
                line_end=len(source_code.splitlines()) or 1,
                imports=file_imports,
            )
        )

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sym = self._extract_python_function(node, file_path, project_id, parent_symbol=None)
                symbols.append(sym)
            elif isinstance(node, ast.ClassDef):
                cls_sym = self._extract_python_class(node, file_path, project_id)
                symbols.append(cls_sym)
                # Methods
                for sub_node in node.body:
                    if isinstance(sub_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_sym = self._extract_python_function(
                            sub_node, file_path, project_id, parent_symbol=cls_sym.name
                        )
                        method_sym.symbol_type = CodeSymbolType.METHOD
                        symbols.append(method_sym)

        return symbols

    def _extract_python_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: str,
        project_id: Optional[str],
        parent_symbol: Optional[str],
    ) -> CodeSymbol:
        # Build signature string
        args_list: List[str] = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                try:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                except Exception:
                    pass
            args_list.append(arg_str)

        ret_str = ""
        if node.returns:
            try:
                ret_str = f" -> {ast.unparse(node.returns)}"
            except Exception:
                pass

        prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
        sig = f"{prefix}{node.name}({', '.join(args_list)}){ret_str}"

        # Extract calls inside function
        calls: List[str] = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                try:
                    called_name = ast.unparse(child.func)
                    calls.append(called_name)
                except Exception:
                    pass

        line_end = getattr(node, "end_lineno", node.lineno)
        return CodeSymbol(
            project_id=project_id,
            file_path=file_path,
            name=f"{parent_symbol}.{node.name}" if parent_symbol else node.name,
            symbol_type=CodeSymbolType.FUNCTION,
            signature=sig,
            docstring=ast.get_docstring(node) or "",
            line_start=node.lineno,
            line_end=line_end,
            calls=calls,
            parent_symbol=parent_symbol,
        )

    def _extract_python_class(
        self,
        node: ast.ClassDef,
        file_path: str,
        project_id: Optional[str],
    ) -> CodeSymbol:
        bases: List[str] = []
        for b in node.bases:
            try:
                bases.append(ast.unparse(b))
            except Exception:
                pass

        base_str = f"({', '.join(bases)})" if bases else ""
        sig = f"class {node.name}{base_str}"

        line_end = getattr(node, "end_lineno", node.lineno)
        return CodeSymbol(
            project_id=project_id,
            file_path=file_path,
            name=node.name,
            symbol_type=CodeSymbolType.CLASS,
            signature=sig,
            docstring=ast.get_docstring(node) or "",
            line_start=node.lineno,
            line_end=line_end,
            metadata={"bases": bases},
        )

    def _parse_python_regex_fallback(
        self,
        source_code: str,
        file_path: str,
        project_id: Optional[str],
    ) -> List[CodeSymbol]:
        symbols: List[CodeSymbol] = []
        lines = source_code.splitlines()
        func_re = re.compile(r"^\s*(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\((.*?)\)", re.MULTILINE)
        class_re = re.compile(r"^\s*class\s+([a-zA-Z0-9_]+)(?:\((.*?)\))?:", re.MULTILINE)

        for match in class_re.finditer(source_code):
            cname = match.group(1)
            line_no = source_code[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    project_id=project_id,
                    file_path=file_path,
                    name=cname,
                    symbol_type=CodeSymbolType.CLASS,
                    signature=match.group(0).strip(),
                    line_start=line_no,
                    line_end=line_no + 1,
                )
            )

        for match in func_re.finditer(source_code):
            fname = match.group(1)
            line_no = source_code[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    project_id=project_id,
                    file_path=file_path,
                    name=fname,
                    symbol_type=CodeSymbolType.FUNCTION,
                    signature=match.group(0).strip(),
                    line_start=line_no,
                    line_end=line_no + 1,
                )
            )
        return symbols

    def parse_javascript_typescript(
        self,
        source_code: str,
        file_path: str,
        project_id: Optional[str],
    ) -> List[CodeSymbol]:
        """Regex-based symbol extractor for JS/TS."""
        symbols: List[CodeSymbol] = []
        func_re = re.compile(r"(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\((.*?)\)")
        class_re = re.compile(r"(?:export\s+)?class\s+([a-zA-Z0-9_]+)(?:\s+extends\s+([a-zA-Z0-9_]+))?")
        arrow_re = re.compile(r"(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>")

        for m in class_re.finditer(source_code):
            line_no = source_code[: m.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    project_id=project_id,
                    file_path=file_path,
                    name=m.group(1),
                    symbol_type=CodeSymbolType.CLASS,
                    signature=m.group(0).strip(),
                    line_start=line_no,
                    line_end=line_no + 1,
                )
            )

        for m in func_re.finditer(source_code):
            line_no = source_code[: m.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    project_id=project_id,
                    file_path=file_path,
                    name=m.group(1),
                    symbol_type=CodeSymbolType.FUNCTION,
                    signature=m.group(0).strip(),
                    line_start=line_no,
                    line_end=line_no + 1,
                )
            )

        for m in arrow_re.finditer(source_code):
            line_no = source_code[: m.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    project_id=project_id,
                    file_path=file_path,
                    name=m.group(1),
                    symbol_type=CodeSymbolType.FUNCTION,
                    signature=f"const {m.group(1)} = ({m.group(2)}) => ...",
                    line_start=line_no,
                    line_end=line_no + 1,
                )
            )

        return symbols

    def parse_jvm_languages(
        self,
        source_code: str,
        file_path: str,
        project_id: Optional[str],
    ) -> List[CodeSymbol]:
        """Regex-based symbol extractor for Java and Kotlin."""
        symbols: List[CodeSymbol] = []
        class_re = re.compile(r"(?:public\s+|private\s+|protected\s+)?(?:final\s+|abstract\s+)?class\s+([a-zA-Z0-9_]+)")
        fun_re = re.compile(r"(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:[a-zA-Z0-9_<>,\[\]]+\s+)([a-zA-Z0-9_]+)\s*\((.*?)\)\s*\{")

        for m in class_re.finditer(source_code):
            line_no = source_code[: m.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    project_id=project_id,
                    file_path=file_path,
                    name=m.group(1),
                    symbol_type=CodeSymbolType.CLASS,
                    signature=m.group(0).strip(),
                    line_start=line_no,
                    line_end=line_no + 1,
                )
            )

        for m in fun_re.finditer(source_code):
            line_no = source_code[: m.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    project_id=project_id,
                    file_path=file_path,
                    name=m.group(1),
                    symbol_type=CodeSymbolType.FUNCTION,
                    signature=m.group(0).strip(),
                    line_start=line_no,
                    line_end=line_no + 1,
                )
            )

        return symbols
