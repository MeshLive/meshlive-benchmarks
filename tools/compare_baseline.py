"""Compare your benchmark suite results with the MeshLive baseline, request by request.

Usage:
  python -B tools/compare_baseline.py --suite-result PATH/suite-result.json [--suite-result ...]
         [--alias-map mine=S24,other=M31] [--csv out.csv]

Each result in a suite-result.json written by tools/run_benchmark_suite.py is turned into a portable request
(the semantic request with local file paths replaced by input SHA-256 values and phone aliases upper-cased),
hashed into a baseline_key, and joined with summary/baseline.csv. Only standard library modules are used.
"""
import argparse, csv, hashlib, json, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIAS = {'s24': 'S24', 's22': 'S22', 'm31': 'M31', 'asus': 'ASUS', 'xiaomi': 'Xiaomi', 'a55': 'A55', 'a15s': 'A15s'}
REQ_DROP = {'id', 'state', 'eligibility', 'environment', 'note', 'expected_apk_sha256', 'raw_fixture_file',
            'raw_fixture_files', 'raw_fixture_sha256', 'raw_fixture_sha256s', 'raw_fixture_metadata',
            'raw_fixture_metadatas', 'reference_audio', 'reference_audios', 'fixture_provenance'}
DROP_KEYS = {'evidence', 'evidence_directory', 'analysis_directory', 'manifest', 'path', 'paths', 'serial',
             'node_prefix', 'battery_at_start', 'thermal_at_start', 'call_id', 'callId', 'sidecars', 'scope',
             'sha256', 'file', 'files', 'log', 'logs', 'directory', 'output'}


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items() if k not in DROP_KEYS}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, float):
        return round(o, 4)
    return o


def alias_tree(o, amap):
    if isinstance(o, dict):
        return {amap.get(k, k): alias_tree(v, amap) for k, v in o.items()}
    if isinstance(o, list):
        return [alias_tree(v, amap) for v in o]
    if isinstance(o, str) and o in amap:
        return amap[o]
    return o


def portable_request(sc, amap):
    vids, auds = {}, {}
    if sc.get('raw_fixture_sha256'):
        vids[sc.get('source')] = sc['raw_fixture_sha256']
    vids.update(sc.get('raw_fixture_sha256s') or {})
    if isinstance(sc.get('reference_audio'), dict):
        auds[sc.get('source')] = sc['reference_audio'].get('sha256')
    for ph, a in (sc.get('reference_audios') or {}).items():
        auds[ph] = a.get('sha256')
    if not vids:
        return None  # live Camera2 input: not comparable with this baseline
    req = alias_tree(clean({k: v for k, v in sc.items() if k not in REQ_DROP}), amap)
    req['inputs'] = {amap.get(ph, ph): {'video_sha256': vids[ph], 'audio_sha256': auds.get(ph)}
                     for ph in sorted(vids, key=lambda p: amap.get(p, p))}
    req['inputs'] = dict(sorted(req['inputs'].items()))
    return req


def baseline_key(req):
    return hashlib.sha256(json.dumps(req, sort_keys=True, separators=(',', ':')).encode()).hexdigest()[:20]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--suite-result', action='append', required=True)
    ap.add_argument('--alias-map', default='', help='your_alias=BASELINE_ALIAS pairs, comma separated')
    ap.add_argument('--baseline', default=os.path.join(HERE, 'summary', 'baseline.csv'))
    ap.add_argument('--csv')
    a = ap.parse_args(argv)
    amap = dict(ALIAS)
    for pair in filter(None, a.alias_map.split(',')):
        mine, ours = pair.split('=', 1)
        amap[mine.strip()] = ours.strip()
    base = {r['baseline_key']: r for r in csv.DictReader(open(a.baseline, encoding='utf-8'))}
    out = []
    for path in a.suite_result:
        doc = json.load(open(path, encoding='utf-8'))
        for r in doc.get('results', []):
            req = portable_request(r.get('scenario') or {}, amap)
            if req is None:
                continue
            k = baseline_key(req)
            b = base.get(k)
            fams = {n: f.get('status') for n, f in (r.get('families') or {}).items() if isinstance(f, dict)}
            out.append({'baseline_key': k, 'your_status': r.get('status'),
                        'your_failed_families': ' '.join(n for n, s in fams.items() if s == 'FAIL'),
                        'baseline_status': b['latest_status'] if b else 'NO BASELINE',
                        'baseline_failed_families': b['failed_families'] if b else '',
                        'baseline_build': b['latest_build_id'] if b else '',
                        'baseline_history': b['history'] if b else '',
                        'baseline_file': b['latest_file'] if b else '', 'your_case_id': r.get('case_id')})
    w = csv.DictWriter(open(a.csv, 'w', newline='', encoding='utf-8') if a.csv else sys.stdout,
                       fieldnames=list(out[0].keys()) if out else ['baseline_key'])
    w.writeheader(); w.writerows(out)
    matched = sum(1 for o in out if o['baseline_status'] != 'NO BASELINE')
    print(f'{len(out)} comparable results, {matched} with a baseline entry', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
