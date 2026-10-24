import json,os,mimetypes
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,unquote
from pathlib import Path
from bosio.core.orchestrator import Orchestrator
WEB=Path(__file__).resolve().parent.parent/"web"
class H(BaseHTTPRequestHandler):
    orch=None
    def _j(self,s,d):
        p=json.dumps(d,ensure_ascii=False).encode(); self.send_response(s)
        self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(p))); self.end_headers(); self.wfile.write(p)
    def _f(self,f):
        if not f.is_file(): return self._j(404,{"error":"No encontrado"})
        p=f.read_bytes(); self.send_response(200)
        self.send_header("Content-Type",mimetypes.guess_type(str(f))[0] or "application/octet-stream")
        self.send_header("Content-Length",str(len(p))); self.end_headers(); self.wfile.write(p)
    def _b(self):
        n=int(self.headers.get("Content-Length",0))
        if not n: return {}
        try: return json.loads(self.rfile.read(n).decode())
        except Exception: raise ValueError("JSON invalido")
    def do_GET(self):
        path=unquote(urlparse(self.path).path)
        if path in ("/","/index.html"): return self._f(WEB/"index.html")
        if path.startswith("/web/"):
            rel=path[5:]
            if ".." in rel: return self._j(404,{"error":"Ruta invalida"})
            return self._f(WEB/rel)
        o=self.orch
        if path=="/health": return self._j(200,{"status":"ok","version":"0.3.0"})
        if path=="/api/projects": return self._j(200,o.list_projects())
        parts=path.strip("/").split("/")
        if len(parts)==3 and parts[:2]==["api","projects"]:
            p=o.get_project(parts[2]); return self._j(200,p) if p else self._j(404,{"error":"No encontrado"})
        if len(parts)==4 and parts[:2]==["api","projects"]:
            pid,res=parts[2],parts[3]
            if not o.get_project(pid): return self._j(404,{"error":"No encontrado"})
            if res=="files": return self._j(200,o.get_files(pid))
            if res=="tasks": return self._j(200,o.get_tasks(pid))
            if res=="export": return self._j(200,o.export_project(pid))
        return self._j(404,{"error":"Ruta no encontrada"})
    def do_POST(self):
        path=urlparse(self.path).path; o=self.orch
        try: b=self._b()
        except ValueError as e: return self._j(400,{"error":str(e)})
        if path=="/api/projects":
            try: return self._j(201,o.create_project(b.get("name",""),b.get("prompt","")))
            except ValueError as e: return self._j(422,{"error":str(e)})
        parts=path.strip("/").split("/")
        if len(parts)==4 and parts[:2]==["api","projects"] and parts[3]=="run":
            try: return self._j(200,o.run_project(parts[2]))
            except KeyError: return self._j(404,{"error":"No encontrado"})
        return self._j(404,{"error":"Ruta no encontrada"})
    def log_message(self,*a): pass
def create_server(host="0.0.0.0",port=None,db_path=None):
    port=port or int(os.getenv("PORT","8000")); db=db_path or os.getenv("DATABASE_PATH","/tmp/bosio.db")
    h=type("BH",(H,),{"orch":Orchestrator(db)}); return ThreadingHTTPServer((host,port),h)
if __name__=="__main__":
    s=create_server(); print("BOSIO corriendo"); s.serve_forever()
