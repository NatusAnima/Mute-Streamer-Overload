import itertools
from typing import List, Tuple, Set

def is_valid_placement(positions: List[Tuple[int, int]]) -> bool:
    """Check if a set of positions are valid (no same row, column, or diagonal)"""
    if len(positions) != len(set(positions)):
        return False
    
    rows = set()
    cols = set()
    diag1 = set()  # main diagonal (top-left to bottom-right)
    diag2 = set()  # anti-diagonal (top-right to bottom-left)
    
    for r, c in positions:
        if r in rows or c in cols:
            return False
        if (r - c) in diag1 or (r + c) in diag2:
            return False
            
        rows.add(r)
        cols.add(c)
        diag1.add(r - c)
        diag2.add(r + c)
    
    return True

def solve_gem_puzzle():
    """Solve the gem placement puzzle using backtracking"""
    # Define gem counts
    gems = {
        'R': 3,  # Red
        'W': 4,  # White
        'G': 3,  # Green
        'Y': 3,  # Gold (using O to avoid confusion)
        'B': 3   # Blue
    }
    
    # All possible positions on 4x4 board
    all_positions = [(r, c) for r in range(4) for c in range(4)]
    
    # Create list of gems to place
    gem_list = []
    for color, count in gems.items():
        gem_list.extend([color] * count)
    
    print(f"Placing {len(gem_list)} gems: {gem_list}")
    print(f"Total positions available: {len(all_positions)}")
    
    def backtrack(gem_index: int, board: List[List[str]], used_positions: Set[Tuple[int, int]]):
        """Backtracking function to place gems"""
        if gem_index == len(gem_list):
            return True  # All gems placed successfully
        
        current_color = gem_list[gem_index]
        
        # Get positions already used by this color
        color_positions = []
        for r in range(4):
            for c in range(4):
                if board[r][c] == current_color:
                    color_positions.append((r, c))
        
        # Try each available position
        for r, c in all_positions:
            if (r, c) in used_positions:
                continue
            
            # Check if this position conflicts with same color gems
            test_positions = color_positions + [(r, c)]
            if not is_valid_placement(test_positions):
                continue
            
            # Place the gem
            board[r][c] = current_color
            used_positions.add((r, c))
            
            # Recursively place next gem
            if backtrack(gem_index + 1, board, used_positions):
                return True
            
            # Backtrack
            board[r][c] = '.'
            used_positions.remove((r, c))
        
        return False
    
    # Initialize empty board
    board = [['.' for _ in range(4)] for _ in range(4)]
    used_positions = set()
    
    if backtrack(0, board, used_positions):
        return board
    else:
        return None

def print_board(board):
    """Print the board in a nice format"""
    if board is None:
        print("No solution found!")
        return
    
    print("\nSolution found:")
    print("  0 1 2 3")
    for i, row in enumerate(board):
        print(f"{i} {' '.join(row)}")
    
    # Verify solution
    print("\nVerifying solution:")
    colors = set()
    for row in board:
        for cell in row:
            if cell != '.':
                colors.add(cell)
    
    for color in colors:
        positions = []
        for r in range(4):
            for c in range(4):
                if board[r][c] == color:
                    positions.append((r, c))
        
        print(f"Color {color}: {positions} - Valid: {is_valid_placement(positions)}")

def count_gems_in_solution(board):
    """Count gems in the solution"""
    if board is None:
        return
    
    counts = {}
    for row in board:
        for cell in row:
            if cell != '.':
                counts[cell] = counts.get(cell, 0) + 1
    
    print(f"\nGem counts in solution: {counts}")

# Solve the puzzle
print("Solving gem placement puzzle...")
solution = solve_gem_puzzle()
print_board(solution)
count_gems_in_solution(solution)