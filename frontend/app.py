# frontend/app.py

import io
import json
import base64
import requests
import pandas as pd
import streamlit as st

# -------------------------------------------------------------------
# CONFIGURACIÓN BÁSICA
# -------------------------------------------------------------------

API_URL = "http://127.0.0.1:8003"  # ajusta el puerto si cambias el backend

st.set_page_config(
    page_title="DocuFlow – Demo 0.2",
    page_icon="📄",
    layout="centered",
)

# -------------------------------------------------------------------
# UI PRINCIPAL
# -------------------------------------------------------------------

st.title("📄 DocuFlow – Demo 0.2")
st.caption("Motor de validación documental con Golden Rule Set 1.0 (v0.2 audit-ready)")

st.markdown("### 1. Carga tu documento")

uploaded_file = st.file_uploader(
    "Arrastra aquí un archivo o haz clic para seleccionarlo",
    type=["pdf", "docx"],
    help="Formatos soportados: PDF, DOCX",
)

document_type = st.selectbox(
    "Tipo de documento",
    options=[
        "sarlaft",
        "contrato_operativo",
        "manual_procedimientos",
        "otro",
    ],
    index=0,
)

validate_button = st.button("✅ Validar documento")

# Contenedores para resultados
summary_container = st.container()
detail_container = st.container()
evidence_container = st.container()
download_container = st.container()

# -------------------------------------------------------------------
# MAPEOS PARA BADGES
# -------------------------------------------------------------------

SEVERITY_BADGES = {
    "CRITICA": "🔴 Crítica",
    "ALTA": "🟠 Alta",
    "MEDIA": "🟡 Media",
    "BAJA": "🟢 Baja",
}

STATUS_BADGES = {
    "PASS": "✅ PASS",
    "PARTIAL": "🟡 PARCIAL",
    "FAIL": "❌ FAIL",
}

# -------------------------------------------------------------------
# FUNCIÓN AUXILIAR PARA LLAMAR AL BACKEND
# -------------------------------------------------------------------


def call_backend_validate(file, document_type: str):
    """Envía el archivo al backend /validate y retorna el JSON."""
    files = {"file": (file.name, file.getvalue(), file.type)}
    data = {"document_type": document_type}

    try:
        response = requests.post(
            f"{API_URL}/validate",
            files=files,
            data=data,
            timeout=300,  # timeout ampliado para documentos largos
        )
    except requests.exceptions.RequestException as e:
        # Error de conexión (backend caído, puerto mal, etc.)
        raise RuntimeError(f"No se pudo conectar con el backend: {e}")

    # Solo tratamos como error códigos 4xx o 5xx
    if response.status_code >= 400:
        raise RuntimeError(
            f"Error {response.status_code} desde backend: {response.text}"
        )

    # Intentar parsear JSON
    try:
        return response.json()
    except ValueError:
        # El backend respondió 200 pero no fue JSON válido
        raise RuntimeError(
            f"Respuesta no válida desde backend (no es JSON): {response.text[:500]}"
        )


# -------------------------------------------------------------------
# LÓGICA PRINCIPAL
# -------------------------------------------------------------------

if validate_button:
    if not uploaded_file:
        st.error("Por favor carga un documento antes de validar.")
    else:
        with st.spinner("Validando documento..."):
            try:
                result = call_backend_validate(uploaded_file, document_type)

                summary = result.get("summary", {})
                rules_results = result.get("results", [])
                evidence = result.get("evidence", {})
                pdf_b64 = result.get("pdf_base64", None)
                document_name = result.get("document_name", uploaded_file.name)
                file_hash = result.get("file_hash_sha256", "")

            except Exception as e:
                st.error(f"Error al validar el documento: {e}")
                st.stop()

        # -------------------------------------------------------------------
        # 2. RESUMEN DE CUMPLIMIENTO
        # -------------------------------------------------------------------
        with summary_container:
            st.markdown("### 2. Resumen de cumplimiento")

            col1, col2, col3 = st.columns(3)

            compliance = summary.get("compliance_percentage", 0.0)
            passed = summary.get("rules_passed", 0)
            total = summary.get("total_rules", 0)

            with col1:
                st.metric("Cumplimiento general", f"{compliance:.1f}%")
            with col2:
                st.metric("Reglas OK", f"{passed}/{total}")
            with col3:
                short_name = (
                    document_name[:20] + "..."
                    if len(document_name) > 20
                    else document_name
                )
                st.metric("Documento", short_name)

            if file_hash:
                st.caption(f"🔐 Hash SHA-256 del archivo: `{file_hash[:16]}...`")

        # -------------------------------------------------------------------
        # 3. DETALLE POR REGLA (CON BADGES)
        # -------------------------------------------------------------------
        with detail_container:
            st.markdown("### 3. Detalle por regla (semáforo de severidad)")

            if rules_results:
                df = pd.DataFrame(rules_results)

                # Normalizar a mayúsculas por seguridad
                df["severity_raw"] = df["severity"].astype(str).str.upper()
                df["status_raw"] = df["status"].astype(str).str.upper()

                # Agregar columnas con badges
                df["Severidad"] = df["severity_raw"].map(SEVERITY_BADGES).fillna(
                    df["severity"]
                )
                df["Estado"] = df["status_raw"].map(STATUS_BADGES).fillna(df["status"])

                # Renombrar otras columnas para mostrar amigables
                col_rename = {
                    "id": "ID",
                    "name": "Nombre",
                    "matches": "Matches",
                    "required_matches": "Matches requeridos",
                    "confidence": "Confianza (%)",
                }
                df_display = df.rename(columns=col_rename)

                # Orden de columnas en la tabla (si existe confianza, se incluye)
                cols_order = [
                    "ID",
                    "Nombre",
                    "Severidad",
                    "Estado",
                    "Matches",
                    "Matches requeridos",
                ]
                if "Confianza (%)" in df_display.columns:
                    cols_order.append("Confianza (%)")

                df_display = df_display[cols_order]

                st.dataframe(df_display, width="stretch")
            else:
                st.info("No se encontraron resultados de reglas para este documento.")

        # -------------------------------------------------------------------
        # 3.b MODO AUDITORÍA – EVIDENCIA POR REGLA (ALINEADO AL TEXTO)
        # -------------------------------------------------------------------
        with evidence_container:
            st.markdown("### 🔍 Modo auditoría: evidencia por regla")

            if rules_results:
                for r in rules_results:
                    rule_id = r.get("id", "")
                    name = r.get("name", "")
                    status = (r.get("status", "") or "").upper()
                    severity = (r.get("severity", "") or "").upper()
                    confidence = r.get("confidence", None)
                    evidence_snippets = r.get("evidence", [])

                    status_badge = STATUS_BADGES.get(status, status)
                    severity_badge = SEVERITY_BADGES.get(severity, severity)

                    extra = f" · Confianza: {confidence:.1f}%" if isinstance(
                        confidence, (int, float)
                    ) else ""
                    label = f"{status_badge} · {severity_badge} · {rule_id} – {name}{extra}"

                    with st.expander(label, expanded=False):
                        if not evidence_snippets:
                            st.write("_Sin evidencia capturada para esta regla_")
                        else:
                            for idx, snippet in enumerate(evidence_snippets, start=1):
                                # Soportar tanto dict (nuevo formato) como string (fallback)
                                if isinstance(snippet, dict):
                                    text = snippet.get("text", "")
                                    keyword = snippet.get("keyword")
                                    pos = snippet.get("position")
                                    ratio = snippet.get("position_ratio")
                                else:
                                    text = str(snippet)
                                    keyword = None
                                    pos = None
                                    ratio = None

                                st.markdown(f"**Evidencia {idx}:**")

                                meta_parts = []
                                if keyword:
                                    meta_parts.append(f"Keyword: `{keyword}`")
                                if pos is not None and ratio is not None:
                                    meta_parts.append(
                                        f"Posición aprox.: {pos} "
                                        f"(≈ {ratio*100:.1f}% del documento)"
                                    )

                                if meta_parts:
                                    st.caption(" · ".join(meta_parts))

                                # Snippet alineado: texto tal cual viene del documento
                                st.code(text, language="text")
                                st.markdown("---")
            else:
                st.info("No hay evidencia disponible para mostrar.")

        # -------------------------------------------------------------------
        # 4. DESCARGAS: JSON + PDF
        # -------------------------------------------------------------------
        with download_container:
            st.markdown("### 4. Evidencia estructurada (JSON / PDF)")

            # Botón para descargar JSON
            evidence_bytes = io.BytesIO()
            evidence_bytes.write(json.dumps(evidence, indent=2).encode("utf-8"))
            evidence_bytes.seek(0)

            st.download_button(
                label="💾 Descargar evidencia JSON",
                data=evidence_bytes,
                file_name="docuflow_evidence.json",
                mime="application/json",
            )

            # Botón para descargar PDF si viene desde backend
            if pdf_b64:
                try:
                    pdf_bytes = base64.b64decode(pdf_b64)
                    st.download_button(
                        label="📄 Descargar reporte PDF",
                        data=pdf_bytes,
                        file_name="docuflow_report.pdf",
                        mime="application/pdf",
                    )
                    # Mini info de depuración: tamaño del PDF
                    st.caption(f"Tamaño del PDF generado: {len(pdf_bytes)} bytes")
                except Exception as e:
                    st.warning(
                        f"No se pudo decodificar el PDF generado. "
                        f"Detalle técnico: {e}"
                    )
            else:
                st.info(
                    "PDF no recibido desde el backend. "
                    "Si ves este mensaje en la demo 0.2, revisa que el backend "
                    "esté enviando el campo 'pdf_base64'."
                )

else:
    st.info("Carga un documento y haz clic en **✅ Validar documento** para comenzar.")