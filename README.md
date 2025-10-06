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


- Finally, run the game:
 - Finally, run the game:
  
```
  python3 alien_invasion.py
```

## Run & Train (developer-focused instructions)

These instructions explain the recommended order for running tools and game entrypoints when working with ML models and recordings.

1) Install dependencies

```
pip install -r requirements.txt
```

2) (Optional) Train or prepare ML models before running the game

If you plan to run the game with a non-Easy difficulty that uses ML controllers, prepare models first. The AI utilities will look for model files under `data/models/`.

From project root you can run the AI manager to train or verify models:

```
python -m src.ai_manager --train
# or to force retrain
python -m src.ai_manager --train --force
```

If no recordings exist yet, train will fail — in that case play a few sessions in Easy difficulty to create recordings (see step 4).

3) Run the dev entrypoint (recommended for development)

The repo includes a developer entrypoint with extra logging and recorder integration. Use this to capture gameplay recordings easily:

```
python dev_alien_invasion.py
```

4) How recording works (Easy difficulty)

- Starting a gameplay session (press START → choose difficulty) will begin the game. When gameplay becomes active the game will automatically open a Recorder session.
- While playing, per-frame features are collected via `src.recorder.collect_frame_features` and written into a CSV file.
- When the gameplay session ends or you quit, the recorder flushes and closes the CSV and prints the saved path to the console (for example `data/recordings/gameplay_Easy_YYYYmmdd_HHMMSS.csv`).
- If you want to generate recordings without ML models present, run the game in `Easy` difficulty and play a variety of actions (move in all directions, fire, pick up items) for the dataset to be useful.

5) Where files are saved

- Recordings: `data/recordings/*.csv` — created automatically by the recorder when gameplay starts.
- Models: `data/models/*.joblib` — saved by training utilities like `src.train_models.*` or `src.ai_manager`.

6) Git safety (already configured)

- The repository `.gitignore` excludes generated data directories such as `data/recordings/` and `data/models/` to avoid committing large/binary files.

7) Quick troubleshooting

- If you start the game with a non-Easy difficulty and the game refuses to start because models are missing, either train models (step 2) or play and record gameplay in Easy first (step 4) to produce recordings and then train.
- If you expect a recording to be created but cannot find the file, check the game console for a message like `Recording saved to: data/recordings/<filename>.csv` after you stop playing.

If you'd like, I can add a short `RUNNING.md` with these steps and a couple example commands for Windows PowerShell.
