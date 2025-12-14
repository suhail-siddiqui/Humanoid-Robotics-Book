import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  // Manual sidebar configuration for the Physical AI & Humanoid Robotics Book
  tutorialSidebar: [
    {
      type: 'category',
      label: 'Introduction',
      items: ['intro'],
      collapsed: false,
    },
    {
      type: 'category',
      label: 'Module 1: Foundations of Physical AI',
      items: [
        'modules/foundations/index',
        'modules/foundations/lesson-1-introduction-to-physical-ai',
        'modules/foundations/lesson-2-embodied-cognition',
        'modules/foundations/lesson-3-physics-and-constraints'
      ],
      collapsed: false,
    },
    {
      type: 'category',
      label: 'Module 2: Humanoid Robotics Architecture',
      items: [
        'modules/architecture/index',
        'modules/architecture/lesson-1-physical-design',
        'modules/architecture/lesson-2-actuators-sensors',
        'modules/architecture/lesson-3-locomotion-balance'
      ],
      collapsed: false,
    },
    {
      type: 'category',
      label: 'Module 3: AI for Humanoids',
      items: [
        'modules/ai-for-humanoids/index',
        'modules/ai-for-humanoids/lesson-1-reinforcement-learning',
        'modules/ai-for-humanoids/lesson-2-perception',
        'modules/ai-for-humanoids/lesson-3-cognitive-architectures'
      ],
      collapsed: false,
    },
    {
      type: 'category',
      label: 'Module 4: Building & Deploying Humanoid Robots',
      items: [
        'modules/deployment/index',
        'modules/deployment/lesson-1-hardware-integration',
        'modules/deployment/lesson-2-ros2-rt-stack',
        'modules/deployment/lesson-3-safety-protocols'
      ],
      collapsed: false,
    },
  ],
};

export default sidebars;
