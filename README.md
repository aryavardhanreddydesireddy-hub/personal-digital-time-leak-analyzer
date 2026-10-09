# Personal Digital Time Leak Analyzer

A beginner-friendly Python project that helps users manually record study, work, entertainment, and social-media sessions, then review their time patterns.

## Features
- Add activity sessions through a Streamlit web interface.
- Save records in a local SQLite database.
- View time totals and category charts.
- Use a Scikit-learn Isolation Forest model to flag unusual session durations.
- Generate a simple rule-based summary and download activity history as CSV.

## Tech stack
Python, Streamlit, SQLite, Pandas, Scikit-learn.

## Run locally (Windows)
1. Install Python 3.11 or newer from https://www.python.org/downloads/ and enable **Add Python to PATH** during installation.
2. Extract this project folder.
3. Open Command Prompt inside the `Personal_Digital_Time_Leak_Analyzer` folder.
4. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
5. Activate it:
   ```bash
   .venv\Scripts\activate
   ```
6. Install packages:
   ```bash
   python -m pip install -r requirements.txt
   ```
7. Start the app:
   ```bash
   streamlit run app.py
   ```
8. The app opens in your browser. Use **Load sample data** to test it.

## Database
SQLite creates `data/time_leak.db` automatically. The database is ignored by Git because it is local user data. Sample data is fictional.

## Important scope note
The current version uses manual activity logging and a rule-based text summary. The anomaly detector uses Isolation Forest. It does **not** automatically monitor a device, and it does **not** call an LLM yet. Add and test those features before describing them as completed.

## Suggested next steps
- Add date-range filters and weekly comparisons.
- Add unit tests for data insertion and insight calculations.
- Add an optional local LLM integration (for example, through Ollama) for natural-language suggestions.
- Add screenshots of the working app to this README.
