# Forge v1.0

A modular Streamlit workout application built around a four-week,
45-minute strength program with shoulder-smart substitutions.

## Project structure

```text
Forge_v1_0/
├── app.py
├── forge_core.py
├── requirements.txt
├── pages/
│   ├── 1_Workout.py
│   ├── 2_History.py
│   ├── 3_Analytics.py
│   └── 4_Settings.py
├── data/
│   └── workout_plan.csv
├── database/
│   └── workout_logs.db   # created automatically
└── assets/
```

## Run on Windows

Open PowerShell in the Forge folder and run:

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

## Preserve existing V2 logs

If your prior V2 folder contains `workout_logs.db`, copy it into:

```text
Forge_v1_0\database\
```

Do that before logging new Forge v1.0 workouts.

## Pages

- Dashboard: program and weekly overview
- Workout: set logging, prior performance, suggestions, timer
- History: filtering, export, deletion
- Analytics: sessions, volume, RPE, pain, exercise trends
- Settings: backup and restore

## Storage warning

SQLite persists normally on your own computer. Streamlit Community Cloud
may reset locally written files after restarts or redeployments. Export
history backups until permanent cloud storage is connected.

## Forge v1.1 Cloud
- Uses Supabase when Streamlit secrets are configured.
- Keeps local SQLite as a fallback for local development.
- Dashboard, Workout, History, Analytics, deletion, and exports use the same cloud data.
- Never commit secret keys or `.streamlit/secrets.toml` to GitHub.
