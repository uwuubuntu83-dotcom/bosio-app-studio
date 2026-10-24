import json
from functools import wraps
from bosio.core.database import connect,init_db,now,new_id,DB_WRITE_LOCK
PIPELINE=[("product","Definir requisitos"),("architecture","Seleccionar arquitectura"),("frontend","Generar aplicacion"),("qa","Validar archivos")]
def locked(m):
    @wraps(m)
    def w(self,*a,**k):
        with DB_WRITE_LOCK: return m(self,*a,**k)
    return w
class Orchestrator:
    def __init__(self,db_path=None):
        self.conn=connect(db_path); init_db(self.conn)
    @locked
    def create_project(self,name,prompt):
        if not name.strip() or not prompt.strip(): raise ValueError("Nombre y prompt obligatorios")
        pid,ts=new_id(),now()
        self.conn.execute("INSERT INTO projects VALUES(?,?,?,?,?,?)",(pid,name.strip(),prompt.strip(),"planning",ts,ts))
        for team,title in PIPELINE: self.conn.execute("INSERT INTO tasks(id,project_id,team,title,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",(new_id(),pid,team,title,"pending",ts,ts))
        self.conn.execute("INSERT INTO cost_records(id,project_id,provider,model,amount,kind,created_at) VALUES(?,?,?,?,?,?,?)",(new_id(),pid,"local","template",0.0,"actual",ts))
        self.conn.commit(); return self.get_project(pid)
    @locked
    def get_project(self,pid):
        r=self.conn.execute("SELECT * FROM projects WHERE id=?",(pid,)).fetchone(); return dict(r) if r else None
    @locked
    def list_projects(self): return [dict(r) for r in self.conn.execute("SELECT * FROM projects ORDER BY created_at DESC")]
    @locked
    def get_tasks(self,pid): return [dict(r) for r in self.conn.execute("SELECT * FROM tasks WHERE project_id=? ORDER BY created_at",(pid,))]
    @locked
    def get_files(self,pid): return [dict(r) for r in self.conn.execute("SELECT * FROM project_files WHERE project_id=? ORDER BY path",(pid,))]
    @locked
    def run_project(self,pid,max_attempts=3):
        p=self.get_project(pid)
        if not p: raise KeyError("Proyecto no encontrado")
        g=None
        for t in self.get_tasks(pid):
            if t["status"]=="passed": continue
            self._u(t["id"],status="running",error=None); a=t["attempts"]+1
            try:
                if t["team"]=="product": r={"ok":True}
                elif t["team"]=="architecture": r={"stack":"HTML estatico"}
                elif t["team"]=="frontend": g=self._s(pid,p["prompt"]); r={"files":sorted(g)}
                elif t["team"]=="qa":
                    fs=g or {f["path"]:f["content"] for f in self.get_files(pid)}
                    errs=self._v(fs)
                    if errs: raise ValueError("; ".join(errs))
                    r={"status":"PASS"}
                else: raise ValueError("Equipo desconocido")
                self._u(t["id"],status="passed",attempts=a,result=json.dumps(r,ensure_ascii=False))
            except Exception as e:
                self._u(t["id"],status="failed" if a>=max_attempts else "pending",attempts=a,error=str(e))
        f=any(x["status"]=="failed" for x in self.get_tasks(pid))
        st="failed" if f else "completed"
        self.conn.execute("UPDATE projects SET status=?,updated_at=? WHERE id=?",(st,now(),pid)); self.conn.commit()
        return self.get_project(pid)
    @locked
    def _s(self,pid,prompt):
        from bosio.core.generator import generate_app
        g=generate_app(prompt)
        for path,content in g.items():
            e=self.conn.execute("SELECT id FROM project_files WHERE project_id=? AND path=?",(pid,path)).fetchone()
            if e: self.conn.execute("UPDATE project_files SET content=?,version=version+1 WHERE id=?",(content,e["id"]))
            else: self.conn.execute("INSERT INTO project_files VALUES(?,?,?,?,1)",(new_id(),pid,path,content))
        self.conn.commit(); return g
    @staticmethod
    def _v(fs):
        from bosio.core.generator import validate_generated_files
        return validate_generated_files(fs)
    @locked
    def _u(self,tid,**f):
        f["updated_at"]=now()
        self.conn.execute(f"UPDATE tasks SET {', '.join(k+'=?' for k in f)} WHERE id=?",list(f.values())+[tid]); self.conn.commit()
    @locked
    def export_project(self,pid):
        p=self.get_project(pid)
        if not p: raise KeyError("Proyecto no encontrado")
        return {"project":p,"files":self.get_files(pid),"tasks":self.get_tasks(pid)}
