/*
 * ROS2 Humanoid Robot Controller Example
 * 
 * This example demonstrates key concepts from Module 4, Lesson 2:
 * - ROS2 node structure for humanoid robot control
 * - Real-time control considerations in ROS2
 * - Communication between different robot subsystems
 * - Quality of Service (QoS) settings for real-time performance
 */

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <control_msgs/msg/joint_jacobian.hpp>
#include <geometry_msgs/msg/vector3.hpp>
#include <tf2_ros/transform_broadcaster.h>
#include <realtime_tools/realtime_publisher.h>

#include <vector>
#include <string>
#include <memory>
#include <chrono>
#include <cmath>

// Real-time safe controller for humanoid robot joints
class JointController : public rclcpp::Node {
public:
    JointController() 
    : Node("joint_controller"),
      loop_rate_(200) {  // 200Hz control loop
        
        // Declare parameters
        this->declare_parameter<std::vector<std::string>>("joint_names", 
            std::vector<std::string>{"hip_left", "knee_left", "ankle_left", 
                                   "hip_right", "knee_right", "ankle_right"});
        
        // Get joint names from parameters
        joint_names_ = this->get_parameter("joint_names").as_string_array();
        
        // Initialize joint states
        initializeJointStates();
        
        // Create publishers with real-time safe QoS
        joint_command_publisher_ = this->create_publisher<std_msgs::msg::Float64MultiArray>(
            "/joint_commands", 
            rclcpp::QoS(10).reliable().durability_volatile());
            
        joint_state_publisher_ = this->create_publisher<sensor_msgs::msg::JointState>(
            "/joint_states", 
            rclcpp::QoS(50).reliable().durability_volatile());
        
        // Create subscribers
        joint_state_subscriber_ = this->create_subscription<sensor_msgs::msg::JointState>(
            "/joint_states_feedback",
            rclcpp::QoS(50).reliable().durability_volatile(),
            std::bind(&JointController::jointStateCallback, this, std::placeholders::_1));
            
        // Create timer for control loop
        control_timer_ = this->create_wall_timer(
            std::chrono::milliseconds(5),  // 200Hz = 5ms period
            std::bind(&JointController::controlLoop, this));
        
        // Initialize transform broadcaster
        tf_broadcaster_ = std::make_shared<tf2_ros::TransformBroadcaster>(this);
        
        RCLCPP_INFO(this->get_logger(), "Joint Controller initialized with %zu joints", joint_names_.size());
    }

private:
    // Control loop rate
    rclcpp::Rate loop_rate_;
    
    // Joint names and states
    std::vector<std::string> joint_names_;
    sensor_msgs::msg::JointState current_joint_state_;
    std::vector<double> target_positions_;
    std::vector<double> target_velocities_;
    std::vector<double> target_efforts_;
    
    // ROS2 communication objects
    rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr joint_command_publisher_;
    rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr joint_state_publisher_;
    rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_subscriber_;
    rclcpp::TimerBase::SharedPtr control_timer_;
    
    // TF broadcaster
    std::shared_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
    
    // Timing
    rclcpp::Time last_update_time_;
    
    void initializeJointStates() {
        current_joint_state_.name = joint_names_;
        current_joint_state_.position.resize(joint_names_.size(), 0.0);
        current_joint_state_.velocity.resize(joint_names_.size(), 0.0);
        current_joint_state_.effort.resize(joint_names_.size(), 0.0);
        
        target_positions_.resize(joint_names_.size(), 0.0);
        target_velocities_.resize(joint_names_.size(), 0.0);
        target_efforts_.resize(joint_names_.size(), 0.0);
        
        // Set initial target positions (some slight bend in knees)
        for (size_t i = 0; i < joint_names_.size(); ++i) {
            if (joint_names_[i].find("knee") != std::string::npos) {
                target_positions_[i] = 0.1;  // Slight bend in knees for stable stance
            }
        }
    }
    
    void jointStateCallback(const sensor_msgs::msg::JointState::SharedPtr msg) {
        // Update current joint states from feedback
        for (size_t i = 0; i < msg->name.size(); ++i) {
            // Find corresponding index in our joint array
            for (size_t j = 0; j < current_joint_state_.name.size(); ++j) {
                if (current_joint_state_.name[j] == msg->name[i]) {
                    if (i < msg->position.size()) current_joint_state_.position[j] = msg->position[i];
                    if (i < msg->velocity.size()) current_joint_state_.velocity[j] = msg->velocity[i];
                    if (i < msg->effort.size()) current_joint_state_.effort[j] = msg->effort[i];
                    break;
                }
            }
        }
    }
    
    void controlLoop() {
        // Get current time
        rclcpp::Time current_time = this->now();
        
        // Update joint positions based on control algorithm
        updateJointControl(current_time);
        
        // Publish joint states
        current_joint_state_.header.stamp = current_time;
        joint_state_publisher_->publish(current_joint_state_);
        
        // Publish joint commands
        publishJointCommands();
        
        // Publish transforms for robot state
        publishTransforms(current_time);
    }
    
    void updateJointControl(const rclcpp::Time& current_time) {
        // Simple PD controller for each joint
        double dt = (current_time - last_update_time_).seconds();
        if (dt <= 0) dt = 0.005;  // Default to 5ms if first iteration
        
        for (size_t i = 0; i < joint_names_.size(); ++i) {
            // Calculate error
            double error = target_positions_[i] - current_joint_state_.position[i];
            double vel_error = target_velocities_[i] - current_joint_state_.velocity[i];
            
            // PD control: torque = kp * position_error + kd * velocity_error
            double kp = 100.0;  // Position gain
            double kd = 10.0;   // Velocity gain
            
            double effort = kp * error + kd * vel_error;
            
            // Apply effort limits
            effort = std::clamp(effort, -100.0, 100.0);
            
            // Update joint state with computed effort
            current_joint_state_.effort[i] = effort;
            
            // Simulate joint dynamics (in real system, this would come from actual hardware)
            double acceleration = effort / 1.0;  // Simplified: F = ma
            current_joint_state_.velocity[i] += acceleration * dt;
            current_joint_state_.position[i] += current_joint_state_.velocity[i] * dt;
        }
        
        last_update_time_ = current_time;
    }
    
    void publishJointCommands() {
        std_msgs::msg::Float64MultiArray command_msg;
        command_msg.data = std::vector<double>(current_joint_state_.effort.begin(), 
                                              current_joint_state_.effort.end());
        joint_command_publisher_->publish(command_msg);
    }
    
    void publishTransforms(const rclcpp::Time& current_time) {
        // Publish transforms for each joint (simplified for example)
        for (size_t i = 0; i < joint_names_.size(); ++i) {
            geometry_msgs::msg::TransformStamped t;
            
            t.header.stamp = current_time;
            t.header.frame_id = "base_link";
            t.child_frame_id = joint_names_[i] + "_link";
            
            // Set transform based on joint position (simplified)
            t.transform.translation.x = 0.1 * i;  // Space joints apart
            t.transform.translation.y = 0.0;
            t.transform.translation.z = 0.0;
            
            // Convert joint angle to quaternion (simplified - just rotating around Y axis)
            double angle = current_joint_state_.position[i];
            t.transform.rotation.x = 0.0;
            t.transform.rotation.y = sin(angle / 2.0);
            t.transform.rotation.z = 0.0;
            t.transform.rotation.w = cos(angle / 2.0);
            
            tf_broadcaster_->sendTransform(t);
        }
    }
};

// Balance controller node that works with joint controller
class BalanceController : public rclcpp::Node {
public:
    BalanceController() 
    : Node("balance_controller") {
        
        // Create subscriber for IMU data
        imu_subscriber_ = this->create_subscription<geometry_msgs::msg::Vector3>(
            "/imu_data", 
            rclcpp::QoS(10).reliable().durability_volatile(),
            std::bind(&BalanceController::imuCallback, this, std::placeholders::_1));
        
        // Create publisher for balance corrections
        balance_correction_publisher_ = this->create_publisher<std_msgs::msg::Float64MultiArray>(
            "/balance_corrections", 
            rclcpp::QoS(10).reliable().durability_volatile());
        
        // Timer for balance calculations
        balance_timer_ = this->create_wall_timer(
            std::chrono::milliseconds(10),  // 100Hz balance updates
            std::bind(&BalanceController::balanceUpdate, this));
        
        RCLCPP_INFO(this->get_logger(), "Balance Controller initialized");
    }

private:
    rclcpp::Subscription<geometry_msgs::msg::Vector3>::SharedPtr imu_subscriber_;
    rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr balance_correction_publisher_;
    rclcpp::TimerBase::SharedPtr balance_timer_;
    
    geometry_msgs::msg::Vector3 last_imu_data_;
    std::vector<double> balance_corrections_;
    
    void imuCallback(const geometry_msgs::msg::Vector3::SharedPtr msg) {
        last_imu_data_ = *msg;
    }
    
    void balanceUpdate() {
        // Simple balance control based on IMU data
        // Calculate required corrections to maintain balance
        
        // For this example, we'll use a simple control law
        // In real systems, this would be more sophisticated (e.g., inverted pendulum model)
        double roll_correction = -last_imu_data_.x * 20.0;  // Counteract roll
        double pitch_correction = -last_imu_data_.y * 20.0; // Counteract pitch
        
        // Create correction message
        std_msgs::msg::Float64MultiArray correction_msg;
        correction_msg.data = {roll_correction, pitch_correction, 0.0, 0.0, 0.0, 0.0};
        
        balance_correction_publisher_->publish(correction_msg);
        
        // Log balance status periodically
        static int counter = 0;
        if (++counter % 50 == 0) {  // Every 500ms
            RCLCPP_INFO(this->get_logger(), 
                       "Balance status - Roll: %.3f, Pitch: %.3f, Corrections: [%.2f, %.2f]", 
                       last_imu_data_.x, last_imu_data_.y, roll_correction, pitch_correction);
        }
    }
};

// Main function to demonstrate ROS2 architecture
int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);
    
    std::cout << "ROS2 Humanoid Robot Controller Example" << std::endl;
    std::cout << "=====================================" << std::endl;
    std::cout << "This example demonstrates:" << std::endl;
    std::cout << "1. ROS2 node structure for robot control" << std::endl;
    std::cout << "2. Real-time control considerations" << std::endl;
    std::cout << "3. Communication between subsystems" << std::endl;
    std::cout << "4. Quality of Service settings for performance" << std::endl;
    std::cout << std::endl;
    
    try {
        // Create and spin nodes
        auto joint_controller = std::make_shared<JointController>();
        auto balance_controller = std::make_shared<BalanceController>();
        
        // Use multi-threaded executor to handle both nodes
        rclcpp::executors::MultiThreadedExecutor executor;
        executor.add_node(joint_controller);
        executor.add_node(balance_controller);
        
        RCLCPP_INFO(rclcpp::get_logger("main"), "Starting robot controllers...");
        executor.spin();
    }
    catch (const std::exception& e) {
        std::cerr << "Error running ROS2 nodes: " << e.what() << std::endl;
        rclcpp::shutdown();
        return 1;
    }
    
    rclcpp::shutdown();
    return 0;
}