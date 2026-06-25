"""
probabilistic.py

This module handles probabilistic reasoning for tracking a ghost's location.
It includes a Hidden Markov Model (HMM) implementation for belief updates based
on noisy sensor readings, and a Variable Elimination example for Bayesian Networks.
"""

from typing import List, Tuple, Dict, Any
from core.maze import Maze, DIRECTIONS

# ==============================================================================
# HMM GHOST TRACKING FILTER
# ==============================================================================

def get_valid_neighbours_with_self(maze: Maze, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Returns list of valid cell coordinates adjacent to pos, including pos itself."""
    r, c = pos
    nbrs = [pos]
    for dr, dc in DIRECTIONS.values():
        nr, nc = r + dr, c + dc
        if maze.in_bounds((nr, nc)) and maze.grid[nr][nc] != maze.WALL:
            nbrs.append((nr, nc))
    return nbrs

def sensor_probability(reading: int, true_dist: int) -> float:
    """Noisy sensor model: P(sensor_reading | true_distance)."""
    diff = abs(reading - true_dist)
    if diff == 0:
        return 0.70
    elif diff == 1:
        return 0.20
    elif diff == 2:
        return 0.08
    else:
        return 0.02  # Minimal probability to prevent beliefs from going to absolute zero

def hmm_belief_update(
    maze: Maze,
    current_belief: List[List[float]],
    sensor_reading: int,
    agent_pos: Tuple[int, int]
) -> List[List[float]]:
    """
    Performs a standard HMM belief update (filtering):
    1. Transition Update (prediction step)
    2. Observation Update (correction step)
    3. Normalization
    """
    rows = maze.rows
    cols = maze.cols

    # Initialize intermediate transition grid
    transition_belief = [[0.0] * cols for _ in range(rows)]

    # 1. Prediction (Transition) step: Ghost moves to adjacent cell or stays still
    for r in range(rows):
        for c in range(cols):
            if current_belief[r][c] > 0.0:
                pos = (r, c)
                nbrs = get_valid_neighbours_with_self(maze, pos)
                prob_share = current_belief[r][c] / len(nbrs)
                for nr, nc in nbrs:
                    transition_belief[nr][nc] += prob_share

    # 2. Correction (Observation) step: multiply by sensor likelihood
    updated_belief = [[0.0] * cols for _ in range(rows)]
    total_sum = 0.0
    ar, ac = agent_pos

    for r in range(rows):
        for c in range(cols):
            if maze.grid[r][c] == maze.WALL:
                updated_belief[r][c] = 0.0
                continue
            
            # Compute true Manhattan distance to agent
            true_dist = abs(r - ar) + abs(c - ac)
            likelihood = sensor_probability(sensor_reading, true_dist)
            updated_belief[r][c] = transition_belief[r][c] * likelihood
            total_sum += updated_belief[r][c]

    # 3. Normalization
    if total_sum > 0.0:
        for r in range(rows):
            for c in range(cols):
                updated_belief[r][c] /= total_sum
    else:
        # Fallback: Reset to uniform belief over valid open cells if likelihood wiped out
        open_cells = []
        for r in range(rows):
            for c in range(cols):
                if maze.grid[r][c] != maze.WALL:
                    open_cells.append((r, c))
        uniform_prob = 1.0 / len(open_cells) if open_cells else 0.0
        for r in range(rows):
            for c in range(cols):
                if maze.grid[r][c] != maze.WALL:
                    updated_belief[r][c] = uniform_prob
                else:
                    updated_belief[r][c] = 0.0

    return updated_belief

# ==============================================================================
# BAYESIAN NETWORK & VARIABLE ELIMINATION WORKED EXAMPLE
# ==============================================================================

def variable_elimination_example() -> Dict[str, Any]:
    """
    Worked example tracing Variable Elimination on a simple diagnostic Bayes Net:
      Variables:
        G: Ghost is Near (True/False)
        S: Motion Sensor Triggered (True/False)
        A: Alarm Active (Observed as True)
      Query: P(G | A=True)
      Eliminating variable: S
    """
    # Define CPTs as list of rows
    # Variable order in factors: G is 0/1 (False/True), S is 0/1 (False/True)
    # f1(G) = P(G)
    f1 = {False: 0.8, True: 0.2}
    
    # f2(G, S) = P(S | G)
    # Key: (G, S) -> Prob
    f2 = {
        (False, False): 0.9,
        (False, True):  0.1,
        (True, False):  0.1,
        (True, True):   0.9
    }
    
    # f3(S) = P(A=True | S)
    # Since Alarm is observed as True:
    f3 = {
        False: 0.05,  # P(A=True | S=False) (false alarm rate)
        True:  0.95   # P(A=True | S=True)  (alarm trigger rate)
    }

    # Step 1: Multiply factors containing S: f4(G, S) = f2(G, S) * f3(S)
    f4 = {}
    for G in [False, True]:
        for S in [False, True]:
            f4[(G, S)] = f2[(G, S)] * f3[S]

    # Step 2: Sum out S from f4(G, S) to get f5(G) = sum_S f4(G, S)
    f5 = {}
    for G in [False, True]:
        f5[G] = f4[(G, False)] + f4[(G, True)]

    # Step 3: Multiply f1(G) * f5(G) to get f6(G)
    f6 = {}
    for G in [False, True]:
        f6[G] = f1[G] * f5[G]

    # Step 4: Normalize f6(G) to get final posterior P(G | A=True)
    alpha = f6[False] + f6[True]
    p_g_given_a = {
        False: f6[False] / alpha,
        True:  f6[True] / alpha
    }

    return {
        "f1": f1,
        "f2": {str(k): v for k, v in f2.items()},
        "f3": f3,
        "f4": {str(k): v for k, v in f4.items()},
        "f5": f5,
        "f6": f6,
        "p_g_given_a": p_g_given_a,
        "alpha": alpha,
        "trace": [
            "1. Define initial factors based on model CPTs and observation Alarm=True.",
            f"   - Prior factor f1(G) = [P(G=F)={f1[False]:.2f}, P(G=T)={f1[True]:.2f}]",
            "   - Sensor model factor f2(G, S) = P(S | G)",
            f"   - Alarm sensor observation f3(S) = [P(A=T|S=F)={f3[False]:.2f}, P(A=T|S=T)={f3[True]:.2f}]",
            "2. Select variable S to eliminate.",
            "3. Group factors containing S: f2(G, S) and f3(S).",
            "4. Multiply factors: f4(G, S) = f2(G, S) * f3(S)",
            f"   - f4(F, F) = {f2[(False, False)]:.2f} * {f3[False]:.2f} = {f4[(False, False)]:.4f}",
            f"   - f4(F, T) = {f2[(False, True)]:.2f} * {f3[True]:.2f} = {f4[(False, True)]:.4f}",
            f"   - f4(T, F) = {f2[(True, False)]:.2f} * {f3[False]:.2f} = {f4[(True, False)]:.4f}",
            f"   - f4(T, T) = {f2[(True, True)]:.2f} * {f3[True]:.2f} = {f4[(True, True)]:.4f}",
            "5. Sum out S from f4: f5(G) = sum_S f4(G, S)",
            f"   - f5(False) = f4(F, F) + f4(F, T) = {f4[(False, False)]:.4f} + {f4[(False, True)]:.4f} = {f5[False]:.4f}",
            f"   - f5(True)  = f4(T, F) + f4(T, T) = {f4[(True, False)]:.4f} + {f4[(True, True)]:.4f} = {f5[True]:.4f}",
            "6. Multiply remaining factors containing query G: f6(G) = f1(G) * f5(G)",
            f"   - f6(False) = {f1[False]:.2f} * {f5[False]:.4f} = {f6[False]:.5f}",
            f"   - f6(True)  = {f1[True]:.2f} * {f5[True]:.4f} = {f6[True]:.5f}",
            "7. Normalize to find final query probability distribution:",
            f"   - Sum alpha = f6(False) + f6(True) = {alpha:.5f}",
            f"   - P(G=False | Alarm=True) = {f6[False]:.5f} / {alpha:.5f} = {p_g_given_a[False]:.4f}",
            f"   - P(G=True | Alarm=True)  = {f6[True]:.5f} / {alpha:.5f} = {p_g_given_a[True]:.4f}"
        ]
    }
