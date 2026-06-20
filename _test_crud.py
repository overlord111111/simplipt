import urllib.request, urllib.parse, time

base = "http://localhost:8080"

# Test create
data = urllib.parse.urlencode({"nome": "teste_crud"}).encode()
r = urllib.request.urlopen(base + "/_admin/criar", data)
print("CREATE:", r.status)
time.sleep(0.5)

# Test editor
r2 = urllib.request.urlopen(base + "/_admin/editar/teste_crud.spt")
print("EDITOR:", r2.status)
body = r2.read().decode()
if 'Ola, mundo' in body:
    print("EDITOR CONTENT: OK")

# Test save new code
data2 = urllib.parse.urlencode({"codigo": 'falar "crud funcionando!"\n'}).encode()
r3 = urllib.request.urlopen(base + "/_admin/salvar/teste_crud.spt", data2)
print("SAVE:", r3.status)

# Test execute
r4 = urllib.request.urlopen(base + "/_admin/executar/teste_crud.spt")
import re
body4 = r4.read().decode()
m = re.search(r'class=.saida.>(.+?)</pre>', body4, re.DOTALL)
if m:
    print("EXECUTE:", m.group(1).strip())
