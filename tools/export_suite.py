"""Export baseline requests as a plain benchmark suite + bundle that tools/bind_benchmark_inputs.py can bind.

Usage:
  python -B tools/export_suite.py --out-dir DIR [--key KEY ...] [--phones S24,M31,...] [--mode private_call]
         [--input vsg/coverage-640x480-15/640x480-15fps] [--alias-map S24=myphone,...]

Writes DIR/baseline-suite.json (cases without inputs, IDs "baseline-<key>") and DIR/baseline-bundle.json
(grouped by execution kind and required families). Then, from the app repository root:
  python -B tools/bind_benchmark_inputs.py --suite DIR/baseline-bundle.json --case baseline-<key> \
      --fixtures benchmarks/inputs/<generated>/raw-fixtures.json --devices tools/benchmark_devices.json \
      --output benchmarks/catalog/<new> [--with-reference-audio]
Use --with-reference-audio when the request's audio input is the generator's reference_audio.wav; use the
speech-attached fixtures manifest (tools/build_speech_reference.py attach) when it is speech-v1; omit it when the
baseline audio is "live-mic". Only the standard library is used.
"""
import argparse, csv, json, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOWER = {'S24': 's24', 'S22': 's22', 'M31': 'm31', 'ASUS': 'asus', 'Xiaomi': 'xiaomi', 'A55': 'a55', 'A15s': 'a15s'}


def alias_tree(o, amap):
    if isinstance(o, dict):
        return {amap.get(k, k): alias_tree(v, amap) for k, v in o.items()}
    if isinstance(o, list):
        return [alias_tree(v, amap) for v in o]
    if isinstance(o, str) and o in amap:
        return amap[o]
    return o


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--key', action='append', default=[])
    ap.add_argument('--phones', default='', help='only requests whose phones are all in this list (baseline aliases)')
    ap.add_argument('--mode', default='')
    ap.add_argument('--input', default='')
    ap.add_argument('--alias-map', default='', help='BASELINE_ALIAS=your_alias pairs, comma separated')
    a = ap.parse_args(argv)
    amap = dict(LOWER)
    for pair in filter(None, a.alias_map.split(',')):
        ours, mine = pair.split('=', 1)
        amap[ours.strip()] = mine.strip()
    allowed = set(filter(None, a.phones.split(',')))
    cases, groups = [], {}
    for row in csv.DictReader(open(os.path.join(HERE, 'summary', 'baseline.csv'), encoding='utf-8')):
        if a.key and row['baseline_key'] not in a.key:
            continue
        if a.mode and row['mode'] != a.mode:
            continue
        if a.input and a.input not in row['inputs'].split():
            continue
        doc = json.load(open(os.path.join(HERE, row['latest_file']), encoding='utf-8'))
        phones = {p['alias'] for p in doc['phones']}
        if allowed and not phones <= allowed:
            continue
        req = {k: v for k, v in doc['case']['request'].items() if k != 'inputs'}
        case = alias_tree(req, amap)
        case.update({'id': 'baseline-' + row['baseline_key'], 'state': 'NOT RUN',
                     'eligibility': f"MeshLive baseline request {row['baseline_key']} (inputs: {row['inputs']}; audio: {row['audio']})"})
        cases.append(case)
        fam = tuple(doc['result'].get('required_families') or [])
        execution = doc['execution'].get('concurrency') or 'isolated'
        groups.setdefault((execution, fam), []).append(case['id'])
    os.makedirs(a.out_dir, exist_ok=True)
    suite_path = os.path.join(a.out_dir, 'baseline-suite.json')
    json.dump({'schema_version': 1, 'purpose': 'Requests exported from the MeshLive benchmark baseline', 'cases': cases},
              open(suite_path, 'w', encoding='utf-8'), indent=1)
    json.dump({'schema_version': 1, 'suites': [
        {'path': os.path.abspath(suite_path), 'execution': ex, 'required_families': list(fam), 'case_ids': ids}
        for (ex, fam), ids in sorted(groups.items())]},
        open(os.path.join(a.out_dir, 'baseline-bundle.json'), 'w', encoding='utf-8'), indent=1)
    print(f'{len(cases)} requests exported to {a.out_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
