import argparse
import json
import tempfile
from pathlib import Path
from .core import History, select, build_prompt


def main():
    parser = argparse.ArgumentParser(description='Compare offline conversation-memory strategies on synthetic history')
    parser.add_argument('--budget', type=int, default=650, help='Evidence JSON character budget, not tokens')
    parser.add_argument('--query', default='What database did we choose for deployment?')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        store = History(Path(directory) / 'demo.sqlite3')
        dialogue = [
            ('user', 'For deployment we chose PostgreSQL as the database.'),
            ('assistant', 'I will document the database decision.'),
            ('user', 'The dashboard should use a blue theme.'),
            ('assistant', 'The dashboard draft has a blue theme.'),
            ('user', 'For deployment we changed the database decision to SQLite for the local demo.'),
            ('assistant', 'The next task is writing a README.'),
            ('user', 'Please write the tutorial in Persian.'),
            ('assistant', 'We can explain the code step by step.'),
        ]
        for role, text in dialogue:
            store.append('demo', role, text)
        store.append('other-session', 'user', 'This unrelated conversation must never be included.')
        output = {'synthetic': True, 'model_called': False, 'query': args.query, 'comparisons': []}
        for method in ('recent', 'compact', 'retrieve', 'hybrid'):
            selection = select(store.messages('demo'), args.query, method, args.budget)
            selection['prompt'] = build_prompt(args.query, selection)
            output['comparisons'].append(selection)
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
