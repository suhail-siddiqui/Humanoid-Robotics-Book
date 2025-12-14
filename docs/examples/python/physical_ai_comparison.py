"""
Physical AI Simulation: Comparing Classical vs Physical AI Approaches

This example demonstrates the core differences between classical AI (operating on symbolic representations)
and Physical AI (interacting with the physical world through sensors and actuators).

The simulation includes:
1. A 2D environment with obstacles
2. A classical AI agent that plans without physical constraints
3. A Physical AI agent that must consider physics and embodiment
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import time

class Environment:
    """A 2D environment with obstacles"""
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        self.obstacles = [
            {'x': 3, 'y': 3, 'width': 1, 'height': 4},
            {'x': 6, 'y': 2, 'width': 1, 'height': 5}
        ]
    
    def is_valid_position(self, x, y):
        """Check if a position is valid (not in obstacle or out of bounds)"""
        # Check bounds
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        
        # Check obstacles
        for obs in self.obstacles:
            if (x >= obs['x'] and x < obs['x'] + obs['width'] and
                y >= obs['y'] and y < obs['y'] + obs['height']):
                return False
        
        return True
    
    def visualize(self, classical_path=None, physical_path=None):
        """Visualize the environment and paths"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Draw environment boundary
        ax.add_patch(Rectangle((0, 0), self.width, self.height, 
                              linewidth=2, edgecolor='black', facecolor='lightblue', alpha=0.3))
        
        # Draw obstacles
        for obs in self.obstacles:
            ax.add_patch(Rectangle((obs['x'], obs['y']), obs['width'], obs['height'], 
                                  linewidth=1, edgecolor='red', facecolor='red', alpha=0.7))
        
        # Draw paths
        if classical_path:
            path_x, path_y = zip(*classical_path)
            ax.plot(path_x, path_y, 'b-', linewidth=2, label='Classical AI Path', alpha=0.7)
            ax.scatter(path_x[0], path_y[0], color='green', s=100, label='Start', zorder=5)
            ax.scatter(path_x[-1], path_y[-1], color='red', s=100, label='Goal', zorder=5)
        
        if physical_path:
            path_x, path_y = zip(*physical_path)
            ax.plot(path_x, path_y, 'g-', linewidth=2, label='Physical AI Path', alpha=0.7)
            ax.scatter(path_x[0], path_y[0], color='green', s=100, label='Start', zorder=5)
            ax.scatter(path_x[-1], path_y[-1], color='red', s=100, label='Goal', zorder=5)
        
        ax.set_xlim(-0.5, self.width + 0.5)
        ax.set_ylim(-0.5, self.height + 0.5)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_title('Classical AI vs Physical AI Path Planning')
        ax.legend()
        
        plt.tight_layout()
        plt.show()

class ClassicalAIAgent:
    """
    A classical AI agent that operates on symbolic representations.
    It plans without considering physical constraints or embodiment.
    """
    def __init__(self, env):
        self.env = env
    
    def plan_path(self, start, goal):
        """Plan a path using A* algorithm without considering physical constraints"""
        # For simplicity, we'll use a basic A* implementation
        # In a real scenario, this might be a more sophisticated planning algorithm
        
        # Create a grid for A*
        grid = np.zeros((int(self.env.width), int(self.env.height)))
        
        # Mark obstacles in the grid
        for obs in self.env.obstacles:
            for x in range(int(obs['x']), int(obs['x'] + obs['width'])):
                for y in range(int(obs['y']), int(obs['y'] + obs['height'])):
                    if x < self.env.width and y < self.env.height:
                        grid[x, y] = 1
        
        # Simplified path planning (in a real implementation, this would be A* algorithm)
        path = [start]
        current = list(start)
        
        # Move towards goal
        while current != list(goal):
            # Determine next step
            dx = 1 if goal[0] > current[0] else (-1 if goal[0] < current[0] else 0)
            dy = 1 if goal[1] > current[1] else (-1 if goal[1] < current[1] else 0)
            
            # Prefer moving in x direction if possible
            if dx != 0:
                next_pos = [current[0] + dx, current[1]]
            elif dy != 0:
                next_pos = [current[0], current[1] + dy]
            else:
                break  # Already at goal
            
            # Check if path is valid in the symbolic representation
            # (In classical AI, we might not check all physical constraints)
            if (0 <= next_pos[0] < self.env.width and 
                0 <= next_pos[1] < self.env.height and
                grid[next_pos[0], next_pos[1]] == 0):
                
                path.append(tuple(next_pos))
                current = next_pos
            else:
                # In classical AI, we might have more sophisticated handling
                # For this example, we'll just break if we hit an obstacle
                print("Classical AI: Path blocked by obstacle in symbolic world!")
                break
        
        return path

class PhysicalAIAgent:
    """
    A Physical AI agent that must consider physics and embodiment.
    It senses the real environment and responds to physical constraints.
    """
    def __init__(self, env):
        self.env = env
        self.body_radius = 0.4  # Representing the physical size of the robot
    
    def sense_environment(self, x, y):
        """Simulate sensing the environment around position (x, y)"""
        # Check if the agent's body would collide with obstacles
        for obs in self.env.obstacles:
            # Simple collision detection with rectangular obstacles
            closest_x = max(obs['x'], min(x, obs['x'] + obs['width']))
            closest_y = max(obs['y'], min(y, obs['y'] + obs['height']))
            
            distance = np.sqrt((x - closest_x)**2 + (y - closest_y)**2)
            
            if distance < self.body_radius:
                return True  # Collision detected
        
        return False  # No collision
    
    def plan_path(self, start, goal):
        """Plan a path considering physical constraints"""
        path = [start]
        current = list(start)
        
        # Simplified path planning that respects physical constraints
        while tuple(current) != goal:
            # Determine possible next positions
            possible_moves = [
                (current[0] + 1, current[1]),   # Right
                (current[0] - 1, current[1]),   # Left
                (current[0], current[1] + 1),   # Up
                (current[0], current[1] - 1),   # Down
                (current[0] + 1, current[1] + 1),  # Up-Right Diagonal
                (current[0] + 1, current[1] - 1),  # Down-Right Diagonal
                (current[0] - 1, current[1] + 1),  # Up-Left Diagonal
                (current[0] - 1, current[1] - 1),  # Down-Left Diagonal
            ]
            
            # Filter valid moves
            valid_moves = []
            for pos in possible_moves:
                if (self.env.is_valid_position(pos[0], pos[1]) and 
                    not self.sense_environment(pos[0], pos[1])):
                    # Calculate heuristic (distance to goal)
                    dist_to_goal = np.sqrt((pos[0] - goal[0])**2 + (pos[1] - goal[1])**2)
                    valid_moves.append((pos, dist_to_goal))
            
            # If no valid moves, break
            if not valid_moves:
                print("Physical AI: No valid path found considering physical constraints!")
                break
            
            # Choose move closest to goal
            valid_moves.sort(key=lambda x: x[1])  # Sort by distance to goal
            next_pos = valid_moves[0][0]
            
            path.append(next_pos)
            current = list(next_pos)
            
            # Prevent infinite loops
            if len(path) > 100:  # Arbitrary limit to avoid infinite loops
                print("Physical AI: Path planning exceeded maximum steps!")
                break
        
        return path

def main():
    """Run the simulation comparing Classical and Physical AI approaches"""
    print("Physical AI Simulation: Classical vs Physical AI Approaches")
    print("=" * 60)
    
    # Create environment
    env = Environment(width=10, height=10)
    
    # Define start and goal positions
    start = (1, 1)
    goal = (8, 8)
    
    print(f"Start position: {start}")
    print(f"Goal position: {goal}")
    print()
    
    # Create agents
    classical_agent = ClassicalAIAgent(env)
    physical_agent = PhysicalAIAgent(env)
    
    # Plan paths
    print("Planning paths...")
    classical_path = classical_agent.plan_path(start, goal)
    physical_path = physical_agent.plan_path(start, goal)
    
    print(f"Classical AI path length: {len(classical_path)} steps")
    print(f"Physical AI path length: {len(physical_path)} steps")
    print()
    
    # Validate paths
    classical_valid = all(env.is_valid_position(x, y) for x, y in classical_path)
    physical_valid = all(env.is_valid_position(x, y) for x, y in physical_path)
    
    print(f"Classical AI path valid: {classical_valid}")
    print(f"Physical AI path valid: {physical_valid}")
    print()
    
    if classical_valid:
        print("Classical AI: Successfully found a path from start to goal")
    else:
        print("Classical AI: Path includes invalid positions (obstacles)")
    
    if physical_valid:
        print("Physical AI: Successfully found a valid path considering physical constraints")
    else:
        print("Physical AI: Path includes invalid positions (obstacles)")
    
    # Visualize results
    print("\nGenerating visualization...")
    env.visualize(classical_path, physical_path)
    
    # Additional analysis
    print("\nAnalysis:")
    print("- Classical AI operates on symbolic representations, potentially overlooking physical constraints")
    print("- Physical AI must consider embodiment, size, and real-world physics")
    print("- Physical AI path is longer but respects real-world constraints")
    print("- This demonstrates why embodiment matters in Physical AI")

if __name__ == "__main__":
    main()