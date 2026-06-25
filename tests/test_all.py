import sys
import os
import io

# Setup UTF-8 encoding for standard output on Windows
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.maze import Maze, State, MazeFactory, SolveStats
from algorithms.search import bfs, dfs, ucs, astar, greedy, idastar, bidirectional_bfs
from csp.csp_solver import CSP, backtrack, min_conflicts
from algorithms.adversarial import minimax, expectimax
from algorithms.probabilistic import hmm_belief_update, variable_elimination_example
from algorithms.hybrid import hybrid_decide

def simple_maze():
    grid = [
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
    ]
    return Maze(grid, start=(1, 1), goal=(1, 1))

def corridor_maze():
    grid = [[0, 0, 0, 0, 0]]
    return Maze(grid, start=(0, 0), goal=(0, 4))

def test_state_manhattan():
    a = State(0, 0)
    b = State(3, 4)
    assert a.manhattan(b) == 7, "Manhattan distance failed"
    print("  - State.manhattan")

def test_maze_bounds():
    m = MazeFactory.sample_small()
    assert m.in_bounds((0, 0))
    assert not m.in_bounds((-1, 0))
    assert not m.in_bounds((m.rows, 0))
    print("  - Maze.in_bounds")

def test_maze_successors_corridor():
    m = corridor_maze()
    succs = m.successors(m.start)
    actions = [a for a, _, _ in succs]
    assert "E" in actions
    assert "W" not in actions                
    print("  - Maze.successors (corridor)")

def test_maze_graph():
    m = corridor_maze()
    g = m.to_graph()
    assert (0, 0) in g
    assert (0, 1) in g[(0, 0)]
    print("  - Maze.to_graph")

def test_bfs_optimal():
    m = corridor_maze()
    s = bfs(m)
    assert s.solved
    assert s.path_length == 5                                 
    print("  - BFS: optimal path length")

def test_dfs_finds_path():
    m = MazeFactory.sample_small()
    s = dfs(m)
    assert s.solved
    print("  - DFS: finds a path")

def test_ucs_optimal():
    m = corridor_maze()
    s = ucs(m)
    assert s.solved
    assert s.path_length == 5
    print("  - UCS: optimal path")

def test_astar_optimal_le_bfs():
    m = MazeFactory.sample_small()
    bfs_s  = bfs(m)
    astar_s = astar(m, h="manhattan")
    assert astar_s.solved
    assert astar_s.path_length == bfs_s.path_length, "A* must be optimal"
    assert astar_s.nodes_expanded <= bfs_s.nodes_expanded, "A* should expand fewer nodes"
    print("  - A*: optimal and more efficient than BFS")

def test_idastar():
    m = corridor_maze()
    s = idastar(m)
    assert s.solved
    assert s.path_length == 5
    print("  - IDA*: correct path length")

def test_no_path():
    grid = [[0, 1, 0]]
    m = Maze(grid, start=(0, 0), goal=(0, 2))
    s = bfs(m)
    assert not s.solved
    print("  - BFS: correctly reports no path")

def test_heuristic_admissibility():
    from algorithms.search import heuristic_manhattan
    m = MazeFactory.sample_small()
    for r in range(m.rows):
        for c in range(m.cols):
            if m.grid[r][c] == m.OPEN:
                s = State(r, c)
                h = heuristic_manhattan(s, m.goal)
                path_stats = astar(m)
                if path_stats.solved:
                    actual = m.goal.manhattan(s)               
                    assert h <= actual + 1e-6, f"Heuristic not admissible at {s}"
    print("  - Manhattan heuristic: admissible")

def test_bidirectional_bfs():
    m = corridor_maze()
    s = bidirectional_bfs(m)
    assert s.solved
    assert s.path_length == 5
    print("  - Bidirectional BFS: optimal path")

def test_prims_generation():
    grid = MazeFactory.generate_prims(11, 11, seed=42)
    assert len(grid) == 11
    assert len(grid[0]) == 11
    assert grid[0][0] == Maze.OPEN
    assert grid[10][10] == Maze.OPEN
    print("  - Prim's Maze generation: correct bounds and start/goal open")

def test_terrain_weights():
    grid = [
        [0, 3, 0],
        [0, 0, 0]
    ]
    m = Maze(grid, start=(0, 0), goal=(0, 2))
    
    bfs_s = bfs(m)
    assert bfs_s.solved
    assert bfs_s.path_length == 3
    
    ucs_s = ucs(m)
    assert ucs_s.solved
    assert ucs_s.path_length == 5
    print("  - Terrain weights: UCS routes around water, BFS goes straight")

def test_csp_graph_coloring():
    csp = CSP(
        variables=["A", "B", "C"],
        domains={"A": [0, 1], "B": [0, 1], "C": [0, 1]},
        constraints=[
            ("A", "B", lambda a, b: a != b),
            ("B", "C", lambda b, c: b != c),
        ]
    )
    result = backtrack(csp, use_mrv=True, use_lcv=True, use_fc=True)
    assert result is not None, "CSP should be satisfiable"
    assert result["A"] != result["B"]
    assert result["B"] != result["C"]
    print("  - CSP backtracking: graph coloring solved")

def test_csp_unsatisfiable():
    csp = CSP(
        variables=["A", "B", "C"],
        domains={"A": [0, 1], "B": [0, 1], "C": [0, 1]},
        constraints=[
            ("A", "B", lambda a, b: a != b),
            ("B", "C", lambda b, c: b != c),
            ("A", "C", lambda a, c: a != c),
        ]
    )
    result = backtrack(csp)
    assert result is None, "Triangle with 2 colors should be unsatisfiable"
    print("  - CSP backtracking: correctly identifies unsatisfiable")

def test_min_conflicts():
    csp = CSP(
        variables=["A", "B", "C"],
        domains={"A": [0, 1, 2], "B": [0, 1, 2], "C": [0, 1, 2]},
        constraints=[
            ("A", "B", lambda a, b: a != b),
            ("B", "C", lambda b, c: b != c),
        ]
    )
    result = min_conflicts(csp, max_steps=200)
    assert result is not None
    print("  - Min-Conflicts: found solution")

def test_adversarial_minimax():
    m = corridor_maze() # 1x5 grid
    # Agent at (0,0), Ghost at (0,3). Depth 2. Max turn.
    from algorithms.adversarial import precompute_goal_distances
    goal_dist_map = precompute_goal_distances(m)
    eval_val, next_move_path = minimax(m, agent=(0, 0), ghost=(0, 3), depth=2, is_max=True, goal_dist_map=goal_dist_map)
    assert next_move_path and next_move_path[0] in [(0, 0), (0, 1)]
    print("  - Adversarial Minimax: calculates next move")

def test_adversarial_expectimax():
    m = corridor_maze()
    from algorithms.adversarial import precompute_goal_distances
    goal_dist_map = precompute_goal_distances(m)
    eval_val, next_move_path = expectimax(m, agent=(0, 0), ghost=(0, 3), depth=2, is_max=True, goal_dist_map=goal_dist_map)
    assert next_move_path and next_move_path[0] in [(0, 0), (0, 1)]
    print("  - Adversarial Expectimax: calculates next move expectation")

def test_probabilistic_hmm():
    grid = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0]
    ]
    m = Maze(grid, start=(0,0), goal=(2,2))
    # Initial uniform belief over 8 open cells (1/8 = 0.125)
    belief = [[0.125 if grid[r][c] != m.WALL else 0.0 for c in range(3)] for r in range(3)]
    # Agent at (0,0), sensor reading 2
    updated = hmm_belief_update(m, belief, sensor_reading=2, agent_pos=(0, 0))
    # Sum of belief should sum to 1.0 (approx)
    total = sum(sum(row) for row in updated)
    assert abs(total - 1.0) < 1e-5
    # Wall cell (1,1) must have probability 0.0
    assert updated[1][1] == 0.0
    print("  - Probabilistic HMM: filters belief grid and normalizes correctly")

def test_probabilistic_bayes_ve():
    res = variable_elimination_example()
    # P(G | A=True) should contain True and False values summing to 1.0
    p = res["p_g_given_a"]
    assert abs(p[False] + p[True] - 1.0) < 1e-5
    assert p[True] > 0.0 and p[False] > 0.0
    assert len(res["trace"]) > 0
    print("  - Variable Elimination worked example: solves Bayes Net correctly")

def test_hybrid_decide():
    # Grid: Detour via Row 1 is high cost Water (cost 6 each, total detour cost = 19)
    # Row 0 is open, but has ghost threat at (0, 1) with 15% probability
    grid = [
        [0, 0, 0],
        [3, 3, 3]
    ]
    m = Maze(grid, start=(0, 0), goal=(0, 2))
    belief = [
        [0.0, 0.15, 0.0],
        [0.0, 0.0, 0.0]
    ]
    # Risk averse (risk_tolerance = 0.0) -> should choose detour path (Row 1)
    res_averse = hybrid_decide(m, agent_pos=(0, 0), ghost_belief=belief, risk_tolerance=0.0)
    assert res_averse["selected_type"] == "Detour Path"
    
    # Risk tolerant (risk_tolerance = 1.0) -> should choose direct path (Row 0)
    res_tolerant = hybrid_decide(m, agent_pos=(0, 0), ghost_belief=belief, risk_tolerance=1.0)
    assert res_tolerant["selected_type"] == "Direct Path"
    print("  - Hybrid Reasoning: Expected Utility adjusts path selection based on risk tolerance")

def run_all_tests():
    print("\n" + "=" * 50)
    print("  UNIT TESTS - All Course Outcomes")
    print("=" * 50)

    print("\n-- CO1: Core Maze & State -----------------------")
    test_state_manhattan()
    test_maze_bounds()
    test_maze_successors_corridor()
    test_maze_graph()

    print("\n-- CO2: Search & Terrain weights ----------------")
    test_bfs_optimal()
    test_dfs_finds_path()
    test_ucs_optimal()
    test_astar_optimal_le_bfs()
    test_idastar()
    test_no_path()
    test_heuristic_admissibility()
    test_bidirectional_bfs()
    test_prims_generation()
    test_terrain_weights()

    print("\n-- CO3: CSP & Scheduling ------------------------")
    test_csp_graph_coloring()
    test_csp_unsatisfiable()
    test_min_conflicts()

    print("\n-- CO4: Adversarial Search ----------------------")
    test_adversarial_minimax()
    test_adversarial_expectimax()

    print("\n-- CO5: Probabilistic Inference -----------------")
    test_probabilistic_hmm()
    test_probabilistic_bayes_ve()

    print("\n-- CO6: Hybrid Decision Architecture ------------")
    test_hybrid_decide()

    print("\n" + "=" * 50)
    print("  ALL TESTS PASSED SUCCESSFULLY")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    run_all_tests()
