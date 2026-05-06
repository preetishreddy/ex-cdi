"""
Decision Conflict Detection

Scans all active decisions for pairs that contradict each other using a
two-stage pipeline:

  Stage 1 — Cosine pre-filter (MiniLM embeddings)
      Only pairs with cosine similarity > 0.25 (related topic area) are
      sent to the LLM. This reduces ~946 possible pairs to ~50-100 calls.

  Stage 2 — LLM conflict judgement (Groq / Llama 70B)
      The LLM receives both decisions with title + description + rationale
      and returns structured JSON: {conflicts, type, explanation, severity}.

Conflicts are stored in the `decision_conflicts` table (idempotent — existing
pairs are skipped unless --force is used).

Usage:
    python scripts/check_conflicts.py              # detect and save
    python scripts/check_conflicts.py --dry-run    # detect, print, don't save
    python scripts/check_conflicts.py --report     # print saved conflicts
    python scripts/check_conflicts.py --force      # re-check all pairs
    python scripts/check_conflicts.py --min-sim 0.3  # tighter pre-filter
"""

import os
import sys
import json
import argparse
import itertools
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from knowledge_base.models import Decision, DecisionConflict

# ── LLM setup ──────────────────────────────────────────────────────────────

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL   = 'llama-3.3-70b-versatile'

_client: Optional[OpenAI] = None

def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=GROQ_API_KEY, base_url='https://api.groq.com/openai/v1')
    return _client


# ── Embedding setup (reuse MiniLM from Change 1) ──────────────────────────

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

_embed_model = None
_embed_cache: dict = {}

def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        print('  Loading embedding model (all-MiniLM-L6-v2)...')
        _embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        print('  Embedding model ready')
    return _embed_model

def _embed(text: str):
    if text in _embed_cache:
        return _embed_cache[text]
    vec = _get_embed_model().encode(text, normalize_embeddings=True)
    _embed_cache[text] = vec
    return vec

def cosine_sim(a: str, b: str) -> float:
    if not EMBEDDINGS_AVAILABLE:
        return 1.0  # if no embeddings, pass everything to LLM
    return float(np.dot(_embed(a), _embed(b)))


# ── LLM conflict judgement ─────────────────────────────────────────────────

CONFLICT_PROMPT = """You are an expert software architect reviewing two architectural decisions for a software project.

Decision A:
  Title: {title_a}
  Description: {desc_a}
  Rationale: {rationale_a}
  Category: {category_a}
  Tags: {tags_a}

Decision B:
  Title: {title_b}
  Description: {desc_b}
  Rationale: {rationale_b}
  Category: {category_b}
  Tags: {tags_b}

Do these two decisions conflict with each other? A conflict means they cannot both be fully implemented simultaneously, or that choosing both creates ambiguity, duplication of responsibility, or contradictory constraints.

Reply ONLY with a JSON object in this exact format:
{{
  "conflicts": true or false,
  "conflict_type": "direct" | "indirect" | "potential",
  "explanation": "one or two sentences explaining the conflict, or null if no conflict",
  "severity": "low" | "medium" | "high"
}}

Definitions:
- direct: mutually exclusive — implementing both is impossible or clearly wrong
- indirect: both can coexist but create architectural tension or confusion
- potential: uncertain; human review recommended
- severity high: blocks the team or causes production risk
- severity medium: causes confusion or technical debt
- severity low: minor overlap, worth noting
"""

def _decision_summary(d: Decision) -> dict:
    return {
        'title':     d.title,
        'desc':      (d.description or '')[:300],
        'rationale': (d.rationale or '')[:300],
        'category':  d.category or 'unknown',
        'tags':      ', '.join(d.tags or []) or 'none',
    }

def llm_check_conflict(a: Decision, b: Decision, model: str = GROQ_MODEL) -> Optional[dict]:
    sa = _decision_summary(a)
    sb = _decision_summary(b)
    prompt = CONFLICT_PROMPT.format(
        title_a=sa['title'],    desc_a=sa['desc'],      rationale_a=sa['rationale'],
        category_a=sa['category'], tags_a=sa['tags'],
        title_b=sb['title'],    desc_b=sb['desc'],      rationale_b=sb['rationale'],
        category_b=sb['category'], tags_b=sb['tags'],
    )
    try:
        resp = get_client().chat.completions.create(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.0,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        print(f'    LLM error: {e}')
        return None


# ── Database operations ────────────────────────────────────────────────────

def save_conflict(a: Decision, b: Decision, result: dict, dry_run: bool) -> bool:
    # Normalise pair order so (a,b) and (b,a) map to the same row
    id_a, id_b = sorted([str(a.id), str(b.id)])
    from knowledge_base.models import Decision as D
    da = D.objects.get(id=id_a)
    db_ = D.objects.get(id=id_b)

    if dry_run:
        return True

    _, created = DecisionConflict.objects.get_or_create(
        decision_a=da,
        decision_b=db_,
        defaults={
            'conflict_type': result.get('conflict_type', 'potential'),
            'explanation':   result.get('explanation'),
            'severity':      result.get('severity', 'low'),
        }
    )
    return created


def existing_pair(a: Decision, b: Decision) -> bool:
    id_a, id_b = sorted([str(a.id), str(b.id)])
    return DecisionConflict.objects.filter(
        decision_a_id=id_a, decision_b_id=id_b
    ).exists() or DecisionConflict.objects.filter(
        decision_a_id=id_b, decision_b_id=id_a
    ).exists()


# ── Report ─────────────────────────────────────────────────────────────────

SEV_COLOUR = {'high': '!!', 'medium': '~ ', 'low': '  '}

def print_report():
    conflicts = DecisionConflict.objects.select_related('decision_a', 'decision_b').order_by(
        '-severity', 'decision_a__title'
    )
    if not conflicts.exists():
        print('  No conflicts recorded.')
        return

    by_severity = {'high': [], 'medium': [], 'low': []}
    for c in conflicts:
        by_severity[c.severity].append(c)

    for sev in ('high', 'medium', 'low'):
        group = by_severity[sev]
        if not group:
            continue
        label = sev.upper()
        print(f'\n  ── {label} ──')
        for c in group:
            print(f"  [{SEV_COLOUR[sev]}]  {c.decision_a.title[:45]!r}")
            print(f"          ↔  {c.decision_b.title[:45]!r}")
            print(f"             type: {c.conflict_type}")
            if c.explanation:
                print(f"             {c.explanation[:120]}")
            print()

    print(f"  Total: {conflicts.count()}  "
          f"(high: {len(by_severity['high'])}, "
          f"medium: {len(by_severity['medium'])}, "
          f"low: {len(by_severity['low'])})")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Detect conflicts between active decisions')
    parser.add_argument('--dry-run',  action='store_true', help='Detect but do not save')
    parser.add_argument('--report',   action='store_true', help='Print saved conflicts and exit')
    parser.add_argument('--force',    action='store_true', help='Re-check already-seen pairs')
    parser.add_argument('--min-sim',  type=float, default=0.25,
                        help='Minimum cosine similarity to pass to LLM (default: 0.25)')
    parser.add_argument('--model',    type=str,   default=GROQ_MODEL, help='Groq model name')
    args = parser.parse_args()

    print('=' * 62)
    print('Decision Conflict Detector')
    print('=' * 62)

    if args.report:
        print()
        print_report()
        return

    decisions = list(Decision.objects.filter(status='active'))
    print(f'\nActive decisions loaded: {len(decisions)}')

    if not EMBEDDINGS_AVAILABLE:
        print('  WARNING: sentence-transformers not installed — all pairs sent to LLM')
    else:
        # Pre-warm embeddings
        print('  Pre-warming embeddings...')
        for d in decisions:
            _embed(d.title)
        print(f'  {len(_embed_cache)} titles embedded')

    pairs = list(itertools.combinations(decisions, 2))
    print(f'  Total pairs: {len(pairs)}')

    # Stage 1: cosine pre-filter
    candidate_pairs = []
    for a, b in pairs:
        sim = cosine_sim(a.title, b.title)
        if sim >= args.min_sim:
            candidate_pairs.append((a, b, sim))

    print(f'  Pairs above similarity threshold ({args.min_sim}): {len(candidate_pairs)}')

    # Skip already-checked pairs unless --force
    if not args.force:
        candidate_pairs = [(a, b, s) for a, b, s in candidate_pairs if not existing_pair(a, b)]
        print(f'  New pairs to check: {len(candidate_pairs)}')

    print()
    print('-' * 62)

    found = 0
    skipped = 0
    errors = 0

    for i, (a, b, sim) in enumerate(candidate_pairs, 1):
        print(f'  [{i}/{len(candidate_pairs)}] sim={sim:.3f}')
        print(f'    A: {a.title[:55]}')
        print(f'    B: {b.title[:55]}')

        result = llm_check_conflict(a, b, model=args.model)

        if result is None:
            errors += 1
            print('    → error (skipped)')
            continue

        if result.get('conflicts'):
            sev  = result.get('severity', 'low')
            ctype = result.get('conflict_type', 'potential')
            expl  = (result.get('explanation') or '')[:100]
            print(f'    → CONFLICT [{sev.upper()}] {ctype}: {expl}')
            if not args.dry_run:
                save_conflict(a, b, result, dry_run=False)
            found += 1
        else:
            print('    → no conflict')
            skipped += 1

    print()
    print('=' * 62)
    print('COMPLETE')
    print('=' * 62)
    print(f'  Pairs checked : {len(candidate_pairs)}')
    print(f'  Conflicts found: {found}')
    print(f'  No conflict   : {skipped}')
    print(f'  Errors        : {errors}')

    if found and not args.dry_run:
        print()
        print('Saved conflicts:')
        print_report()


if __name__ == '__main__':
    main()
