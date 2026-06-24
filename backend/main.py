from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile, os, json
from analyzer import analyze_document

app = FastAPI(title="DocuFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "service": "DocuFlow API"}

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    doc_type: str = Form(default="sarlaft"),
    organization: str = Form(default=""),
    reviewer: str = Form(default="")
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Solo se aceptan archivos PDF")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        result = analyze_document(tmp_path, doc_type)
        result["documento"] = file.filename
        result["organizacion"] = organization
        result["revisor_asignado"] = reviewer
        return JSONResponse(result)
    except json.JSONDecodeError:
        raise HTTPException(500, "Error procesando respuesta del motor IA")
    except Exception as e:
        raise HTTPException(500, f"Error en análisis: {str(e)}")
    finally:
        os.unlink(tmp_path)

@app.post("/review/{hallazgo_id}")
async def update_review(
    hallazgo_id: str,
    estado: str = Form(...),
    comentario: str = Form(default=""),
    revisor: str = Form(default="")
):
    return {
        "hallazgo_id": hallazgo_id,
        "estado_revision": estado,
        "comentario": comentario,
        "revisor": revisor,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }
