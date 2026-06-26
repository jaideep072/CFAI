"""
app.py

This module contains the Flask web server for the Intelligent Maze Solver.
It exposes REST API endpoints to generate mazes, solve them using various
search algorithms, run adversarial search simulations, and test probabilistic
ghost tracking.
"""

import os
import sys
from flask import Flask, jsonify, request, render_template

# Ensure the root directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.maze import Maze, MazeFactory, State
from algorithms.search import bfs, dfs, ucs, greedy, astar, idastar, bidirectional_bfs
from csp.csp_solver import backtrack, maze_path_coloring_csp, waypoint_scheduling_csp
from algorithms.adversarial import minimax, expectimax, precompute_goal_distances
from algorithms.probabilistic import hmm_belief_update, variable_elimination_example
from algorithms.hybrid import hybrid_decide

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/app')
def index():
    return render_template('index.html')

@app.route('/api/maze/generate', methods=['POST'])
def generate_maze():
    try:
        data = request.json or {}
        maze_type = data.get('type', 'random')
        rows = int(data.get('rows', 11))
        cols = int(data.get('cols', 11))
        seed = int(data.get('seed', 42))

        # Adjust dimensions if custom is requested (must be odd for recursive backtracking)
        if maze_type == 'small':
            maze = MazeFactory.sample_small()
            grid = maze.grid
            start = list(maze.start.as_tuple())
            goal = list(maze.goal.as_tuple())
        elif maze_type == 'large':
            maze = MazeFactory.sample_large(seed=seed)
            grid = maze.grid
            start = list(maze.start.as_tuple())
            goal = list(maze.goal.as_tuple())
        elif maze_type == 'custom_prims':
            # Ensure odd dimensions for the maze generator
            if rows % 2 == 0:
                rows += 1
            if cols % 2 == 0:
                cols += 1
            grid = MazeFactory.generate_prims(rows, cols, seed=seed)
            start = [0, 0]
            goal = [rows - 1, cols - 1]
        elif maze_type == 'empty':
            grid = [[0 for _ in range(cols)] for _ in range(rows)]
            start = [0, 0]
            goal = [rows - 1, cols - 1]
        else:
            # Ensure odd dimensions for the maze generator
            if rows % 2 == 0:
                rows += 1
            if cols % 2 == 0:
                cols += 1
            grid = MazeFactory.generate(rows, cols, seed=seed)
            start = [0, 0]
            goal = [rows - 1, cols - 1]

        return jsonify({
            'grid': grid,
            'start': start,
            'goal': goal,
            'rows': len(grid),
            'cols': len(grid[0])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/maze/solve', methods=['POST'])
def solve_maze():
    try:
        data = request.json or {}
        grid = data.get('grid')
        start = data.get('start')
        goal = data.get('goal')
        algorithm = data.get('algorithm', 'bfs').lower()
        heuristic = data.get('heuristic', 'manhattan').lower()
        weight = float(data.get('weight', 1.0))

        if not grid or not start or not goal:
            return jsonify({'error': 'Missing grid, start, or goal'}), 400

        # Construct Maze object
        maze = Maze(grid, start=tuple(start), goal=tuple(goal))

        # We will collect step-by-step frames for animation using a callback
        steps = []
        def solve_callback(current_state, closed_states, frontier_states):
            # Convert States to coordinate lists
            visited_list = []
            for s in closed_states:
                if hasattr(s, 'as_tuple'):
                    visited_list.append(list(s.as_tuple()))
                elif isinstance(s, tuple):
                    visited_list.append(list(s))

            frontier_list = []
            for s in frontier_states:
                if hasattr(s, 'as_tuple'):
                    frontier_list.append(list(s.as_tuple()))
                elif isinstance(s, tuple):
                    frontier_list.append(list(s))

            curr = list(current_state.as_tuple()) if hasattr(current_state, 'as_tuple') else list(current_state)
            steps.append({
                'current': curr,
                'visited': visited_list,
                'frontier': frontier_list
            })

        # Select and run algorithm
        stats = None
        if algorithm == 'bfs':
            stats = bfs(maze, callback=solve_callback)
        elif algorithm == 'dfs':
            stats = dfs(maze, callback=solve_callback)
        elif algorithm == 'ucs':
            stats = ucs(maze, callback=solve_callback)
        elif algorithm == 'greedy':
            stats = greedy(maze, h=heuristic, callback=solve_callback)
        elif algorithm == 'astar':
            stats = astar(maze, h=heuristic, weight=1.0, callback=solve_callback)
        elif algorithm == 'weighted_astar':
            stats = astar(maze, h=heuristic, weight=weight, callback=solve_callback)
        elif algorithm == 'idastar':
            # IDA* does not support callback in the same way, but we can solve it and trace path
            stats = idastar(maze)
        elif algorithm == 'bidirectional_bfs':
            stats = bidirectional_bfs(maze, callback=solve_callback)
        else:
            return jsonify({'error': f'Unsupported algorithm: {algorithm}'}), 400

        if not stats:
            return jsonify({'error': 'Solver failed to run'}), 500

        return jsonify({
            'solved': stats.solved,
            'path': stats.path,
            'steps': steps,
            'stats': {
                'algorithm': stats.algorithm,
                'solved': stats.solved,
                'path_length': stats.path_length,
                'nodes_expanded': stats.nodes_expanded,
                'elapsed_ms': stats.elapsed_ms,
                'peak_frontier': stats.peak_frontier
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

@app.route('/api/csp/color', methods=['POST'])
def color_path():
    try:
        data = request.json or {}
        path = data.get('path')
        n_colors = int(data.get('n_colors', 3))

        if not path or len(path) < 2:
            return jsonify({'success': False, 'error': 'Path is too short for coloring'}), 400

        cell_names = [f"cell_{r}_{c}" for r, c in path]
        csp = maze_path_coloring_csp(cell_names, n_colors=n_colors)
        result = backtrack(csp, use_mrv=True, use_lcv=True, use_fc=True)

        if result:
            # Format colors dictionary for return: {"cell_r_c": color_idx}
            return jsonify({
                'success': True,
                'colors': result
            })
        else:
            return jsonify({
                'success': False,
                'error': f'No coloring solution exists with {n_colors} colors.'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/csp/schedule', methods=['POST'])
def schedule_waypoints():
    try:
        data = request.json or {}
        path = data.get('path')
        
        if not path or len(path) < 2:
            return jsonify({'success': False, 'error': 'Path is too short for waypoint scheduling'}), 400

        cell_names = [f"cell_{r}_{c}" for r, c in path]
        
        # Select every 3rd cell (up to 5 cells) as waypoints
        waypoints = cell_names[::3][:5]
        time_slots = len(waypoints) + 2
        
        sched_csp = waypoint_scheduling_csp(waypoints, time_slots=time_slots)
        sched_result = backtrack(sched_csp, use_mrv=True, use_lcv=True, use_fc=True)

        if sched_result:
            return jsonify({
                'success': True,
                'waypoints': waypoints,
                'schedule': sched_result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Waypoint scheduling is infeasible with given time slots.'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/maze/benchmark', methods=['POST'])
def benchmark_maze():
    try:
        data = request.json or {}
        grid = data.get('grid')
        start = data.get('start')
        goal = data.get('goal')

        if not grid or not start or not goal:
            return jsonify({'error': 'Missing grid, start, or goal'}), 400

        maze = Maze(grid, start=tuple(start), goal=tuple(goal))

        algorithms = [
            ("BFS",             lambda: bfs(maze)),
            ("DFS",             lambda: dfs(maze)),
            ("UCS",             lambda: ucs(maze)),
            ("Bidirectional BFS", lambda: bidirectional_bfs(maze)),
            ("Greedy(Manhattan)", lambda: greedy(maze, "manhattan")),
            ("A*(Manhattan)",   lambda: astar(maze, "manhattan")),
            ("A*(Euclidean)",   lambda: astar(maze, "euclidean")),
            ("WA*(w=1.5)",      lambda: astar(maze, "manhattan", weight=1.5)),
            ("IDA*",            lambda: idastar(maze)),
        ]
        
        results = []
        for name, fn in algorithms:
            try:
                stats = fn()
                results.append({
                    'algorithm': name,
                    'solved': stats.solved,
                    'path_length': stats.path_length,
                    'nodes_expanded': stats.nodes_expanded,
                    'elapsed_ms': stats.elapsed_ms,
                    'peak_frontier': stats.peak_frontier
                })
            except Exception as alg_err:
                results.append({
                    'algorithm': name,
                    'solved': False,
                    'error': str(alg_err)
                })

        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/adversarial/move', methods=['POST'])
def adversarial_move():
    try:
        data = request.json or {}
        grid = data.get('grid')
        agent_pos = tuple(data.get('agent_pos'))
        agent_dir = data.get('agent_dir', [0, 0])
        ghosts = data.get('ghosts', [])
        if not ghosts and data.get('ghost_pos'):
            ghosts = [{'pos': data.get('ghost_pos'), 'type': 'chaser'}]

        mode = data.get('mode', 'manual')
        depth = int(data.get('depth', 3))

        if not grid or not agent_pos or not ghosts:
            return jsonify({'error': 'Missing grid, agent_pos, or ghosts'}), 400

        # Construct Maze wrapper for dimensions and wall queries
        maze = Maze(grid, start=agent_pos, goal=(len(grid)-1, len(grid[0])-1))
        goal_dist_map = precompute_goal_distances(maze)

        # 1. Compute Agent Next Move (Max player) - Only for AI mode
        eval_val = 0.0
        predicted_agent_only = []
        if mode == 'manual':
            next_agent = agent_pos
        elif mode == 'expectimax':
            eval_val, next_agent_path = expectimax(maze, agent_pos, tuple(ghosts[0]['pos']), depth, True, goal_dist_map)
            next_agent = next_agent_path[0] if next_agent_path else agent_pos
            predicted_agent_only = next_agent_path[::2]
        else:
            eval_val, next_agent_path = minimax(maze, agent_pos, tuple(ghosts[0]['pos']), depth, True, goal_dist_map)
            next_agent = next_agent_path[0] if next_agent_path else agent_pos
            predicted_agent_only = next_agent_path[::2]

        # 2. Compute Ghost Next Moves
        next_ghosts = []
        import random
        for g in ghosts:
            r, c = g['pos']
            gtype = g.get('type', 'chaser')
            
            neighbors = []
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < maze.rows and 0 <= nc < maze.cols and grid[nr][nc] != 1:
                    neighbors.append((nr, nc))
                    
            if not neighbors:
                next_ghosts.append({'pos': [r, c], 'type': gtype})
                continue
                
            target = next_agent
            
            if gtype == 'ambush':
                target = (next_agent[0] + agent_dir[0]*4, next_agent[1] + agent_dir[1]*4)
            elif gtype == 'scatter':
                target = (maze.rows - 1, 0)
            elif gtype == 'random':
                next_ghosts.append({'pos': list(random.choice(neighbors)), 'type': gtype})
                continue
                
            best_move = neighbors[0]
            min_dist = float('inf')
            for nr, nc in neighbors:
                dist = abs(nr - target[0]) + abs(nc - target[1])
                if dist < min_dist:
                    min_dist = dist
                    best_move = (nr, nc)
            
            next_ghosts.append({'pos': list(best_move), 'type': gtype})

        return jsonify({
            'next_agent_move': list(next_agent),
            'next_ghosts': next_ghosts,
            'predicted_agent_path': [list(p) for p in predicted_agent_only],
            'evaluation': eval_val
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/probabilistic/track', methods=['POST'])
def probabilistic_track():
    try:
        data = request.json or {}
        grid = data.get('grid')
        belief = data.get('belief')
        sensor_reading = int(data.get('sensor_reading', 0))
        agent_pos = tuple(data.get('agent_pos'))

        if not grid or not agent_pos:
            return jsonify({'error': 'Missing grid or agent_pos'}), 400

        maze = Maze(grid, start=agent_pos, goal=(len(grid)-1, len(grid[0])-1))
        rows, cols = len(grid), len(grid[0])

        # If no belief is initialized, start with uniform distribution over valid cells
        if not belief or len(belief) != rows or len(belief[0]) != cols:
            open_cells = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] != maze.WALL]
            prob = 1.0 / len(open_cells) if open_cells else 0.0
            belief = [[prob if grid[r][c] != maze.WALL else 0.0 for c in range(cols)] for r in range(rows)]

        updated_belief = hmm_belief_update(maze, belief, sensor_reading, agent_pos)

        return jsonify({
            'belief': updated_belief
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/probabilistic/bayes_ve', methods=['POST'])
def probabilistic_bayes_ve():
    try:
        result = variable_elimination_example()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/hybrid/decide', methods=['POST'])
def hybrid_decide_endpoint():
    try:
        data = request.json or {}
        grid = data.get('grid')
        agent_pos = tuple(data.get('agent_pos'))
        ghost_belief = data.get('ghost_belief')
        risk_tolerance = float(data.get('risk_tolerance', 0.5))

        if not grid or not agent_pos or not ghost_belief:
            return jsonify({'error': 'Missing grid, agent_pos, or ghost_belief'}), 400

        maze = Maze(grid, start=agent_pos, goal=(len(grid)-1, len(grid[0])-1))
        
        result = hybrid_decide(maze, agent_pos, ghost_belief, risk_tolerance)
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5001)
