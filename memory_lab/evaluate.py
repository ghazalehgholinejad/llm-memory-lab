"""Reproducible synthetic evidence evaluation; no model inference."""
import argparse
import json
from .core import select

METHODS = ('recent', 'compact', 'retrieve', 'hybrid')
MESSAGES = [
    {'id': 1, 'role': 'user', 'text': 'The deployment database was PostgreSQL.'},
    {'id': 2, 'role': 'user', 'text': 'Write the tutorial in Persian.'},
    {'id': 3, 'role': 'assistant', 'text': 'The dashboard draft uses blue colors.'},
    {'id': 4, 'role': 'user', 'text': 'Database planning notes: ' + 'We discussed the local prototype. ' * 5 + 'Correction: use SQLite.'},
    {'id': 5, 'role': 'user', 'text': 'The evaluation deadline is Friday.'},
    {'id': 6, 'role': 'assistant', 'text': 'Next we will review the README.'},
]
CASES = [
    {'id': 'database-correction', 'query': 'Which database now?', 'expected': {4: 'Correction: use SQLite.'}},
    {'id': 'tutorial-language', 'query': 'tutorial language', 'expected': {2: 'Persian'}},
    {'id': 'deadline', 'query': 'evaluation deadline', 'expected': {5: 'Friday'}},
    {'id': 'paraphrase', 'query': 'When must we finish?', 'expected': {5: 'Friday'}},
    {'id': 'two-decisions', 'query': 'database tutorial', 'expected': {2: 'Persian', 4: 'Correction: use SQLite.'}},
]


def score(evidence, expected):
    """Expected maps source IDs to exact required excerpts.

    Source recall alone can credit a truncated message missing the actual fact;
    excerpt recall checks whether the expected text survived too.
    """
    if not expected or any(type(k) is not int or not isinstance(v, str) or not v for k, v in expected.items()):
        raise ValueError('Expected evidence needs integer IDs and nonempty excerpts')
    selected = {m['source_id']: m['text'] for m in evidence}
    found = sorted(set(expected) & set(selected))
    retained = [key for key in found if expected[key] in selected[key]]
    return {'source_recall': len(found)/len(expected),
            'excerpt_recall': len(retained)/len(expected),
            'source_precision': len(found)/len(selected) if selected else 0.0,
            'missing_source_ids': sorted(set(expected) - set(found)),
            'missing_excerpt_ids': sorted(set(expected) - set(retained))}


def benchmark(budget=450, limit=6):
    rows, summaries = [], []
    for method in METHODS:
        results = []
        for case in CASES:
            selected = select(MESSAGES, case['query'], method, budget, limit)
            metrics = score(selected['evidence'], case['expected'])
            row = {'case_id': case['id'], 'query': case['query'], 'method': method,
                   'selected_ids': [m['source_id'] for m in selected['evidence']],
                   'characters': selected['characters'], **metrics}
            rows.append(row)
            results.append(row)
        summaries.append({'method': method, **{key: sum(r[key] for r in results)/len(results)
            for key in ('source_recall', 'excerpt_recall', 'source_precision', 'characters')}})
    return {'synthetic': True, 'model_called': False, 'dataset_version': 1,
            'budget_characters': budget, 'message_limit': limit,
            'case_count': len(CASES), 'aggregation': 'macro mean over cases',
            'summary': summaries, 'cases': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--budget', type=int, default=450)
    parser.add_argument('--limit', type=int, default=6)
    parser.add_argument('--output', help='New JSON report file; refuses overwrite')
    args = parser.parse_args()
    report = benchmark(args.budget, args.limit)
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        with open(args.output, 'x', encoding='utf-8') as stream:
            stream.write(encoded)
    else:
        print(encoded, end='')


if __name__ == '__main__':
    main()
