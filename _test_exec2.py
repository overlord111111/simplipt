import urllib.request, re

# Reload: create test file, then execute
body = urllib.request.urlopen('http://localhost:8080/_admin/executar/teste_exec.spt').read().decode()
m = re.search(r'class="saida">(.+?)</pre>', body, re.DOTALL)
saida = m.group(1).strip() if m else 'NOT FOUND'
print('SAIDA:', repr(saida))
