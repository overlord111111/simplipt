import urllib.request, re
import sys

files = ['teste_exec.spt', 'admin/dashboard.spt']
for f in files:
    url = f'http://localhost:8080/_admin/executar/{f}'
    body = urllib.request.urlopen(url).read().decode()
    m = re.search(r'class="saida">(.+?)</pre>', body, re.DOTALL)
    saida = m.group(1).strip() if m else 'NOT FOUND'
    print(f'=== {f} ===')
    print(saida)
    print()
