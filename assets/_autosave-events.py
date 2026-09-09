import json,time
rows=[json.loads(l) for l in open('/Users/sovthpaw/.hermes/senter-bridge/events.jsonl') if 'Senter Wiki edit' in l]
the operator=[r for r in rows if r.get('bot')=='the operator']
print(len(the operator),'the operator edit posts; last at', time.strftime('%H:%M:%S',time.localtime(the operator[-1]['ts'])), 'now', time.strftime('%H:%M:%S'))
for r in the operator[-6:]: print(time.strftime('%H:%M:%S',time.localtime(r['ts'])), r['summary'][:70])
