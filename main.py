"""
main.py

This module contains the Command Line Interface (CLI) for the Intelligent Maze Solver.
It provides an interactive text-based menu to generate mazes, run search algorithms,
visualize the steps, and test adversarial and probabilistic scenarios.
"""

import os
import sys
import io
import time
from typing import List, Set, Tuple

if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

DUPLICATE_TO_FILE = True
_original_print = print

def print(*args, **kwargs):
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    file = kwargs.get('file', None)
    
    if file is None or file == sys.stdout or file == sys.stderr:
        msg = sep.join(str(arg) for arg in args) + end
        if file == sys.stderr:
            sys.stderr.write(msg)
        else:
            sys.stdout.write(msg)
            sys.stdout.flush()
        
        if DUPLICATE_TO_FILE:
            try:
                with open("output.txt", "a", encoding="utf-8") as f:
                    f.write(msg)
            except Exception:
                pass
    else:
        _original_print(*args, **kwargs)

from core.maze import Maze, State, MazeFactory, Cell, SolveStats
from algorithms.search import bfs, dfs, greedy, astar, print_benchmark, bidirectional_bfs
from csp.csp_solver import backtrack, maze_path_coloring_csp, waypoint_scheduling_csp
from algorithms.adversarial import minimax, expectimax
from algorithms.probabilistic import hmm_belief_update, variable_elimination_example, get_valid_neighbours_with_self
from algorithms.hybrid import hybrid_decide

try:
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write("=== MAZE SOLVER CLI LOG ===\nStarted: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
except Exception:
    pass

ENVIRONMENT_DECLARATION = """
================================================================================
                      ENVIRONMENT & PEAS DECLARATION
================================================================================
PEAS Profile:
------------
  - Performance Measure :
      1. Path Length (fewer steps are better; optimal path preferred)
      2. Nodes Expanded (less state-space search is more efficient)
      3. Execution Time (milliseconds taken to find the solution)
      4. Memory Consumption (peak frontier size in memory)

  - Environment :
      1. Grid Layout: A 2D grid containing open paths (0) and walls (1).
      2. Dimensions: Variable sizes (from 7x9 small to 21x21 large, or custom).
      3. Boundaries: Defined grid edges (cannot move out of bounds).

  - Actuators :
      1. Movement directions: Move North (N), South (S), East (E), or West (W).

  - Sensors :
      1. Agent Position: Coordinates of the current cell.
      2. Wall Detection: Querying whether target cells are walls or open.

Environment Characteristics:
---------------------------
  - Observable   : Fully Observable (the agent has access to the full map layout).
  - Agent Type   : Single-Agent (only the solving agent navigates the maze).
  - Deterministic: Deterministic (moving N/S/E/W succeeds with probability 1.0).
  - Episodic     : Sequential (each movement decision affects subsequent positions).
  - Static       : Static (the walls and target do not change during search).
  - Discrete     : Discrete (the state space consists of discrete grid cells).
================================================================================
"""

current_maze: Maze = MazeFactory.sample_small()
animation_delay = 0.05
last_solved_path: List[Cell] = []

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def make_animation_callback(maze: Maze, delay: float):
    def callback(current_state: State, closed_states: Set[State], frontier_states: List[State]):
        global DUPLICATE_TO_FILE
                                                                                       
        DUPLICATE_TO_FILE = False
        
        clear_screen()
        visited_cells = {s.as_tuple() for s in closed_states}
        current_cell = current_state.as_tuple()
        
        grid_render = maze.render(visited=visited_cells, current=current_cell)
        _original_print(grid_render)
        _original_print(f"\nExpanding cell : {current_cell}")
        _original_print(f"Frontier size  : {len(frontier_states)}")
        _original_print(f"Visited size   : {len(closed_states)}")
        
        time.sleep(delay)
                              
        DUPLICATE_TO_FILE = True
    return callback

def run_uninformed():
    global last_solved_path
    print("\n" + "="*50)
    print("  UNINFORMED SEARCH PATHFINDING (BFS & DFS)")
    print("="*50)
    print("1. Breadth-First Search (BFS) - Finds optimal path length")
    print("2. Depth-First Search (DFS)   - Fast, but path may be suboptimal")
    print("3. Bidirectional BFS         - Meeting-in-the-middle search")
    print("0. Back")
    
    choice = input("\nSelect algorithm: ").strip()
    if choice == "1":
        print("\nRunning BFS...")
        callback = None
        if animation_delay > 0:
            callback = make_animation_callback(current_maze, animation_delay)
        
        stats = bfs(current_maze, callback=callback)
        clear_screen()
        print("\n=== BFS SEARCH COMPLETED ===")
        print(stats.report())
        print("Final Path Visualized:")
        print(current_maze.render(path=stats.path))
        if stats.solved:
            last_solved_path = stats.path
    elif choice == "2":
        print("\nRunning DFS...")
        callback = None
        if animation_delay > 0:
            callback = make_animation_callback(current_maze, animation_delay)
            
        stats = dfs(current_maze, callback=callback)
        clear_screen()
        print("\n=== DFS SEARCH COMPLETED ===")
        print(stats.report())
        print("Final Path Visualized:")
        print(current_maze.render(path=stats.path))
        if stats.solved:
            last_solved_path = stats.path
    elif choice == "3":
        print("\nRunning Bidirectional BFS...")
        callback = None
        if animation_delay > 0:
            callback = make_animation_callback(current_maze, animation_delay)
            
        stats = bidirectional_bfs(current_maze, callback=callback)
        clear_screen()
        print("\n=== BIDIRECTIONAL BFS SEARCH COMPLETED ===")
        print(stats.report())
        print("Final Path Visualized:")
        print(current_maze.render(path=stats.path))
        if stats.solved:
            last_solved_path = stats.path

def run_informed():
    global last_solved_path
    print("\n" + "="*50)
    print("  INFORMED SEARCH PATHFINDING (GREEDY & A*)")
    print("="*50)
    print("1. Greedy Best-First Search - Explores using heuristic (fast, suboptimal)")
    print("2. A* Search                - Explores using g(n)+h(n) (optimal, efficient)")
    print("0. Back")
    
    choice = input("\nSelect algorithm: ").strip()
    if choice not in ("1", "2"):
        return
        
    print("\nSelect Heuristic:")
    print("1. Manhattan Distance (Recommended - admissible)")
    print("2. Euclidean Distance (Admissible but weaker)")
    print("3. Chebyshev / Diagonal Distance")
    print("4. Zero Heuristic (h=0, A* degrades to UCS)")
    
    h_choice = input("\nSelect heuristic: ").strip()
    h_map = {"1": "manhattan", "2": "euclidean", "3": "diagonal", "4": "zero"}
    heuristic_name = h_map.get(h_choice, "manhattan")
    
    callback = None
    if animation_delay > 0:
        callback = make_animation_callback(current_maze, animation_delay)

    if choice == "1":
        print(f"\nRunning Greedy Best-First Search with '{heuristic_name}' heuristic...")
        stats = greedy(current_maze, h=heuristic_name, callback=callback)
        clear_screen()
        print("\n=== GREEDY BEST-FIRST COMPLETED ===")
        print(stats.report())
        print("Final Path Visualized:")
        print(current_maze.render(path=stats.path))
        if stats.solved:
            last_solved_path = stats.path
    elif choice == "2":
        print(f"\nRunning A* Search with '{heuristic_name}' heuristic...")
        stats = astar(current_maze, h=heuristic_name, callback=callback)
        clear_screen()
        print("\n=== A* SEARCH COMPLETED ===")
        print(stats.report())
        print("Final Path Visualized:")
        print(current_maze.render(path=stats.path))
        if stats.solved:
            last_solved_path = stats.path

def run_csp_coloring():
    if not last_solved_path:
        print("\nWARNING: No path is currently solved in memory.")
        print("Please run a search pathfinder (BFS/DFS/Greedy/A*) first!")
        input("\nPress Enter to return...")
        return
    
    print("\n" + "="*50)
    print("  CONSTRAINT SATISFACTION PROBLEM (CSP) PATH COLORING")
    print("="*50)
    print(f"Goal: Assign 1 of 3 colors (Red, Green, Blue) to each of the {len(last_solved_path)} path steps")
    print("      such that no two adjacent steps share the same color.")
    
    cell_names = [f"cell_{r}_{c}" for r, c in last_solved_path]
    csp = maze_path_coloring_csp(cell_names, n_colors=3)
    
    print("\nSolving using CSP Backtracking Search with MRV, LCV, and Forward Checking...")
    result = backtrack(csp, use_mrv=True, use_lcv=True, use_fc=True)
    
    if result:
        print("\nSUCCESS! Color Assignment Found:")
        colors_map = {0: "Red", 1: "Green", 2: "Blue"}
        ansi_colors = {0: "\033[91m", 1: "\033[92m", 2: "\033[94m"}
        ansi_reset = "\033[0m"
        
        colored_path = []
        for cell in cell_names:
            col_idx = result[cell]
            col_name = colors_map[col_idx]
            colored_path.append(f"{cell}:{col_name}")
            
        print(" -> ".join(colored_path))
        
        print("\n" + "-"*50)
        print("  WAYPOINT SCHEDULING CSP")
        print("-"*50)
        print("Goal: Schedule path waypoints into strictly increasing chronological time slots.")
        
        waypoints = cell_names[::3][:5]
        print(f"Selected Waypoints: {waypoints}")
        
        sched_csp = waypoint_scheduling_csp(waypoints, time_slots=len(waypoints) + 2)
        sched_result = backtrack(sched_csp, use_mrv=True, use_lcv=True, use_fc=True)
        
        if sched_result:
            print("\nSUCCESS! Schedule Found:")
            for wp, slot in sched_result.items():
                print(f"  {wp} -> Time Slot {slot}")
        else:
            print("\nFAILED: Waypoint scheduling is infeasible with given time slots.")
    else:
        print("\nFAILED: No coloring solution exists for 3 colors on this path.")
        
    input("\nPress Enter to return...")

def select_generate_maze():
    global current_maze, last_solved_path
    print("\n" + "="*50)
    print("  MAZE SELECTION & GENERATION")
    print("="*50)
    print("1. Load Small Sample Maze (7x9)")
    print("2. Load Large Sample Maze (21x21)")
    print("3. Generate Custom Random Maze (Recursive Backtracking)")
    print("4. Generate Custom Random Maze (Randomized Prim's)")
    print("0. Back")
    
    choice = input("\nSelect choice: ").strip()
    if choice == "1":
        current_maze = MazeFactory.sample_small()
        last_solved_path = []
        print("\nLoaded small sample maze:")
        print(current_maze.render())
    elif choice == "2":
        current_maze = MazeFactory.sample_large()
        last_solved_path = []
        print("\nLoaded large sample maze:")
        print(current_maze.render())
    elif choice == "3":
        try:
            r = int(input("Enter number of rows (odd integer, e.g., 11): ").strip())
            c = int(input("Enter number of cols (odd integer, e.g., 11): ").strip())
            seed = int(input("Enter random seed (integer): ").strip())
            grid = MazeFactory.generate(r, c, seed=seed)
            current_maze = Maze(grid, start=(0, 0), goal=(r - 1, c - 1))
            last_solved_path = []
            print(f"\nGenerated custom random {r}x{c} maze (Seed: {seed}):")
            print(current_maze.render())
        except Exception as e:
            print(f"\nError generating maze: {e}. Reverting to small sample.")
            current_maze = MazeFactory.sample_small()
    elif choice == "4":
        try:
            r = int(input("Enter number of rows (odd integer, e.g., 11): ").strip())
            c = int(input("Enter number of cols (odd integer, e.g., 11): ").strip())
            seed = int(input("Enter random seed (integer): ").strip())
            grid = MazeFactory.generate_prims(r, c, seed=seed)
            current_maze = Maze(grid, start=(0, 0), goal=(r - 1, c - 1))
            last_solved_path = []
            print(f"\nGenerated custom Prim's {r}x{c} maze (Seed: {seed}):")
            print(current_maze.render())
        except Exception as e:
            print(f"\nError generating maze: {e}. Reverting to small sample.")
            current_maze = MazeFactory.sample_small()
            
    input("\nPress Enter to continue...")

def select_delay():
    global animation_delay
    print("\n" + "="*50)
    print("  CONFIGURE ANIMATION SPEED")
    print("="*50)
    print("1. Fast (0.01 seconds)")
    print("2. Normal (0.05 seconds - Default)")
    print("3. Slow (0.2 seconds)")
    print("4. Off (Instant solve)")
    
    choice = input("\nSelect speed: ").strip()
    if choice == "1":
        animation_delay = 0.01
    elif choice == "2":
        animation_delay = 0.05
    elif choice == "3":
        animation_delay = 0.2
    elif choice == "4":
        animation_delay = 0.0
    print(f"\nAnimation delay set to {animation_delay} seconds.")
    input("\nPress Enter to return...")

def run_diagnostics():
    print(current_maze)
    print_benchmark(current_maze)
    input("\nPress Enter to return...")

def render_adversarial(maze: Maze, agent: Tuple[int, int], ghost: Tuple[int, int]) -> str:
    lines = []
    for r in range(maze.rows):
        row_str = ""
        for c in range(maze.cols):
            cell = (r, c)
            if cell == agent:
                row_str += " A"
            elif cell == ghost:
                row_str += " X"
            elif cell == maze.goal.as_tuple():
                row_str += " *"
            elif maze.grid[r][c] == maze.WALL:
                row_str += " █"
            elif maze.grid[r][c] == 2:
                row_str += " ░"
            elif maze.grid[r][c] == 3:
                row_str += " ▓"
            else:
                row_str += "  "
        lines.append(row_str)
    return "\n".join(lines)

def run_adversarial_sim():
    global current_maze
    print("\n" + "="*50)
    print("  ADVERSARIAL SEARCH SIMULATION (CO4)")
    print("="*50)
    print("1. Minimax Search with Alpha-Beta Pruning")
    print("2. Expectimax Search (Stochastic Opponent)")
    print("0. Back")
    
    choice = input("\nSelect choice: ").strip()
    if choice not in ("1", "2"):
        return
        
    mode = "minimax" if choice == "1" else "expectimax"
    
    try:
        depth = int(input("Enter search depth (default 4): ").strip() or "4")
    except ValueError:
        depth = 4
        
    # Default Ghost Position: bottom-right or another valid open cell
    ghost_r, ghost_c = current_maze.rows - 2, current_maze.cols - 2
    if not current_maze.is_open((ghost_r, ghost_c)):
        found = False
        for r in range(current_maze.rows - 1, -1, -1):
            for c in range(current_maze.cols - 1, -1, -1):
                if current_maze.is_open((r, c)) and (r, c) != current_maze.start.as_tuple() and (r, c) != current_maze.goal.as_tuple():
                    ghost_r, ghost_c = r, c
                    found = True
                    break
            if found:
                break

    print(f"Default Ghost Position: ({ghost_r}, {ghost_c})")
    pos_input = input("Enter Ghost Position 'row,col' (or press Enter for default): ").strip()
    if pos_input:
        try:
            r, c = map(int, pos_input.split(","))
            if current_maze.is_open((r, c)):
                ghost_r, ghost_c = r, c
            else:
                print("Cell is a wall. Using default.")
        except Exception:
            print("Invalid input. Using default.")
            
    agent_pos = current_maze.start.as_tuple()
    ghost_pos = (ghost_r, ghost_c)
    
    auto_play = False
    step_count = 0
    
    while True:
        clear_screen()
        print("\n" + "="*50)
        print(f"  ADVERSARIAL GAME STATE (Turn: {step_count})")
        print("="*50)
        print(f"  Algorithm : {mode.upper()} (Depth: {depth})")
        print(f"  Agent Pos : {agent_pos} (A) | Goal Pos : {current_maze.goal.as_tuple()} (*)")
        print(f"  Ghost Pos : {ghost_pos} (X)")
        print("-"*50)
        print(render_adversarial(current_maze, agent_pos, ghost_pos))
        print("-"*50)
        
        # Calculate evaluations
        if mode == "expectimax":
            eval_val, next_agent_path = expectimax(current_maze, agent_pos, ghost_pos, depth, is_max=True)
        else:
            eval_val, next_agent_path = minimax(current_maze, agent_pos, ghost_pos, depth, is_max=True)
            
        print(f"Agent's Move Evaluation Score: {eval_val:.2f}")
        if next_agent_path:
            next_agent = next_agent_path[0]
            print(f"Agent chooses to move to: {next_agent}")
            print(f"Predicted Optimal Path (Principal Variation): {next_agent_path}")
        else:
            print("Agent stands still / no moves.")
            next_agent = agent_pos
            
        # Check terminal state before ghost moves
        if agent_pos == current_maze.goal.as_tuple():
            print("\nVICTORY! Agent has reached the goal safely!")
            input("\nPress Enter to return...")
            break
        if agent_pos == ghost_pos:
            print("\nDEFEAT! The Ghost caught the Agent!")
            input("\nPress Enter to return...")
            break
            
        if not auto_play:
            user_action = input("\n[Enter] Next Step | [A] Auto-Play | [Q] Quit: ").strip().lower()
            if user_action == 'q':
                break
            elif user_action == 'a':
                auto_play = True
        else:
            time.sleep(0.5)
            
        # Update agent position
        agent_pos = next_agent
        
        # Compute ghost move
        _, next_ghost_path = minimax(current_maze, agent_pos, ghost_pos, depth=2, is_max=False)
        if next_ghost_path:
            ghost_pos = next_ghost_path[0]
        
        step_count += 1

def render_hmm(maze: Maze, agent: Tuple[int, int], belief: List[List[float]]) -> str:
    lines = []
    for r in range(maze.rows):
        row_str = ""
        for c in range(maze.cols):
            cell = (r, c)
            if cell == agent:
                row_str += " A"
            elif maze.grid[r][c] == maze.WALL:
                row_str += " █"
            else:
                p = belief[r][c]
                if p > 0.25:
                    row_str += " ▓"
                elif p > 0.10:
                    row_str += " ▒"
                elif p > 0.02:
                    row_str += " ░"
                else:
                    row_str += "  "
        lines.append(row_str)
    return "\n".join(lines)

def run_probabilistic_inference():
    global current_maze
    print("\n" + "="*50)
    print("  PROBABILISTIC INFERENCE & GHOST TRACKING (CO5)")
    print("="*50)
    print("1. HMM Ghost Tracking Simulation")
    print("2. Variable Elimination Worked Example")
    print("0. Back")
    
    choice = input("\nSelect choice: ").strip()
    if choice == "2":
        clear_screen()
        print("\n" + "="*50)
        print("  VARIABLE ELIMINATION DETAILED TRACE")
        print("="*50)
        result = variable_elimination_example()
        for line in result["trace"]:
            print(line)
        input("\nPress Enter to return...")
    elif choice == "1":
        # Initialize Uniform Belief
        rCount = current_maze.rows
        cCount = current_maze.cols
        open_cells = [(r, c) for r in range(rCount) for c in range(cCount) if current_maze.grid[r][c] != current_maze.WALL]
        if not open_cells:
            print("No open cells in maze.")
            input("\nPress Enter...")
            return
        prob = 1.0 / len(open_cells)
        belief = [[prob if current_maze.grid[r][c] != current_maze.WALL else 0.0 for c in range(cCount)] for r in range(rCount)]
        
        # Ghost true position starts in a random or default open cell (not start/goal)
        ghost_pos = (rCount - 2, cCount - 2)
        if not current_maze.is_open(ghost_pos):
            for cell in reversed(open_cells):
                if cell != current_maze.start.as_tuple() and cell != current_maze.goal.as_tuple():
                    ghost_pos = cell
                    break
                    
        agent_pos = current_maze.start.as_tuple()
        step = 0
        import random
        
        while True:
            clear_screen()
            print("\n" + "="*50)
            print(f"  HMM GHOST TRACKING SIMULATION (Step: {step})")
            print("="*50)
            print("  Belief Grid Visualizer:")
            print("  [ A: Agent | █: Wall | ▓: P>25% | ▒: P>10% | ░: P>2% ]")
            print("-"*50)
            print(render_hmm(current_maze, agent_pos, belief))
            print("-"*50)
            
            # Compute true distance & sensor reading
            true_dist = abs(agent_pos[0] - ghost_pos[0]) + abs(agent_pos[1] - ghost_pos[1])
            rand = random.random()
            noise = 0
            if 0.7 < rand <= 0.8:
                noise = -1
            elif 0.8 < rand <= 0.9:
                noise = 1
            elif 0.9 < rand <= 0.95:
                noise = -2
            elif rand > 0.95:
                noise = 2
            sensor_reading = max(0, true_dist + noise)
            
            print(f"  True Ghost Position (Hidden from Agent) : {ghost_pos}")
            print(f"  True Manhattan Distance to Agent        : {true_dist}")
            print(f"  Noisy Distance Sensor Reading           : {sensor_reading}")
            
            # Top-5 Highest Belief Cells
            flat_beliefs = []
            for r in range(rCount):
                for c in range(cCount):
                    if belief[r][c] > 0.001:
                        flat_beliefs.append(((r, c), belief[r][c]))
            flat_beliefs.sort(key=lambda x: x[1], reverse=True)
            
            print("\n  Top 5 Most Probable Ghost Cells:")
            for idx, (cell, p) in enumerate(flat_beliefs[:5]):
                print(f"    {idx+1}. Cell {cell} -> Probability: {p*100:.2f}%")
            
            user_input = input("\n[Enter] Next Step | [Q] Quit: ").strip().lower()
            if user_input == 'q':
                break
                
            # Update HMM beliefs
            belief = hmm_belief_update(current_maze, belief, sensor_reading, agent_pos)
            
            # Move ghost stochastically to matching neighbor
            nbrs = get_valid_neighbours_with_self(current_maze, ghost_pos)
            if nbrs:
                ghost_pos = random.choice(nbrs)
                
            step += 1

def make_ghost_belief(maze: Maze, ghost_pos: Tuple[int, int]) -> List[List[float]]:
    belief = [[0.0] * maze.cols for _ in range(maze.rows)]
    nbrs = get_valid_neighbours_with_self(maze, ghost_pos)
    if nbrs:
        prob = 1.0 / len(nbrs)
        for r, c in nbrs:
            belief[r][c] = prob
    return belief

def run_hybrid_reasoning():
    global current_maze
    print("\n" + "="*50)
    print("  HYBRID REASONING ENGINE (CO6)")
    print("="*50)
    print("Goal: Evaluate expected utility of Direct path vs detour path")
    print("      based on path traversal cost and probability of capture.")
    
    # Input Risk Tolerance
    try:
        risk_input = input("\nEnter Agent Risk Tolerance [0.0 - 1.0] (default 0.5): ").strip()
        risk_tolerance = float(risk_input) if risk_input else 0.5
        if not (0.0 <= risk_tolerance <= 1.0):
            print("Invalid range. Using default 0.5")
            risk_tolerance = 0.5
    except ValueError:
        print("Invalid input. Using default 0.5")
        risk_tolerance = 0.5
        
    # Place Ghost
    ghost_r, ghost_c = current_maze.rows // 2, current_maze.cols // 2
    if not current_maze.is_open((ghost_r, ghost_c)):
        found = False
        for r in range(current_maze.rows):
            for c in range(current_maze.cols):
                if current_maze.is_open((r, c)) and (r, c) != current_maze.start.as_tuple() and (r, c) != current_maze.goal.as_tuple():
                    ghost_r, ghost_c = r, c
                    found = True
                    break
            if found:
                break
                
    print(f"\nDefault Ghost Location (creating threat zone): ({ghost_r}, {ghost_c})")
    pos_input = input("Enter Ghost threat cell 'row,col' (or press Enter for default): ").strip()
    if pos_input:
        try:
            r, c = map(int, pos_input.split(","))
            if current_maze.is_open((r, c)):
                ghost_r, ghost_c = r, c
            else:
                print("Cell is a wall. Using default.")
        except Exception:
            print("Invalid format. Using default.")
            
    # Generate Belief centered around ghost
    ghost_pos = (ghost_r, ghost_c)
    belief = make_ghost_belief(current_maze, ghost_pos)
    
    print("\nRunning hybrid decision cycle...")
    result = hybrid_decide(current_maze, current_maze.start.as_tuple(), belief, risk_tolerance)
    
    # Print Explainable Trace
    print("\n" + "="*50)
    print("  HYBRID DECISION EXPLAINABLE TRACE")
    print("="*50)
    for line in result["trace"]:
        print(line)
        
    # Draw resulting path on Grid
    print("\n" + "="*50)
    print("  SELECTED PATH VISUALIZATION")
    print("="*50)
    path = result["selected_path"]
    
    # Render with waypoints
    wp_set = set()
    wp_slots = {}
    if result["csp_success"]:
        for wp_cell_str, slot in result["schedule"].items():
            parts = wp_cell_str.split('_')
            cell = (int(parts[1]), int(parts[2]))
            wp_set.add(cell)
            wp_slots[cell] = slot
            
    # Custom rendering to show selected path, threat area, and waypoints
    for r in range(current_maze.rows):
        row_str = ""
        for c in range(current_maze.cols):
            cell = (r, c)
            if cell == current_maze.start.as_tuple():
                row_str += " S"
            elif cell == current_maze.goal.as_tuple():
                row_str += " G"
            elif cell in wp_set:
                row_str += f" T{wp_slots[cell]}" # Waypoint time slot T_i
            elif cell in path:
                row_str += " ·"
            elif cell == ghost_pos:
                row_str += " X" # Ghost position
            elif belief[r][c] > 0.05:
                row_str += " ░" # Threat zone
            elif current_maze.grid[r][c] == current_maze.WALL:
                row_str += " █"
            else:
                row_str += "  "
        print(row_str)
        
    input("\nPress Enter to return...")

def main_menu():
    while True:
        clear_screen()
        print("==================================================")
        print("     INTELLIGENT MAZE SOLVER (CO1 - CO6)")
        print("==================================================")
        print(f" Current Maze: {current_maze.rows}x{current_maze.cols}")
        print(f" Animation   : {'ON (' + str(animation_delay) + 's)' if animation_delay > 0 else 'OFF'}")
        print(f" Solved Path : {len(last_solved_path)} cells in memory")
        print("--------------------------------------------------")
        print("1. View Environment & PEAS Declaration")
        print("2. Select / Generate Maze")
        print("3. Configure Animation Speed")
        print("4. Run Uninformed Search (BFS, DFS, Bi-BFS)")
        print("5. Run Informed Search (Greedy, A*)")
        print("6. Run CSP Path Coloring & Scheduling")
        print("7. Run Comparative Benchmarks")
        print("8. Run Adversarial Search / Multi-Agent Sim (CO4)")
        print("9. Run Probabilistic Inference & Ghost Tracking (CO5)")
        print("10. Run Hybrid Decision Architecture (CO6)")
        print("0. Exit")
        print("==================================================")
        
        choice = input("Enter option: ").strip()
        
        if choice == "1":
            clear_screen()
            print(ENVIRONMENT_DECLARATION)
            input("\nPress Enter to return...")
        elif choice == "2":
            clear_screen()
            select_generate_maze()
        elif choice == "3":
            clear_screen()
            select_delay()
        elif choice == "4":
            clear_screen()
            run_uninformed()
            input("\nPress Enter to continue...")
        elif choice == "5":
            clear_screen()
            run_informed()
            input("\nPress Enter to continue...")
        elif choice == "6":
            clear_screen()
            run_csp_coloring()
        elif choice == "7":
            clear_screen()
            run_diagnostics()
        elif choice == "8":
            clear_screen()
            run_adversarial_sim()
        elif choice == "9":
            clear_screen()
            run_probabilistic_inference()
        elif choice == "10":
            clear_screen()
            run_hybrid_reasoning()
        elif choice == "0":
            print("\nExiting. Thank you for using the Intelligent Maze Solver!")
            break

if __name__ == "__main__":
    main_menu()
