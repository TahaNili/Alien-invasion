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


## Quick Start (run the game)

These steps assume you're working on Windows (PowerShell) or a POSIX shell. Use the commands that match your environment.

1. Install dependencies (one-time):

```powershell
pip install -r requirements.txt
```

2. Run the normal entrypoint (packaged for end users):

```powershell
python alien_invasion.py
```

3. For development (extra logging, recorder integration), use the dev entrypoint:

```powershell
python dev_alien_invasion.py
```

The developer entrypoint will automatically start the recorder when gameplay begins and print recording paths when sessions end.

## Run, Train & Development (developer-focused)

This project includes utilities for recording gameplay and training ML models used by enemy controllers. The recommended workflow depends on what you want to do:

- Play as an end-user (no ML training required): run `alien_invasion.py`.
- Develop or collect data for ML: run the `dev_alien_invasion.py` entrypoint to get recorder integration.
- Train or retrain ML models: use `src.ai_manager` or the training helper scripts.

Recommended sequence for ML workflows:

1) Install dependencies (PowerShell):

```powershell
pip install -r requirements.txt
```

2) Generate recordings (if you don't have any models yet)

- Run the developer entrypoint to capture per-frame features automatically:

```powershell
python dev_alien_invasion.py
```

- Press START → choose `Easy` difficulty to ensure the game doesn't block recording (Easy does not require ML models).
- Play several sessions (try movement, firing, picking up items, getting hit). When you quit a session the recorder will print the saved CSV path, e.g.:

```
Recording saved to: data/recordings/gameplay_Easy_20251006_143215.csv
```

3) Train ML models

- Once you have recordings, train models with the AI manager. From the project root:

```powershell
python -m src.ai_manager --train
# force retrain
python -m src.ai_manager --train --force
```

- Trained models are saved under `data/models/*.joblib`.

4) Run the normal or dev game with trained models

- If trained models exist and you want enemies to use them, you can choose `Normal` or higher difficulties in the difficulty screen. The game will refuse to start those difficulties if models are missing and will prompt you to train.

```powershell
python alien_invasion.py      # end-user run
python dev_alien_invasion.py  # development run (recorder + extra logging)
```

Where files are saved

- Recordings: `data/recordings/*.csv` (auto-created by the recorder when gameplay begins in the dev entrypoint).
- Models: `data/models/*.joblib` (saved by training utilities like `src.ai_manager`).

Git & safety

- `.gitignore` already excludes generated directories such as `data/recordings/` and `data/models/` to avoid committing large files.

Troubleshooting tips

- Game refuses to start non-Easy difficulty:
  - This means ML models required for that difficulty are missing. Train models (`python -m src.ai_manager --train`) or generate recordings in Easy and re-run training.

- Recordings not appearing:
  - Make sure you ran `dev_alien_invasion.py` (recorder is enabled there).
  - Watch the console log for the `Recording saved to:` message.

- Difficulty changes not applying to enemies:
  - The project applies presets when enemies are spawned via `DifficultyManager`. If you observe all enemies behaving like Easy, ensure you start the game using the difficulty screen so presets are applied.

Want a runnable quick reference file?

I can add a short `RUNNING.md` containing the PowerShell commands above and a tiny checklist for devs. Say "yes" and I'll add it.
