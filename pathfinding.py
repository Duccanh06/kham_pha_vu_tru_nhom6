"""
Pathfinding Algorithms Module
Implements: BFS, DFS, A*, Dijkstra
Used by enemies for navigation and mini-map visualization.
"""
import heapq
import math
from collections import deque


# ─── Helpers ──────────────────────────────────────────────────────────────────
def heuristic_manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def heuristic_euclidean(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def get_neighbors(grid, node, diagonal=False):
    """Return passable neighbors of node (row, col)."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    r, c = node
    dirs = [(0,1),(1,0),(0,-1),(-1,0)]
    if diagonal:
        dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
    result = []
    for dr, dc in dirs:
        nr, nc = r+dr, c+dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 1:
            result.append((nr, nc))
    return result

def reconstruct_path(came_from, start, goal):
    path = []
    node = goal
    while node != start:
        path.append(node)
        node = came_from[node]
    path.append(start)
    path.reverse()
    return path


# ─── BFS ──────────────────────────────────────────────────────────────────────
def bfs(grid, start, goal):
    """
    Breadth-First Search — guarantees shortest path on unweighted grid.
    Returns (path, visited_order)
    """
    queue = deque([start])
    came_from = {start: None}
    visited_order = [start]

    while queue:
        current = queue.popleft()
        if current == goal:
            path = []
            node = goal
            while node is not None:
                path.append(node)
                node = came_from[node]
            path.reverse()
            return path, visited_order

        for neighbor in get_neighbors(grid, current):
            if neighbor not in came_from:
                came_from[neighbor] = current
                visited_order.append(neighbor)
                queue.append(neighbor)

    return [], visited_order  # No path found


# ─── DFS ──────────────────────────────────────────────────────────────────────
def dfs(grid, start, goal):
    """
    Depth-First Search — explores deep paths first (not optimal).
    Returns (path, visited_order)
    """
    stack = [start]
    came_from = {start: None}
    visited_order = []

    while stack:
        current = stack.pop()
        if current in visited_order:
            continue
        visited_order.append(current)

        if current == goal:
            path = []
            node = goal
            while node is not None:
                path.append(node)
                node = came_from[node]
            path.reverse()
            return path, visited_order

        for neighbor in get_neighbors(grid, current):
            if neighbor not in came_from:
                came_from[neighbor] = current
                stack.append(neighbor)

    return [], visited_order


# ─── A* ───────────────────────────────────────────────────────────────────────
def astar(grid, start, goal):
    """
    A* Search — optimal with heuristic guidance.
    Returns (path, visited_order)
    """
    open_set = []
    heapq.heappush(open_set, (0 + heuristic_manhattan(start, goal), 0, start))
    came_from = {start: None}
    g_score = {start: 0}
    visited_order = []

    while open_set:
        f, g, current = heapq.heappop(open_set)
        if current in visited_order:
            continue
        visited_order.append(current)

        if current == goal:
            return reconstruct_path(came_from, start, goal), visited_order

        for neighbor in get_neighbors(grid, current, diagonal=True):
            dr = abs(neighbor[0]-current[0])
            dc = abs(neighbor[1]-current[1])
            step_cost = 1.414 if (dr+dc == 2) else 1.0
            tentative_g = g_score[current] + step_cost

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                came_from[neighbor] = current
                f_new = tentative_g + heuristic_manhattan(neighbor, goal)
                heapq.heappush(open_set, (f_new, tentative_g, neighbor))

    return [], visited_order


# ─── Dijkstra ─────────────────────────────────────────────────────────────────
def dijkstra(grid, start, goal):
    """
    Dijkstra's Algorithm — optimal on weighted graphs.
    Grid cells with value 2 = high-cost terrain (asteroids = 5x cost).
    Returns (path, visited_order)
    """
    def cell_cost(r, c):
        v = grid[r][c]
        if v == 2: return 3.0   # debris field
        if v == 3: return 5.0   # asteroid cluster
        return 1.0

    open_set = [(0, start)]
    dist = {start: 0}
    came_from = {start: None}
    visited_order = []

    while open_set:
        d, current = heapq.heappop(open_set)
        if current in visited_order:
            continue
        visited_order.append(current)

        if current == goal:
            return reconstruct_path(came_from, start, goal), visited_order

        r, c = current
        for neighbor in get_neighbors(grid, current, diagonal=True):
            nr, nc = neighbor
            dr = abs(nr-r); dc = abs(nc-c)
            move_cost = (1.414 if (dr+dc==2) else 1.0) * cell_cost(nr, nc)
            new_d = dist[current] + move_cost

            if neighbor not in dist or new_d < dist[neighbor]:
                dist[neighbor] = new_d
                came_from[neighbor] = current
                heapq.heappush(open_set, (new_d, neighbor))

    return [], visited_order


# ─── Algorithm selector ───────────────────────────────────────────────────────
ALGORITHMS = {
    'BFS':      bfs,
    'DFS':      dfs,
    'A*':       astar,
    'Dijkstra': dijkstra,
}

def find_path(grid, start, goal, algorithm='A*'):
    func = ALGORITHMS.get(algorithm, astar)
    return func(grid, start, goal)
