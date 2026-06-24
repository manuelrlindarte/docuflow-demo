import anthropic
import pdfplumber
import yaml
import json
import os
from pathlib import Path
from datetime import datetime

def load_rules(doc_type: str = "sarlaft") -> list:
    rules_path = Path(__file__).parent / "rulesets" / "golden_rules_sarlaft.yml"
    with open(rules_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [r for r in data["rules"] if doc_type in r.get("document_types", [])]

def extract_text(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def build_prompt(doc_text: str, rules: list) -> str:
    rules_block = ""
    for rule in rules:
        rules_block += f"""
REGLA {rule['id']} — {rule['name']} [Severidad: {rule['severity']}]
Criterio: {rule['description']}
---"""

    return f"""Eres el motor de análisis documental de DocuFlow.
Evalúas documentos regulatorios colombianos bajo criterios SARLAFT/SAGRILAFT
(Circular Básica Jurídica SFC, Capítulo XI).

CRITERIOS DE EVALUACIÓN:
{rules_block}

DOCUMENTO A ANALIZAR:
{doc_text[:12000]}

INSTRUCCIONES:
Para cada criterio evalúa si el documento cumple, cumple parcialmente, o incumple.
Usa juicio semántico — no busques palabras exactas sino conceptos.
Para cada hallazgo cita el texto exacto del documento que justifica tu evaluación.

Responde ÚNICAMENTE con este JSON, sin texto adicional:
{{
  "score_confianza": <número 0-100>,
  "nivel_riesgo": "<CRÍTICO|ALTO|MEDIO|BAJO>",
  "resumen_ejecutivo": "<2-3 oraciones para el comité directivo>",
  "hallazgos": [
    {{
      "regla_id": "<ID de la regla>",
      "regla_nombre": "<nombre>",
      "severidad": "<CRITICA|ALTA|MEDIA>",
      "estado": "<INCUMPLE|PARCIAL|CUMPLE>",
      "descripcion": "<qué falta o qué está mal>",
      "evidencia_documento": "<texto exacto del documento>",
      "recomendacion": "<acción concreta para corregir>"
    }}
  ],
  "estadisticas": {{
    "total_reglas": <n>,
    "cumple": <n>,
    "parcial": <n>,
    "incumple": <n>
  }}
}}"""

def analyze_document(pdf_path: str, doc_type: str = "sarlaft") -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no encontrada en variables de entorno")
    
    client = anthropic.Anthropic(api_key=api_key)
    rules = load_rules(doc_type)
    doc_text = extract_text(pdf_path)
    prompt = build_prompt(doc_text, rules)
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = message.content[0].text
    clean = response_text.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1].replace("json","").strip()
    result = json.loads(clean)
    
    result["metadata"] = {
        "doc_type": doc_type,
        "fecha_analisis": datetime.utcnow().isoformat(),
        "reglas_aplicadas": len(rules),
        "motor_ia": "claude-sonnet-4-6",
        "version_ruleset": "1.0"
    }
    
    return result
