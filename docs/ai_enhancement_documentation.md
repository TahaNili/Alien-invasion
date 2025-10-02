# AI Enhancement Documentation

## Overview
This document details the implementation of enhanced AI capabilities for enemies in the Alien Invasion game. The enhancement includes intelligent behavior patterns, machine learning-based decision making, and a difficulty management system.

## Architecture Components

### 1. Controller System
Located in `src/controllers/`, this system implements a modular approach to enemy AI through different controller types.

#### 1.1 Base Controller (`base_controller.py`)
The foundation of the controller system that defines the core interface:
- `observe()`: Gathers environmental data and game state
- `decide()`: Makes decisions based on observations
- `on_event()`: Handles game events
- Provides abstract base class for all other controllers

#### 1.2 Behavior Controller (`behavior_controller.py`)
Implements state machine-based behavior patterns:
- States: patrol → chase → fight → pickup → flee
- Features:
  - State transitions based on distance and conditions
  - Basic movement and shooting decisions
  - Dodge mechanics with cooldown
  - Predictive shooting capability
- Params:
  - dodge_cooldown_ms: Cooldown time between dodges
  - Other customizable behavior parameters

#### 1.3 ML Controller (`ml_controller.py`)
Machine learning-based decision making:
- Integration with AIManager for ML model predictions
- Features:
  - Decision throttling to optimize performance
  - Fallback behavior when ML is not confident
  - Learning from player patterns
  - Dynamic adaptation to player strategies

### 2. Item System (`item_agent.py`)
Manages intelligent item interaction:
- `should_pickup()`: Decides whether to pick up an item based on:
  - Current health/shield status
  - Item type and rarity
  - Strategic value
- `should_use()`: Determines optimal item usage timing
- Modular design for easy addition of new item types

### 3. Difficulty Management (`difficulty_manager.py`)
Handles game difficulty scaling:
- 5 difficulty levels: Easy → Normal → Hard → Expert → Unbeatable
- Features:
  - Preset parameters for each difficulty level
  - Controller factory for spawning appropriate AI types
  - Dynamic parameter adjustment
  - Progressive difficulty scaling

## Implementation Progress

### Completed Tasks:
1. Created controller system skeleton
   - Implemented base interface
   - Added behavior controller with FSM
   - Integrated ML controller with AIManager

2. Implemented item interaction system
   - Added pickup logic
   - Implemented usage decision making
   - Created modular item handling

3. Created difficulty management system
   - Defined difficulty presets
   - Implemented controller factory
   - Added parameter management

### Pending Tasks:
1. Spawn System Integration
   - Hook into spawn_random_alien
   - Add difficulty-based spawning

2. Testing and Tuning
   - Test each difficulty level
   - Tune parameters
   - Balance gameplay

## Technical Details

### State Machine Logic
The behavior controller uses a simple but effective state machine:
```python
if dist < 200:
    state = "chase"    # Close range: pursue and attack
else:
    state = "patrol"   # Far range: patrol area
```

### ML Model Integration
The ML controller uses several models:
- Logistic Regression: For binary decisions
- Decision Trees: For complex tactical choices
- KNN: For pattern recognition

### Difficulty Parameters
Each difficulty level adjusts:
- Enemy speed
- Attack frequency
- Dodge probability
- Item usage intelligence
- ML model confidence thresholds

## Future Enhancements
1. Additional Behavior States
   - Group coordination
   - Resource control
   - Map zone control

2. Advanced ML Features
   - Real-time learning
   - Player style adaptation
   - Cooperative learning between enemies

3. Dynamic Difficulty Adjustment
   - Player performance tracking
   - Automatic difficulty scaling
   - Custom difficulty presets