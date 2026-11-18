"""
Modèles de données du projet hydraulique (Ventouses & Vidanges).
Gère la liste des points hauts, des points bas, les paramètres globaux
et l'orchestration des calculs.
"""

from dataclasses import dataclass, field, asdict, fields
from typing import List, Dict, Optional, Any
import json
import os

from core.hydraulic_models import (
    calculate_strickler_rupture_flow,
    calculate_filling_air_flow,
    calculate_drain_dimensioning,
    calculate_allievi_wave_speed
)
from core.catalog import (
    get_standard_dn_drain,
    PIPE_MATERIALS
)
from core.catalogues_ceai_snh import (
    DEFAULT_AIR_CATALOG_CONFIG,
    recommander_equipement_air,
)


@dataclass
class AirValvePoint:
    """Représente un point haut équipé de ventouse / clapet."""
    id: int
    pm: float
    z_terrain: float              # Cote projet / terrain (m)
    dn_conduite_m: float          # Diamètre conduite en m (ex: 2.0 ou 1.6)
    pm_amont: Optional[float]     # PM de la vidange/point bas amont
    z_amont: Optional[float]      # Cote vidange amont (m)
    pm_aval: Optional[float]      # PM de la vidange/point bas aval
    z_aval: Optional[float]       # Cote vidange aval (m)
    initial_equipment: str = ""   # Équipement initialement prévu (dans l'ancien dossier)
    initial_flow_admitted: float = 0.0 # Débit équipé initial (m3/s)

    # Résultats calculés
    l_amont_m: float = 0.0
    l_aval_m: float = 0.0
    h_amont_m: float = 0.0
    h_aval_m: float = 0.0
    q_air_amont_m3s: float = 0.0
    q_air_aval_m3s: float = 0.0
    q_air_max_m3s: float = 0.0
    q_filling_m3h: float = 0.0
    q_degas_m3h: float = 0.0

    # Équipement corrigé recommandé
    recommended_equipment: str = ""
    retained_equipment: str = ""
    q_admis_m3s: float = 0.0
    is_compliant: bool = True
    comment: str = ""

    def calculate(
        self,
        ks_strickler: float = 104.0,
        v_filling_ms: float = 0.5,
        delta_p_admiss_mce: float = 3.0,
        q_nom_eau_m3s: float = 5.3,
        catalog_config: str = DEFAULT_AIR_CATALOG_CONFIG,
    ):
        # Longueurs
        self.l_amont_m = abs(self.pm - self.pm_amont) if (self.pm_amont is not None) else 0.0
        self.l_aval_m = abs(self.pm_aval - self.pm) if (self.pm_aval is not None) else 0.0

        # Amont
        if self.pm_amont is not None and self.z_amont is not None:
            res_up = calculate_strickler_rupture_flow(
                d_inner_m=self.dn_conduite_m,
                length_m=self.l_amont_m,
                z_air_valve_m=self.z_terrain,
                z_drain_m=self.z_amont,
                delta_p_admiss_mce=delta_p_admiss_mce,
                ks_strickler=ks_strickler
            )
            self.h_amont_m = res_up["h_moteur_m"]
            self.q_air_amont_m3s = res_up["q_air_m3s"]
        else:
            self.h_amont_m = 0.0
            self.q_air_amont_m3s = 0.0

        # Aval
        if self.pm_aval is not None and self.z_aval is not None:
            res_down = calculate_strickler_rupture_flow(
                d_inner_m=self.dn_conduite_m,
                length_m=self.l_aval_m,
                z_air_valve_m=self.z_terrain,
                z_drain_m=self.z_aval,
                delta_p_admiss_mce=delta_p_admiss_mce,
                ks_strickler=ks_strickler
            )
            self.h_aval_m = res_down["h_moteur_m"]
            self.q_air_aval_m3s = res_down["q_air_m3s"]
        else:
            self.h_aval_m = 0.0
            self.q_air_aval_m3s = 0.0

        self.q_air_max_m3s = round(max(self.q_air_amont_m3s, self.q_air_aval_m3s), 2)

        # Remplissage
        res_fill = calculate_filling_air_flow(d_inner_m=self.dn_conduite_m, v_filling_ms=v_filling_ms)
        self.q_filling_m3h = res_fill["q_air_remplissage_m3h"]

        # Dégazage
        self.q_degas_m3h = round(0.02 * q_nom_eau_m3s * 3600.0, 1)

        # Recommandation automatique selon la base catalogue sélectionnée
        rec = recommander_equipement_air(
            debit_m3s=self.q_air_max_m3s,
            dn_conduite_m=self.dn_conduite_m,
            v_filling_ms=v_filling_ms,
            catalog_config=catalog_config,
        )
        self.recommended_equipment = rec["equipment_str"]
        if not self.retained_equipment:
            self.retained_equipment = self.recommended_equipment

        self.q_admis_m3s = rec.get("q_admis_m3s", rec.get("total_admission_flow_m3s", 0.0))
        self.is_compliant = self.q_admis_m3s >= self.q_air_max_m3s and rec.get("is_compliant_filling", True)

        comments = []
        if self.h_amont_m == 0 and self.pm_amont is not None and self.z_amont is not None and self.z_terrain is not None and (self.z_terrain - self.z_amont < 3.0):
            comments.append("Tronçon amont : Dénivelée < 3m (colonne insuffisante)")
        if self.h_aval_m == 0 and self.pm_aval is not None and self.z_aval is not None and self.z_terrain is not None and (self.z_terrain - self.z_aval < 3.0):
            comments.append("Tronçon aval : Dénivelée < 3m (colonne insuffisante)")
        if self.initial_flow_admitted > 0 and self.initial_flow_admitted < self.q_air_max_m3s:
            comments.append(f"Alerte note initiale : sous-équipé ({self.initial_flow_admitted} < {self.q_air_max_m3s} m3/s)")
        if rec.get("is_compliant_filling") is False:
            comments.append("Alerte remplissage : évacuation d'air insuffisante")

        self.comment = " | ".join(comments) if comments else "Conforme aux 3 fonctions"


@dataclass
class DrainPoint:
    """Représente un point bas équipé d'un ouvrage de vidange."""
    id: int
    pm: float
    z_terrain: float              # Cote du point bas (m)
    dn_conduite_m: float          # Diamètre conduite principale (m)
    pm_amont: Optional[float]     # PM ventouse amont
    z_amont: Optional[float]      # Cote ventouse amont (m)
    pm_aval: Optional[float]      # PM ventouse aval
    z_aval: Optional[float]       # Cote ventouse aval (m)
    dn_initial_doc_mm: Optional[int] = None # DN proposé dans la note initiale (souvent 400 uniformisé)

    # Résultats calculés
    l_amont_m: float = 0.0
    l_aval_m: float = 0.0
    l_total_m: float = 0.0
    h_amont_m: float = 0.0
    h_aval_m: float = 0.0
    h_moy_m: float = 0.0
    volume_water_m3: float = 0.0
    d_exact_mm: float = 0.0
    dn_recommended_mm: int = 400
    dn_retained_mm: int = 400
    t_real_hours: float = 2.0
    t_real_str: str = "2h00"
    is_compliant: bool = True
    comment: str = ""

    def calculate(self, target_time_hours: float = 2.0, discharge_coeff_k: float = 0.70):
        self.l_amont_m = abs(self.pm - self.pm_amont) if (self.pm is not None and self.pm_amont is not None) else 0.0
        self.l_aval_m = abs(self.pm_aval - self.pm) if (self.pm is not None and self.pm_aval is not None) else 0.0
        self.l_total_m = self.l_amont_m + self.l_aval_m

        self.h_amont_m = max(0.0, (self.z_amont - self.z_terrain)) if (self.z_amont is not None and self.z_terrain is not None) else 0.0
        self.h_aval_m = max(0.0, (self.z_aval - self.z_terrain)) if (self.z_aval is not None and self.z_terrain is not None) else 0.0

        res = calculate_drain_dimensioning(
            dn_pipe_m=self.dn_conduite_m,
            l_upstream_m=self.l_amont_m,
            h_upstream_m=self.h_amont_m,
            l_downstream_m=self.l_aval_m,
            h_downstream_m=self.h_aval_m,
            target_time_hours=target_time_hours,
            discharge_coeff_k=discharge_coeff_k,
            dn_retained_mm=self.dn_retained_mm
        )

        self.h_moy_m = res["h_moy_m"]
        self.volume_water_m3 = res["v_water_m3"]
        self.d_exact_mm = res["d_exact_mm"]
        self.dn_recommended_mm = res["dn_recommended_mm"]
        if not self.dn_retained_mm:
            self.dn_retained_mm = self.dn_recommended_mm

        # Recalcul temps réel avec dn_retained_mm
        self.t_real_hours = round(target_time_hours * ((self.d_exact_mm / float(self.dn_retained_mm)) ** 2), 2)
        from core.hydraulic_models import format_hours_minutes
        self.t_real_str = format_hours_minutes(self.t_real_hours)
        self.is_compliant = self.t_real_hours <= target_time_hours + 0.05

        if self.is_compliant:
            self.comment = f"Conforme (vidange en {self.t_real_str} <= {target_time_hours}h)"
        else:
            self.comment = f"Alerte : sous-dimensionné pour DN {self.dn_retained_mm} ({self.t_real_str} > {target_time_hours}h)"


@dataclass
class HydraulicProject:
    """Structure générale d'un projet d'adduction."""
    name: str = "Nouveau projet hydraulique"
    description: str = "Dimensionnement et vérification hydraulique des ventouses et vidanges"
    dn_main_conduite_m: float = 2.0
    pipe_material: str = "PRV (Polyester Renforcé Verre)"
    pipe_thickness_m: float = 0.035
    ks_strickler: float = 104.0
    v_filling_ms: float = 0.5
    delta_p_admiss_mce: float = 3.0
    q_nominal_water_m3s: float = 5.3
    target_drain_time_hours: float = 2.0
    drain_discharge_k: float = 0.70
    air_catalog_config: str = DEFAULT_AIR_CATALOG_CONFIG

    air_valves: List[AirValvePoint] = field(default_factory=list)
    drains: List[DrainPoint] = field(default_factory=list)

    def calculate_all(self):
        """Recalcule tous les points hauts et tous les points bas."""
        for v in self.air_valves:
            v.calculate(
                ks_strickler=self.ks_strickler,
                v_filling_ms=self.v_filling_ms,
                delta_p_admiss_mce=self.delta_p_admiss_mce,
                q_nom_eau_m3s=self.q_nominal_water_m3s,
                catalog_config=self.air_catalog_config,
            )

        for d in self.drains:
            d.calculate(
                target_time_hours=self.target_drain_time_hours,
                discharge_coeff_k=self.drain_discharge_k
            )

    def get_summary_stats(self) -> Dict[str, Any]:
        """Retourne des indicateurs synthétiques clés."""
        total_valves = len(self.air_valves)
        valves_compliant = sum(1 for v in self.air_valves if v.is_compliant)
        total_drains = len(self.drains)
        drains_compliant = sum(1 for d in self.drains if d.is_compliant)

        total_air_max_m3s = sum(v.q_air_max_m3s for v in self.air_valves)
        total_water_vol_m3 = sum(d.volume_water_m3 for d in self.drains)

        mat_info = PIPE_MATERIALS.get(self.pipe_material, PIPE_MATERIALS["PRV (Polyester Renforcé Verre)"])
        e_pa = mat_info["E_Pa"]
        wave_speed = calculate_allievi_wave_speed(
            d_inner_m=self.dn_main_conduite_m,
            thickness_m=self.pipe_thickness_m,
            e_young_pa=e_pa
        )

        return {
            "total_air_valves": total_valves,
            "air_valves_compliant": valves_compliant,
            "air_valves_non_compliant": total_valves - valves_compliant,
            "total_drains": total_drains,
            "drains_compliant": drains_compliant,
            "drains_non_compliant": total_drains - drains_compliant,
            "wave_speed_allievi_ms": round(wave_speed, 1),
            "total_water_volume_m3": round(total_water_vol_m3, 1),
            "max_air_intake_m3s": round(max([v.q_air_max_m3s for v in self.air_valves], default=0.0), 2)
        }

    def auto_generate_drains_from_valves(self, default_dn_retained_mm: int = 400) -> int:
        """
        Déduit et génère automatiquement la liste des vidanges (points bas)
        à partir des points amont et aval définis sur les ventouses.
        Évite la double saisie fastidieuse sur les longs profils en long.
        """
        if not self.air_valves:
            return 0

        # Dictionnaire des points bas uniques {pm: {"z": z, "dn_m": dn}}
        drain_dict: Dict[float, Dict[str, float]] = {}
        for v in self.air_valves:
            if v.pm_amont is not None:
                pm_key = round(float(v.pm_amont), 2)
                z = float(v.z_amont) if v.z_amont is not None else 0.0
                if pm_key not in drain_dict:
                    drain_dict[pm_key] = {"z": z, "dn_m": v.dn_conduite_m}
            if v.pm_aval is not None:
                pm_key = round(float(v.pm_aval), 2)
                z = float(v.z_aval) if v.z_aval is not None else 0.0
                if pm_key not in drain_dict:
                    drain_dict[pm_key] = {"z": z, "dn_m": v.dn_conduite_m}

        if not drain_dict:
            return 0

        sorted_drain_pms = sorted(drain_dict.keys())
        sorted_valves = sorted(self.air_valves, key=lambda x: x.pm)

        # Conserver les diamètres retenus s'il existait déjà des vidanges au même PM
        existing_retained = {round(d.pm, 2): d.dn_retained_mm for d in self.drains}

        new_drains: List[DrainPoint] = []
        for idx, pm in enumerate(sorted_drain_pms, 1):
            info = drain_dict[pm]

            # Recherche de la ventouse immédiatement amont (PM_v < PM_drain)
            valves_up = [v for v in sorted_valves if v.pm < pm]
            v_up = max(valves_up, key=lambda v: v.pm) if valves_up else None

            # Recherche de la ventouse immédiatement aval (PM_v > PM_drain)
            valves_down = [v for v in sorted_valves if v.pm > pm]
            v_down = min(valves_down, key=lambda v: v.pm) if valves_down else None

            retained_dn = existing_retained.get(pm, default_dn_retained_mm)

            drain = DrainPoint(
                id=idx,
                pm=pm,
                z_terrain=info["z"],
                dn_conduite_m=info["dn_m"],
                pm_amont=v_up.pm if v_up else None,
                z_amont=v_up.z_terrain if v_up else None,
                pm_aval=v_down.pm if v_down else None,
                z_aval=v_down.z_terrain if v_down else None,
                dn_retained_mm=retained_dn
            )
            new_drains.append(drain)

        self.drains = new_drains
        self.calculate_all()
        return len(new_drains)

    def reconcile_topology(self):
        """
        Harmonise et réconcilie la topologie entre ventouses et vidanges :
        si les PM amont/aval d'une vidange ne correspondent pas à des ventouses existantes
        (ou ont été saisis par erreur avec des cotes au lieu de PM), ils sont réalignés sur les vraies ventouses.
        """
        if not self.air_valves or not self.drains:
            return

        sorted_valves = sorted(self.air_valves, key=lambda v: v.pm)
        valve_pms = {round(v.pm, 2): v for v in sorted_valves}

        for d in self.drains:
            # Vérifier si pm_amont est une vraie ventouse
            up_match = valve_pms.get(round(d.pm_amont, 2)) if d.pm_amont is not None else None
            if not up_match:
                valves_up = [v for v in sorted_valves if v.pm < d.pm]
                if valves_up:
                    best_up = max(valves_up, key=lambda v: v.pm)
                    d.pm_amont = best_up.pm
                    d.z_amont = best_up.z_terrain

            # Vérifier si pm_aval est une vraie ventouse
            down_match = valve_pms.get(round(d.pm_aval, 2)) if d.pm_aval is not None else None
            if not down_match:
                valves_down = [v for v in sorted_valves if v.pm > d.pm]
                if valves_down:
                    best_down = min(valves_down, key=lambda v: v.pm)
                    d.pm_aval = best_down.pm
                    d.z_aval = best_down.z_terrain

        self.calculate_all()

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise le projet (paramètres, points et résultats calculés) en dictionnaire JSON-compatible."""
        return asdict(self)

    @classmethod
    def _filter_fields(cls, datacls, data: Dict[str, Any]) -> Dict[str, Any]:
        allowed = {f.name for f in fields(datacls)}
        return {k: v for k, v in (data or {}).items() if k in allowed}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HydraulicProject":
        """Reconstruit un projet à partir d'un dictionnaire et recalcule les résultats."""
        data = data or {}
        proj_fields = {f.name for f in fields(cls)}
        base = {k: v for k, v in data.items() if k in proj_fields and k not in ("air_valves", "drains")}
        project = cls(**cls._filter_fields(cls, base))

        raw_valves = data.get("air_valves") or []
        valves: List[AirValvePoint] = []
        for item in raw_valves:
            try:
                valves.append(AirValvePoint(**cls._filter_fields(AirValvePoint, item)))
            except Exception:
                continue
        project.air_valves = valves

        raw_drains = data.get("drains") or []
        drains: List[DrainPoint] = []
        for item in raw_drains:
            try:
                drains.append(DrainPoint(**cls._filter_fields(DrainPoint, item)))
            except Exception:
                continue
        project.drains = drains

        project.calculate_all()
        return project

    def save_to_file(self, filepath: str):
        """Enregistre le projet au format JSON (conserve paramètres, imports et choix retenus)."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)) or ".", exist_ok=True)
        payload = {
            "format": "mk-st-venant-project",
            "version": 1,
            "project": self.to_dict(),
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "HydraulicProject":
        """Charge un projet depuis un fichier JSON et recalcule les résultats."""
        with open(filepath, "r", encoding="utf-8") as f:
            payload = json.load(f)
        data = payload.get("project", payload) if isinstance(payload, dict) else {}
        return cls.from_dict(data if isinstance(data, dict) else {})
