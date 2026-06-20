import urllib.request, re, time, os

os.chdir(r'C:\Users\Master\Documents\Projetos\ia jarbs\projetos\simplipt')

# Create test file
with open('testar_exec.spt', 'w') as f:
    f.write('falar "hello from script"\n')

time.sleep(1)

body = urllib.request.urlopen('http://localhost:8080/_admin/executar/testar_exec.spt').read().decode()
m = re.search(r'class="saida">(.+?)</pre>', body, re.DOTALL)
saida = m.group(1).strip() if m else 'NOT FOUND'
print('RESULT:', repr(saida))
