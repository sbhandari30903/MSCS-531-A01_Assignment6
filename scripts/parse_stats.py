#!/usr/bin/env python3
import re, sys, os, csv, glob

RUNS = sys.argv[1] if len(sys.argv) > 1 else '../runs'

re_ipc = re.compile(r'system\.cpu(\d+)\.ipc\s+(\S+)')
re_cpi = re.compile(r'system\.cpu(\d+)\.cpi\s+(\S+)')
re_ticks = re.compile(r'simTicks\s+(\d+)')

rows = []
by_tag = {}

for stats_file in glob.glob(os.path.join(RUNS, '*', 'stats.txt')):
    tag = stats_file.split(os.sep)[-2]
    with open(stats_file) as f:
        text = f.read()

    ipcs = {int(i): float(v) for i, v in re_ipc.findall(text)}
    cpis = {int(i): float(v) for i, v in re_cpi.findall(text)}
    m = re_ticks.search(text)
    ticks = int(m.group(1)) if m else None

    # tag format: op{opl}_iss{iss}_T{t}
    import re as _re
    m2 = _re.match(r'op(\d+)_iss(\d+)_T(\d+)', tag)
    opl, iss, t = map(int, m2.groups())

    avg_ipc = sum(ipcs.values()) / len(ipcs) if ipcs else 0.0
    avg_cpi = sum(cpis.values()) / len(cpis) if cpis else 0.0

    row = dict(tag=tag, opLat=opl, issueLat=iss, threads=t, ticks=ticks,
               avgIPC=avg_ipc, avgCPI=avg_cpi)
    rows.append(row)
    by_tag[tag] = row

# Speedup vs T=1 (per (opLat, issueLat))
for r in rows:
    base_tag = f"op{r['opLat']}_iss{r['issueLat']}_T1"
    base = by_tag.get(base_tag)
    if base and base['ticks'] and r['ticks']:
        r['speedup_vs_T1'] = base['ticks'] / r['ticks']
    else:
        r['speedup_vs_T1'] = ''

out_csv = os.path.join(RUNS, 'summary.csv')
with open(out_csv, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=[
        'tag','opLat','issueLat','threads','ticks','avgIPC','avgCPI','speedup_vs_T1'
    ])
    w.writeheader()
    for r in sorted(rows, key=lambda x:(x['opLat'], x['issueLat'], x['threads'])):
        w.writerow(r)

print(f"Wrote {out_csv}")

