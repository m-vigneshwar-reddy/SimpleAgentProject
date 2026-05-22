"""
Customer Churn Analyzer (package copy)
"""
import csv
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
CSV_FILE = DATA_DIR / "customers.csv"
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def parse_csv(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            r2 = {k: (v if v != '' else None) for k, v in r.items()}
            for key in ('logins_30d', 'logins_7d', 'avg_time_minutes_30d', 'core_feature_calls_30d', 'api_calls_30d', 'support_tickets_30d', 'unresolved_tickets', 'spend_30d', 'feature_adoption_score'):
                if r2.get(key) is not None:
                    try:
                        r2[key] = float(r2[key])
                    except:
                        r2[key] = 0
            rows.append(r2)
    return rows


def parse_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_account(a):
    def days_since(date_str):
        try:
            d = datetime.strptime(date_str, '%Y-%m-%d')
            return (datetime.now() - d).days
        except:
            return 9999

    signals = []
    log30 = float(a.get('logins_30d') or 0)
    log7 = float(a.get('logins_7d') or 0)
    engagement_drop = False
    if log30 > 0:
        expected_7 = log30 * (7.0 / 30.0)
        if log7 < expected_7 * 0.5:
            engagement_drop = True
            signals.append(('Engagement Decay', f'{int(log30)} logins in 30d vs {int(log7)} in last 7d'))

    unresolved = int(a.get('unresolved_tickets') or 0)
    neg_pct = float(a.get('ticket_sentiment_neg_pct') or 0)
    support_spike = False
    if unresolved > 0 or (a.get('support_tickets_30d') and float(a.get('support_tickets_30d')) >= 3):
        support_spike = True
        signals.append(('Friction & Support', f'{int(a.get("support_tickets_30d", 0))} tickets (unresolved:{unresolved}), neg_sentiment:{neg_pct}'))

    payment_status = (a.get('payment_status') or '').lower()
    last_payment_days = days_since(a.get('last_payment_date') or '1970-01-01')
    contract_end_days = days_since(a.get('contract_end_date') or '9999-12-31')
    health_issue = False
    if payment_status != 'ok' or last_payment_days > 60:
        health_issue = True
        signals.append(('Account Health', f'payment_status={payment_status}, last_payment_days={last_payment_days}'))
    if contract_end_days <= 60:
        signals.append(('Account Health', f'contract ending in {contract_end_days} days'))

    adoption = float(a.get('feature_adoption_score') or 0)
    spend = float(a.get('spend_30d') or 0)
    value_disconnection = False
    if spend > 0 and adoption < 30:
        value_disconnection = True
        signals.append(('Value Disconnection', f'spend_30d={spend}, adoption_score={adoption}'))

    major_flags = 0
    major_flags += 1 if engagement_drop else 0
    major_flags += 1 if support_spike and neg_pct >= 0.4 else 0
    major_flags += 1 if health_issue else 0
    major_flags += 1 if value_disconnection else 0

    if major_flags >= 3:
        risk_class = 'High'
        churn_prob = 75 + min(20, major_flags * 5)
    elif major_flags == 2:
        risk_class = 'Medium'
        churn_prob = 35 + major_flags * 15
    else:
        risk_class = 'Low'
        churn_prob = 10 + major_flags * 10

    if payment_status != 'ok' or (contract_end_days <= 14):
        horizon = 'Imminent (0-14 days)'
    elif risk_class == 'High':
        horizon = 'Mid-Term (15-60 days)'
    else:
        horizon = 'Low Risk'

    primary = signals[0][1] if signals else 'No clear red flags'
    secondary = signals[1][1] if len(signals) > 1 else ''

    if engagement_drop and health_issue:
        beh = 'Recent sharp engagement decline combined with payment or contract issues — activity and financial signals both weakening.'
    elif engagement_drop:
        beh = 'User activity has fallen sharply; likely losing interest or facing blockers in core workflows.'
    elif health_issue:
        beh = 'Account shows billing or contract health problems which increase churn risk.'
    elif support_spike:
        beh = 'Multiple support tickets with negative sentiment indicate unresolved friction.'
    else:
        beh = 'Usage and payments are generally healthy.'

    if payment_status != 'ok':
        trigger = f'Create high-priority billing recovery workflow; alert CSM and auto-send invoice reminder to {a.get("customer_name")}. '
    elif engagement_drop:
        trigger = 'Send segmented re-engagement email with 1-click tutorial and targeted in-app nudge for core workflows.'
    elif support_spike:
        trigger = 'Open high-priority support escalation; assign senior engineer and schedule a sync call.'
    else:
        trigger = 'Monitor weekly; no immediate trigger.'

    if value_disconnection:
        value_intervention = 'Offer tailored onboarding/implementation session and provide sample workflows that map product features to their ROI.'
    elif support_spike:
        value_intervention = 'Schedule a 30-min technical deep-dive with a solutions engineer and provide temporary workaround documentation.'
    elif engagement_drop:
        value_intervention = 'Offer a live optimization session and short checklist to restore core usage.'
    else:
        value_intervention = 'Share advanced best-practices and customer case studies matching their tier.'

    if risk_class == 'High':
        commercial = 'Offer targeted discount or 1-month credit contingent on implementation milestones; propose contract extension with dedicated onboarding.'
    elif risk_class == 'Medium':
        commercial = 'Propose plan review and small loyalty credit; prioritize feature enablement credits.'
    else:
        commercial = 'No commercial action; continue value reinforcement.'

    return {
        'customer_id': a.get('customer_id'),
        'customer_name': a.get('customer_name'),
        'risk_profile': {
            'risk_classification': risk_class,
            'churn_probability_percent': int(churn_prob),
            'time_horizon': horizon
        },
        'core_drivers': {
            'primary_driver': primary,
            'secondary_driver': secondary
        },
        'behavioral_summary': beh,
        'playbook': {
            'trigger_action_immediate_next_24_hours': trigger,
            'value_intervention_next_7_days': value_intervention,
            'commercial_safeguard': commercial
        },
        'signals': signals
    }


def main():
    datasets = []
    if CSV_FILE.exists():
        datasets.extend(parse_csv(CSV_FILE))

    reports = [analyze_account(a) for a in datasets]
    out_path = REPORTS_DIR / 'churn_reports.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(reports, f, indent=2)

    for r in reports:
        print('\n' + '=' * 60)
        print(f"🚨 CHURN RISK REPORT: {r['customer_name']} ({r['customer_id']})")
        print('\n#### 1. Risk Profile')
        rp = r['risk_profile']
        print(f"*   **Risk Classification:** {rp['risk_classification']}")
        print(f"*   **Churn Probability:** {rp['churn_probability_percent']}%")
        print(f"*   **Time Horizon:** {rp['time_horizon']}")
        print('\n#### 2. Core Drivers of Risk')
        cd = r['core_drivers']
        print(f"*   **Primary Driver:** {cd['primary_driver']}")
        print(f"*   **Secondary Driver:** {cd['secondary_driver']}")
        print('\n#### 3. Behavioral Summary')
        print(r['behavioral_summary'])
        print('\n#### 4. Automated & Manual Playbook (Next Steps)')
        pb = r['playbook']
        print(f"*   **Trigger Action (Immediate - Next 24 Hours):** {pb['trigger_action_immediate_next_24_hours']}")
        print(f"*   **Value Intervention (Next 7 Days):** {pb['value_intervention_next_7_days']}")
        print(f"*   **Commercial Safeguard:** {pb['commercial_safeguard']}")
    print('\nReports written to:', out_path)


if __name__ == '__main__':
    main()
