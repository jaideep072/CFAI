"""
maze.py

This module defines the core data structures for the maze environment.
It includes the `State` class for positions, the `Maze` class for the grid 
and rules (successors, visibility), and the `MazeFactory` for generating 
various types of mazes (e.g., Prim's, Recursive Backtracking).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Set
import random
import time

Cell = Tuple[int, int]                      
Grid = List[List[int]]                          

DIRECTIONS: Dict[str, Cell] = {
    "N": (-1,  0),
    "S": ( 1,  0),
    "E": ( 0,  1),
    "W": ( 0, -1),
}

@dataclass(frozen=True)
class State:
    row: int
    col: int

    def __add__(self, delta: Cell) -> "State":
        return State(self.row + delta[0], self.col + delta[1])

    def as_tuple(self) -> Cell:
        return (self.row, self.col)

    def manhattan(self, other: "State") -> int:
        return abs(self.row - other.row) + abs(self.col - other.col)

class Maze:

    OPEN = 0
    WALL = 1

    def __init__(
        self,
        grid: Grid,
        start: Cell = (0, 0),
        goal: Cell = None,
        partially_observable: bool = False,
        vision_radius: int = 2,
    ):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0])
        self.start = State(*start)
        self.goal = State(*(goal or (self.rows - 1, self.cols - 1)))
        self.partially_observable = partially_observable
        self.vision_radius = vision_radius
        self._validate()

    def _validate(self):
        assert self.is_open(self.start.as_tuple()), "Start cell must be open"
        assert self.is_open(self.goal.as_tuple()),  "Goal cell must be open"

    def in_bounds(self, cell: Cell) -> bool:
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_open(self, cell: Cell) -> bool:
        r, c = cell
        return self.in_bounds((r, c)) and self.grid[r][c] != self.WALL

    def is_wall(self, cell: Cell) -> bool:
        return not self.is_open(cell)

    def successors(self, state: State) -> List[Tuple[str, State, float]]:
        result = []
        for action, delta in DIRECTIONS.items():
            nxt = state + delta
            r, c = nxt.as_tuple()
            if self.is_open((r, c)):
                # Return traversal cost based on cell type:
                # Open (0) -> 1.0, Mud (2) -> 3.0, Water (3) -> 6.0
                cell_val = self.grid[r][c]
                cost = 1.0
                if cell_val == 2:
                    cost = 3.0
                elif cell_val == 3:
                    cost = 6.0
                result.append((action, nxt, cost))
        return result

    def observe(self, state: State) -> Dict[Cell, int]:
        visible: Dict[Cell, int] = {}
        r0, c0 = state.row, state.col
        for dr in range(-self.vision_radius, self.vision_radius + 1):
            for dc in range(-self.vision_radius, self.vision_radius + 1):
                if abs(dr) + abs(dc) <= self.vision_radius:
                    cell = (r0 + dr, c0 + dc)
                    if self.in_bounds(cell):
                        visible[cell] = self.grid[r0 + dr][c0 + dc]
        return visible

    def to_graph(self) -> Dict[Cell, List[Cell]]:
        graph: Dict[Cell, List[Cell]] = {}
        for r in range(self.rows):
            for c in range(self.cols):
                if self.is_open((r, c)):
                    nbrs = []
                    for delta in DIRECTIONS.values():
                        nr, nc = r + delta[0], c + delta[1]
                        if self.is_open((nr, nc)):
                            nbrs.append((nr, nc))
                    graph[(r, c)] = nbrs
        return graph

    def render(
        self,
        path: List[Cell] = None,
        visited: Set[Cell] = None,
        current: Cell = None,
    ) -> str:
        path_set    = set(path or [])
        visited_set = set(visited or [])
        lines = []
        for r in range(self.rows):
            row_str = ""
            for c in range(self.cols):
                cell = (r, c)
                if cell == self.start.as_tuple():
                    row_str += " S"
                elif cell == self.goal.as_tuple():
                    row_str += " G"
                elif cell == current:
                    row_str += " @"
                elif cell in path_set:
                    row_str += " ·"
                elif cell in visited_set:
                    row_str += " ○"
                elif self.grid[r][c] == self.WALL:
                    row_str += " █"
                elif self.grid[r][c] == 2:
                    row_str += " ░"
                elif self.grid[r][c] == 3:
                    row_str += " ▓"
                else:
                    row_str += "  "
            lines.append(row_str)
        return "\n".join(lines)

    def __repr__(self):
        return f"Maze({self.rows}×{self.cols}, start={self.start}, goal={self.goal})"

class MazeFactory:

    @staticmethod
    def generate(rows: int, cols: int, seed: int = 42) -> Grid:
        rng = random.Random(seed)
                              
        grid = [[Maze.WALL] * cols for _ in range(rows)]

        def carve(r: int, c: int):
            grid[r][c] = Maze.OPEN
            dirs = [(0, 2), (0, -2), (2, 0), (-2, 0)]
            rng.shuffle(dirs)
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == Maze.WALL:
                    grid[r + dr // 2][c + dc // 2] = Maze.OPEN
                    carve(nr, nc)

        carve(0, 0)
                                    
        grid[0][0] = Maze.OPEN
        grid[rows - 1][cols - 1] = Maze.OPEN
        return grid

    @staticmethod
    def generate_prims(rows: int, cols: int, seed: int = 42) -> Grid:
        rng = random.Random(seed)
        grid = [[Maze.WALL] * cols for _ in range(rows)]
        
        # Start at a random odd cell
        start_r = 1 if rows > 1 else 0
        start_c = 1 if cols > 1 else 0
        grid[start_r][start_c] = Maze.OPEN
        
        # Walls list: list of (r, c, parent_r, parent_c) representing walls between cells
        walls = []
        
        def add_walls(r, c):
            for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                nr, nc = r + dr, c + dc
                if 0 < nr < rows - 1 and 0 < nc < cols - 1:
                    if grid[nr][nc] == Maze.WALL:
                        walls.append((nr, nc, r, c))
                        
        add_walls(start_r, start_c)
        
        while walls:
            idx = rng.randint(0, len(walls) - 1)
            nr, nc, pr, pc = walls.pop(idx)
            
            if grid[nr][nc] == Maze.WALL:
                # Carve path to parent and cell itself
                grid[nr][nc] = Maze.OPEN
                grid[(nr + pr) // 2][(nc + pc) // 2] = Maze.OPEN
                add_walls(nr, nc)
                
        # Ensure start and goal are open
        grid[0][0] = Maze.OPEN
        if rows > 1 and cols > 1:
            grid[0][1] = Maze.OPEN
            grid[1][0] = Maze.OPEN
        grid[rows - 1][cols - 1] = Maze.OPEN
        grid[rows - 2][cols - 1] = Maze.OPEN
        grid[rows - 1][cols - 2] = Maze.OPEN
        return grid

    @staticmethod
    def from_string(s: str) -> Grid:
        lines = s.strip().splitlines()
        grid = []
        for line in lines:
            row = [Maze.WALL if ch == "#" else Maze.OPEN for ch in line]
            grid.append(row)
        return grid

    @staticmethod
    def sample_small() -> "Maze":
        s = """
#########
#S  #   #
### # # #
#   # # #
# ### ###
#       #
##### # #
#     #G#
#########""".lstrip("\n")
        grid = MazeFactory.from_string(s)
        return Maze(grid, start=(1, 1), goal=(7, 7))

    @staticmethod
    def sample_large(seed: int = 42) -> "Maze":
        grid = MazeFactory.generate(21, 21, seed=seed)
        return Maze(grid, start=(0, 0), goal=(20, 20))

@dataclass
class SolveStats:
    algorithm: str
    solved: bool
    path_length: int
    nodes_expanded: int
    elapsed_ms: float
    peak_frontier: int
    path: List[Cell] = field(default_factory=list)

    def report(self) -> str:
        status = "✓ SOLVED" if self.solved else "✗ NO PATH"
        return (
            f"[{self.algorithm}] {status}\n"
            f"  Path length    : {self.path_length}\n"
            f"  Nodes expanded : {self.nodes_expanded}\n"
            f"  Peak frontier  : {self.peak_frontier}\n"
            f"  Time           : {self.elapsed_ms:.2f} ms\n"
        )
