"""
adversarial.py

This module contains algorithms for adversarial search, specifically 
Minimax and Expectimax, used to simulate a game between the agent and a ghost.

*MULTIPLE PATH PREDICTION:*
These algorithms have been updated to return the "Principal Variation" (a multiple-path sequence). 
Instead of just returning the immediate next best move, they return a list of predicted optimal moves 
that the agent and ghost expect to follow, assuming both play optimally (or stochastically for Expectimax).
"""

import math
from typing import Tuple, List, Optional
from core.maze import Maze, State, DIRECTIONS

def precompute_goal_distances(maze: Maze) -> List[List[float]]:
    """
    Computes a static map of true BFS distances from every cell to the goal.
    This gives the agent a flawless heuristic for reaching the goal instead of Manhattan distance.
    """
    rows, cols = maze.rows, maze.cols
    dist_map = [[math.inf]*cols for _ in range(rows)]
    
    gr, gc = maze.goal.row, maze.goal.col
    dist_map[gr][gc] = 0.0
    queue = [(gr, gc, 0.0)]
    visited = set([(gr, gc)])
    
    while queue:
        r, c, d = queue.pop(0)
        for dr, dc in DIRECTIONS.values():
            nr, nc = r + dr, c + dc
            if maze.in_bounds((nr, nc)) and maze.grid[nr][nc] != maze.WALL and (nr, nc) not in visited:
                visited.add((nr, nc))
                dist_map[nr][nc] = d + 1.0
                queue.append((nr, nc, d + 1.0))
                
    return dist_map

def get_bfs_dist(maze: Maze, start: Tuple[int, int], goal: Tuple[int, int]) -> float:
    """
    Computes the shortest path distance between start and goal.
    Used to calculate true distance between ghost and agent dynamically.
    """
    if start == goal: return 0.0
    queue = [(start[0], start[1], 0.0)]
    visited = set([start])
    while queue:
        r, c, d = queue.pop(0)
        for dr, dc in DIRECTIONS.values():
            nr, nc = r + dr, c + dc
            if (nr, nc) == goal:
                return d + 1.0
            if maze.in_bounds((nr, nc)) and maze.grid[nr][nc] != maze.WALL and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc, d + 1.0))
    return math.inf

def state_evaluation(maze: Maze, agent: Tuple[int, int], ghost: Tuple[int, int], goal_dist_map: List[List[float]]) -> float:
    """
    Evaluates a state for the agent.
    Higher values are better for the agent (Max) and worse for the ghost (Min).
    """
    ar, ac = agent
    
    # Terminal conditions
    if agent == ghost:
        return -10000.0  # Ghost catches agent (lose)
    if agent == maze.goal.as_tuple():
        return 10000.0  # Agent reaches goal (win)

    # True pathfinding distances
    dist_to_goal = goal_dist_map[ar][ac]
    
    # If the agent is unreachable to the goal (blocked), fallback to heavy penalty
    if dist_to_goal == math.inf:
        dist_to_goal = 1000.0
        
    dist_to_ghost = get_bfs_dist(maze, agent, ghost)
    if dist_to_ghost == math.inf:
        dist_to_ghost = 1000.0

    # Weight costs of the current cell to penalize mud/water path choices slightly
    cell_val = maze.grid[ar][ac]
    cost_penalty = 0.0
    if cell_val == 2:
        cost_penalty = 2.0
    elif cell_val == 3:
        cost_penalty = 5.0

    # Utility formula: minimize distance to goal, maximize distance to ghost, penalize terrain cost
    if dist_to_ghost <= 3:
        # High evasion priority
        return -5.0 * dist_to_goal + 20.0 * dist_to_ghost - cost_penalty
    else:
        # Standard navigation priority
        return -10.0 * dist_to_goal + 1.0 * dist_to_ghost - cost_penalty

def get_successors(maze: Maze, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Returns valid neighboring positions (not walls)."""
    r, c = pos
    successors = []
    # Always include option to stand still in adversarial games (evade ghost or wait)
    successors.append(pos)
    for dr, dc in DIRECTIONS.values():
        nr, nc = r + dr, c + dc
        if maze.in_bounds((nr, nc)) and maze.grid[nr][nc] != maze.WALL:
            successors.append((nr, nc))
    return successors

def minimax(
    maze: Maze,
    agent: Tuple[int, int],
    ghost: Tuple[int, int],
    depth: int,
    is_max: bool,
    goal_dist_map: List[List[float]],
    alpha: float = -math.inf,
    beta: float = math.inf
) -> Tuple[float, List[Tuple[int, int]]]:
    """
    Minimax search with Alpha-Beta pruning.
    Returns: (eval_value, best_action_path)
    """
    # Base cases
    if depth == 0 or agent == ghost or agent == maze.goal.as_tuple():
        return state_evaluation(maze, agent, ghost, goal_dist_map), []

    best_path = []

    if is_max:
        max_eval = -math.inf
        for next_agent in get_successors(maze, agent):
            eval_val, path = minimax(maze, next_agent, ghost, depth - 1, False, goal_dist_map, alpha, beta)
            if eval_val > max_eval:
                max_eval = eval_val
                best_path = [next_agent] + path
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break  # Beta pruning
        return max_eval, best_path
    else:
        min_eval = math.inf
        for next_ghost in get_successors(maze, ghost):
            # Ghost makes its move. Evaluate next state with depth reduced, switching to agent's turn (Max)
            eval_val, path = minimax(maze, agent, next_ghost, depth - 1, True, goal_dist_map, alpha, beta)
            if eval_val < min_eval:
                min_eval = eval_val
                best_path = [next_ghost] + path
            beta = min(beta, eval_val)
            if beta <= alpha:
                break  # Alpha pruning
        return min_eval, best_path

def expectimax(
    maze: Maze,
    agent: Tuple[int, int],
    ghost: Tuple[int, int],
    depth: int,
    is_max: bool,
    goal_dist_map: List[List[float]]
) -> Tuple[float, List[Tuple[int, int]]]:
    """
    Expectimax search. Agent acts optimally (Max), Ghost moves stochastically.
    Ghost behavior:
      - 70% chance to take the move that strictly minimizes distance to the agent.
      - 30% chance to distribute uniformly over all valid neighbors.
    Returns: (expected_utility, best_action_path)
    """
    if depth == 0 or agent == ghost or agent == maze.goal.as_tuple():
        return state_evaluation(maze, agent, ghost, goal_dist_map), []

    best_path = []

    if is_max:
        max_eval = -math.inf
        for next_agent in get_successors(maze, agent):
            eval_val, path = expectimax(maze, next_agent, ghost, depth - 1, False, goal_dist_map)
            if eval_val > max_eval:
                max_eval = eval_val
                best_path = [next_agent] + path
        return max_eval, best_path
    else:
        # Stochastic Ghost turn
        successors = get_successors(maze, ghost)
        if not successors:
            return expectimax(maze, agent, ghost, depth - 1, True, goal_dist_map)

        # 1. Identify move that minimizes true BFS distance to agent (chase move)
        chase_move = min(successors, key=lambda p: get_bfs_dist(maze, p, agent))

        # 2. Formulate probability distribution
        # 70% weight to chase_move
        # 30% weight divided uniformly among all valid neighbors (including chase_move)
        probs = {}
        for s in successors:
            probs[s] = 0.3 / len(successors)
        probs[chase_move] += 0.7

        # 3. Calculate expected value
        expected_val = 0.0
        best_child_path = []
        for s in successors:
            eval_val, path = expectimax(maze, agent, s, depth - 1, True, goal_dist_map)
            expected_val += probs[s] * eval_val
            if s == chase_move:
                best_child_path = path

        # Best move for ghost (from ghost's local perspective of minimizing, though we return expectation)
        best_path = [chase_move] + best_child_path
        return expected_val, best_path
