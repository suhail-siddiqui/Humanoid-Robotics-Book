"""
Reinforcement Learning for Humanoid Motor Control

This example demonstrates key concepts from Module 3, Lesson 1:
- Using reinforcement learning for motor control
- Implementing the basics of policy optimization
- Creating a simulated humanoid control environment
- Applying Deep Q-Network (DQN) for balance control
"""

import numpy as np
import matplotlib.pyplot as plt
import random
from collections import deque
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

class InvertedPendulumEnv:
    """
    A simplified simulation of an inverted pendulum, representing balance control
    for a humanoid robot (like maintaining balance on one foot).
    """
    def __init__(self):
        # Physical parameters
        self.length = 1.0  # Length of the pendulum in meters
        self.mass = 1.0    # Mass of the pendulum in kg
        self.gravity = 9.81  # Gravity in m/s^2
        
        # State: [angle, angular_velocity]
        self.state = np.zeros(2)
        
        # Action space: force applied at the base [-10, 10] N
        self.action_space = (-10.0, 10.0)
        
        # Time parameters
        self.dt = 0.02  # Time step (50Hz)
        
        # Constraints
        self.angle_limit = np.pi / 6  # 30 degrees max from vertical
        self.angular_vel_limit = 5.0  # Max angular velocity
        self.max_steps = 1000  # Max steps per episode
        
        self.reset()
    
    def reset(self):
        """Reset the environment to a random initial state"""
        # Start near equilibrium but with some random offset
        self.state = np.array([
            np.random.uniform(-0.1, 0.1),  # Small random angle
            np.random.uniform(-0.1, 0.1)   # Small random angular velocity
        ])
        self.steps = 0
        return self.state
    
    def step(self, action):
        """Execute one time step in the environment"""
        # Clamp action to valid range
        action = np.clip(action, self.action_space[0], self.action_space[1])
        
        angle, angular_vel = self.state
        
        # Physics: torque = force * length * cos(angle)
        # Simplified pendulum dynamics
        torque = action * self.length * np.cos(angle) - 0.1 * angular_vel  # Add damping
        angular_acc = (self.gravity / self.length) * np.sin(angle) + torque / (self.mass * self.length**2)
        
        # Update state using Euler integration
        new_angular_vel = angular_vel + angular_acc * self.dt
        new_angle = angle + new_angular_vel * self.dt
        
        # Apply constraints
        new_angular_vel = np.clip(new_angular_vel, -self.angular_vel_limit, self.angular_vel_limit)
        new_angle = np.clip(new_angle, -self.angle_limit, self.angle_limit)
        
        # Update state
        self.state = np.array([new_angle, new_angular_vel])
        self.steps += 1
        
        # Calculate reward
        # Reward for staying upright and penalty for force used
        reward = 1.0 - abs(new_angle) - 0.01 * abs(action) - 0.1 * abs(new_angular_vel)
        
        # Check if episode is done (failed or max steps reached)
        done = bool(
            abs(new_angle) > self.angle_limit or  # Fallen over
            abs(new_angular_vel) > self.angular_vel_limit or  # Too fast
            self.steps >= self.max_steps  # Max steps reached
        )
        
        # Give a penalty for ending early
        if done and self.steps < self.max_steps:
            reward -= 10  # Penalty for falling
        
        return self.state, reward, done, {}
    
    def render(self, mode='human'):
        """Render the environment (simple text output for this example)"""
        angle_deg = self.state[0] * 180 / np.pi
        print(f"Angle: {angle_deg:6.2f}°, Angular Vel: {self.state[1]:6.2f} rad/s, Action: {self.get_last_action():6.2f} N")

class DQN(nn.Module):
    """
    Deep Q-Network for learning the Q-function
    """
    def __init__(self, state_size, action_size, hidden_size=64):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(state_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, hidden_size)
        self.fc4 = nn.Linear(hidden_size, action_size)
    
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        return self.fc4(x)

class DQNAgent:
    """
    Deep Q-Network Agent for learning motor control policies
    """
    def __init__(self, state_size, action_size, lr=1e-3, gamma=0.99, epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.995):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=10000)
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon  # Exploration rate
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.learning_rate = lr
        
        # Neural networks
        self.qnetwork_local = DQN(state_size, action_size)
        self.qnetwork_target = DQN(state_size, action_size)
        self.optimizer = optim.Adam(self.qnetwork_local.parameters(), lr=lr)
        
        # Update target network
        self.update_target_network()
    
    def update_target_network(self):
        """Copy weights from local network to target network"""
        self.qnetwork_target.load_state_dict(self.qnetwork_local.state_dict())
    
    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay memory"""
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state, training=True):
        """Choose an action based on the current state"""
        if training and np.random.random() <= self.epsilon:
            # Explore: random action
            return np.random.uniform(-1, 1)  # Continuous action space: normalize to [-1, 1] then scale
        
        # Exploit: choose best action from Q-network
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        q_values = self.qnetwork_local(state_tensor)
        
        # For continuous action space, we would typically use actor-critic methods
        # For this example, we'll discretize the action space to make it compatible with DQN
        # Scale the normalized action (-1 to 1) to the actual action space
        action = torch.tanh(q_values).item()  # Use tanh to ensure action is in [-1, 1]
        return action
    
    def replay(self, batch_size=32):
        """Train the model on a batch of experiences"""
        if len(self.memory) < batch_size:
            return
        
        batch = random.sample(self.memory, batch_size)
        states = torch.FloatTensor([e[0] for e in batch])
        actions = torch.FloatTensor([e[1] for e in batch]).unsqueeze(1)
        rewards = torch.FloatTensor([e[2] for e in batch]).unsqueeze(1)
        next_states = torch.FloatTensor([e[3] for e in batch])
        dones = torch.BoolTensor([e[4] for e in batch]).unsqueeze(1)
        
        # Current Q values
        current_q_values = self.qnetwork_local(states).gather(1, (actions + 1) / 2 * 31)  # Discretize action for indexing
        
        # Next Q values from target model
        next_q_values = self.qnetwork_target(next_states).max(1)[0].detach().unsqueeze(1)
        target_q_values = rewards + (self.gamma * next_q_values * ~dones)
        
        # Compute loss
        loss = F.mse_loss(current_q_values, target_q_values)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

class ContinuousDQNAgent:
    """
    Adapted DQN for continuous action spaces
    """
    def __init__(self, state_size, action_size=1, lr=1e-3, gamma=0.99, epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.995):
        self.state_size = state_size
        self.action_size = action_size  # Number of action dimensions
        self.memory = deque(maxlen=10000)
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon  # Exploration rate
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.learning_rate = lr
        
        # Neural networks for continuous control
        self.qnetwork_local = DQN(state_size, 32)  # Discretized output for action selection
        self.qnetwork_target = DQN(state_size, 32)
        self.optimizer = optim.Adam(self.qnetwork_local.parameters(), lr=lr)
        
        # Update target network
        self.update_target_network()
    
    def update_target_network(self):
        """Copy weights from local network to target network"""
        self.qnetwork_target.load_state_dict(self.qnetwork_local.state_dict())
    
    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay memory"""
        # Normalize action to [-1, 1] range for storage
        normalized_action = action / 10.0  # Assuming action space is [-10, 10]
        self.memory.append((state, normalized_action, reward, next_state, done))
    
    def act(self, state, training=True):
        """Choose an action based on the current state"""
        if training and np.random.random() <= self.epsilon:
            # Explore: random action
            return np.random.uniform(-10, 10)  # Actual action in full range
        
        # Exploit: choose best action from Q-network
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        q_values = self.qnetwork_local(state_tensor)
        
        # For this example, discretize action space to 32 values between -10 and 10
        action_idx = torch.argmax(q_values).item()
        action = -10 + (action_idx / 31) * 20  # Map from [0, 31] to [-10, 10]
        
        return action
    
    def replay(self, batch_size=32):
        """Train the model on a batch of experiences"""
        if len(self.memory) < batch_size:
            return
        
        batch = random.sample(self.memory, batch_size)
        states = torch.FloatTensor([e[0] for e in batch])
        actions = torch.FloatTensor([e[1] for e in batch]).unsqueeze(1)  # Normalized actions
        rewards = torch.FloatTensor([e[2] for e in batch]).unsqueeze(1)
        next_states = torch.FloatTensor([e[3] for e in batch])
        dones = torch.BoolTensor([e[4] for e in batch]).unsqueeze(1)
        
        # Convert normalized actions to discrete indices for Q-network
        action_indices = ((actions + 1) / 2 * 31).long().clamp(0, 31)  # Convert to [0, 31]
        
        # Current Q values for the taken actions
        current_q_values = self.qnetwork_local(states).gather(1, action_indices)
        
        # Next Q values from target model (for all actions)
        next_q_values = self.qnetwork_target(next_states)
        # Take the maximum Q-value for the next state
        max_next_q_values = next_q_values.max(1)[0].detach().unsqueeze(1)
        target_q_values = rewards + (self.gamma * max_next_q_values * ~dones)
        
        # Compute loss
        loss = F.mse_loss(current_q_values, target_q_values)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

def train_agent(episodes=1000):
    """
    Train the RL agent to balance the inverted pendulum
    """
    env = InvertedPendulumEnv()
    state_size = env.state.shape[0]
    agent = ContinuousDQNAgent(state_size)
    
    scores = deque(maxlen=100)  # Last 100 scores
    scores_deque = []
    steps_list = []
    
    print("Training started...")
    print("Episode\tAverage Score\tSteps")
    print("-" * 40)
    
    for episode in range(episodes):
        state = env.reset()
        total_reward = 0
        steps = 0
        
        while True:
            action = agent.act(state)
            next_state, reward, done, _ = env.step(action)
            
            agent.remember(state, action, reward, next_state, done)
            
            state = next_state
            total_reward += reward
            steps += 1
            
            if done:
                break
            
            if len(agent.memory) > 32:
                agent.replay(32)
        
        scores.append(total_reward)
        scores_deque.append(total_reward)
        steps_list.append(steps)
        
        # Update target network periodically
        if episode % 100 == 0:
            agent.update_target_network()
        
        if episode % 100 == 0:
            avg_score = np.mean(scores)
            print(f"{episode:5d}\t{avg_score:10.2f}\t\t{steps:3d}")
    
    # Plot the training progress
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot scores
    ax1.plot(scores_deque)
    ax1.set_ylabel('Episode Score')
    ax1.set_title('Training Progress: Episode Scores')
    ax1.grid(True)
    
    # Plot steps per episode
    ax2.plot(steps_list)
    ax2.set_xlabel('Episode')
    ax2.set_ylabel('Steps')
    ax2.set_title('Training Progress: Steps per Episode (Longer is Better)')
    ax2.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    return agent, env

def test_agent(agent, env, episodes=5):
    """
    Test the trained agent
    """
    print("\nTesting trained agent...")
    
    for episode in range(episodes):
        state = env.reset()
        total_reward = 0
        steps = 0
        agent.epsilon = 0  # No exploration during testing
        
        print(f"\nEpisode {episode + 1}:")
        print("Step\tAngle(°)\tAng_Vel\tAction\tReward\tTotal_Reward")
        print("-" * 60)
        
        while steps < 500:  # Limit steps for display
            action = agent.act(state, training=False)
            next_state, reward, done, _ = env.step(action)
            
            angle_deg = state[0] * 180 / np.pi
            print(f"{steps:4d}\t{angle_deg:7.2f}\t\t{state[1]:6.2f}\t{action:6.2f}\t{reward:6.2f}\t{total_reward + reward:8.2f}")
            
            state = next_state
            total_reward += reward
            steps += 1
            
            if done:
                print(f"Episode finished after {steps} steps with total reward: {total_reward:.2f}")
                break
        
        if not done:
            print(f"Episode reached max steps ({steps}) with total reward: {total_reward:.2f}")

def main():
    """
    Main function to demonstrate RL for motor control
    """
    print("Reinforcement Learning for Humanoid Motor Control")
    print("=" * 50)
    print("This example demonstrates:")
    print("1. Using RL for balance control (inverted pendulum)")
    print("2. Implementing DQN for continuous control")
    print("3. Training agent to maintain balance")
    print("4. Evaluating learned policies")
    print()
    
    # Train the agent
    trained_agent, env = train_agent(episodes=500)
    
    # Test the trained agent
    test_agent(trained_agent, env, episodes=3)
    
    print("\nKey observations about RL for motor control:")
    print("- The agent learns to balance by trial and error")
    print("- It discovers control strategies that maintain the pendulum upright")
    print("- The reward function shapes the learning behavior")
    print("- Continuous action spaces require special handling in Q-learning")
    print("- Real humanoid robots have multiple degrees of freedom, making the problem more complex")

if __name__ == "__main__":
    main()