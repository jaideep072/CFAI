"""
search.py

This module contains various search algorithms used to solve the maze.
It implements uninformed search (BFS, DFS, Bidirectional BFS) and 
informed search (UCS, Greedy Best-First, A*, IDA*). It also includes 
benchmarking tools to evaluate the performance of these algorithms.
"""

from __future__ import annotations
import heapq
import time
from collections import deque
from typing import Callable, Dict, List, Optional, Set, Tuple

from core.maze import Maze, State, Cell, SolveStats

def heuristic_manhattan(s: State, goal: State) -> float:
    return s.manhattan(goal)

def heuristic_euclidean(s: State, goal: State) -> float:
    return ((s.row - goal.row)**2 + (s.col - goal.col)**2) ** 0.5

def heuristic_zero(s: State, goal: State) -> float:
    return 0.0

def heuristic_diagonal(s: State, goal: State) -> float:
    return max(abs(s.row - goal.row), abs(s.col - goal.col))

HEURISTICS: Dict[str, Callable] = {
    "manhattan": heuristic_manhattan,
    "euclidean": heuristic_euclidean,
    "zero":      heuristic_zero,
    "diagonal":  heuristic_diagonal,
}

def _reconstruct(came_from: Dict[State, Optional[State]], goal: State) -> List[Cell]:
    path = []
    node: Optional[State] = goal
    while node is not None:
        path.append(node.as_tuple())
        node = came_from.get(node)
    path.reverse()
    return path

def bfs(maze: Maze, trace: bool = False, callback: Optional[Callable[[State, Set[State], List[State]], None]] = None) -> SolveStats:
    t0 = time.perf_counter()
    start, goal = maze.start, maze.goal

    frontier: deque[State] = deque([start])
    came_from: Dict[State, Optional[State]] = {start: None}
    expanded = 0
    peak_frontier = 1

    while frontier:
        peak_frontier = max(peak_frontier, len(frontier))
        node = frontier.popleft()
        expanded += 1

        if trace:
            print(f"  [BFS] expanding {node.as_tuple()}")

        if callback:
            callback(node, set(came_from.keys()), list(frontier))

        if node == goal:
            path = _reconstruct(came_from, goal)
            elapsed = (time.perf_counter() - t0) * 1000
            return SolveStats("BFS", True, len(path), expanded, elapsed, peak_frontier, path)

        for _, nxt, _ in maze.successors(node):
            if nxt not in came_from:
                came_from[nxt] = node
                frontier.append(nxt)

    elapsed = (time.perf_counter() - t0) * 1000
    return SolveStats("BFS", False, 0, expanded, elapsed, peak_frontier)

def dfs(maze: Maze, trace: bool = False, callback: Optional[Callable[[State, Set[State], List[State]], None]] = None) -> SolveStats:
    t0 = time.perf_counter()
    start, goal = maze.start, maze.goal

    stack: List[Tuple[State, Optional[State]]] = [(start, None)]
    came_from: Dict[State, Optional[State]] = {}
    closed: Set[State] = set()
    expanded = 0
    peak_frontier = 1

    while stack:
        peak_frontier = max(peak_frontier, len(stack))
        node, parent = stack.pop()

        if node in closed:
            continue
        closed.add(node)
        came_from[node] = parent
        expanded += 1

        if trace:
            print(f"  [DFS] expanding {node.as_tuple()}")

        if callback:
            callback(node, closed, [item[0] for item in stack])

        if node == goal:
            path = _reconstruct(came_from, goal)
            elapsed = (time.perf_counter() - t0) * 1000
            return SolveStats("DFS", True, len(path), expanded, elapsed, peak_frontier, path)

        for _, nxt, _ in maze.successors(node):
            if nxt not in closed:
                stack.append((nxt, node))

    elapsed = (time.perf_counter() - t0) * 1000
    return SolveStats("DFS", False, 0, expanded, elapsed, peak_frontier)

def ucs(maze: Maze, trace: bool = False, callback: Optional[Callable[[State, Set[State], List[State]], None]] = None) -> SolveStats:
    t0 = time.perf_counter()
    start, goal = maze.start, maze.goal

    counter = 0
    frontier: List[Tuple[float, int, State]] = [(0.0, counter, start)]
    cost_so_far: Dict[State, float] = {start: 0.0}
    came_from: Dict[State, Optional[State]] = {start: None}
    closed: Set[State] = set()
    expanded = 0
    peak_frontier = 1

    while frontier:
        peak_frontier = max(peak_frontier, len(frontier))
        g, _, node = heapq.heappop(frontier)

        if node in closed:
            continue
        closed.add(node)
        expanded += 1

        if trace:
            print(f"  [UCS] expanding {node.as_tuple()} g={g:.1f}")

        if callback:
            callback(node, closed, [item[2] for item in frontier])

        if node == goal:
            path = _reconstruct(came_from, goal)
            elapsed = (time.perf_counter() - t0) * 1000
            return SolveStats("UCS", True, len(path), expanded, elapsed, peak_frontier, path)

        for _, nxt, step_cost in maze.successors(node):
            new_g = g + step_cost
            if nxt not in cost_so_far or new_g < cost_so_far[nxt]:
                cost_so_far[nxt] = new_g
                came_from[nxt] = node
                counter += 1
                heapq.heappush(frontier, (new_g, counter, nxt))

    elapsed = (time.perf_counter() - t0) * 1000
    return SolveStats("UCS", False, 0, expanded, elapsed, peak_frontier)

def greedy(maze: Maze, h: str = "manhattan", trace: bool = False, callback: Optional[Callable[[State, Set[State], List[State]], None]] = None) -> SolveStats:
    t0 = time.perf_counter()
    start, goal = maze.start, maze.goal
    hfn = HEURISTICS[h]

    counter = 0
    frontier: List[Tuple[float, int, State]] = [(hfn(start, goal), counter, start)]
    came_from: Dict[State, Optional[State]] = {start: None}
    closed: Set[State] = set()
    expanded = 0
    peak_frontier = 1

    while frontier:
        peak_frontier = max(peak_frontier, len(frontier))
        _, _, node = heapq.heappop(frontier)

        if node in closed:
            continue
        closed.add(node)
        expanded += 1

        if trace:
            print(f"  [Greedy] expanding {node.as_tuple()} h={hfn(node,goal):.1f}")

        if callback:
            callback(node, closed, [item[2] for item in frontier])

        if node == goal:
            path = _reconstruct(came_from, goal)
            elapsed = (time.perf_counter() - t0) * 1000
            return SolveStats(f"Greedy({h})", True, len(path), expanded, elapsed, peak_frontier, path)

        for _, nxt, _ in maze.successors(node):
            if nxt not in closed:
                came_from[nxt] = node
                counter += 1
                heapq.heappush(frontier, (hfn(nxt, goal), counter, nxt))

    elapsed = (time.perf_counter() - t0) * 1000
    return SolveStats(f"Greedy({h})", False, 0, expanded, elapsed, peak_frontier)

def astar(
    maze: Maze,
    h: str = "manhattan",
    weight: float = 1.0,
    trace: bool = False,
    callback: Optional[Callable[[State, Set[State], List[State]], None]] = None,
) -> SolveStats:
    t0 = time.perf_counter()
    start, goal = maze.start, maze.goal
    hfn = HEURISTICS[h]

    g_start = 0.0
    h_start = hfn(start, goal)
    counter = 0

    frontier: List[Tuple[float, float, int, State]] = [
        (g_start + weight * h_start, h_start, counter, start)
    ]
    g_score: Dict[State, float] = {start: g_start}
    came_from: Dict[State, Optional[State]] = {start: None}
    closed: Set[State] = set()
    expanded = 0
    peak_frontier = 1

    while frontier:
        peak_frontier = max(peak_frontier, len(frontier))
        f, h_val, _, node = heapq.heappop(frontier)

        if node in closed:
            continue
        closed.add(node)
        expanded += 1

        if trace:
            g = g_score[node]
            print(f"  [A*] expanding {node.as_tuple()} g={g:.1f} h={h_val:.1f} f={f:.1f}")

        if callback:
            callback(node, closed, [item[3] for item in frontier])

        if node == goal:
            path = _reconstruct(came_from, goal)
            elapsed = (time.perf_counter() - t0) * 1000
            name = f"A*({h})" if weight == 1.0 else f"WA*({h},w={weight})"
            return SolveStats(name, True, len(path), expanded, elapsed, peak_frontier, path)

        for _, nxt, step_cost in maze.successors(node):
            new_g = g_score[node] + step_cost
            if nxt not in g_score or new_g < g_score[nxt]:
                g_score[nxt] = new_g
                came_from[nxt] = node
                h_nxt = hfn(nxt, goal)
                counter += 1
                heapq.heappush(
                    frontier,
                    (new_g + weight * h_nxt, h_nxt, counter, nxt)
                )

    elapsed = (time.perf_counter() - t0) * 1000
    return SolveStats(f"A*({h})", False, 0, expanded, elapsed, peak_frontier)

def idastar(maze: Maze, h: str = "manhattan", trace: bool = False) -> SolveStats:
    t0 = time.perf_counter()
    hfn = HEURISTICS[h]
    start, goal = maze.start, maze.goal
    expanded = 0
    peak_frontier = 0

    threshold = hfn(start, goal)
    path = [start]
    path_set = {start}

    def search(node: State, g: float, thresh: float):
        nonlocal expanded, peak_frontier
        f = g + hfn(node, goal)
        if f > thresh:
            return f                                        
        if node == goal:
            return "FOUND"
        minimum = float("inf")
        expanded += 1
        peak_frontier = max(peak_frontier, len(path))
        for _, nxt, cost in maze.successors(node):
            if nxt not in path_set:                   
                path.append(nxt)
                path_set.add(nxt)
                result = search(nxt, g + cost, thresh)
                if result == "FOUND":
                    return "FOUND"
                if result < minimum:
                    minimum = result
                path.pop()
                path_set.remove(nxt)
        return minimum

    while True:
        result = search(start, 0.0, threshold)
        if result == "FOUND":
            final_path = [s.as_tuple() for s in path]
            elapsed = (time.perf_counter() - t0) * 1000
            return SolveStats("IDA*", True, len(final_path), expanded, elapsed, peak_frontier, final_path)
        if result == float("inf"):
            elapsed = (time.perf_counter() - t0) * 1000
            return SolveStats("IDA*", False, 0, expanded, elapsed, peak_frontier)
        threshold = result
        if trace:
            print(f"  [IDA*] new threshold = {threshold:.1f}")

def bidirectional_bfs(
    maze: Maze,
    trace: bool = False,
    callback: Optional[Callable[[State, Set[State], List[State]], None]] = None,
) -> SolveStats:
    t0 = time.perf_counter()
    start, goal = maze.start, maze.goal

    if start == goal:
        elapsed = (time.perf_counter() - t0) * 1000
        return SolveStats("Bidirectional BFS", True, 1, 0, elapsed, 1, [start.as_tuple()])

    frontier_f: deque[State] = deque([start])
    frontier_b: deque[State] = deque([goal])

    came_from_f: Dict[State, Optional[State]] = {start: None}
    came_from_b: Dict[State, Optional[State]] = {goal: None}

    expanded = 0
    peak_frontier = 2
    meeting_node = None

    while frontier_f and frontier_b:
        peak_frontier = max(peak_frontier, len(frontier_f) + len(frontier_b))

        # 1. Forward step
        curr_f = frontier_f.popleft()
        expanded += 1

        if trace:
            print(f"  [Bi-BFS] Forward expanding {curr_f.as_tuple()}")

        if callback:
            closed_states = set(came_from_f.keys()).union(came_from_b.keys())
            frontier_states = list(frontier_f) + list(frontier_b)
            callback(curr_f, closed_states, frontier_states)

        if curr_f in came_from_b:
            meeting_node = curr_f
            break

        for _, nxt, _ in maze.successors(curr_f):
            if nxt not in came_from_f:
                came_from_f[nxt] = curr_f
                frontier_f.append(nxt)

        # 2. Backward step
        curr_b = frontier_b.popleft()
        expanded += 1

        if trace:
            print(f"  [Bi-BFS] Backward expanding {curr_b.as_tuple()}")

        if callback:
            closed_states = set(came_from_f.keys()).union(came_from_b.keys())
            frontier_states = list(frontier_f) + list(frontier_b)
            callback(curr_b, closed_states, frontier_states)

        if curr_b in came_from_f:
            meeting_node = curr_b
            break

        for _, nxt, _ in maze.successors(curr_b):
            if nxt not in came_from_b:
                came_from_b[nxt] = curr_b
                frontier_b.append(nxt)

    if meeting_node is not None:
        # Reconstruct forward path
        path_f = []
        node = meeting_node
        while node is not None:
            path_f.append(node.as_tuple())
            node = came_from_f.get(node)
        path_f.reverse()

        # Reconstruct backward path
        path_b = []
        node = came_from_b.get(meeting_node)
        while node is not None:
            path_b.append(node.as_tuple())
            node = came_from_b.get(node)

        path = path_f + path_b
        elapsed = (time.perf_counter() - t0) * 1000
        return SolveStats("Bidirectional BFS", True, len(path), expanded, elapsed, peak_frontier, path)

    elapsed = (time.perf_counter() - t0) * 1000
    return SolveStats("Bidirectional BFS", False, 0, expanded, elapsed, peak_frontier)

def benchmark(maze: Maze) -> List[SolveStats]:
    algorithms = [
        ("BFS",             lambda: bfs(maze)),
        ("DFS",             lambda: dfs(maze)),
        ("UCS",             lambda: ucs(maze)),
        ("Bidirectional BFS", lambda: bidirectional_bfs(maze)),
        ("Greedy(manhattan)", lambda: greedy(maze, "manhattan")),
        ("A*(manhattan)",   lambda: astar(maze, "manhattan")),
        ("A*(euclidean)",   lambda: astar(maze, "euclidean")),
        ("WA*(w=1.5)",      lambda: astar(maze, "manhattan", weight=1.5)),
        ("IDA*",            lambda: idastar(maze)),
    ]
    results = []
    for name, fn in algorithms:
        stats = fn()
        stats.algorithm = name
        results.append(stats)
    return results

def print_benchmark(maze: Maze):
    print(f"\n{'='*60}")
    print(f"  SEARCH ALGORITHM BENCHMARK  - {maze}")
    print(f"{'='*60}")
    print(f"{'Algorithm':<22} {'Solved':<8} {'PathLen':<9} {'Expanded':<10} {'ms':<8} {'Peak-F'}")
    print(f"{'-'*60}")
    for s in benchmark(maze):
        solved = "YES" if s.solved else "NO"
        print(f"{s.algorithm:<22} {solved:<8} {s.path_length:<9} {s.nodes_expanded:<10} {s.elapsed_ms:<8.2f} {s.peak_frontier}")
    print(f"{'='*60}\n")
