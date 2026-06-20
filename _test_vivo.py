import urllib.request, re, time, os

os.chdir(r'C:\Users\Master\Documents\Projetos\ia jarbs\projetos\simplipt')

# Create test file
with open('testar_vivo.spt', 'w') as f:
    f.write('falar "vivo e funcionando!"\n')

time.sleep(1)

try:
    body = urllib.request.urlopen('http://localhost:8080/_admin/executar/testar_vivo.spt').read().decode()
    m = re.search(r'class="saida">(.+?)</pre>', body, re.DOTALL)
    saida = m.group(1).strip() if m else 'MATCH FAILED'
    print('RESULT:', repr(saida))
except Exception as e:
    print('ERRO:', e)
