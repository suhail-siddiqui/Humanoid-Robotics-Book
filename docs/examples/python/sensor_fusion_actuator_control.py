"""
Actuator Control and Sensor Fusion Example for Humanoid Robots

This example demonstrates key concepts from Module 2, Lesson 2:
- Integration of multiple sensors (IMU, encoders, force sensors)
- Sensor fusion for improved state estimation
- Actuator control with feedback
- Safety considerations in actuator control
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R
import time

class HumanoidJoint:
    """
    Represents a single joint in a humanoid robot with actuator and sensors
    """
    def __init__(self, joint_name, gear_ratio=100, max_torque=50.0, max_velocity=5.0):
        self.name = joint_name
        self.gear_ratio = gear_ratio  # Gear ratio of the actuator
        self.max_torque = max_torque  # Maximum torque in Nm
        self.max_velocity = max_velocity  # Maximum velocity in rad/s
        
        # Initial state
        self.angle = 0.0  # Current angle in radians
        self.velocity = 0.0  # Current velocity in rad/s
        self.torque = 0.0  # Current torque in Nm
        
        # Sensor values
        self.encoder_reading = 0.0  # Encoder provides angle measurement
        self.torque_sensor_reading = 0.0  # Torque sensor reading
        self.temperature = 25.0  # Temperature in Celsius
        
        # Safety limits
        self.angle_min = -np.pi  # Minimum angle (-180 degrees)
        self.angle_max = np.pi   # Maximum angle (180 degrees)
        
    def update(self, command_torque, dt):
        """
        Update the joint state based on the commanded torque
        """
        # Apply physical constraints to the command
        command_torque = np.clip(command_torque, -self.max_torque, self.max_torque)
        
        # Simple physics model: torque -> acceleration -> velocity -> position
        # In reality, this would involve more complex dynamics
        angular_acceleration = command_torque / (0.1 * self.gear_ratio)  # Simplified inertia model
        
        # Update velocity and position using basic integration
        self.velocity += angular_acceleration * dt
        self.velocity = np.clip(self.velocity, -self.max_velocity, self.max_velocity)
        self.angle += self.velocity * dt
        
        # Apply joint limits
        self.angle = np.clip(self.angle, self.angle_min, self.angle_max)
        
        # Update sensor readings (with some simulated noise to make it realistic)
        self.encoder_reading = self.angle + np.random.normal(0, 0.001)  # Small encoder noise
        self.torque_sensor_reading = command_torque + np.random.normal(0, 0.1)  # Torque sensor noise
        self.temperature += 0.01 * abs(command_torque)  # Temperature increases with torque
        
        # Update the actual torque to what was applied
        self.torque = command_torque
        
    def get_state(self):
        """Return the current state of the joint"""
        return {
            'angle': self.angle,
            'velocity': self.velocity,
            'torque': self.torque,
            'encoder_reading': self.encoder_reading,
            'torque_sensor_reading': self.torque_sensor_reading,
            'temperature': self.temperature
        }

class IMUSensor:
    """
    Inertial Measurement Unit sensor
    """
    def __init__(self, position=np.array([0, 0, 0])):
        self.position = position
        self.orientation = R.from_quat([0, 0, 0, 1])  # Initially aligned
        self.angular_velocity = np.array([0.0, 0.0, 0.0])
        self.linear_acceleration = np.array([0.0, 0.0, -9.81])  # Gravity at rest
        
        # Simulated drift and noise parameters
        self.gyro_drift = np.random.normal(0, 0.001, 3)
        self.accel_noise = 0.01
        
    def update_orientation(self, dt, external_angular_velocity):
        """Update orientation based on angular velocity"""
        # Add some process noise
        process_noise = np.random.normal(0, 0.0001, 3)
        effective_ang_vel = external_angular_velocity + self.gyro_drift + process_noise
        
        # Update orientation (simplified integration for demonstration)
        angle = np.linalg.norm(effective_ang_vel) * dt
        if angle > 0:
            axis = effective_ang_vel / np.linalg.norm(effective_ang_vel)
            dR = R.from_rotvec(axis * angle)
            self.orientation = dR * self.orientation
        
        self.angular_velocity = effective_ang_vel
        
    def get_measurement(self):
        """Get the current measurement with noise"""
        # Add noise to measurements
        noisy_angular_velocity = self.angular_velocity + np.random.normal(0, 0.01, 3)
        noisy_linear_acceleration = self.linear_acceleration + np.random.normal(0, self.accel_noise, 3)
        noisy_orientation = self.orientation.as_quat() + np.random.normal(0, 0.001, 4)
        noisy_orientation = noisy_orientation / np.linalg.norm(noisy_orientation)  # Renormalize
        
        return {
            'orientation': noisy_orientation,
            'angular_velocity': noisy_angular_velocity,
            'linear_acceleration': noisy_linear_acceleration
        }

class SensorFusion:
    """
    Simple sensor fusion system combining IMU, encoder, and other sensor data
    """
    def __init__(self):
        self.process_noise = 0.1
        self.measurement_noise = 0.1
        self.estimate = 0.0
        self.uncertainty = 1.0
        
    def update_with_measurement(self, measurement, measurement_uncertainty=0.1):
        """
        Update estimate using a new measurement (simplified Kalman filter approach)
        """
        # Kalman gain calculation
        kalman_gain = self.uncertainty / (self.uncertainty + measurement_uncertainty)
        
        # Update estimate
        self.estimate = self.estimate + kalman_gain * (measurement - self.estimate)
        
        # Update uncertainty
        self.uncertainty = (1 - kalman_gain) * self.uncertainty
        
        return self.estimate

class HumanoidRobot:
    """
    Simplified humanoid robot model with multiple joints and sensors
    """
    def __init__(self):
        # Create joints (simplified - just 3 for this example)
        self.joints = {
            'hip': HumanoidJoint('hip', gear_ratio=150, max_torque=80.0),
            'knee': HumanoidJoint('knee', gear_ratio=100, max_torque=60.0),
            'ankle': HumanoidJoint('ankle', gear_ratio=80, max_torque=40.0)
        }
        
        # Create IMU sensors
        self.imus = {
            'torso': IMUSensor(position=np.array([0, 0, 0.5])),
            'foot': IMUSensor(position=np.array([0, 0, 0]))
        }
        
        # Sensor fusion objects
        self.balance_estimator = SensorFusion()
        
        # Robot state
        self.time = 0.0
        self.dt = 0.01  # 100Hz update rate
        
    def update(self, joint_commands):
        """
        Update the robot with new commands
        """
        # Update all joints with their respective commands
        for joint_name, command_torque in joint_commands.items():
            if joint_name in self.joints:
                self.joints[joint_name].update(command_torque, self.dt)
        
        # Simulate robot dynamics based on joint movements
        # This is a very simplified model for demonstration
        hip_angle = self.joints['hip'].angle
        knee_angle = self.joints['knee'].angle
        ankle_angle = self.joints['ankle'].angle
        
        # Simulate effect on IMUs based on joint angles
        # This is a simplified model - in reality, the relationship would be more complex
        body_tilt = 0.1 * hip_angle + 0.05 * knee_angle
        external_ang_vel = np.array([body_tilt * 2, 0, 0])  # Simplified angular velocity
        
        # Update IMUs
        for name, imu in self.imus.items():
            imu.update_orientation(self.dt, external_ang_vel)
        
        # Update sensor fusion
        # Use encoder value from hip joint as a balance-related measurement
        hip_encoder_reading = self.joints['hip'].encoder_reading
        self.balance_estimator.update_with_measurement(hip_encoder_reading)
        
        # Increment time
        self.time += self.dt
    
    def get_all_sensory_data(self):
        """
        Get all sensory data from the robot
        """
        sensory_data = {}
        
        # Get joint sensor data
        for joint_name, joint in self.joints.items():
            sensory_data[f'{joint_name}_state'] = joint.get_state()
        
        # Get IMU data
        for imu_name, imu in self.imus.items():
            sensory_data[f'{imu_name}_imu'] = imu.get_measurement()
        
        # Get fused data
        sensory_data['balance_estimate'] = self.balance_estimator.estimate
        
        return sensory_data
    
    def check_safety_limits(self):
        """
        Check if the robot is within safety limits
        """
        safety_status = {
            'safe': True,
            'issues': []
        }
        
        # Check joint limits
        for joint_name, joint in self.joints.items():
            state = joint.get_state()
            
            # Check temperature
            if state['temperature'] > 60:  # Overheating
                safety_status['safe'] = False
                safety_status['issues'].append(f"{joint_name} overheating: {state['temperature']:.1f}°C")
            
            # Check torque limits
            if abs(state['torque']) > joint.max_torque * 0.9:  # 90% of max as warning
                safety_status['safe'] = False
                safety_status['issues'].append(f"{joint_name} approaching torque limit: {abs(state['torque']):.1f}Nm")
        
        return safety_status

def simulate_control_loop(robot, duration=5.0):
    """
    Simulate a control loop for the humanoid robot
    """
    # Setup visualization
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
    
    time_data = []
    hip_angle_data = []
    knee_angle_data = []
    ankle_angle_data = []
    torso_orientation_data = []
    
    start_time = robot.time
    
    print("Starting simulation...")
    print("Time(s)\tHip\t\tKnee\t\tAnkle\t\tSafety")
    print("-" * 70)
    
    while robot.time - start_time < duration:
        # Simple control strategy: move to a target position and hold
        target_angles = {
            'hip': 0.1 * np.sin(robot.time * 2),   # Oscillate hip
            'knee': 0.05 * np.sin(robot.time * 2),  # Follow hip movement
            'ankle': -0.1 * np.sin(robot.time * 2)  # Counter-balance
        }
        
        # Calculate simple PD control commands
        joint_commands = {}
        for joint_name in robot.joints.keys():
            current_angle = robot.joints[joint_name].angle
            error = target_angles[joint_name] - current_angle
            velocity = robot.joints[joint_name].velocity
            
            # PD control: torque = Kp * error + Kd * velocity
            torque = 15.0 * error - 0.5 * velocity
            joint_commands[joint_name] = torque
        
        # Update robot
        robot.update(joint_commands)
        
        # Check safety
        safety_status = robot.check_safety_limits()
        
        # Print status
        if robot.time % 1.0 < robot.dt:  # Print every second
            print(f"{robot.time:6.2f}\t{robot.joints['hip'].angle:6.3f}\t\t"
                  f"{robot.joints['knee'].angle:6.3f}\t\t{robot.joints['ankle'].angle:6.3f}\t\t"
                  f"{'OK' if safety_status['safe'] else 'ISSUES'}")
        
        # Collect data for plotting
        time_data.append(robot.time)
        hip_angle_data.append(robot.joints['hip'].angle)
        knee_angle_data.append(robot.joints['knee'].angle)
        ankle_angle_data.append(robot.joints['ankle'].angle)
        
        # Get torso orientation (simplified to just the roll angle)
        torso_data = robot.get_all_sensory_data()['torso_imu']
        # Extract roll angle from quaternion (simplified)
        roll_angle = 2 * np.arcsin(torso_data['orientation'][0])  # Simplified
        torso_orientation_data.append(roll_angle)
        
        # Check safety and possibly adjust control
        if not safety_status['safe']:
            print(f"Safety issues at time {robot.time:.2f}s: {safety_status['issues']}")
            # In a real system, we would implement emergency stop or remedial action
            # For this simulation, we'll just continue but log the issue
    
    print(f"\nSimulation completed after {duration}s")
    
    # Plot the results
    ax1.plot(time_data, hip_angle_data, label='Hip Angle', linewidth=2)
    ax1.plot(time_data, knee_angle_data, label='Knee Angle', linewidth=2)
    ax1.plot(time_data, ankle_angle_data, label='Ankle Angle', linewidth=2)
    ax1.set_ylabel('Joint Angle (rad)')
    ax1.set_title('Joint Angles Over Time')
    ax1.legend()
    ax1.grid(True)
    
    ax2.plot(time_data, torso_orientation_data, 'g-', linewidth=2, label='Torso Roll Angle')
    ax2.set_ylabel('Roll Angle (rad)')
    ax2.set_title('Torso Orientation Over Time')
    ax2.legend()
    ax2.grid(True)
    
    # Show sensory data at the end
    sensory_data = robot.get_all_sensory_data()
    ax3.text(0.05, 0.8, f"Balance Estimate: {sensory_data['balance_estimate']:.3f}", 
             transform=ax3.transAxes, fontsize=12, verticalalignment='top')
    ax3.text(0.05, 0.6, f"Hip Angle: {sensory_data['hip_state']['angle']:.3f}", 
             transform=ax3.transAxes, fontsize=12, verticalalignment='top')
    ax3.text(0.05, 0.4, f"Knee Torque: {sensory_data['knee_state']['torque_sensor_reading']:.3f}", 
             transform=ax3.transAxes, fontsize=12, verticalalignment='top')
    ax3.text(0.05, 0.2, f"Ankle Temp: {sensory_data['ankle_state']['temperature']:.1f}°C", 
             transform=ax3.transAxes, fontsize=12, verticalalignment='top')
    ax3.set_title('Final Sensory Data')
    ax3.axis('off')
    
    plt.tight_layout()
    plt.show()

def main():
    """
    Main function to demonstrate sensor fusion and actuator control
    """
    print("Humanoid Robot Actuator Control and Sensor Fusion")
    print("=" * 55)
    print("This example demonstrates:")
    print("1. Multiple joint actuators with sensors")
    print("2. IMU sensors for balance information") 
    print("3. Sensor fusion for state estimation")
    print("4. Safety monitoring and limits")
    print()
    
    # Create robot instance
    robot = HumanoidRobot()
    
    # Demonstrate individual joint control
    print("Testing individual joint control...")
    print(f"Hip joint initial state: {robot.joints['hip'].get_state()}")
    
    # Apply a small torque to the hip for a brief moment
    for _ in range(100):  # 100 steps = 1 second at 0.01 dt
        robot.update({'hip': 10.0})  # Apply 10 Nm to hip
        time.sleep(0.001)  # Small delay for real-time feel
    
    print(f"Hip joint after torque: {robot.joints['hip'].get_state()}")
    print()
    
    # Run full control simulation
    simulate_control_loop(robot, duration=5.0)
    
    # Demonstrate sensor fusion
    print("\nDemonstrating Sensor Fusion:")
    print("The robot combines information from encoders, IMUs, and other sensors")
    print("to estimate its balance state more accurately than any single sensor.")
    
    # Show how different sensors contribute
    sensory_data = robot.get_all_sensory_data()
    
    print(f"\nHip joint encoder reading: {sensory_data['hip_state']['encoder_reading']:.3f}")
    print(f"Torso IMU roll angle: {2*np.arcsin(sensory_data['torso_imu']['orientation'][0]):.3f}")  # Simplified
    print(f"Fused balance estimate: {sensory_data['balance_estimate']:.3f}")

if __name__ == "__main__":
    main()