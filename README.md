# We Can Make This Game Better!

Welcome to the Alien Invasion project. This is an open-source effort where developers, designers, and gamers come together to create something extraordinary. We’re focused on pushing the limits of what this game can be, and we need your expertise to make that happen.

## Advanced Features: AI-Powered Gameplay

This game features advanced AI enemies on higher difficulty levels. Here's what you need to know:

### ML Features

- **Easy Mode**: No AI required - perfect for casual play
- **Normal and Above**: AI-powered enemies for extra challenge
- **ML Training**: Optional feature to enable advanced difficulties

### Setting Up AI Features

The project includes an AI system for enemy controllers that is optional and powered by simple ML models (Logistic Regression, Decision Tree, KNN). Training uses recorded gameplay data (CSV files) produced by the game's recorder. The models are saved under `data/models/` as joblib files and are required for "Normal" difficulty and above.

The foundation is set, but now it’s time to build something even better. If you’re ready to contribute, collaborate, and help take this project to the next level, we’re excited to have you on board.

<div align="center" style="line-height: 1;">
  <a href="https://github.com/MatinAfzal/Alien-invasion/releases" target="_blank" style="margin: 2px;">
    <img alt="Homepage" src="https://img.shields.io/badge/Github-Latest%20release-7289da?logo=futurelearn&logoColor=white&color=7289da" style="display: inline-block; vertical-align: middle;"/>
  </a>
  <a href="https://discord.com/invite/jBhmM2j2GN" target="_blank" style="margin: 2px;">
    <img alt="Chat" src="https://img.shields.io/badge/Discord-MatinAfzal-7289da?logo=Discord&logoColor=white&color=7289da" style="display: inline-block; vertical-align: middle;"/>
  </a>
  <a href="https://github.com/MatinAfzal/Alien-invasion/discussions/43" target="_blank" style="margin: 2px;">
    <img alt="Chat" src="https://img.shields.io/badge/Discussions-TODO%20List-7289da?logo=todoist&logoColor=white&color=green" style="display: inline-block; vertical-align: middle;"/>
  </a>
</div> 

---

<table align="center">
  <tr>
    <th>Version</th>
    <th>Date</th>
    <th>Release</th>
  </tr>
    <tr>
    <td>V1.3.0</td>
    <td>May 3, 2025</td>
    <td>
      <a href="https://github.com/MatinAfzal/Alien-invasion/releases/tag/V1.3.0" target="_blank">
        <img src="https://img.shields.io/badge/Release-V1.3.0-7289da?logo=alienware&logoColor=green&color=violet" alt="Release Badge">
      </a>
    </td>
  </tr>
  <tr>
    <td>V1.2.0</td>
    <td>Feb 3, 2025</td>
    <td>
      <a href="https://github.com/MatinAfzal/Alien-invasion/releases/tag/V1.2.0" target="_blank">
        <img src="https://img.shields.io/badge/Release-V1.2.0-7289da?logo=alienware&logoColor=green&color=violet" alt="Release Badge">
      </a>
    </td>
  </tr>
  <tr>
    <td>V1.1.0</td>
    <td>Jan 8, 2025</td>
    <td>
      <a href="https://github.com/MatinAfzal/Alien-invasion/releases/tag/V1.1.0" target="_blank">
        <img src="https://img.shields.io/badge/Release-V1.1.0-7289da?logo=alienware&logoColor=green&color=violet" alt="Release Badge">
      </a>
    </td>
  </tr>
  <tr>
    <td>V1.0.0</td>
    <td>Nov 16, 2024</td>
    <td>
      <a href="https://github.com/MatinAfzal/Alien-invasion/releases/tag/V1.0.0" target="_blank">
        <img src="https://img.shields.io/badge/Release-V1.0.0-7289da?logo=alienware&logoColor=green&color=violet" alt="Release Badge">
      </a>
    </td>
  </tr>
</table>


## How to Contribute

- To contribute to the Alien Invasion project, please make your pull requests to the [develop](https://github.com/MatinAfzal/Alien-invasion/tree/develop) branch with a clear and detailed description in English of the changes you've made. 

- It's important to ensure your PRs are standardized, PEP8 compliant, and that you avoid large commits. Instead, break your changes into smaller, logical commits to make the review process smoother. 

- If you're adding new assets like sound effects, music, or textures, ensure that the sources are listed in the Copyright.txt file in the appropriate directory, and include the source links in your PR description if possible. 

- For ideas on what to work on, check the [TODO list discussion](https://github.com/MatinAfzal/Alien-invasion/discussions/43), or feel free to join our [Discord server](https://discord.com/invite/jBhmM2j2GN) to collaborate and share your progress. 

We appreciate your contributions and look forward to building something great.

## Project Setup

- Clone this [repository](https://github.com/MatinAfzal/Alien-invasion) or download the [latest version](https://github.com/MatinAfzal/Alien-invasion/releases).

- Next, navigate to the project directory:

```
   cd Alien-invasion
```

- Make sure you have Python 3 or later installed. Then, install the dependencies:
```
   pip install -r requirements.txt
```

Important compatibility note:

- This project uses modern typing and standard library features that require Python 3.9 or newer. We recommend using Python 3.9+ (3.10/3.11 tested).
- Key dependencies are listed in `requirements.txt` (pygame, numpy, pandas, scikit-learn, joblib). A representative snapshot from `requirements.txt`:

  - pygame>=2.6.1
  - numpy>=1.26.4
  - pandas>=2.1.4
  - scikit-learn>=1.3.2
  - joblib>=1.3.2

If you use a virtual environment, activate it before installing requirements.



## Quick Start

Getting started with Alien Invasion is easy! These steps work on all platforms:

1. Install dependencies:
```powershell
pip install -r requirements.txt
```

2. Launch the game:
```powershell
python alien_invasion.py
```

That's it! You're ready to start playing. Choose Easy difficulty to begin - it's perfect for new players and requires no additional setup.

The developer entrypoint automatically starts the recorder when gameplay begins and prints the recording file path when you quit.

Note: `dev_alien_invasion.py` enables additional logging and will start the recorder automatically when gameplay begins (it prints the path to the CSV on stop). Regular `alien_invasion.py` also uses the recorder when a gameplay session is active, but `dev_alien_invasion.py` is preferred for collecting training data.


## Development, ML Training, and Recording

This project supports gameplay recording and ML-based enemy controllers. Here’s how to use these features:

- **Play as a user:** Run `alien_invasion.py` (no ML required).
- **Develop or collect data:** Run `dev_alien_invasion.py` (enables recorder and extra logging).
- **Train ML models:** Use `src/ai_manager` or helper scripts.

To enable advanced AI features:

1. **Train the AI models** (one-time setup):
   ```powershell
   # From the project root
   python -m src.ai_manager --train
   ```
   This will create the necessary AI models in `data/models/`.

Additional training notes and troubleshooting

- Model files: the project expects three models saved as joblib files in `data/models/` (commonly named `logistic.joblib`, `tree.joblib`, `knn.joblib`). The AI manager saves a small metadata object with each model (including the feature names used during training).
- Training preconditions: training uses the most recent CSV file from `data/recordings/`. The recorder writes per-frame feature CSVs with a default set of columns (frame, timestamp, dt, ship_centerx, ship_centery, ship_angle, moving_right, moving_left, moving_up, moving_down, bullets_count, aliens_count, ...). For training to succeed the recording must contain movement columns (`moving_right`, `moving_left`, `moving_up`, `moving_down`) with at least two different movement classes present in the data.
- Force retrain: you can force retraining even if models exist using `--force`:

```
python -m src.ai_manager --train --force
```

- In-game training: The difficulty screen provides a "Train" action that runs the same command in a background subprocess (`python -m src.ai_manager --train`) and reports progress. Training is performed in a subprocess to avoid blocking the game loop.

- If training fails: check the logs printed to the terminal for errors, ensure there are CSV recordings in `data/recordings/`, and verify that the recording includes the movement flag columns. If recordings are missing, run `dev_alien_invasion.py` and play for a short time to produce data.

- Model compatibility: the AI manager attempts to verify that saved models were trained on the same feature set as the latest recording and will retrain if there is a mismatch.

2. **Launch the game normally**:
   ```powershell
   python alien_invasion.py
   ```

3. **Select your difficulty**:
   - Easy: No AI required
   - Normal and above: Uses trained AI models

Don't worry about missing this step - the game will guide you through the process when you try to play higher difficulties. You can always enjoy the full game experience on Easy mode without any AI setup.

## Game Files

Important locations:
- `data/models/`: AI model files (created when you train)
- `src/`: Source code files
- `data/assets/`: Game graphics and sounds

Recorder & data file details

- Recordings are written to `data/recordings/` and use the filename pattern: `sessionname_YYYYmmdd_HHMMSS.csv`.
- The recorder writes a header row with default columns; callers and training code ignore unexpected columns but require movement columns for model target construction.
- When you stop a recording the recorder prints the full path to the saved CSV file in the console.

## Troubleshooting

Common questions and solutions:

- **"Can't select Normal/Hard difficulty"**
  - Solution: Run `python -m src.ai_manager --train` to enable advanced difficulties
  
- **"Changes to difficulty not working"**
  - Solution: Make sure to use the in-game difficulty screen
  - Changes take effect when new enemies spawn

- **"Game is too hard/easy"**
  - Easy mode: Best for learning the game
  - Normal: Requires AI models, provides more challenge
  - Hard and above: For experienced players only!

