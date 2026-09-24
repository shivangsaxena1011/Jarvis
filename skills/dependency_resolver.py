"""
SHIVANI Skill Dependency Resolver
Resolves dependency graphs, detects missing prerequisites, prevents circular dependencies,
and computes optimal skill installation / initialization order.
"""

from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from skills.manifest import SkillManifest


class DependencyResolutionResult(BaseModel):
    is_valid: bool
    install_order: List[str] = Field(default_factory=list)
    missing_dependencies: List[str] = Field(default_factory=list)
    cyclic_dependencies: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class DependencyResolver:
    """Computes topological dependency ordering and detects graph cycles."""

    CORE_CAPABILITIES = {
        "browser",
        "computer",
        "phone",
        "filesystem",
        "terminal",
        "knowledge",
        "memory",
        "planning",
        "vision",
        "audio",
        "research",
        "presentation",
        "github",
        "gmail",
    }

    def __init__(self, available_manifests: Optional[Dict[str, SkillManifest]] = None):
        self.manifests: Dict[str, SkillManifest] = available_manifests or {}

    def register_manifest(self, manifest: SkillManifest) -> None:
        self.manifests[manifest.name] = manifest

    def check_missing_dependencies(self, skill_name: str) -> List[str]:
        """Returns list of dependencies that are neither installed skills nor core capabilities."""
        manifest = self.manifests.get(skill_name)
        if not manifest:
            return [f"Skill '{skill_name}' not found in registry."]

        missing = []
        for dep in manifest.dependencies:
            clean_dep = dep.split(">=")[0].split("<")[0].split("==")[0].strip()
            if clean_dep not in self.CORE_CAPABILITIES and clean_dep not in self.manifests:
                missing.append(dep)
        return missing

    def detect_cycles(self) -> Optional[List[str]]:
        """
        Detects circular dependencies across registered skills using DFS cycle detection.
        Returns the cycle path if found, or None.
        """
        adj: Dict[str, List[str]] = defaultdict(list)
        for name, m in self.manifests.items():
            for dep in m.dependencies:
                clean_dep = dep.split(">=")[0].split("<")[0].split("==")[0].strip()
                if clean_dep in self.manifests:
                    adj[name].append(clean_dep)

        visited: Dict[str, int] = {}  # 0 = unvisited, 1 = visiting, 2 = visited
        path: List[str] = []

        def dfs(node: str) -> Optional[List[str]]:
            visited[node] = 1
            path.append(node)

            for neighbor in adj.get(node, []):
                if visited.get(neighbor, 0) == 1:
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]
                elif visited.get(neighbor, 0) == 0:
                    found = dfs(neighbor)
                    if found:
                        return found

            path.pop()
            visited[node] = 2
            return None

        for node in self.manifests:
            if visited.get(node, 0) == 0:
                cycle = dfs(node)
                if cycle:
                    return cycle

        return None

    def resolve(self, target_skills: Optional[List[str]] = None) -> DependencyResolutionResult:
        """Resolves dependencies and returns a structured DependencyResolutionResult."""
        targets = target_skills or list(self.manifests.keys())
        is_valid, order, errors = self.resolve_install_order(targets)

        missing_deps: List[str] = []
        cycle_deps: List[str] = []
        for err in errors:
            if "missing" in err.lower():
                missing_deps.append(err)
            elif "circular" in err.lower() or "cycle" in err.lower():
                cycle_deps.append(err)

        return DependencyResolutionResult(
            is_valid=is_valid,
            install_order=order,
            missing_dependencies=missing_deps,
            cyclic_dependencies=cycle_deps,
            errors=errors,
        )

    def resolve_install_order(self, skill_names: List[str]) -> Tuple[bool, List[str], List[str]]:
        """
        Computes topological installation order for requested skills.
        Returns (success, order_list, errors).
        """
        errors: List[str] = []

        # Check for cycles
        cycle = self.detect_cycles()
        if cycle:
            return False, [], [f"Circular dependency detected: {' -> '.join(cycle)}"]

        # Check missing dependencies
        needed_skills: Set[str] = set()
        queue = deque(skill_names)
        while queue:
            curr = queue.popleft()
            if curr in needed_skills:
                continue
            if curr in self.manifests:
                needed_skills.add(curr)
                missing = self.check_missing_dependencies(curr)
                if missing:
                    errors.append(f"Skill '{curr}' has missing dependencies: {', '.join(missing)}")
                for dep in self.manifests[curr].dependencies:
                    clean_dep = dep.split(">=")[0].split("<")[0].split("==")[0].strip()
                    if clean_dep in self.manifests and clean_dep not in needed_skills:
                        queue.append(clean_dep)
            elif curr not in self.CORE_CAPABILITIES:
                errors.append(f"Required dependency '{curr}' is not available.")

        if errors:
            return False, [], errors

        # Topological sort via Kahn's algorithm
        in_degree: Dict[str, int] = {s: 0 for s in needed_skills}
        adj: Dict[str, List[str]] = defaultdict(list)

        for s in needed_skills:
            m = self.manifests[s]
            for dep in m.dependencies:
                clean_dep = dep.split(">=")[0].split("<")[0].split("==")[0].strip()
                if clean_dep in needed_skills:
                    adj[clean_dep].append(s)
                    in_degree[s] += 1

        zero_in = deque([s for s, deg in in_degree.items() if deg == 0])
        order: List[str] = []

        while zero_in:
            node = zero_in.popleft()
            order.append(node)
            for succ in adj[node]:
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    zero_in.append(succ)

        if len(order) != len(needed_skills):
            return False, [], ["Failed to resolve complete topological ordering."]

        return True, order, []
