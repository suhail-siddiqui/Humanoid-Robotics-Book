"""
Humanoid Robot Design Concept Demonstrator

This script demonstrates key design concepts for humanoid robots,
focusing on degrees of freedom, kinematic chains, and balance considerations.
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Tuple, List


@dataclass
class Joint:
    """Represents a robotic joint with position and constraints."""
    name: str
    min_angle: float  # radians
    max_angle: float  # radians
    current_angle: float = 0.0  # radians
    axis: Tuple[float, float, float] = (0, 0, 1)  # rotation axis


@dataclass
class Link:
    """Represents a rigid link between joints."""
    name: str
    length: float  # meters
    mass: float    # kg
    com_offset: Tuple[float, float, float] = (0, 0, 0)  # center of mass offset


@dataclass
class Leg:
    """Represents a simplified leg with hip, knee, and ankle joints."""
    name: str
    segments: List[Tuple[Joint, Link]]  # (joint, link) pairs
    
    def calculate_com(self) -> float:
        """Calculate center of mass along the leg."""
        total_mass = sum(link.mass for _, link in self.segments)
        if total_mass == 0:
            return 0
        
        weighted_sum = 0
        position = 0  # Starting position
        
        for joint, link in self.segments:
            # Position of this segment's COM
            seg_pos = position + link.length / 2
            weighted_sum += seg_pos * link.mass
            position += link.length
            
        return weighted_sum / total_mass
    
    def calculate_reach(self) -> float:
        """Calculate maximum reach of the leg."""
        return sum(link.length for _, link in self.segments)


class HumanoidRobot:
    """
    A simplified model of a humanoid robot to demonstrate design principles.
    
    This class shows how design decisions impact robot capabilities.
    """
    
    def __init__(self, name: str, hip_height: float, leg_segments: List[Tuple[Joint, Link]]):
        self.name = name
        self.hip_height = hip_height  # Height from ground to hip joint
        self.left_leg = Leg("Left Leg", leg_segments.copy())
        self.right_leg = Leg("Right Leg", leg_segments.copy())
        
        # Calculate derived properties based on design
        self.total_height = self._calculate_total_height()
        self.com_height = self._calculate_com_height()
        self.stability_margin = self._calculate_stability_margin()
    
    def _calculate_total_height(self) -> float:
        """Estimate total height based on leg design."""
        max_leg_length = self.left_leg.calculate_reach()
        # Approximate torso height as roughly equal to hip height
        return max_leg_length + self.hip_height
    
    def _calculate_com_height(self) -> float:
        """Calculate approximate center of mass height."""
        # Simplified calculation assuming legs contribute half of total mass
        leg_com = self.left_leg.calculate_com()
        return self.hip_height + leg_com
    
    def _calculate_stability_margin(self) -> float:
        """Calculate stability based on foot size and stance width."""
        # Simplified stability metric
        # Larger feet and wider stances improve stability
        foot_size = 0.15  # meters (approximate)
        stance_width = 0.3  # meters (distance between feet)
        return foot_size * stance_width / self.total_height
    
    def get_dof_count(self) -> int:
        """Return total degrees of freedom in both legs."""
        return len(self.left_leg.segments) + len(self.right_leg.segments)
    
    def evaluate_balance(self, tilt_angle: float) -> bool:
        """
        Evaluate if the robot would maintain balance at a given tilt.
        
        Args:
            tilt_angle: Angle of tilt in radians
            
        Returns:
            True if robot would remain balanced, False otherwise
        """
        # Simplified balance check based on COG position
        # In reality, this would need more complex physics simulation
        max_tilt = 0.2  # Maximum tilt before considering unbalanced
        return abs(tilt_angle) < max_tilt
    
    def estimate_power_consumption(self) -> float:
        """
        Estimate power consumption per meter traveled.
        
        Returns:
            Estimated power consumption in watts
        """
        # Simplified estimation based on robot size and design
        # Heavier robots require more power
        estimated_weight = self.get_estimated_weight()
        base_power = 50  # base power consumption
        weight_factor = estimated_weight / 50  # normalized to 50kg robot
        return base_power * weight_factor
    
    def get_estimated_weight(self) -> float:
        """Estimate robot weight based on component masses."""
        left_leg_weight = sum(link.mass for _, link in self.left_leg.segments)
        right_leg_weight = sum(link.mass for _, link in self.right_leg.segments)
        # Approximate torso/head/arms as equivalent to leg weights combined
        torso_weight = (left_leg_weight + right_leg_weight)
        return left_leg_weight + right_leg_weight + torso_weight


def demonstrate_design_tradeoffs():
    """Demonstrate tradeoffs in humanoid design."""
    print("=== Humanoid Robot Design Concepts ===\n")
    
    # Define joints for a simple leg
    hip_joint = Joint("Hip", -math.pi/2, math.pi/2, axis=(0, 1, 0))
    knee_joint = Joint("Knee", 0, math.pi * 0.9, axis=(0, 1, 0))
    ankle_joint = Joint("Ankle", -math.pi/4, math.pi/4, axis=(0, 1, 0))
    
    # Define links for a simple leg
    thigh = Link("Thigh", 0.4, 5.0, (0.2, 0, 0))  # 40cm, 5kg
    shin = Link("Shin", 0.4, 4.0, (0.2, 0, 0))    # 40cm, 4kg
    foot = Link("Foot", 0.2, 1.0, (0.1, 0, 0))    # 20cm, 1kg
    
    # Create leg segments: (joint, link) pairs
    leg_segments = [
        (hip_joint, thigh),
        (knee_joint, shin),
        (ankle_joint, foot)
    ]
    
    # Create robot with specific design parameters
    robot = HumanoidRobot("DemoBot", hip_height=0.9, leg_segments=leg_segments)
    
    print(f"Robot: {robot.name}")
    print(f"Total Height: {robot.total_height:.2f} m")
    print(f"Estimated Weight: {robot.get_estimated_weight():.1f} kg")
    print(f"Degrees of Freedom (legs only): {robot.get_dof_count()}")
    print(f"Center of Mass Height: {robot.com_height:.2f} m")
    print(f"Stability Margin: {robot.stability_margin:.3f}")
    print(f"Estimated Power Consumption: {robot.estimate_power_consumption():.1f} W/m")
    
    print("\n=== Balance Evaluation ===")
    for tilt in [0.1, 0.15, 0.25]:
        balanced = robot.evaluate_balance(tilt)
        print(f"Tilt {math.degrees(tilt):.1f}°: {'Balanced' if balanced else 'Unbalanced'}")
    
    print("\n=== Design Trade-offs ===")
    print("1. Height vs. Stability: Taller robots have higher COG, reducing stability")
    print("2. Weight vs. Power: Heavier robots consume more power")
    print("3. DOF vs. Complexity: More joints enable better movement but increase control complexity")
    print("4. Size vs. Environment: Larger robots need more space but can handle bigger payloads")


if __name__ == "__main__":
    demonstrate_design_tradeoffs()