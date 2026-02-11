SFC_REFERENCES = {
    "CE-022-2007": "Circular Externa 022 de 2007 - SARLAFT",
    "CE-029-2014": "Circular Externa 029 de 2014 - Oficial de Cumplimiento",
    "SB-DIG-2025": "Supervisión Digital SFC 2025",
    "SR-11-7": "SR 11-7 Model Risk Management"
}

ENTITY_PROFILES = {
    "cooperativa": {
        "display_name": "Cooperativa Financiera Vigilada",
        "forbidden_terms": [
            {
                "id": "FU-COOP-001",
                "terms": ["oficial principal sarlaft", "oficial principal y oficial suplente"],
                "severity": "HIGH",
                "title": "Estructura de Oficial Principal/Suplente típica de banco Tier 1",
                "reason": "Lenguaje sugiere copia de política bancaria.",
                "recommendation": (
                    "Reemplazar por 'Oficial de Cumplimiento designado por el Consejo de Administración' "
                    "y ajustar el esquema de reporte a órganos cooperativos."
                ),
                "sfc_ref_id": "CE-029-2014"
            },
            {
                "id": "FU-COOP-002",
                "terms": ["corresponsalía bancaria", "corresponsalia bancaria", "swift bic", "operaciones swift"],
                "severity": "HIGH",
                "title": "Operaciones internacionales/corresponsalía no típicas para cooperativa",
                "reason": "Sugiere operación internacional estilo banco.",
                "recommendation": (
                    "Eliminar referencias a corresponsalía/SWIFT. "
                    "Si existen remesas, aclarar que se realizan mediante entidades autorizadas como intermediarias."
                ),
                "sfc_ref_id": "CE-022-2007"
            },
            {
                "id": "FU-COOP-003",
                "terms": ["casa matriz", "filial", "subsidiaria", "holding"],
                "severity": "MEDIUM",
                "title": "Estructura corporativa tipo grupo financiero",
                "reason": "Lenguaje sugiere copia de documentos de conglomerado.",
                "recommendation": (
                    "Reemplazar por estructura cooperativa: Asamblea General, Consejo de Administración, Junta de Vigilancia."
                ),
                "sfc_ref_id": None
            }
        ],
        "required_sections": [
            {
                "id": "FU-COOP-REQ-001",
                "name": "Estructura de gobierno cooperativo",
                "keywords": ["asamblea", "consejo de administración", "junta de vigilancia"],
                "severity": "HIGH",
                "recommendation": (
                    "Añadir una sección que describa órganos de gobierno cooperativo y roles en SARLAFT."
                ),
                "sfc_ref_id": None
            }
        ],
        "overkill_patterns": []
    },

    "sedpe": {
        "display_name": "SEDPE",
        "forbidden_terms": [
            {
                "id": "FU-SEDPE-001",
                "terms": ["red de oficinas físicas", "sucursales", "puntos de atención presencial"],
                "severity": "HIGH",
                "title": "Red física no típica en SEDPE",
                "reason": "SEDPE normalmente opera por canales digitales.",
                "recommendation": "Reemplazar por canales digitales: app móvil, web, APIs, aliados.",
                "sfc_ref_id": "SB-DIG-2025"
            }
        ],
        "required_sections": [
            {
                "id": "FU-SEDPE-REQ-001",
                "name": "Riesgos tecnológicos/ciberseguridad",
                "keywords": ["ciberseguridad", "riesgo tecnológico", "seguridad de la información"],
                "severity": "HIGH",
                "recommendation": "Incluir sección específica de riesgos tecnológicos y controles.",
                "sfc_ref_id": "SB-DIG-2025"
            }
        ],
        "overkill_patterns": []
    }
}

INCONSISTENCY_DETECTORS = [
    {
        "id": "INC-001",
        "name": "Alcance nacional vs operaciones internacionales",
        "severity": "HIGH",
        "check_has": ["solo operaciones nacionales", "únicamente en colombia", "operación nacional"],
        "check_also_has": ["corresponsalía", "swift", "operaciones internacionales", "exterior"],
        "reason": "Declara operación solo nacional pero incluye procedimientos internacionales.",
        "recommendation": "Alinear alcance geográfico declarado con los procesos descritos.",
        "sfc_ref_id": "CE-022-2007"
    }
]
