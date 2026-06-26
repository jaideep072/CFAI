"""
hybrid.py

This module integrates different components (search, probabilistic tracking, and CSP)
into a Hybrid Decision cycle. It helps the agent decide whether to take a direct path 
or a detour based on calculated expected utility and risk tolerance.
"""

import math
from typing import List, Tuple, Dict, Any, Optional
from core.maze import Maze, State, Cell
from algorithms.search import astar, bfs
from csp.csp_solver import waypoint_scheduling_csp, backtrack

def compute_path_probability_of_capture(path: List[Cell], belief: List[List[float]]) -> float:
    """
    Computes the joint probability of capture along a path.
    Assumes independence of cell occupation: P(safe) = Product_over_path (1 - P(ghost_at_c))
    P(capture) = 1 - P(safe)
    """
    p_safe = 1.0
    for r, c in path:
        p_ghost = belief[r][c]
        p_safe *= (1.0 - p_ghost)
    
    # Return probability of capture
    return 1.0 - p_safe

class RiskMaze(Maze):
    """A custom maze that applies pathfinding penalties based on ghost belief probabilities."""
    def __init__(self, grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int], ghost_belief: List[List[float]]):
        super().__init__(grid, start=start, goal=goal)
        self.ghost_belief = ghost_belief
        
    def successors(self, state: State) -> List[Tuple[str, State, float]]:
        succs = super().successors(state)
        res = []
        for action, nxt, cost in succs:
            r, c = nxt.as_tuple()
            # Apply a heavy penalty based on ghost probability to force A* to find safer routes
            penalty = self.ghost_belief[r][c] * 500.0
            res.append((action, nxt, cost + penalty))
        return res

def hybrid_decide(
    maze: Maze,
    agent_pos: Tuple[int, int],
    ghost_belief: List[List[float]],
    risk_tolerance: float = 0.5
) -> Dict[str, Any]:
    """
    Executes a hybrid decision cycle:
    1. Generates candidate paths (Direct vs Detour).
    2. Evaluates expected utility based on path cost and ghost capture risk.
    3. Schedules path checkpoints using CSP.
    4. Outputs a step-by-step explainable reasoning trace.
    """
    # Helper: calculate path cost
    def path_cost(path: List[Cell]) -> float:
        cost = 0.0
        for i in range(len(path) - 1):
            r, c = path[i+1]
            cell_val = maze.grid[r][c]
            if cell_val == 2:
                cost += 3.0
            elif cell_val == 3:
                cost += 6.0
            else:
                cost += 1.0
        return cost

    # Candidate 1: Direct Path (Standard A* on the current grid)
    # Temporary set start/goal to local agent/goal positions
    local_maze = Maze(maze.grid, start=agent_pos, goal=maze.goal.as_tuple())
    astar_stats = astar(local_maze, h="manhattan")
    path_direct = astar_stats.path if astar_stats.solved else []
    
    # Candidate 2: Detour Path (A* penalizing cells based on ghost belief)
    detour_maze = RiskMaze(maze.grid, start=agent_pos, goal=maze.goal.as_tuple(), ghost_belief=ghost_belief)
    detour_stats = astar(detour_maze, h="manhattan")
    path_detour = detour_stats.path if detour_stats.solved else []
    
    # If no detour path is found, fall back to BFS path as a secondary alternative
    if not path_detour:
        bfs_stats = bfs(local_maze)
        path_detour = bfs_stats.path if bfs_stats.solved else []

    # Expected Utility Calculation
    # U(success) = 100 - PathCost
    # U(capture) = -500
    # Expected Utility = P(safe) * U(success) + P(capture) * U(capture)
    # We scale the capture penalty by (1 - risk_tolerance)
    
    # Direct Path Evaluation
    cost_direct = path_cost(path_direct) if path_direct else float('inf')
    p_capture_direct = compute_path_probability_of_capture(path_direct, ghost_belief) if path_direct else 1.0
    u_success_direct = max(0.0, 100.0 - cost_direct)
    u_capture_scaled = -500.0 * (1.0 - risk_tolerance)
    eu_direct = (1.0 - p_capture_direct) * u_success_direct + p_capture_direct * u_capture_scaled if path_direct else -999.0
    
    # Detour Path Evaluation
    cost_detour = path_cost(path_detour) if path_detour else float('inf')
    p_capture_detour = compute_path_probability_of_capture(path_detour, ghost_belief) if path_detour else 1.0
    u_success_detour = max(0.0, 100.0 - cost_detour)
    eu_detour = (1.0 - p_capture_detour) * u_success_detour + p_capture_detour * u_capture_scaled if path_detour else -999.0

    # Decision Selection
    selected_path = path_direct
    selected_type = "Direct Path"
    reason = "Direct path chosen because risk is low or risk tolerance is high."

    if path_detour and eu_detour > eu_direct:
        selected_path = path_detour
        selected_type = "Detour Path"
        reason = "Detour path chosen because direct path has high capture risk and agent is risk-averse."
    elif not path_direct:
        selected_path = path_detour
        selected_type = "Detour Path (Fallback)"
        reason = "Direct path is blocked or unavailable. Falling back to detour path."

    # CSP Waypoint Scheduling along the selected path
    csp_success = False
    schedule = {}
    waypoints = []
    
    if len(selected_path) >= 3:
        # Convert path cells to string names for CSP variables
        cell_names = [f"cell_{r}_{c}" for r, c in selected_path]
        # Select checkpoints along the path (e.g. start, middle, end)
        waypoints = [cell_names[0], cell_names[len(cell_names)//2], cell_names[-1]]
        # Remove duplicates
        waypoints = list(dict.fromkeys(waypoints))
        
        time_slots = len(waypoints) + 2
        sched_csp = waypoint_scheduling_csp(waypoints, time_slots=time_slots)
        sched_result = backtrack(sched_csp, use_mrv=True, use_lcv=True, use_fc=True)
        if sched_result:
            csp_success = True
            schedule = sched_result

    # Explainable Trace Log
    trace = [
        "=== HYBRID DECISION CYCLE STATE ===",
        f"Agent Position: {agent_pos}",
        f"Risk Tolerance setting: {risk_tolerance:.2f} (0=Averse, 1=Tolerant)",
        "",
        "--- Candidate Path Evaluations ---",
        f"1. Direct Path:",
        f"   - Path: {path_direct[:4]}... ({len(path_direct)} cells)" if path_direct else "   - No path found",
        f"   - Total Cost: {cost_direct:.1f}",
        f"   - Capture Probability: {p_capture_direct * 100:.1f}%",
        f"   - Utility on Success: {u_success_direct:.1f}",
        f"   - Expected Utility: {eu_direct:.2f}",
        "",
        f"2. Safe Detour Path:",
        f"   - Path: {path_detour[:4]}... ({len(path_detour)} cells)" if path_detour else "   - No path found",
        f"   - Total Cost: {cost_detour:.1f}",
        f"   - Capture Probability: {p_capture_detour * 100:.1f}%",
        f"   - Utility on Success: {u_success_detour:.1f}",
        f"   - Expected Utility: {eu_detour:.2f}",
        "",
        "--- Decision Logic ---",
        f"Decision selection: {selected_type}",
        f"Rationale: {reason}",
        "",
        "--- CSP Waypoint Checkpoint Scheduling ---"
    ]
    if csp_success:
        trace.append(f"Checkpoints Scheduled Successfully: {waypoints}")
        for wp, slot in schedule.items():
            trace.append(f"  - Checkpoint {wp} scheduled at Time T_{slot}")
    else:
        trace.append("Waypoint scheduling bypassed or failed (path too short or constraints unsatisfied).")

    return {
        "selected_path": selected_path,
        "selected_type": selected_type,
        "cost": cost_direct if selected_type == "Direct Path" else cost_detour,
        "capture_probability": p_capture_direct if selected_type == "Direct Path" else p_capture_detour,
        "expected_utility": eu_direct if selected_type == "Direct Path" else eu_detour,
        "csp_success": csp_success,
        "schedule": schedule,
        "trace": trace
    }
