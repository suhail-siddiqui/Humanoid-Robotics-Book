/*
 * Actuator Control and Sensor Integration Example for Humanoid Robots
 * 
 * This C++ example demonstrates key concepts from Module 2, Lesson 2:
 * - Hardware abstraction for actuators and sensors
 * - Real-time control patterns
 * - Sensor fusion techniques
 * - Safety monitoring in actuator systems
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <thread>
#include <mutex>
#include <map>
#include <string>
#include <cmath>
#include <algorithm>
#include <stdexcept>

// Utility functions for time measurement
namespace Utils {
    double get_time() {
        return std::chrono::duration<double>(
            std::chrono::high_resolution_clock::now().time_since_epoch()
        ).count();
    }

    void sleep_for(double seconds) {
        std::this_thread::sleep_for(std::chrono::duration<double>(seconds));
    }
}

// Forward declarations
class JointController;
class SensorFusion;
class SafetyMonitor;

// Data structures for sensor readings
struct JointState {
    double position = 0.0;      // Radians
    double velocity = 0.0;      // Rad/s
    double torque = 0.0;        // Nm
    double temperature = 25.0;  // Celsius
    std::chrono::steady_clock::time_point timestamp;
    
    JointState() : timestamp(std::chrono::steady_clock::now()) {}
};

struct ImuData {
    double orientation[4] = {0, 0, 0, 1};  // Quaternion [x, y, z, w]
    double angular_velocity[3] = {0, 0, 0}; // Rad/s [x, y, z]
    double linear_acceleration[3] = {0, 0, 9.81}; // m/s^2 [x, y, z]
    std::chrono::steady_clock::time_point timestamp;
    
    ImuData() : timestamp(std::chrono::steady_clock::now()) {}
};

// Base class for sensors
class Sensor {
protected:
    std::string name_;
    double noise_level_;
    bool is_connected_;

public:
    Sensor(const std::string& name, double noise_level = 0.0) 
        : name_(name), noise_level_(noise_level), is_connected_(true) {}
    
    virtual ~Sensor() = default;
    
    virtual void read() = 0;
    virtual bool isConnected() const { return is_connected_; }
    std::string getName() const { return name_; }
    
    // Add noise to a value (simulation)
    double addNoise(double value) {
        if (noise_level_ <= 0) return value;
        
        // Simple noise simulation (in a real system, use proper RNG)
        static int noise_counter = 0;
        noise_counter++;
        return value + noise_level_ * sin(noise_counter * 0.1);
    }
};

// Joint sensor class
class JointSensor : public Sensor {
private:
    JointState state_;
    std::mutex mutex_;

public:
    JointSensor(const std::string& name, double noise_level = 0.01) 
        : Sensor(name, noise_level) {}
    
    void read() override {
        std::lock_guard<std::mutex> lock(mutex_);
        
        // In a real system, this would interface with hardware
        // For simulation, we'll generate realistic values
        state_.position = addNoise(state_.position + 0.01 * sin(Utils::get_time()));
        state_.velocity = addNoise(state_.velocity + 0.001 * cos(Utils::get_time()));
        state_.torque = addNoise(state_.torque + 0.05 * sin(Utils::get_time() * 2));
        state_.temperature = addNoise(state_.temperature + 0.0001 * abs(state_.torque));
        state_.timestamp = std::chrono::steady_clock::now();
    }
    
    JointState getState() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return state_;
    }
    
    void setState(const JointState& state) {
        std::lock_guard<std::mutex> lock(mutex_);
        state_ = state;
    }
};

// IMU sensor class
class ImuSensor : public Sensor {
private:
    ImuData data_;
    std::mutex mutex_;

public:
    ImuSensor(const std::string& name, double noise_level = 0.001) 
        : Sensor(name, noise_level) {}
    
    void read() override {
        std::lock_guard<std::mutex> lock(mutex_);
        
        // In a real system, this would interface with IMU hardware
        // For simulation, we'll generate realistic values
        data_.angular_velocity[0] = addNoise(0.1 * sin(Utils::get_time()));
        data_.angular_velocity[1] = addNoise(0.05 * sin(Utils::get_time() * 1.5));
        data_.linear_acceleration[2] = addNoise(9.81 + 0.1 * cos(Utils::get_time() * 0.5));
        
        // Update orientation based on angular velocity (simplified)
        double dt = 0.01; // 10ms
        data_.orientation[0] += data_.angular_velocity[0] * dt * 0.5;
        data_.orientation[1] += data_.angular_velocity[1] * dt * 0.5;
        
        // Normalize quaternion
        double norm = sqrt(data_.orientation[0]*data_.orientation[0] + 
                          data_.orientation[1]*data_.orientation[1] + 
                          data_.orientation[2]*data_.orientation[2] + 
                          data_.orientation[3]*data_.orientation[3]);
        if (norm > 0) {
            for (int i = 0; i < 4; i++) {
                data_.orientation[i] /= norm;
            }
        }
        
        data_.timestamp = std::chrono::steady_clock::now();
    }
    
    ImuData getData() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return data_;
    }
};

// Actuator class with control
class Actuator {
private:
    std::string name_;
    double current_torque_;
    double max_torque_;
    double gear_ratio_;
    double efficiency_;
    std::mutex mutex_;

public:
    Actuator(const std::string& name, double max_torque = 50.0, double gear_ratio = 100.0)
        : name_(name), current_torque_(0.0), max_torque_(max_torque), 
          gear_ratio_(gear_ratio), efficiency_(0.9) {}
    
    bool setTorque(double torque) {
        std::lock_guard<std::mutex> lock(mutex_);
        
        // Apply limits
        torque = std::clamp(torque, -max_torque_, max_torque_);
        current_torque_ = torque;
        
        // Simulate electrical response time
        Utils::sleep_for(0.001); // 1ms delay
        
        return true;
    }
    
    double getTorque() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return current_torque_;
    }
    
    std::string getName() const { return name_; }
    double getMaxTorque() const { return max_torque_; }
};

// Joint controller with safety monitoring
class JointController {
private:
    std::string name_;
    Actuator actuator_;
    JointSensor position_sensor_;
    JointSensor torque_sensor_;
    std::mutex mutex_;
    
    // Control parameters
    double target_position_;
    double target_velocity_;
    double kp_, ki_, kd_;  // PID gains
    double error_sum_;
    double last_error_;
    
    // Joint limits
    double min_position_;
    double max_position_;
    
    // Safety parameters
    double max_temperature_;
    double max_velocity_;
    
    bool enabled_;
    
public:
    JointController(const std::string& name)
        : name_(name), actuator_(name + "_actuator"), 
          position_sensor_(name + "_pos", 0.001), 
          torque_sensor_(name + "_torque", 0.01),
          target_position_(0.0), target_velocity_(0.0),
          kp_(100.0), ki_(10.0), kd_(5.0),
          error_sum_(0.0), last_error_(0.0),
          min_position_(-M_PI), max_position_(M_PI),
          max_temperature_(70.0), max_velocity_(5.0),
          enabled_(false) {}
    
    bool initialize() {
        // Initialize sensors and actuator
        enabled_ = true;
        std::cout << "Joint controller '" << name_ << "' initialized\n";
        return true;
    }
    
    void update(double dt) {
        if (!enabled_) return;
        
        // Read sensors
        position_sensor_.read();
        JointState state = position_sensor_.getState();
        
        // Compute control error
        double error = target_position_ - state.position;
        error_sum_ += error * dt;
        double error_derivative = (error - last_error_) / dt;
        
        // Compute PID control output
        double torque_command = kp_ * error + ki_ * error_sum_ + kd_ * error_derivative;
        
        // Apply velocity limiting
        if (abs(state.velocity) > max_velocity_) {
            torque_command = 0; // Stop if velocity limit exceeded
        }
        
        // Apply temperature-based limiting
        if (state.temperature > max_temperature_ * 0.9) {
            torque_command *= 0.5; // Reduce torque when near temperature limit
        }
        
        // Send command to actuator
        actuator_.setTorque(torque_command);
        
        // Update for next iteration
        last_error_ = error;
        
        // Update sensor state with new torque
        state.torque = torque_command;
        position_sensor_.setState(state);
    }
    
    void setTargetPosition(double position) {
        target_position_ = std::clamp(position, min_position_, max_position_);
    }
    
    JointState getState() const {
        return position_sensor_.getState();
    }
    
    std::string getName() const { return name_; }
    bool isEnabled() const { return enabled_; }
    
    // Safety checks
    bool isSafe() const {
        JointState state = getState();
        return (state.temperature < max_temperature_ && 
                abs(state.velocity) < max_velocity_ &&
                abs(state.position) <= max_position_ &&
                abs(state.position) >= min_position_);
    }
};

// Sensor fusion class using Kalman filter concepts
class SensorFusion {
private:
    std::map<std::string, JointState> joint_states_;
    std::map<std::string, ImuData> imu_data_;
    mutable std::mutex mutex_;
    
    // Simple state estimation (in real system, would use proper Kalman filters)
    double balance_estimate_;
    double confidence_;

public:
    SensorFusion() : balance_estimate_(0.0), confidence_(1.0) {}
    
    void updateJointState(const std::string& joint_name, const JointState& state) {
        std::lock_guard<std::mutex> lock(mutex_);
        joint_states_[joint_name] = state;
        
        // Simple balance estimation based on hip joint angles
        if (joint_name.find("hip") != std::string::npos) {
            updateBalanceEstimate(state.position);
        }
    }
    
    void updateImuData(const std::string& sensor_name, const ImuData& data) {
        std::lock_guard<std::mutex> lock(mutex_);
        imu_data_[sensor_name] = data;
        
        // Update balance estimate based on IMU orientation
        updateBalanceEstimateFromImu(data.orientation);
    }
    
    double getBalanceEstimate() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return balance_estimate_;
    }
    
    std::map<std::string, JointState> getJointStates() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return joint_states_;
    }
    
private:
    void updateBalanceEstimate(double joint_position) {
        // Simplified: weight this measurement based on confidence
        double new_estimate = joint_position;
        balance_estimate_ = 0.7 * balance_estimate_ + 0.3 * new_estimate;
    }
    
    void updateBalanceEstimateFromImu(const double orientation[4]) {
        // Simplified: extract roll from quaternion
        double roll = atan2(2.0 * (orientation[3] * orientation[0] + orientation[1] * orientation[2]),
                           1.0 - 2.0 * (orientation[0] * orientation[0] + orientation[1] * orientation[1]));
        
        // Update estimate
        balance_estimate_ = 0.8 * balance_estimate_ + 0.2 * roll;
    }
};

// Safety monitoring system
class SafetyMonitor {
private:
    std::vector<JointController*> controllers_;
    std::vector<JointSensor*> joint_sensors_;
    std::vector<ImuSensor*> imu_sensors_;
    
    bool emergency_stop_active_;
    std::mutex mutex_;

public:
    SafetyMonitor() : emergency_stop_active_(false) {}
    
    void addController(JointController* controller) {
        controllers_.push_back(controller);
    }
    
    void addJointSensor(JointSensor* sensor) {
        joint_sensors_.push_back(sensor);
    }
    
    void addImuSensor(ImuSensor* sensor) {
        imu_sensors_.push_back(sensor);
    }
    
    bool checkSafety() {
        std::lock_guard<std::mutex> lock(mutex_);
        
        // Check if emergency stop is active
        if (emergency_stop_active_) {
            return false;
        }
        
        // Check joint controllers
        for (auto* controller : controllers_) {
            if (!controller->isSafe()) {
                std::cout << "SAFETY: Joint " << controller->getName() << " is not safe!\n";
                emergency_stop_active_ = true;
                return false;
            }
        }
        
        // Check sensors
        for (auto* sensor : joint_sensors_) {
            if (!sensor->isConnected()) {
                std::cout << "SAFETY: Joint sensor " << sensor->getName() << " is disconnected!\n";
                return false;
            }
        }
        
        for (auto* sensor : imu_sensors_) {
            if (!sensor->isConnected()) {
                std::cout << "SAFETY: IMU sensor " << sensor->getName() << " is disconnected!\n";
                return false;
            }
        }
        
        return true;
    }
    
    bool isEmergencyStopActive() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return emergency_stop_active_;
    }
    
    void triggerEmergencyStop() {
        std::lock_guard<std::mutex> lock(mutex_);
        emergency_stop_active_ = true;
        std::cout << "EMERGENCY STOP ACTIVATED!\n";
    }
};

// Main humanoid robot controller
class HumanoidController {
private:
    std::vector<JointController> joint_controllers_;
    std::vector<JointSensor> joint_sensors_;
    std::vector<ImuSensor> imu_sensors_;
    
    SensorFusion sensor_fusion_;
    SafetyMonitor safety_monitor_;
    
    double control_frequency_;
    bool is_running_;
    
public:
    HumanoidController(double frequency = 100.0)  // 100Hz by default
        : control_frequency_(frequency), is_running_(false) {
        
        // Initialize robot joints (simplified - just 6 for example)
        std::vector<std::string> joint_names = {
            "left_hip", "left_knee", "left_ankle",
            "right_hip", "right_knee", "right_ankle"
        };
        
        for (const auto& name : joint_names) {
            joint_controllers_.emplace_back(name);
            joint_sensors_.emplace_back(name + "_pos_sensor");
        }
        
        // Add IMU sensors
        imu_sensors_.emplace_back("torso_imu");
        imu_sensors_.emplace_back("head_imu");
        
        // Register with safety monitor
        for (auto& controller : joint_controllers_) {
            safety_monitor_.addController(&controller);
        }
        
        for (auto& sensor : joint_sensors_) {
            safety_monitor_.addJointSensor(&sensor);
        }
        
        for (auto& sensor : imu_sensors_) {
            safety_monitor_.addImuSensor(&sensor);
        }
    }
    
    bool initialize() {
        std::cout << "Initializing Humanoid Robot Controller...\n";
        
        // Initialize all joint controllers
        for (auto& controller : joint_controllers_) {
            if (!controller.initialize()) {
                std::cout << "Failed to initialize controller: " << controller.getName() << "\n";
                return false;
            }
        }
        
        std::cout << "Humanoid controller initialized successfully!\n";
        return true;
    }
    
    void run() {
        if (!initialize()) {
            std::cout << "Failed to initialize controller. Exiting.\n";
            return;
        }
        
        is_running_ = true;
        double dt = 1.0 / control_frequency_;
        auto last_time = std::chrono::steady_clock::now();
        
        std::cout << "Starting control loop at " << control_frequency_ << "Hz\n";
        std::cout << "Time(s)\tLeft Hip Pos\tRight Hip Pos\tBalance Est\tSafety\n";
        std::cout << "--------------------------------------------------------------------\n";
        
        while (is_running_ && !safety_monitor_.isEmergencyStopActive()) {
            auto start_time = std::chrono::steady_clock::now();
            
            // Update all sensors
            for (auto& sensor : joint_sensors_) {
                sensor.read();
            }
            
            for (auto& sensor : imu_sensors_) {
                sensor.read();
            }
            
            // Update sensor fusion
            for (size_t i = 0; i < joint_controllers_.size(); ++i) {
                auto state = joint_sensors_[i].getState();
                sensor_fusion_.updateJointState(joint_controllers_[i].getName(), state);
            }
            
            for (size_t i = 0; i < imu_sensors_.size(); ++i) {
                auto data = imu_sensors_[i].getData();
                sensor_fusion_.updateImuData(imu_sensors_[i].getName(), data);
            }
            
            // Update controllers
            for (auto& controller : joint_controllers_) {
                controller.update(dt);
            }
            
            // Check safety
            bool is_safe = safety_monitor_.checkSafety();
            
            // Print status periodically
            auto current_time = std::chrono::steady_clock::now();
            double elapsed = std::chrono::duration<double>(current_time - last_time).count();
            if (elapsed > 1.0) {  // Print every second
                auto left_hip_state = joint_sensors_[0].getState();  // left_hip
                auto right_hip_state = joint_sensors_[3].getState(); // right_hip
                double balance = sensor_fusion_.getBalanceEstimate();
                
                std::cout << std::fixed << std::setprecision(3)
                         << std::chrono::duration<double>(current_time.time_since_epoch()).count() << "\t"
                         << left_hip_state.position << "\t\t"
                         << right_hip_state.position << "\t\t"
                         << balance << "\t\t"
                         << (is_safe ? "OK" : "EMERGENCY") << "\n";
                
                last_time = current_time;
            }
            
            // Control timing
            auto end_time = std::chrono::steady_clock::now();
            auto elapsed_time = std::chrono::duration<double>(end_time - start_time).count();
            
            if (elapsed_time < dt) {
                // Sleep for remaining time
                auto sleep_time = std::chrono::duration<double>(dt - elapsed_time);
                std::this_thread::sleep_for(sleep_time);
            } else {
                std::cout << "WARNING: Control loop took too long: " << elapsed_time << "s\n";
            }
        }
        
        if (safety_monitor_.isEmergencyStopActive()) {
            std::cout << "Control loop stopped due to safety emergency.\n";
        } else {
            std::cout << "Control loop stopped normally.\n";
        }
    }
    
    void stop() {
        is_running_ = false;
    }
};

int main() {
    std::cout << "Humanoid Robot Actuator Control and Sensor Integration\n";
    std::cout << "=====================================================\n";
    std::cout << "This example demonstrates:\n";
    std::cout << "1. Hardware abstraction for actuators and sensors\n";
    std::cout << "2. Real-time control patterns\n";
    std::cout << "3. Sensor fusion techniques\n";
    std::cout << "4. Safety monitoring in actuator systems\n";
    std::cout << "\n";
    
    try {
        // Create and run the humanoid controller
        HumanoidController robot_controller(200.0);  // 200Hz control frequency
        robot_controller.run();
    }
    catch (const std::exception& e) {
        std::cerr << "Error running robot controller: " << e.what() << std::endl;
        return 1;
    }
    
    std::cout << "\nKey takeaways about actuator and sensor systems:\n";
    std::cout << "- Hardware abstraction enables modularity and maintainability\n";
    std::cout << "- Real-time control requires precise timing and low latency\n";
    std::cout << "- Sensor fusion combines multiple sources for better state estimation\n";
    std::cout << "- Safety systems are critical for preventing damage to robot and humans\n";
    std::cout << "- Proper error handling prevents cascading failures\n";
    
    return 0;
}