"""
Tables de référence PAM/SNH utilisées par le catalogue CEAI/SNH pour la
configuration d'audit (PAM DN200 + clapets SNH).

Construites à partir des spécifications existantes du projet afin d'assurer
la compatibilité avec le module ``catalogues_ceai_snh``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .catalog import PAM_TRIPLE_FUNCTION_VALVES, SNH_AIR_INLET_VALVES


@dataclass(frozen=True)
class ValveTableEntry:
    """Entrée de table compatible avec ``core.catalogues_ceai_snh``."""

    dn: str
    debit_admission_depression_3m_m3s: Optional[float]
    debit_evacuation_surpression_1m_m3h: Optional[float] = None


def _dn_label(dn_mm: int) -> str:
    return f"DN{dn_mm}"


TABLE_PAM = tuple(
    ValveTableEntry(
        dn=_dn_label(spec.dn_mm),
        debit_admission_depression_3m_m3s=spec.admission_flow_3m_m3s,
        debit_evacuation_surpression_1m_m3h=spec.exhaust_flow_1m_m3h,
    )
    for _, spec in sorted(PAM_TRIPLE_FUNCTION_VALVES.items())
)

TABLE_SNH = tuple(
    ValveTableEntry(
        dn=_dn_label(spec.dn_mm),
        debit_admission_depression_3m_m3s=spec.admission_flow_3m_m3s,
        debit_evacuation_surpression_1m_m3h=spec.exhaust_flow_1m_m3h if spec.exhaust_flow_1m_m3h else None,
    )
    for _, spec in sorted(SNH_AIR_INLET_VALVES.items())
)
