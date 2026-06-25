"""
csp_solver.py

This module contains the implementation of a Constraint Satisfaction Problem (CSP)
solver. It provides generic CSP representation and algorithms like Backtracking 
with MRV, LCV, and Forward Checking, as well as Local Search (Min-Conflicts).
It also includes specific problem formulations for the maze domain.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import copy
import random

Variable = str                                  
Value    = Any

@dataclass
class CSP:
    variables:   List[Variable]
    domains:     Dict[Variable, List[Value]]
    constraints: List[Tuple[Variable, Variable, Callable[[Value, Value], bool]]]

    def is_consistent(
        self,
        var: Variable,
        val: Value,
        assignment: Dict[Variable, Value],
    ) -> Tuple[bool, Optional[str]]:
        for x, y, pred in self.constraints:
            if x == var and y in assignment:
                if not pred(val, assignment[y]):
                    return False, f"Constraint ({x}={val} ~ {y}={assignment[y]}) VIOLATED"
            elif y == var and x in assignment:
                if not pred(assignment[x], val):
                    return False, f"Constraint ({x}={assignment[x]} ~ {y}={val}) VIOLATED"
        return True, None

    def neighbours(self, var: Variable) -> Set[Variable]:
        nbrs = set()
        for x, y, _ in self.constraints:
            if x == var: nbrs.add(y)
            if y == var: nbrs.add(x)
        return nbrs

def select_unassigned_mrv_degree(
    csp: CSP,
    assignment: Dict[Variable, Value],
    domains: Dict[Variable, List[Value]],
) -> Variable:
    unassigned = [v for v in csp.variables if v not in assignment]
    def score(v):
        mrv    = len(domains[v])
        degree = -len([n for n in csp.neighbours(v) if n not in assignment])
        return (mrv, degree)
    return min(unassigned, key=score)

def order_values_lcv(
    csp: CSP,
    var: Variable,
    assignment: Dict[Variable, Value],
    domains: Dict[Variable, List[Value]],
) -> List[Value]:
    def count_eliminated(val):
        total = 0
        for nbr in csp.neighbours(var):
            if nbr not in assignment:
                total += sum(
                    1 for nbr_val in domains[nbr]
                    if not all(
                        pred(val, nbr_val) if x == var else True
                        for x, y, pred in csp.constraints
                        if (x == var and y == nbr) or (y == var and x == nbr)
                    )
                )
        return total
    return sorted(domains[var], key=count_eliminated)

def forward_check(
    csp: CSP,
    var: Variable,
    val: Value,
    assignment: Dict[Variable, Value],
    domains: Dict[Variable, List[Value]],
) -> Tuple[bool, Dict[Variable, List[Value]], str]:
    new_domains = copy.deepcopy(domains)
    new_domains[var] = [val]

    for nbr in csp.neighbours(var):
        if nbr not in assignment:
            new_dom = []
            for nbr_val in new_domains[nbr]:
                ok, _ = csp.is_consistent(nbr, nbr_val, {**assignment, var: val})
                if ok:
                    new_dom.append(nbr_val)
            if not new_dom:
                return False, new_domains, f"Forward-check: domain of '{nbr}' wiped out when {var}={val}"
            new_domains[nbr] = new_dom

    return True, new_domains, ""

def backtrack(
    csp: CSP,
    assignment: Dict[Variable, Value] = None,
    domains: Dict[Variable, List[Value]] = None,
    use_mrv: bool = True,
    use_lcv: bool = True,
    use_fc:  bool = True,
    trace:   bool = False,
) -> Optional[Dict[Variable, Value]]:
    if assignment is None:
        assignment = {}
    if domains is None:
        domains = copy.deepcopy(csp.domains)

    if len(assignment) == len(csp.variables):
        return assignment

    if use_mrv:
        var = select_unassigned_mrv_degree(csp, assignment, domains)
    else:
        var = next(v for v in csp.variables if v not in assignment)

    values = order_values_lcv(csp, var, assignment, domains) if use_lcv else domains[var]

    for val in values:
        ok, reason = csp.is_consistent(var, val, assignment)
        if not ok:
            if trace:
                print(f"  [BT] PRUNE {var}={val} → {reason}")
            continue

        assignment[var] = val

        if use_fc:
            fc_ok, new_domains, fc_reason = forward_check(csp, var, val, assignment, domains)
        else:
            fc_ok, new_domains, fc_reason = True, domains, ""

        if fc_ok:
            if trace:
                print(f"  [BT] assign {var}={val}")
            result = backtrack(csp, assignment, new_domains, use_mrv, use_lcv, use_fc, trace)
            if result is not None:
                return result
        else:
            if trace:
                print(f"  [BT] FC fail {var}={val} → {fc_reason}")

        del assignment[var]

    return None

def min_conflicts(
    csp: CSP,
    max_steps: int = 1000,
    seed: int = 42,
    trace: bool = False,
) -> Optional[Dict[Variable, Value]]:
    rng = random.Random(seed)

    assignment: Dict[Variable, Value] = {
        v: rng.choice(csp.domains[v]) for v in csp.variables
    }

    def count_conflicts(var, val, asgn):
        count = 0
        for x, y, pred in csp.constraints:
            if x == var and y in asgn and y != var:
                if not pred(val, asgn[y]): count += 1
            elif y == var and x in asgn and x != var:
                if not pred(asgn[x], val): count += 1
        return count

    for step in range(max_steps):
                                   
        conflicted = [
            v for v in csp.variables
            if count_conflicts(v, assignment[v], assignment) > 0
        ]
        if not conflicted:
            return assignment                   

        var = rng.choice(conflicted)
        best_val = min(
            csp.domains[var],
            key=lambda v: count_conflicts(var, v, assignment)
        )
        assignment[var] = best_val
        if trace and step % 50 == 0:
            total = sum(count_conflicts(v, assignment[v], assignment) for v in csp.variables)
            print(f"  [MinConflicts] step={step} conflicts={total}")

    return None                            

def maze_path_coloring_csp(path_cells: List[str], n_colors: int = 3) -> CSP:
    variables = path_cells
    domains   = {v: list(range(n_colors)) for v in variables}
    constraints = []
    for i in range(len(path_cells) - 1):
        a, b = path_cells[i], path_cells[i + 1]
        constraints.append((a, b, lambda va, vb: va != vb))
    return CSP(variables, domains, constraints)

def waypoint_scheduling_csp(
    waypoints: List[str],
    time_slots: int = 5,
) -> CSP:
    variables = waypoints
    domains   = {v: list(range(1, time_slots + 1)) for v in variables}
    constraints = []
    for i in range(len(waypoints) - 1):
        a, b = waypoints[i], waypoints[i + 1]
                                            
        constraints.append((a, b, lambda ta, tb: ta < tb))
    return CSP(variables, domains, constraints)

def run_csp_demo(path: List[tuple], trace: bool = False):
    if len(path) < 2:
        print("Path too short for CSP demo.")
        return

    cell_names = [f"cell_{r}_{c}" for r, c in path]

    print("\n── CO3: CSP Path Coloring ──────────────────────────────────")
    csp = maze_path_coloring_csp(cell_names, n_colors=3)
    result = backtrack(csp, use_mrv=True, use_lcv=True, use_fc=True, trace=trace)
    if result:
        print(f"  Solution found: {len(set(result.values()))} colors used")
        for cell, color in list(result.items())[:5]:
            print(f"    {cell} → color {color}")
        if len(result) > 5:
            print(f"    ... ({len(result)} total)")
    else:
        print("  No solution found (increase n_colors).")

    print("\n── CO3: Waypoint Scheduling CSP ────────────────────────────")
                                       
    waypoints = cell_names[::3][:6]
    sched_csp = waypoint_scheduling_csp(waypoints, time_slots=len(waypoints) + 2)
    sched = backtrack(sched_csp, use_mrv=True, use_lcv=True, use_fc=True)
    if sched:
        print("  Schedule found:")
        for wp, slot in sched.items():
            print(f"    {wp} → time slot {slot}")
    else:
        print("  Scheduling infeasible with given slots.")

    print("\n── CO3: Min-Conflicts (local search) ───────────────────────")
    mc_csp = maze_path_coloring_csp(cell_names, n_colors=3)
    mc_result = min_conflicts(mc_csp, max_steps=2000)
    if mc_result:
        print(f"  Min-Conflicts: solution found ({len(set(mc_result.values()))} colors)")
    else:
        print("  Min-Conflicts: did not converge.")
