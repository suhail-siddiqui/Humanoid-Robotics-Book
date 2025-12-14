"""
Hardware Integration with AI Systems

This example demonstrates key concepts from Module 4, Lesson 1:
- Hardware-software interfaces for humanoid robots
- Integration of sensors with AI systems
- Real-time performance considerations
- Communication protocols between hardware and AI
"""

import time
import threading
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import queue
import json
from datetime import datetime

class MockHardwareInterface:
    """
    Simulates a hardware interface for a humanoid robot joint
    """
    def __init__(self, joint_name, position=0.0, velocity=0.0, torque=0.0):
        self.joint_name = joint_name
        self.position = position
        self.velocity = velocity
        self.torque = torque
        self.temperature = 25.0  # Temperature in Celsius
        self.is_connected = True
        
        # Simulate hardware delay and noise
        self.communication_delay = 0.001  # 1 ms delay
        self.noise_level = 0.001  # Noise level in measurements
        
        # Hardware limits
        self.pos_limit_min = -np.pi
        self.pos_limit_max = np.pi
        self.vel_limit = 5.0
        self.torque_limit = 50.0
        
        # Error simulation
        self.error_rate = 0.001  # 0.1% chance of error per call
        self.hardware_errors = []
    
    def read_position(self):
        """Read position from hardware with simulated delay and noise"""
        time.sleep(self.communication_delay)
        
        # Simulate sensor noise
        noisy_position = self.position + np.random.normal(0, self.noise_level)
        
        # Simulate occasional hardware errors
        if np.random.random() < self.error_rate:
            self.hardware_errors.append(f"Position reading error at {time.time()}")
            # Return a safe value instead of an error
            return np.clip(self.position, self.pos_limit_min, self.pos_limit_max)
        
        return np.clip(noisy_position, self.pos_limit_min, self.pos_limit_max)
    
    def read_velocity(self):
        """Read velocity from hardware with simulated delay and noise"""
        time.sleep(self.communication_delay)
        
        # Simulate sensor noise
        noisy_velocity = self.velocity + np.random.normal(0, self.noise_level/5)
        
        # Simulate occasional hardware errors
        if np.random.random() < self.error_rate:
            self.hardware_errors.append(f"Velocity reading error at {time.time()}")
            return np.clip(self.velocity, -self.vel_limit, self.vel_limit)
        
        return np.clip(noisy_velocity, -self.vel_limit, self.vel_limit)
    
    def read_torque(self):
        """Read torque from hardware with simulated delay and noise"""
        time.sleep(self.communication_delay)
        
        # Simulate sensor noise
        noisy_torque = self.torque + np.random.normal(0, self.noise_level*10)
        
        # Simulate occasional hardware errors
        if np.random.random() < self.error_rate:
            self.hardware_errors.append(f"Torque reading error at {time.time()}")
            return np.clip(self.torque, -self.torque_limit, self.torque_limit)
        
        return np.clip(noisy_torque, -self.torque_limit, self.torque_limit)
    
    def read_temperature(self):
        """Read temperature from hardware"""
        time.sleep(self.communication_delay * 0.1)  # Temperature reads faster
        return self.temperature
    
    def write_torque(self, torque_cmd):
        """Send torque command to hardware"""
        time.sleep(self.communication_delay)
        
        # Apply limits
        torque_cmd = np.clip(torque_cmd, -self.torque_limit, self.torque_limit)
        
        # Simulate the effect of the command on the joint (simple model)
        acceleration = torque_cmd / 1.0  # Simplified: F = ma, so a = F/m
        self.velocity += acceleration * 0.001  # dt = 1ms in simulation
        self.velocity = np.clip(self.velocity, -self.vel_limit, self.vel_limit)
        self.position += self.velocity * 0.001
        self.position = np.clip(self.position, self.pos_limit_min, self.pos_limit_max)
        
        # Update temperature based on torque (heating effect)
        self.temperature += abs(torque_cmd) * 0.001
        
        # Simulate occasional hardware errors
        if np.random.random() < self.error_rate:
            self.hardware_errors.append(f"Torque command error at {time.time()}")
            return False  # Command failed
        
        self.torque = torque_cmd
        return True  # Command successful
    
    def emergency_stop(self):
        """Emergency stop for the joint"""
        print(f"Emergency stop triggered for {self.joint_name}")
        self.write_torque(0.0)  # Stop immediately
        self.torque = 0.0
        self.velocity = 0.0

class SensorDataBuffer:
    """
    Buffer for sensor data with timestamps
    """
    def __init__(self, max_size=1000):
        self.buffer = deque(maxlen=max_size)
        self.max_size = max_size
    
    def add_reading(self, sensor_type, value):
        """Add a sensor reading with timestamp"""
        timestamp = time.time()
        reading = {
            'timestamp': timestamp,
            'sensor_type': sensor_type,
            'value': value
        }
        self.buffer.append(reading)
    
    def get_recent_readings(self, count=10):
        """Get the most recent readings"""
        return list(self.buffer)[-count:]
    
    def get_readings_since(self, start_time, sensor_type=None):
        """Get readings since a specific time"""
        if sensor_type:
            return [r for r in self.buffer if r['timestamp'] >= start_time and r['sensor_type'] == sensor_type]
        else:
            return [r for r in self.buffer if r['timestamp'] >= start_time]

class AIPerceptionSystem:
    """
    AI-based perception system that processes sensor data
    """
    def __init__(self):
        self.processing_latency = 0.005  # 5 ms for processing
        self.detection_threshold = 0.1  # Threshold for anomaly detection
    
    def process_sensor_data(self, sensor_data):
        """
        Process sensor data using AI techniques
        This is a simplified example - real systems would use ML models
        """
        time.sleep(self.processing_latency)  # Simulate processing time
        
        results = {}
        
        # Anomaly detection in joint positions
        if 'position' in sensor_data:
            pos = sensor_data['position']
            if abs(pos) > np.pi * 0.8:  # Close to joint limits
                results['position_anomaly'] = True
                results['position_alert'] = f"Position {pos:.3f} near limit"
            else:
                results['position_anomaly'] = False
        
        # Velocity analysis
        if 'velocity' in sensor_data:
            vel = sensor_data['velocity']
            if abs(vel) > 4.0:  # High velocity detected
                results['high_velocity'] = True
                results['velocity_alert'] = f"High velocity {vel:.3f}"
            else:
                results['high_velocity'] = False
        
        # Temperature monitoring
        if 'temperature' in sensor_data:
            temp = sensor_data['temperature']
            if temp > 50.0:  # High temperature
                results['overheating'] = True
                results['temperature_alert'] = f"Overheating: {temp:.1f}°C"
            else:
                results['overheating'] = False
        
        # Torque analysis
        if 'torque' in sensor_data:
            torque = sensor_data['torque']
            if abs(torque) > 40.0:  # High torque
                results['high_torque'] = True
                results['torque_alert'] = f"High torque: {torque:.1f} Nm"
            else:
                results['high_torque'] = False
        
        # Predictive analysis: detect if temperature is increasing rapidly
        if 'temperature' in sensor_data and 'torque' in sensor_data:
            # Simplified prediction: if torque is high and temperature is rising
            if sensor_data['torque'] > 30.0 and sensor_data['temperature'] > 40.0:
                results['thermal_prediction'] = "High risk of overheating"
        
        return results

class RealTimeController:
    """
    Real-time controller that manages the timing of operations
    """
    def __init__(self, control_frequency=1000):  # 1000 Hz
        self.control_period = 1.0 / control_frequency
        self.next_execution_time = time.time()
        self.scheduling_errors = 0
        self.actual_execution_times = deque(maxlen=100)
    
    def wait_for_next_cycle(self):
        """Wait until the next control cycle"""
        current_time = time.time()
        self.next_execution_time += self.control_period
        
        # Calculate sleep time
        sleep_time = self.next_execution_time - current_time
        
        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            # Missed deadline
            self.scheduling_errors += 1
            # Reset to the next cycle
            self.next_execution_time = current_time + self.control_period
        
        execution_time = time.time()
        self.actual_execution_times.append(execution_time)
        
        return execution_time

class HardwareAIFramework:
    """
    Main framework integrating hardware and AI systems
    """
    def __init__(self):
        # Create mock hardware interfaces for different joints
        self.joints = {
            'hip_left': MockHardwareInterface('hip_left', position=0.1),
            'knee_left': MockHardwareInterface('knee_left', position=0.2),
            'ankle_left': MockHardwareInterface('ankle_left', position=-0.1),
            'hip_right': MockHardwareInterface('hip_right', position=-0.1),
            'knee_right': MockHardwareInterface('knee_right', position=-0.2),
            'ankle_right': MockHardwareInterface('ankle_right', position=0.1)
        }
        
        # Create sensor buffers
        self.sensor_buffers = {
            joint_name: {
                'position': SensorDataBuffer(),
                'velocity': SensorDataBuffer(),
                'torque': SensorDataBuffer(),
                'temperature': SensorDataBuffer()
            } for joint_name in self.joints.keys()
        }
        
        # Create AI perception system
        self.ai_perception = AIPerceptionSystem()
        
        # Create real-time controller
        self.rt_controller = RealTimeController(control_frequency=500)  # 500 Hz control
        
        # Thread-safe queues for communication
        self.command_queue = queue.Queue()
        self.safety_queue = queue.Queue()
        
        # System status
        self.system_active = True
        self.emergency_stop_active = False
        
        # Data collection for analysis
        self.joint_positions = {name: deque(maxlen=1000) for name in self.joints.keys()}
        self.joint_velocities = {name: deque(maxlen=1000) for name in self.joints.keys()}
        self.joint_torques = {name: deque(maxlen=1000) for name in self.joints.keys()}
    
    def read_all_sensors(self):
        """Read all sensor data from hardware"""
        sensor_data = {}
        
        for joint_name, joint in self.joints.items():
            if joint.is_connected:
                try:
                    sensor_data[joint_name] = {
                        'position': joint.read_position(),
                        'velocity': joint.read_velocity(),
                        'torque': joint.read_torque(),
                        'temperature': joint.read_temperature()
                    }
                    
                    # Add to buffers
                    self.sensor_buffers[joint_name]['position'].add_reading('position', sensor_data[joint_name]['position'])
                    self.sensor_buffers[joint_name]['velocity'].add_reading('velocity', sensor_data[joint_name]['velocity'])
                    self.sensor_buffers[joint_name]['torque'].add_reading('torque', sensor_data[joint_name]['torque'])
                    self.sensor_buffers[joint_name]['temperature'].add_reading('temperature', sensor_data[joint_name]['temperature'])
                    
                    # Update data collections
                    self.joint_positions[joint_name].append(sensor_data[joint_name]['position'])
                    self.joint_velocities[joint_name].append(sensor_data[joint_name]['velocity'])
                    self.joint_torques[joint_name].append(sensor_data[joint_name]['torque'])
                    
                except Exception as e:
                    print(f"Error reading sensors for {joint_name}: {e}")
                    # Add error to safety queue
                    self.safety_queue.put({
                        'error_type': 'sensor_read_failure',
                        'joint': joint_name,
                        'timestamp': time.time(),
                        'error': str(e)
                    })
        
        return sensor_data
    
    def process_sensor_data_with_ai(self, sensor_data):
        """Process sensor data using AI perception system"""
        ai_results = {}
        
        for joint_name, data in sensor_data.items():
            ai_results[joint_name] = self.ai_perception.process_sensor_data(data)
        
        return ai_results
    
    def generate_control_commands(self, ai_results, sensor_data):
        """Generate control commands based on AI results and sensor data"""
        commands = {}
        
        # Simple control logic: if position anomaly detected, try to move back to center
        # In reality, much more sophisticated controllers would be used
        for joint_name, results in ai_results.items():
            if results.get('position_anomaly', False):
                # Move toward center
                current_pos = sensor_data[joint_name]['position']
                error = -current_pos  # Negative to move toward zero
                torque_cmd = np.clip(error * 10.0, -20.0, 20.0)  # P controller with gain of 10
            else:
                # Simple PD controller to maintain position at 0
                current_pos = sensor_data[joint_name]['position']
                current_vel = sensor_data[joint_name]['velocity']
                error = -current_pos  # Want to maintain at 0
                torque_cmd = np.clip(error * 5.0 - current_vel * 0.5, -10.0, 10.0)  # P=5, D=0.5
            
            commands[joint_name] = torque_cmd
        
        return commands
    
    def execute_commands(self, commands):
        """Execute control commands on hardware"""
        results = {}
        
        for joint_name, cmd in commands.items():
            if joint_name in self.joints:
                try:
                    success = self.joints[joint_name].write_torque(cmd)
                    results[joint_name] = success
                    if not success:
                        self.safety_queue.put({
                            'error_type': 'command_failure',
                            'joint': joint_name,
                            'timestamp': time.time(),
                            'command': cmd
                        })
                except Exception as e:
                    print(f"Error executing command for {joint_name}: {e}")
                    results[joint_name] = False
                    self.safety_queue.put({
                        'error_type': 'command_exception',
                        'joint': joint_name,
                        'timestamp': time.time(),
                        'error': str(e)
                    })
        
        return results
    
    def safety_monitoring(self, ai_results):
        """Monitor for safety issues based on AI analysis"""
        safety_issues = []
        
        for joint_name, results in ai_results.items():
            # Check for overheating
            if results.get('overheating', False):
                alert = results.get('temperature_alert', 'Overheating detected')
                safety_issues.append({
                    'joint': joint_name,
                    'issue': 'overheating',
                    'alert': alert,
                    'severity': 'high'
                })
            
            # Check for high torque
            if results.get('high_torque', False):
                alert = results.get('torque_alert', 'High torque detected')
                safety_issues.append({
                    'joint': joint_name,
                    'issue': 'high_torque', 
                    'alert': alert,
                    'severity': 'medium'
                })
            
            # Check for high velocity
            if results.get('high_velocity', False):
                alert = results.get('velocity_alert', 'High velocity detected')
                safety_issues.append({
                    'joint': joint_name,
                    'issue': 'high_velocity',
                    'alert': alert,
                    'severity': 'medium'
                })
        
        # If critical safety issues, trigger emergency stop
        critical_issues = [issue for issue in safety_issues if issue['severity'] == 'high']
        if critical_issues and not self.emergency_stop_active:
            print(f"CRITICAL SAFETY ISSUE: Emergency stop triggered due to: {critical_issues}")
            self.trigger_emergency_stop()
        
        return safety_issues
    
    def trigger_emergency_stop(self):
        """Trigger emergency stop for all joints"""
        self.emergency_stop_active = True
        print("EMERGENCY STOP ACTIVATED: Stopping all joints!")
        
        for joint_name, joint in self.joints.items():
            joint.emergency_stop()
    
    def run_control_loop(self, duration=10.0):
        """Run the main control loop for a specified duration"""
        print(f"Starting hardware-AI integration control loop for {duration} seconds...")
        print("Time\t\tPosition(hip_L)\tVelocity(hip_L)\tTorque(hip_L)")
        print("-" * 70)
        
        start_time = time.time()
        loop_count = 0
        last_print_time = start_time
        
        while time.time() - start_time < duration and self.system_active and not self.emergency_stop_active:
            loop_start_time = time.time()
            
            # Wait for next control cycle
            self.rt_controller.wait_for_next_cycle()
            
            # Read all sensors
            sensor_data = self.read_all_sensors()
            
            # Process data with AI
            ai_results = self.process_sensor_data_with_ai(sensor_data)
            
            # Generate control commands
            commands = self.generate_control_commands(ai_results, sensor_data)
            
            # Monitor safety
            safety_issues = self.safety_monitoring(ai_results)
            
            # Execute commands
            command_results = self.execute_commands(commands)
            
            # Print status periodically
            current_time = time.time()
            if current_time - last_print_time > 1.0:  # Print every second
                hip_left_pos = sensor_data.get('hip_left', {}).get('position', 0)
                hip_left_vel = sensor_data.get('hip_left', {}).get('velocity', 0)
                hip_left_torque = sensor_data.get('hip_left', {}).get('torque', 0)
                
                print(f"{current_time - start_time:6.2f}s\t{hip_left_pos:8.3f}\t\t{hip_left_vel:8.3f}\t\t{hip_left_torque:8.3f}")
                last_print_time = current_time
            
            # Check for errors
            while not self.safety_queue.empty():
                safety_msg = self.safety_queue.get()
                print(f"SAFETY: {safety_msg}")
            
            loop_count += 1
        
        print(f"\nControl loop completed after {loop_count} cycles")
        
        if self.emergency_stop_active:
            print("System stopped due to emergency stop condition.")
        else:
            print(f"Completed {duration} seconds of operation successfully.")
        
        return loop_count

def analyze_performance(hw_ai_framework):
    """
    Analyze the performance of the hardware-AI integration
    """
    print("\nPerformance Analysis:")
    print("=" * 30)
    
    # Plot joint positions over time
    time_points = list(range(len(next(iter(hw_ai_framework.joint_positions.values())))))
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for i, (joint_name, positions) in enumerate(hw_ai_framework.joint_positions.items()):
        if i < 6:
            axes[i].plot(list(positions), label=f'{joint_name} position', linewidth=2)
            axes[i].set_title(f'{joint_name} Position')
            axes[i].set_ylabel('Angle (rad)')
            axes[i].grid(True)
            axes[i].legend()
    
    plt.tight_layout()
    plt.show()
    
    # Print some statistics
    print(f"Total scheduling errors in RT controller: {hw_ai_framework.rt_controller.scheduling_errors}")
    
    for joint_name, joint in hw_ai_framework.joints.items():
        if joint.hardware_errors:
            print(f"{joint_name} had {len(joint.hardware_errors)} hardware errors")
        else:
            print(f"{joint_name} operated without hardware errors")

def main():
    """
    Main function to demonstrate hardware integration with AI systems
    """
    print("Hardware Integration with AI Systems")
    print("=" * 40)
    print("This example demonstrates:")
    print("1. Hardware-software interfaces for robot joints")
    print("2. Sensor data collection and buffering")
    print("3. AI-based perception and analysis")
    print("4. Real-time control considerations")
    print("5. Safety monitoring and emergency stops")
    print()
    
    # Create the hardware-AI integration framework
    hw_ai_system = HardwareAIFramework()
    
    # Run the control loop
    loop_count = hw_ai_system.run_control_loop(duration=15.0)
    
    # Analyze performance
    analyze_performance(hw_ai_system)
    
    print("\nKey takeaways about hardware-AI integration:")
    print("- Real-time communication is critical for control")
    print("- Sensor noise and delays must be considered in AI processing")
    print("- Safety systems must monitor both hardware and AI outputs")
    print("- Buffering and queuing are essential for smooth operation")
    print("- Synchronization between hardware and AI components is crucial")
    print("- Error handling must be robust to prevent system failures")

if __name__ == "__main__":
    main()