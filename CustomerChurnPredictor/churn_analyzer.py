"""
Customer Churn Analyzer (package copy)
"""
import csv
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
CSV_FILE = DATA_DIR / "customers.csv"
JSON_FILE = DATA_DIR / "customers.json"
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# The analysis implementation mirrors the demo in travalPlanProject
from travalPlanProject.churn_analyzer import analyze_account


def main():
    datasets = []
    if CSV_FILE.exists():
        with open(CSV_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                for key in ('logins_30d','logins_7d','avg_time_minutes_30d','core_feature_calls_30d','api_calls_30d','support_tickets_30d','unresolved_tickets','spend_30d','feature_adoption_score'):
                    if r.get(key):
                        try:
                            r[key] = float(r[key])
                        except:
                            r[key] = 0
                datasets.append(r)
    if JSON_FILE.exists():
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datasets.extend(json.load(f))

    reports = [analyze_account(a) for a in datasets]

    out_path = REPORTS_DIR / 'churn_reports.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(reports, f, indent=2)

    print('Wrote reports to', out_path)


if __name__ == '__main__':
    main()
