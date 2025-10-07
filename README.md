# We Can Make This Game Better!

Welcome to the Alien Invasion project. This is an open-source effort where serious developers, designers, and gamers come together to create something extraordinary. We’re focused on pushing the limits of what this game can be, and we need your expertise to make that happen.

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



## Quick Start

These steps work for both Windows (PowerShell) and POSIX shells. Use the commands that match your environment.

1. Install dependencies:
  ```powershell
  pip install -r requirements.txt
  ```

2. Run the main game (for players):
  ```powershell
  python alien_invasion.py
  ```

3. For development (extra logging, gameplay recording):
  ```powershell
  python dev_alien_invasion.py
  ```

The developer entrypoint automatically starts the recorder when gameplay begins and prints the recording file path when you quit.


## Development, ML Training, and Recording

This project supports gameplay recording and ML-based enemy controllers. Here’s how to use these features:

- **Play as a user:** Run `alien_invasion.py` (no ML required).
- **Develop or collect data:** Run `dev_alien_invasion.py` (enables recorder and extra logging).
- **Train ML models:** Use `src/ai_manager` or helper scripts.

### ML Workflow

1. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Generate recordings:**
   - Run the developer entrypoint:
     ```powershell
     python dev_alien_invasion.py
     ```
   - Press START, choose `Easy` difficulty (does not require ML models).
   - Play several sessions (move, fire, pick up items, get hit). When you quit, the recorder prints the CSV path, e.g.:
     ```
     Recording saved to: data/recordings/gameplay_Easy_20251006_143215.csv
     ```

3. **Train ML models:**
   - From the project root:
     ```powershell
     python -m src.ai_manager --train
     # To force retrain:
     python -m src.ai_manager --train --force
     ```
   - Trained models are saved in `data/models/*.joblib`.

4. **Run with trained models:**
   - Choose `Normal` or higher difficulty in the game. If models are missing, the game will prompt you to train.
   - Run either entrypoint:
     ```powershell
     python alien_invasion.py      # end-user
     python dev_alien_invasion.py  # developer
     ```

### File Locations

- **Recordings:** `data/recordings/*.csv` (created automatically)
- **Models:** `data/models/*.joblib` (created by training)

### Git Safety

- `.gitignore` excludes generated data and dev entrypoints by default.

### Troubleshooting

- **Game refuses non-Easy difficulty:**
  - ML models are missing. Train models or record gameplay in Easy and retrain.
- **No recordings found:**
  - Use `dev_alien_invasion.py` and check for `Recording saved to:` in the console.
- **Difficulty changes not applied:**
  - Make sure you use the difficulty screen; presets are applied on spawn.

