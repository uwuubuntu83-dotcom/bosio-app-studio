import json,tempfile,threading,urllib.request
from bosio.core.orchestrator import Orchestrator
from bosio.server import create_server
def test_lifecycle(tmp_path):
    o=Orchestrator(str(tmp_path/"t.db")); p=o.create_project("Test","App de gestion")
    assert o.run_project(p["id"])["status"]=="completed"
    assert {"index.html","README.md"}<={f["path"] for f in o.get_files(p["id"])}
def test_http(tmp_path):
    s=create_server(port=0,db_path=str(tmp_path/"a.db")); port=s.server_address[1]
    threading.Thread(target=s.serve_forever,daemon=True).start(); b=f"http://127.0.0.1:{port}"
    try:
        with urllib.request.urlopen(b+"/") as r: assert b"BOSIO" in r.read()
        q=urllib.request.Request(b+"/api/projects",data=json.dumps({"name":"X","prompt":"App inspecciones"}).encode(),headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(q) as r: p=json.load(r)
        q=urllib.request.Request(b+f"/api/projects/{p['id']}/run",data=b"",method="POST")
        with urllib.request.urlopen(q) as r: assert json.load(r)["status"]=="completed"
    finally: s.shutdown(); s.server_close()
