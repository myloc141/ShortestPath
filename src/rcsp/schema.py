"""Shared data structures for resource-constrained shortest-path (RCSP) tools."""

from __future__ import annotations

from dataclasses import dataclass

from ..network.schema import Network


@dataclass(frozen=True)
class EdgeResource:
    """A resource consumption value attached to one canonical network edge."""

    edge_id: str
    value: float


@dataclass(frozen=True)
class RCSPProblem:
    """A distance-minimization problem with one bounded additive resource."""

    network: Network
    edge_resources: tuple[EdgeResource, ...]
    resource_unit: str


@dataclass(frozen=True)
class ResourceArc:
    """Directed arc representation of a network edge and its two costs."""

    u: str
    v: str
    edge_id: str
    distance: float
    resource: float


@dataclass(frozen=True)
class RCSPResult:
    """Result from an RCSP solver; absent paths indicate no feasible route."""

    status: str
    source: str
    target: str
    resource_limit: float | None
    path: tuple[str, ...] | None
    total_distance: float | None
    total_resource: float | None
    selected_arcs: tuple[tuple[str, str], ...] = ()

    @property
    def is_optimal(self) -> bool:
        return self.status == "Optimal" and self.path is not None


@dataclass(frozen=True)
class BruteForceResult:
    """Exhaustive RCSP result, including all tied optimal simple paths."""

    status: str
    source: str
    target: str
    resource_limit: float | None
    best_distance: float | None
    best_paths: tuple[tuple[str, ...], ...]
    n_paths_total: int
    n_paths_feasible: int


@dataclass(frozen=True)
class SolutionVerification:
    """Individual invariant checks for one returned RCSP solution."""

    checks: tuple[tuple[str, bool], ...]

    @property
    def is_valid(self) -> bool:
        return all(value for _, value in self.checks)


@dataclass(frozen=True)
class RCSPCrossCheck:
    """Comparison of a solver result with exhaustive enumeration."""

    solver_result: RCSPResult
    brute_force_result: BruteForceResult
    objective_matches: bool
    path_is_brute_force_optimal: bool

    @property
    def matches(self) -> bool:
        return self.objective_matches and self.path_is_brute_force_optimal
