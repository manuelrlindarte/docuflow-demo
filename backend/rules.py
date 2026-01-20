# backend/rules.py

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class Rule:
    id: str
    name: str
    description: str
    severity: str          # CRITICA / ALTA / MEDIA / BAJA
    keywords: List[str]
    min_occurrences: int = 1
    recommendation: str = ""  # NUEVO: recomendación de remediación


GOLDEN_RULE_SET_1_0: List[Rule] = [
    Rule(
        id="SARLAFT-001",
        name="Procedimiento de identificación de riesgos LA/FT",
        description=(
            "El documento debe contener procedimiento explícito de "
            "identificación de riesgos de lavado de activos y financiación del terrorismo."
        ),
        severity="CRITICA",
        keywords=["identificación", "metodología", "procedimiento", "riesgo LA/FT", "FPADM"],
        min_occurrences=2,
        recommendation=(
            "Incluya una sección específica donde se describan etapas, metodologías "
            "y herramientas para la identificación de riesgos LA/FT/FPADM, con "
            "responsables y periodicidad definidos."
        ),
    ),
    Rule(
        id="SARLAFT-002",
        name="Roles y responsabilidades SARLAFT",
        description=(
            "Debe definir roles específicos (Oficial de Cumplimiento, responsables por área)."
        ),
        severity="ALTA",
        keywords=["oficial de cumplimiento", "responsable", "rol", "junta directiva"],
        min_occurrences=1,
        recommendation=(
            "Asegure que el documento identifique explícitamente al Oficial de Cumplimiento, "
            "los responsables por área y su relación con la Junta Directiva, incluyendo "
            "atribuciones y deberes concretos."
        ),
    ),
    Rule(
        id="MODEL-001",
        name="Gobernanza de modelos de IA",
        description="Debe incluir sección sobre gobernanza, validación y monitoreo de modelos.",
        severity="ALTA",
        keywords=["modelo", "modelos", "validación de modelos", "gobernanza", "comité"],
        min_occurrences=2,
        recommendation=(
            "Incluya una sección de gobernanza de modelos donde se describan procesos de "
            "desarrollo, validación independiente, monitoreo, gestión de cambios y comité "
            "encargado de aprobar modelos críticos."
        ),
    ),
    Rule(
        id="OPS-001",
        name="Controles y responsables operativos",
        description="Debe definir controles específicos y asignar responsables.",
        severity="MEDIA",
        keywords=["control", "controles", "proceso", "procedimiento", "verificación"],
        min_occurrences=1,
        recommendation=(
            "Documente los controles operativos clave (qué se hace, quién lo hace, con qué "
            "frecuencia y con qué evidencia), indicando claramente el responsable de cada control."
        ),
    ),
    Rule(
        id="TRACE-001",
        name="Trazabilidad de cambios documentales",
        description="Debe incluir control de versiones o registro de cambios en el documento.",
        severity="MEDIA",
        keywords=["versión", "control de cambios", "historial de cambios", "revisión"],
        min_occurrences=1,
        recommendation=(
            "Agregue un cuadro o anexo de control de versiones que incluya versión, fecha, "
            "responsable de aprobación y descripción de cambios relevantes realizados al documento."
        ),
    ),
]


def get_golden_rule_set(document_type: str) -> List[Rule]:
    """
    En esta demo, devolvemos siempre el Golden Rule Set 1.0.
    Más adelante puedes diferenciar por tipo de documento.
    """
    return GOLDEN_RULE_SET_1_0

# Alias de compatibilidad para código viejo
GOLDEN_RULES = GOLDEN_RULE_SET_1_0