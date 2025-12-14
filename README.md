# Physical AI & Humanoid Robotics Book

This project contains a comprehensive book on Physical AI and Humanoid Robotics, built using Docusaurus.

## Table of Contents

1. [Module 1: Foundations of Physical AI](./docs/modules/01-foundations/index.md)
   - Lesson 1.1: Introduction to Physical AI
   - Lesson 1.2: Embodied Cognition and Intelligence
   - Lesson 1.3: Physics and Real-World Constraints in AI Systems

2. [Module 2: Humanoid Robotics Architecture](./docs/modules/02-architecture/index.md)
   - Lesson 2.1: Physical Design of Humanoid Robots (in separate spec repository)
   - Lesson 2.2: Actuators, Motors, Joints, and Sensors
   - Lesson 2.3: Locomotion, Balance, and Gait Control

3. [Module 3: AI for Humanoids](./docs/modules/03-ai-for-humanoids/index.md)
   - Lesson 3.1: Reinforcement Learning for Motor Control
   - Lesson 3.2: Vision, Audio, and Multimodal Perception
   - Lesson 3.3: Cognitive Architectures and Reasoning

4. [Module 4: Building & Deploying Humanoid Robots](./docs/modules/04-deployment/index.md)
   - Lesson 4.1: Hardware Integration with AI Systems
   - Lesson 4.2: ROS2, Real-time Control, and Robotics Software Stack
   - Lesson 4.3: Safety Protocols and Real-world Testing

## Prerequisites

- Node.js (version 18 or higher)
- npm or yarn package manager

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Local Development

```bash
npm start
```

This command starts a local development server and opens up a browser window. Most changes are reflected live without having to restart the server.

## Build for Production

```bash
npm run build
```

This command generates static content into the `build` directory and can be served using any static contents hosting service.

## Deployment

To deploy the book to GitHub Pages:

1. Ensure you have a GitHub repository set up
2. Set the `organizationName` and `projectName` in `docusaurus.config.ts`
3. Run the deployment command:
   ```bash
   GIT_USER=<Your GitHub username> npm run deploy
   ```

## Example Code

The book includes several example implementations in Python, C++, and ROS2:
- Python examples for RL and sensor fusion: `docs/examples/python/`
- C++ examples for actuator control: `docs/examples/cpp/`
- ROS2 examples for humanoid control: `docs/examples/ros2/`

## Contributing

This project follows a specification-driven development approach. For changes, please follow the process outlined in the `.specify` directory.

## License

This project is licensed under the terms specified in the LICENSE file (to be added).

## Acknowledgments

This book was developed following the principles outlined in the Physical AI & Humanoid Robotics Book Constitution.