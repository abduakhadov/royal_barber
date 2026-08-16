import json

log_file = r'c:\Users\User\.gemini\antigravity-ide\brain\8e99092f-f878-48c6-aaad-81cd19038801\.system_generated\logs\transcript_full.jsonl'
out = ''

with open(log_file, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            d = json.loads(line)
            if 'tool_calls' in d:
                for t in d['tool_calls']:
                    if t['name'] == 'write_to_file' and 'booking_app.html' in t['args'].get('TargetFile', ''):
                        out = t['args'].get('CodeContent', '')
                        break
        except:
            pass
        if out: 
            break

if out:
    with open('booking_app.html.backup', 'w', encoding='utf-8') as f:
        f.write(out)
    print('Recovered successfully.')
else:
    print('Could not find the original booking_app.html in logs.')
