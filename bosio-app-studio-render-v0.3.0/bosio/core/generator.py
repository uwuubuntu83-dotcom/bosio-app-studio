HTML="""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>__TITLE__</title><style>body{font-family:system-ui;margin:0;background:#f6f7fb;color:#172033}header{background:#172033;color:#fff;padding:2rem}main{max-width:900px;margin:2rem auto;padding:0 1rem}.card{background:#fff;border-radius:12px;padding:1.5rem;box-shadow:0 2px 10px #0001}button{background:#2563eb;color:#fff;border:0;padding:.7rem 1rem;border-radius:8px;cursor:pointer}</style></head><body><header><h1>__TITLE__</h1><p>Generada por BOSIO APP STUDIO ULTIMATE</p></header><main><section class="card"><h2>Solicitud original</h2><p>__PROMPT__</p><button onclick="alert('Aplicacion generada correctamente')">Probar accion</button></section></main></body></html>"""
def generate_app(prompt):
    t=(prompt.strip().splitlines() or ["Aplicacion BOSIO"])[0][:80] or "Aplicacion BOSIO"
    return {"index.html":HTML.replace("__TITLE__",t).replace("__PROMPT__",prompt),"README.md":"# "+t+"\n\nAplicacion generada por BOSIO.\n"}
def validate_generated_files(fs):
    e=[]
    if "index.html" not in fs: e.append("Falta index.html")
    if "index.html" in fs and "<html" not in fs["index.html"].lower(): e.append("HTML invalido")
    return e
