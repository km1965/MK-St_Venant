"""Catalogue CEAI / TRIFON et référence SNH - organes d'air pour grands DN.

Source : ``Catalogue des équipements.docx`` (racine du projet), annexe de
vérification. Capacités d'air admis en m³/h à la dépression nominale de 3 mCE
(NF EN 805), converties en m³/s par division par 3600.

Trois familles sont répertoriées :
- TRIFON (CEAI) - ventouse (DN50 a DN300) ;
- CEAI - clapet d'admission d'air (DN80 a DN500) ;
- SNH - purgeur sonique (DN200 a DN1500), rôle de purge continue, référence
  distincte du dimensionnement admission.

Les configurations AUDIT (PAM DN200 + clapets SNH) et CEAI sont comparées
côte à côte ; l'utilisateur choisit celle qui est retenue dans les rapports.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .tables import TABLE_PAM, TABLE_SNH

SOURCE_DOCX = "Catalogue des équipements.docx"
ORIGINE_FIRM = "FIRM V1/2025"
PRESSION_REFERENCE = "3 mCE (NF EN 805)"

CONFIG_AUDIT = "PAM DN200 + clapets SNH (audit)"
CONFIG_CEAI = "Trifon CEAI + clapet CEAI"
CONFIGURATIONS: tuple[str, ...] = (CONFIG_AUDIT, CONFIG_CEAI)


@dataclass(frozen=True)
class OrganeAir:
    """Un organe d'air du catalogue, avec sa capacité unitaire."""

    famille: str
    dn: str
    capacite_m3h: float
    retenu: str = "—"
    origine: str = ORIGINE_FIRM

    @property
    def capacite_m3s(self) -> float:
        """Capacité convertie en m³/s."""
        return self.capacite_m3h / 3600.0


# TRIFON (CEAI) — Ventouse. Statut : validé ; origine FIRM V1/2025.
VENTOUSES_TRIFON_CEAI: tuple[OrganeAir, ...] = (
    OrganeAir("Ventouse Trifon CEAI", "DN50", 750),
    OrganeAir("Ventouse Trifon CEAI", "DN65", 1200),
    OrganeAir("Ventouse Trifon CEAI", "DN80", 2100),
    OrganeAir("Ventouse Trifon CEAI", "DN100", 3800),
    OrganeAir("Ventouse Trifon CEAI", "DN150", 8000),
    OrganeAir("Ventouse Trifon CEAI", "DN200", 17000, "---"),
    OrganeAir("Ventouse Trifon CEAI", "DN250", 26000),
    OrganeAir("Ventouse Trifon CEAI", "DN300", 38000, "---"),
)

# CEAI — Clapet d'admission d'air. Statut : validé ; origine FIRM V1/2025.
CLAPETS_CEAI: tuple[OrganeAir, ...] = (
    OrganeAir("Clapet CEAI", "DN80", 1800),
    OrganeAir("Clapet CEAI", "DN100", 2902),
    OrganeAir("Clapet CEAI", "DN150", 6300),
    OrganeAir("Clapet CEAI", "DN200", 11304),
    OrganeAir("Clapet CEAI", "DN250", 17600),
    OrganeAir("Clapet CEAI", "DN300", 26701),
    OrganeAir("Clapet CEAI", "DN350", 34600),
    OrganeAir("Clapet CEAI", "DN400", 47401),
    OrganeAir("Clapet CEAI", "DN500", 70600),
)

# SNH — Purgeur sonique. Référence de purge continue, pas d'admission grand débit.
PURGEURS_SONIQUES_SNH: tuple[OrganeAir, ...] = (
    OrganeAir("Purgeur sonique SNH", "DN200", 9),
    OrganeAir("Purgeur sonique SNH", "DN300", 14),
    OrganeAir("Purgeur sonique SNH", "DN400", 19),
    OrganeAir("Purgeur sonique SNH", "DN500", 27),
    OrganeAir("Purgeur sonique SNH", "DN700", 36),
    OrganeAir("Purgeur sonique SNH", "DN900", 79),
    OrganeAir("Purgeur sonique SNH", "DN1200", 108),
    OrganeAir("Purgeur sonique SNH", "DN1500", 144, "---"),
)


@dataclass(frozen=True)
class PropositionFamille:
    """Proposition dimensionnée pour une famille d'organes."""

    famille: str
    dn: str
    capacite_unitaire_m3s: float
    nombre: int
    debit_m3s: float
    origine: str

    @property
    def capacite_totale_m3s(self) -> float:
        return self.capacite_unitaire_m3s * self.nombre

    @property
    def marge_m3s(self) -> float:
        return self.capacite_totale_m3s - self.debit_m3s

    @property
    def couvert(self) -> bool:
        return self.debit_m3s > 0 and self.capacite_totale_m3s >= self.debit_m3s


def _proposition(
    famille: str,
    dn: str,
    capacite_unitaire_m3s: float,
    debit_m3s: float,
    origine: str,
) -> PropositionFamille:
    """Construit une proposition (capacité unitaire et nombre d'unités)."""
    nombre = (
        math.ceil(debit_m3s / capacite_unitaire_m3s)
        if capacite_unitaire_m3s > 0 and debit_m3s > 0
        else 0
    )
    return PropositionFamille(
        famille, dn, capacite_unitaire_m3s, nombre, debit_m3s, origine
    )


def proposer_organe(
    table: tuple[OrganeAir, ...], debit_m3s: float, famille: str
) -> PropositionFamille:
    """Premier organe couvrant le débit, sinon le plus grand avec cumul d'unités."""
    couvrant = next(
        (o for o in table if debit_m3s > 0 and o.capacite_m3s >= debit_m3s),
        None,
    )
    organe = couvrant or table[-1]
    return _proposition(
        famille, organe.dn, organe.capacite_m3s, debit_m3s, organe.origine
    )


def proposer_clapet_snh(debit_m3s: float) -> PropositionFamille:
    """Proposition issue de la table SNH validée par l'audit (note PDF p. 6)."""
    couvrant = next(
        (
            c for c in TABLE_SNH
            if debit_m3s > 0 and c.debit_admission_depression_3m_m3s is not None
            and c.debit_admission_depression_3m_m3s >= debit_m3s
        ),
        None,
    )
    if couvrant:
        return _proposition(
            "Clapet SNH",
            couvrant.dn,
            couvrant.debit_admission_depression_3m_m3s,
            debit_m3s,
            "Note PDF page 6 (audit)",
        )
    dernier = TABLE_SNH[-1]
    return _proposition(
        "Clapet SNH",
        dernier.dn,
        dernier.debit_admission_depression_3m_m3s or 0.0,
        debit_m3s,
        "Note PDF page 6 (audit)",
    )


def proposer_pam_dn200(debit_m3s: float) -> PropositionFamille:
    """Configuration audit : ventouse PAM DN200 fixée."""
    pam = next(c for c in TABLE_PAM if c.dn == "DN200")
    return _proposition(
        "Ventouse PAM",
        pam.dn,
        pam.debit_admission_depression_3m_m3s or 0.0,
        debit_m3s,
        "Note PDF page 6 (audit) - valeur tableau",
    )


@dataclass(frozen=True)
class ResultatConfiguration:
    """Résultat complet d'une configuration de dimensionnement d'air."""

    nom: str
    debit_m3s: float
    ventouse: PropositionFamille
    clapet: PropositionFamille

    @property
    def couvert(self) -> bool:
        return self.ventouse.couvert and self.clapet.couvert

    @property
    def resume(self) -> str:
        v, c = self.ventouse, self.clapet
        return (
            f"{self.nom} — Qair à couvrir : {self.debit_m3s:.3f} m³/s. "
            f"{v.famille} {v.dn} ×{v.nombre} = {v.capacite_totale_m3s:.3f} m³/s "
            f"(marge {v.marge_m3s:+.3f}) ; "
            f"{c.famille} {c.dn} ×{c.nombre} = {c.capacite_totale_m3s:.3f} m³/s "
            f"(marge {c.marge_m3s:+.3f}). "
            f"Couverture {'OUI' if self.couvert else 'NON'}."
        )


def analyser_configurations(debit_m3s: float) -> dict[str, ResultatConfiguration]:
    """Compare les configurations audit et CEAI pour un débit d'air donné."""
    return {
        CONFIG_AUDIT: ResultatConfiguration(
            CONFIG_AUDIT,
            debit_m3s,
            proposer_pam_dn200(debit_m3s),
            proposer_clapet_snh(debit_m3s),
        ),
        CONFIG_CEAI: ResultatConfiguration(
            CONFIG_CEAI,
            debit_m3s,
            proposer_organe(VENTOUSES_TRIFON_CEAI, debit_m3s, "Ventouse Trifon CEAI"),
            proposer_organe(CLAPETS_CEAI, debit_m3s, "Clapet CEAI"),
        ),
    }


def resume_configuration(resultat: ResultatConfiguration) -> str:
    """Résumé lisible d'une configuration."""
    return resultat.resume


def plus_grand_purgeur_sonique() -> OrganeAir:
    """Purgeur sonique SNH de plus grande capacité (référence de purge)."""
    return PURGEURS_SONIQUES_SNH[-1]


# ------------------------------------------------------------------------------
# Intégration applicative : sélection de base de calcul / référence
# ------------------------------------------------------------------------------
CATALOG_PAM_SNH = "PAM_SNH"
CATALOG_CEAI_SNH = "CEAI_SNH"

CATALOG_CONFIG_LABELS: dict[str, str] = {
    CATALOG_PAM_SNH: "PAM/SNH (existant)",
    CATALOG_CEAI_SNH: "CEAI/SNH (référence)",
}

DEFAULT_AIR_CATALOG_CONFIG = CATALOG_CEAI_SNH


def _format_equipment_string(
    ventouse: PropositionFamille,
    clapet: PropositionFamille,
    purgeur: PropositionFamille | None = None,
) -> str:
    parts = []
    if ventouse.nombre > 0:
        parts.append(f"{ventouse.nombre} {ventouse.famille} {ventouse.dn}")
    if clapet.nombre > 0:
        parts.append(f"{clapet.nombre} {clapet.famille} {clapet.dn}")
    if purgeur and purgeur.nombre > 0:
        parts.append(f"{purgeur.nombre} {purgeur.famille} {purgeur.dn}")
    return " + ".join(parts) if parts else "Aucun équipement requis"


def _capacite_totale(*propositions: PropositionFamille | None) -> float:
    return sum(p.capacite_totale_m3s for p in propositions if p is not None)


def _optimiser_combinaison_ceai(debit_m3s: float) -> tuple[PropositionFamille, PropositionFamille, PropositionFamille | None]:
    """Choisit une combinaison CEAI/SNH optimisée (admission sous 3 mCE).

    Stratégie :
    - privilégier 1 ventouse Trifon CEAI + 1 clapet CEAI, complétés si besoin
      par 1 purgeur sonique SNH d'appoint ;
    - parmi les combinaisons couvrantes sans multiplication d'unités, retenir
      celle avec le plus faible surdimensionnement (capacité totale la plus
      proche du besoin), puis le moins d'organes, puis les calibres les plus
      économiques ;
    - si aucune combinaison 1+1(+1) ne couvre, autoriser le cumul d'unités sur
      les plus grands organes (cas de très forts débits).
    """
    eps = 1e-9
    if debit_m3s <= 0:
        v0 = VENTOUSES_TRIFON_CEAI[0]
        c0 = CLAPETS_CEAI[0]
        v = PropositionFamille(v0.famille, v0.dn, v0.capacite_m3s, 0, 0.0, v0.origine)
        c = PropositionFamille(c0.famille, c0.dn, c0.capacite_m3s, 0, 0.0, c0.origine)
        return v, c, None

    purgeurs = list(PURGEURS_SONIQUES_SNH)
    best_single: tuple | None = None
    best_multi: tuple | None = None

    for v_org in VENTOUSES_TRIFON_CEAI:
        for c_org in CLAPETS_CEAI:
            base_cap = v_org.capacite_m3s + c_org.capacite_m3s
            for p_org in [None] + purgeurs:
                p_cap = p_org.capacite_m3s if p_org else 0.0
                total_single = base_cap + p_cap

                v_prop_1 = PropositionFamille(
                    v_org.famille, v_org.dn, v_org.capacite_m3s, 1, debit_m3s, v_org.origine
                )
                c_prop_1 = PropositionFamille(
                    c_org.famille, c_org.dn, c_org.capacite_m3s, 1, debit_m3s, c_org.origine
                )
                p_prop = (
                    PropositionFamille(
                        p_org.famille, p_org.dn, p_org.capacite_m3s, 1, debit_m3s, p_org.origine
                    )
                    if p_org
                    else None
                )

                if total_single + eps >= debit_m3s:
                    oversize = total_single - debit_m3s
                    nb_organes = 2 + (1 if p_prop else 0)
                    # Priorité : plus faible surdimensionnement, puis moins d'organes,
                    # puis calibres (capacité nominale) les plus petits.
                    score = (
                        oversize,
                        nb_organes,
                        v_org.capacite_m3s + c_org.capacite_m3s + p_cap,
                        1 if p_prop else 0,
                    )
                    candidate = (score, v_prop_1, c_prop_1, p_prop)
                    if best_single is None or candidate[0] < best_single[0]:
                        best_single = candidate
                    continue

                # Repli : cumul d'unités uniquement si 1+1(+1) ne suffit pas
                deficit = debit_m3s - base_cap - p_cap
                extra_c = math.ceil(deficit / c_org.capacite_m3s) if c_org.capacite_m3s > 0 else 0
                c_count = 1 + max(0, extra_c)
                c_prop_m = PropositionFamille(
                    c_org.famille, c_org.dn, c_org.capacite_m3s, c_count, debit_m3s, c_org.origine
                )
                total_m = v_prop_1.capacite_totale_m3s + c_prop_m.capacite_totale_m3s + p_cap
                v_prop_m = v_prop_1
                if total_m + eps < debit_m3s:
                    deficit2 = debit_m3s - c_prop_m.capacite_totale_m3s - p_cap
                    extra_v = math.ceil(deficit2 / v_org.capacite_m3s) if v_org.capacite_m3s > 0 else 0
                    v_count = 1 + max(0, extra_v)
                    v_prop_m = PropositionFamille(
                        v_org.famille, v_org.dn, v_org.capacite_m3s, v_count, debit_m3s, v_org.origine
                    )
                    total_m = v_prop_m.capacite_totale_m3s + c_prop_m.capacite_totale_m3s + p_cap

                covered = total_m + eps >= debit_m3s
                if covered:
                    oversize_m = total_m - debit_m3s
                    extra_units = (v_prop_m.nombre - 1) + (c_prop_m.nombre - 1)
                    total_units = v_prop_m.nombre + c_prop_m.nombre + (p_prop.nombre if p_prop else 0)
                    score_m = (extra_units, oversize_m, total_units, base_cap + p_cap)
                    candidate_m = (score_m, v_prop_m, c_prop_m, p_prop)
                    if best_multi is None or candidate_m[0] < best_multi[0]:
                        best_multi = candidate_m

    if best_single is not None:
        return best_single[1], best_single[2], best_single[3]
    if best_multi is not None:
        return best_multi[1], best_multi[2], best_multi[3]

    # Dernier recours : méthode simple (plus grands organes avec cumul)
    cfg = analyser_configurations(debit_m3s)[CONFIG_CEAI]
    return cfg.ventouse, cfg.clapet, None


def recommander_equipement_ceai_snh(
    debit_m3s: float, dn_conduite_m: float = 0.0, v_filling_ms: float = 0.5
) -> dict:
    """Recommandation selon la configuration CEAI/SNH de référence.

    Optimise la combinaison ventouse Trifon CEAI + clapet CEAI (+ éventuel
    appoint purgeur sonique SNH) pour couvrir le débit d'admission requis sous
    3 mCE avec le minimum de surdimensionnement.
    """
    from math import pi

    v, c, p = _optimiser_combinaison_ceai(debit_m3s)

    q_filling_m3h = v_filling_ms * (pi * (dn_conduite_m ** 2) / 4.0) * 3600.0 if dn_conduite_m > 0 else 0.0
    total_admission = _capacite_totale(v, c, p)
    intake_ok = debit_m3s <= 0 or total_admission + 1e-9 >= debit_m3s

    # Les données d'évacuation au remplissage ne sont pas fournies pour les
    # organes CEAI dans ce catalogue : on considère la fonction remplissage
    # non vérifiable explicitement (non bloquante) tout en conservant le débit.
    filling_ok = True

    result = {
        "equipment_str": _format_equipment_string(v, c, p),
        "total_admission_flow_m3s": round(total_admission, 3),
        "q_admis_m3s": round(total_admission, 3),
        "is_compliant_intake": bool(intake_ok),
        "is_compliant_filling": bool(filling_ok),
        "total_exhaust_flow_m3h": None,
        "filling_flow_m3h": round(q_filling_m3h, 1),
        "coverage_pct": round((total_admission / debit_m3s * 100.0) if debit_m3s > 0 else 100.0, 1),
        "ventouse": {
            "famille": v.famille,
            "dn": v.dn,
            "nombre": v.nombre,
            "capacite_unitaire_m3s": v.capacite_unitaire_m3s,
            "capacite_totale_m3s": v.capacite_totale_m3s,
            "couvert": v.couvert,
        },
        "clapet": {
            "famille": c.famille,
            "dn": c.dn,
            "nombre": c.nombre,
            "capacite_unitaire_m3s": c.capacite_unitaire_m3s,
            "capacite_totale_m3s": c.capacite_totale_m3s,
            "couvert": c.couvert,
        },
        "catalog_config": CATALOG_CEAI_SNH,
        "config_label": CATALOG_CONFIG_LABELS[CATALOG_CEAI_SNH],
        "reference": CONFIG_CEAI,
    }
    if p and p.nombre > 0:
        result["purgeur"] = {
            "famille": p.famille,
            "dn": p.dn,
            "nombre": p.nombre,
            "capacite_unitaire_m3s": p.capacite_unitaire_m3s,
            "capacite_totale_m3s": p.capacite_totale_m3s,
        }
    return result



def recommander_equipement_air(
    debit_m3s: float,
    dn_conduite_m: float,
    v_filling_ms: float = 0.5,
    catalog_config: str = DEFAULT_AIR_CATALOG_CONFIG,
) -> dict:
    """Point d'entrée unique de recommandation selon la base catalogue choisie."""
    if catalog_config == CATALOG_CEAI_SNH:
        return recommander_equipement_ceai_snh(debit_m3s, dn_conduite_m, v_filling_ms)

    # Existant / audit : PAM/SNH
    from .catalog import recommend_air_valve_equipment

    rec = dict(
        recommend_air_valve_equipment(
            q_air_req_m3s=debit_m3s,
            dn_conduite_m=dn_conduite_m,
            v_filling_ms=v_filling_ms,
        )
    )
    rec.setdefault("q_admis_m3s", rec.get("total_admission_flow_m3s", 0.0))
    rec["catalog_config"] = CATALOG_PAM_SNH
    rec["config_label"] = CATALOG_CONFIG_LABELS[CATALOG_PAM_SNH]
    rec["reference"] = CONFIG_AUDIT
    return rec

