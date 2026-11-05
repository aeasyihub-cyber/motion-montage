#!/usr/bin/env python3
"""Within each pause-delimited phrase, spread words by letter count (TTS speaks at a steady rate).
python3 phrase_even.py in.json out.json"""
import json, re, sys
d=json.load(open(sys.argv[1],encoding='utf-8')); W=d['words']
letters=lambda w: len(re.sub(r'[ً-ْـ\W_]','',w))
# phrase boundary where gap between consecutive words >= 0.12s
groups=[[0]]
for i in range(1,len(W)):
    if W[i]['s']-W[i-1]['e']>=0.12: groups.append([i])
    else: groups[-1].append(i)
for g in groups:
    s,e=W[g[0]]['s'],W[g[-1]]['e']
    wts=[letters(W[i]['w'])+1.5 for i in g]; tot=sum(wts); t=s
    for i,wt in zip(g,wts):
        dur=(e-s)*wt/tot
        W[i]['s'],W[i]['e']=round(t,3),round(t+dur,3); t+=dur
d['backend']+='+phrase-even'
json.dump(d,open(sys.argv[2],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(len(groups),'phrases')
