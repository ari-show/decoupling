"""2-Exp-57: do interaction-component spikes co-fire on the same product, many stores, same day?

Subcommands
-----------
extract   Build the held-out sets (C1, C2), run the 2-Exp-44 checkpoints on them and
          save component arrays. Also checks that re-running the seed-17 checkpoint on the
          2-Exp-44 test cache reproduces the saved interaction component.
analyze   Compute the pre-registered statistics (P1-P4) plus descriptive ones for every
          set and seed. No training.
figures   Case-study, date-profile and event hour-profile figures (needs matplotlib).

The statistic and thresholds are fixed in doc/2-Exp-57_interaction_cofiring_campaigns.md
and configs/2-Exp-57_interaction_cofiring_freshretailnet.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

LOGGER = logging.getLogger("2-Exp-57")

STATIC_COLS = ["city_id", "store_id", "management_group_id", "first_category_id", "second_category_id", "third_category_id", "product_id"]
COV_COLS = ["discount", "holiday_flag", "activity_flag", "precpt", "avg_temperature", "avg_humidity", "avg_wind_level"]
SET_START = {"E_exploratory": "2024-05-29", "C1_heldout_same_dates": "2024-05-29", "C2_heldout_unseen_dates": "2024-04-27"}


def load_json(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def seed_dir(cfg: dict[str, Any], seed: int) -> Path:
    return Path(cfg["source_runs"]) / f"seed_{seed}" / cfg["variant"]


# --------------------------------------------------------------------------- extract


def _dataset_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    run_cfg = load_json(seed_dir(cfg, cfg["seeds"][0]) / "config.json")["config"]
    data_cfg = dict(run_cfg["dataset"])
    data_cfg["series_days"] = int(data_cfg["history_days"]) + int(data_cfg["forecast_days"])
    data_cfg["forecast_windows"] = int(data_cfg["forecast_days"])
    data_cfg["subgroup_target"] = data_cfg.get("subgroup_target", "city_id")
    return data_cfg


def _build_set(spec: dict[str, Any], data_cfg: dict[str, Any], frames: dict[str, pd.DataFrame]):
    from decoupled_ts.data import frame_to_examples, _examples_to_tensors

    merged = dict(data_cfg)
    merged["series_start_offset"] = int(spec["series_start_offset"])
    if spec["mode"] == "eval_tail":
        examples = frame_to_examples(frames["train"], merged, max_series=int(spec["max_series"]), target_df=frames["eval"])
    elif spec["mode"] == "train_window":
        start = pd.Timestamp(spec["window_start"])
        end = start + pd.Timedelta(days=int(merged["series_days"]) - 1)
        dt = pd.to_datetime(frames["train"]["dt"])
        window = frames["train"][(dt >= start) & (dt <= end)]
        examples = frame_to_examples(window, merged, max_series=int(spec["max_series"]))
    else:
        raise ValueError(spec["mode"])
    return _examples_to_tensors(examples)


def _check_disjoint(tensors: dict[str, Any], data_cfg: dict[str, Any]) -> int:
    """Return the number of (store, product) pairs shared with the 2-Exp-44 train/valid pool."""
    import torch

    cache = Path(data_cfg["cache_dir"]) / "train_self-target_d30_w24_f2_city_id_store_id-product_id_7500.pt"
    pool = torch.load(cache, map_location="cpu", weights_only=False)["static_ids"].numpy()
    pool_keys = {(int(s), int(p)) for s, p in pool[:, [1, 6]]}
    ids = tensors["static_ids"].numpy()
    return int(sum((int(s), int(p)) in pool_keys for s, p in ids[:, [1, 6]]))


def _predict(ckpt_path: Path, dataset, input_dim: int, device) -> dict[str, np.ndarray]:
    import torch
    from decoupled_ts.residual_experiments import make_residual_model, predict_residuals
    from decoupled_ts.train import make_loader

    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    config, variant = ckpt["config"], ckpt["variant"]
    model = make_residual_model(config, variant, input_dim, int(config["dataset"]["history_days"]), 24).to(device)
    # 2-Exp-44 predates 2-Exp-45's AxisEncoder refactor, which renamed the MLP hour encoder's
    # Linear-ReLU-Linear from `net.{0,2}` to `proj.0` / `head` without changing the computation.
    rename = {"hour_encoder.net.0.": "hour_encoder.proj.0.", "hour_encoder.net.2.": "hour_encoder.head."}
    state = {}
    for key, value in ckpt["model"].items():
        for old, new in rename.items():
            if key.startswith(old):
                key = new + key[len(old) :]
        state[key] = value
    model.load_state_dict(state)
    loader_cfg = {**config, "train": {**config["train"], "num_workers": 0, "pin_memory": False}}
    with torch.no_grad():
        return predict_residuals(model, make_loader(dataset, loader_cfg, shuffle=False), config, device)


def _pack(arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    grid = arrays["grid"]
    return {
        "interaction": arrays["interaction_component"].astype(np.float32),
        "day": arrays["day_component"].astype(np.float32),
        "hour": arrays["hour_component"].astype(np.float32),
        "residual": arrays["residual"].astype(np.float32),
        "observed": arrays["observed"].astype(np.float32),
        "sales": arrays["sales"].astype(np.float32),
        "static_ids": arrays["static_ids"].astype(np.int64),
        "day_covariates": grid[:, :, 0, 2 : 2 + len(COV_COLS)].astype(np.float32),
    }


def cmd_extract(cfg: dict[str, Any]) -> None:
    import torch
    from decoupled_ts.data import FreshRetailNetSeries, infer_input_dim, load_freshretailnet_frame
    from decoupled_ts.train import resolve_device

    data_cfg = _dataset_cfg(cfg)
    input_dim = infer_input_dim(data_cfg)
    device = resolve_device("auto")
    out_root = Path(cfg["output_dir"])
    out_root.mkdir(parents=True, exist_ok=True)
    checks: dict[str, Any] = {}

    # Reproducibility: seed-17 checkpoint on the 2-Exp-44 test cache must give the saved component.
    test = FreshRetailNetSeries.from_config(data_cfg, data_cfg["eval_split"], max_series=int(data_cfg["max_eval_series"]))
    s0 = seed_dir(cfg, cfg["seeds"][0])
    rerun = _predict(s0 / "best.pt", test, input_dim, device)["interaction_component"]
    saved = np.load(s0 / "interaction_component.npy")
    checks["repro_max_abs_diff"] = float(np.max(np.abs(rerun - saved)))
    checks["repro_rel_rms_diff"] = float(np.sqrt(np.mean((rerun - saved) ** 2)) / np.sqrt(np.mean(saved**2)))
    LOGGER.info("reproducibility: %s", checks)

    frames = {"train": load_freshretailnet_frame(data_cfg, data_cfg["train_split"]), "eval": load_freshretailnet_frame(data_cfg, data_cfg["eval_split"])}
    for spec in cfg["sets"]:
        if spec["kind"] != "extract":
            continue
        set_dir = out_root / spec["name"]
        set_dir.mkdir(parents=True, exist_ok=True)
        tensors = _build_set(spec, data_cfg, frames)
        overlap = _check_disjoint(tensors, data_cfg)
        checks[f"{spec['name']}_n_series"] = int(tensors["x"].shape[0])
        checks[f"{spec['name']}_overlap_with_train_valid"] = overlap
        LOGGER.info("%s: n=%d overlap=%d", spec["name"], tensors["x"].shape[0], overlap)
        if overlap:
            raise RuntimeError(f"{spec['name']} shares {overlap} series with the train/valid pool")
        np.savez(set_dir / "inputs.npz", static_ids=tensors["static_ids"].numpy())
        dataset = FreshRetailNetSeries(tensors)
        for seed in cfg["seeds"]:
            arrays = _predict(seed_dir(cfg, seed) / "best.pt", dataset, input_dim, device)
            (set_dir / f"seed_{seed}").mkdir(exist_ok=True)
            np.savez(set_dir / f"seed_{seed}" / "arrays.npz", **_pack(arrays))
            LOGGER.info("%s seed %d saved", spec["name"], seed)
        del tensors, dataset
        torch.cuda.empty_cache()
    with (out_root / "extract_checks.json").open("w", encoding="utf-8") as f:
        json.dump(checks, f, indent=2)


# --------------------------------------------------------------------------- analyze


def load_set(cfg: dict[str, Any], set_name: str, seed: int) -> dict[str, np.ndarray]:
    if set_name == "E_exploratory":
        d = seed_dir(cfg, seed)
        return {
            "interaction": np.load(d / "interaction_component.npy"),
            "residual": np.load(d / "residual.npy"),
            "observed": np.load(d / "observed.npy"),
            "sales": np.load(d / "sales.npy"),
            "static_ids": np.load(d / "static_ids.npy"),
            "day_covariates": np.load(d / "day_covariates.npy"),
            "hour": np.load(d / "hour_component.npy"),
        }
    with np.load(Path(cfg["output_dir"]) / set_name / f"seed_{seed}" / "arrays.npz") as z:
        return {k: z[k] for k in z.files}


def amplitude(values: np.ndarray, observed: np.ndarray, min_hours: int) -> np.ndarray:
    n_obs = observed.sum(2)
    amp = np.sqrt((values**2 * observed).sum(2) / np.maximum(n_obs, 1))
    amp[n_obs < min_hours] = np.nan
    return amp


def empirical_interaction(residual: np.ndarray, observed: np.ndarray) -> np.ndarray:
    r = np.where(observed > 0, residual, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        emp = r - np.nanmean(r, 2, keepdims=True) - np.nanmean(r, 1, keepdims=True) + np.nanmean(r, (1, 2), keepdims=True)
    return np.nan_to_num(emp)


def zscore_within(amp: np.ndarray, min_days: int) -> np.ndarray:
    warnings.filterwarnings("ignore", "Mean of empty slice|Degrees of freedom", RuntimeWarning)
    valid = np.isfinite(amp)
    keep = valid.sum(1) >= min_days
    mu = np.nanmean(np.where(valid, amp, np.nan), 1, keepdims=True)
    sd = np.nanstd(np.where(valid, amp, np.nan), 1, keepdims=True)
    z = (amp - mu) / np.where(sd > 1e-12, sd, np.nan)
    z[~keep] = np.nan
    return z


def _demean_by(values: np.ndarray, keys: np.ndarray) -> np.ndarray:
    """Subtract the NaN-aware mean of ``values`` within each integer key (same shape)."""
    flat, k = values.ravel(), keys.ravel()
    ok = np.isfinite(flat)
    size = int(k.max()) + 1
    s = np.bincount(k[ok], weights=flat[ok], minlength=size)
    c = np.bincount(k[ok], minlength=size)
    mean = s / np.maximum(c, 1)
    return (flat - mean[k]).reshape(values.shape)


class Layout:
    """Integer keys for the fixed-effect removals and the co-firing groupings."""

    def __init__(self, static_ids: np.ndarray, start: str, n_days: int, min_group: int):
        n = static_ids.shape[0]
        self.n, self.d = n, n_days
        dates = pd.date_range(start, periods=n_days)
        self.dates = dates
        dow = dates.dayofweek.to_numpy()
        day = np.arange(n_days)
        city = np.unique(static_ids[:, 0], return_inverse=True)[1]
        self.product = np.unique(static_ids[:, 6], return_inverse=True)[1]
        self.city_date = (city[:, None] * n_days + day[None, :]).astype(np.int64)
        self.product_dow = (self.product[:, None] * 7 + dow[None, :]).astype(np.int64)
        self.groups: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for name, col in (("product", 6), ("store", 1), ("third_category", 5)):
            g = np.unique(static_ids[:, col], return_inverse=True)[1]
            size = np.bincount(g)
            eligible = size[g] >= min_group
            keys = np.where(eligible[:, None], g[:, None] * n_days + day[None, :], -1).astype(np.int64)
            self.groups[name] = (keys, eligible)

    def remove(self, z: np.ndarray, effects: list[str]) -> np.ndarray:
        out = z
        for eff in effects:
            out = _demean_by(out, self.city_date if eff == "city_date" else self.product_dow)
        return out

    def share(self, z: np.ndarray, group: str) -> float:
        keys, _ = self.groups[group]
        flat, k = z.ravel(), keys.ravel()
        ok = np.isfinite(flat) & (k >= 0)
        size = int(k.max()) + 1
        s = np.bincount(k[ok], weights=flat[ok], minlength=size)
        c = np.bincount(k[ok], minlength=size)
        num = np.sum(s[c > 0] ** 2 / c[c > 0])
        den = np.sum(flat[ok] ** 2)
        return float(num / den)


def permute_days(z: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    order = np.argsort(rng.random(z.shape), axis=1)
    return np.take_along_axis(z, order, 1)


def cofiring_test(z: np.ndarray, lay: Layout, st: dict[str, Any], groups: list[str]) -> dict[str, float]:
    rng = np.random.default_rng(int(st["permutation_seed"]))
    eff = st["remove_effects"]
    zr = lay.remove(z, eff)
    obs = {g: lay.share(zr, g) for g in groups}
    null = {g: [] for g in groups}
    for _ in range(int(st["n_permutations"])):
        zp = lay.remove(permute_days(z, rng), eff)
        for g in groups:
            null[g].append(lay.share(zp, g))
    out: dict[str, float] = {}
    for g in groups:
        nv = np.asarray(null[g])
        out[f"S_{g}"] = obs[g]
        out[f"S_{g}_null_mean"] = float(nv.mean())
        out[f"S_{g}_null_sd"] = float(nv.std())
        out[f"R_{g}"] = obs[g] / float(nv.mean())
        out[f"p_{g}"] = float((1 + np.sum(nv >= obs[g])) / (len(nv) + 1))
    return out


def covariates(arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    cov = arrays["day_covariates"]
    act = cov[:, :, COV_COLS.index("activity_flag")]
    disc = cov[:, :, COV_COLS.index("discount")]
    switch = np.zeros_like(act)
    switch[:, 1:] = np.abs(np.diff(act, axis=1))
    return {
        "activity_flag": act,
        "discount": disc,
        "abs_discount_dev": np.abs(disc - np.median(disc, 1, keepdims=True)),
        "activity_switch": switch,
        "stockout_fraction": 1.0 - arrays["observed"].mean(2),
    }


def explanation(z: np.ndarray, arrays: dict[str, np.ndarray], lay: Layout, st: dict[str, Any], names: list[str], cof: dict[str, float]) -> dict[str, float]:
    eff = st["remove_effects"]
    zr = lay.remove(z, eff)
    covs = covariates(arrays)
    valid = np.isfinite(zr)
    cols = []
    for name in names:
        c = np.where(valid, covs[name], np.nan)
        c = c - np.nanmean(c, 1, keepdims=True)
        cols.append(lay.remove(c, eff)[valid])
    X = np.column_stack(cols + [np.ones(valid.sum())])
    y = zr[valid]
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = np.full_like(zr, np.nan)
    resid[valid] = y - X @ beta
    s_after = lay.share(resid, "product")
    excess = cof["S_product"] - cof["S_product_null_mean"]
    out = {
        "explain_r2": float(1.0 - np.var(resid[valid]) / np.var(y)),
        "S_product_after": s_after,
        "explained_fraction": float((cof["S_product"] - s_after) / excess) if excess > 0 else float("nan"),
    }
    for name, b in zip(names, beta[:-1]):
        out[f"beta_{name}"] = float(b)
    return out


def posthoc_volume(z: np.ndarray, arrays: dict[str, np.ndarray], lay: Layout, st: dict[str, Any], cof: dict[str, float]) -> dict[str, float]:
    """Post hoc (not pre-registered): is the co-firing a multiplicative volume effect?

    Regress the same Z on the within-series-centred log daily volume (observed-hour mean sales)
    and report the explained fraction of the product x day excess, plus how closely the
    event-day interaction profile follows the series' own hour component.
    """
    eff = st["remove_effects"]
    zr = lay.remove(z, eff)
    obs, sales = arrays["observed"], arrays["sales"]
    vol = np.log1p((sales * obs).sum(2) / np.maximum(obs.sum(2), 1))
    valid = np.isfinite(zr)
    v = np.where(valid, vol, np.nan)
    v = lay.remove(v - np.nanmean(v, 1, keepdims=True), eff)
    X = np.column_stack([v[valid], np.ones(valid.sum())])
    beta, *_ = np.linalg.lstsq(X, zr[valid], rcond=None)
    resid = np.full_like(zr, np.nan)
    resid[valid] = zr[valid] - X @ beta
    excess = cof["S_product"] - cof["S_product_null_mean"]
    out = {
        "posthoc_corr_z_volume": float(np.corrcoef(zr[valid], v[valid])[0, 1]),
        "posthoc_volume_explained_fraction": float((cof["S_product"] - lay.share(resid, "product")) / excess) if excess > 0 else float("nan"),
    }
    if "hour" in arrays:
        top = valid & (zr > 1.0)
        n_idx, d_idx = np.where(top)
        inter = arrays["interaction"][n_idx, d_idx]
        hour = arrays["hour"][n_idx, d_idx]
        a = inter - inter.mean(1, keepdims=True)
        b = hour - hour.mean(1, keepdims=True)
        r = (a * b).sum(1) / np.sqrt((a**2).sum(1) * (b**2).sum(1) + 1e-12)
        out["posthoc_corr_interaction_hour_profile_on_fire"] = float(np.nanmedian(r))
    return out


def product_day_events(z: np.ndarray, arrays: dict[str, np.ndarray], lay: Layout, st: dict[str, Any], ev: dict[str, Any]) -> pd.DataFrame:
    zr = lay.remove(z, st["remove_effects"])
    covs = covariates(arrays)
    n, d = zr.shape
    prod = np.repeat(lay.product, d)
    day = np.tile(np.arange(d), n)
    df = pd.DataFrame(
        {
            "product": prod,
            "day": day,
            "z": zr.ravel(),
            "act": covs["activity_flag"].ravel(),
            "disc": covs["discount"].ravel(),
            "stockout": covs["stockout_fraction"].ravel(),
        }
    )
    df["fire"] = (df.z > 1.0).astype(float).where(df.z.notna())
    prod_act = df.groupby("product").act.mean()
    prod_disc_med = df.groupby("product").disc.median()
    cell = df.groupby(["product", "day"]).agg(
        n_valid=("z", "count"),
        n_series=("z", "size"),
        mean_z=("z", "mean"),
        frac_fire=("fire", "mean"),
        act=("act", "mean"),
        disc=("disc", "mean"),
        stockout=("stockout", "mean"),
    ).reset_index()
    cell["act_window"] = cell["product"].map(prod_act)
    cell["disc_window_median"] = cell["product"].map(prod_disc_med)
    cell["marked_activity"] = cell.act - cell.act_window >= float(ev["marked_activity_jump"])
    cell["marked_discount"] = cell.disc <= cell.disc_window_median - float(ev["marked_discount_drop"])
    cell["marked"] = cell.marked_activity | cell.marked_discount
    cell = cell[cell.n_valid >= int(ev["min_series"])].copy()
    cell["event"] = (cell.mean_z >= float(ev["min_mean_z"])) & (cell.frac_fire >= float(ev["min_frac_z_above_1"]))
    cell["date"] = lay.dates[cell.day.to_numpy()].strftime("%Y-%m-%d")
    uniq_products = np.unique(arrays["static_ids"][:, 6])
    cell["product_id"] = uniq_products[cell["product"].to_numpy()]
    return cell


def event_metrics(cell: pd.DataFrame) -> dict[str, float]:
    base = float(cell.marked.mean())
    ev = cell[cell.event]
    p_marked_event = float(ev.marked.mean()) if len(ev) else float("nan")
    marked = cell[cell.marked]
    return {
        "n_product_days": int(len(cell)),
        "n_events": int(len(ev)),
        "event_rate": float(cell.event.mean()),
        "p_marked": base,
        "p_marked_given_event": p_marked_event,
        "enrichment": p_marked_event / base if base > 0 else float("nan"),
        "unmarked_event_fraction": 1.0 - p_marked_event if len(ev) else float("nan"),
        "recall_marked": float(marked.event.mean()) if len(marked) else float("nan"),
        "event_stockout_minus_all": float(ev.stockout.mean() - cell.stockout.mean()) if len(ev) else float("nan"),
    }


def date_profile(z: np.ndarray, lay: Layout) -> np.ndarray:
    return np.nanmean(z, 0)


def cmd_analyze(cfg: dict[str, Any]) -> None:
    st, ev, pre = cfg["statistic"], cfg["events"], cfg["preregistered"]
    fig_dir = Path(cfg["figure_dir"])
    fig_dir.mkdir(parents=True, exist_ok=True)
    rows, event_tables, date_rows = [], [], []
    for spec in cfg["sets"]:
        name = spec["name"]
        if cfg.get("_only_sets") and name not in cfg["_only_sets"]:
            continue
        model_events: dict[int, set] = {}
        for seed in cfg["seeds"]:
            arrays = load_set(cfg, name, seed)
            obs = arrays["observed"]
            lay = Layout(arrays["static_ids"], SET_START[name], obs.shape[1], int(st["min_group_series"]))
            amp_model = amplitude(arrays["interaction"], obs, int(st["min_observed_hours"]))
            amp_emp = amplitude(empirical_interaction(arrays["residual"], obs), obs, int(st["min_observed_hours"]))
            z_model = zscore_within(amp_model, int(st["min_valid_days"]))
            z_emp = zscore_within(amp_emp, int(st["min_valid_days"]))
            row: dict[str, Any] = {"set": name, "role": spec["role"], "seed": seed, "n_series": int(obs.shape[0])}
            row["n_series_kept"] = int(np.isfinite(z_model).any(1).sum())
            ok = np.isfinite(amp_model) & np.isfinite(amp_emp)
            row["corr_model_empirical_amp"] = float(np.corrcoef(amp_model[ok], amp_emp[ok])[0, 1])
            cof = cofiring_test(z_model, lay, st, ["product", "store", "third_category"])
            row.update(cof)
            row.update(explanation(z_model, arrays, lay, st, cfg["explanation"]["covariates"], cof))
            row.update(posthoc_volume(z_model, arrays, lay, st, cof))
            cell = product_day_events(z_model, arrays, lay, st, ev)
            row.update(event_metrics(cell))
            emp_cof = cofiring_test(z_emp, lay, st, ["product", "store"])
            row.update({f"emp_{k}": v for k, v in emp_cof.items()})
            emp_cell = product_day_events(z_emp, arrays, lay, st, ev)
            row.update({f"emp_{k}": v for k, v in event_metrics(emp_cell).items()})
            m_ev = set(map(tuple, cell.loc[cell.event, ["product", "day"]].to_numpy()))
            e_ev = set(map(tuple, emp_cell.loc[emp_cell.event, ["product", "day"]].to_numpy()))
            row["event_jaccard_model_empirical"] = len(m_ev & e_ev) / max(len(m_ev | e_ev), 1)
            model_events[seed] = m_ev
            # pre-registered checks
            row["P1_pass"] = bool(row["R_product"] >= pre["P1_product_ratio_min"] and row["p_product"] < pre["P1_p_max"])
            row["P2_pass"] = bool(row["R_product"] > row["R_store"])
            row["P3_below_half"] = bool(row["explained_fraction"] < pre["P3_explained_fraction_threshold"])
            row["P4_enrichment_pass"] = bool(row["enrichment"] >= pre["P4_enrichment_min"])
            row["P4_unmarked_majority"] = bool(row["unmarked_event_fraction"] > pre["P4_unmarked_majority"])
            rows.append(row)
            LOGGER.info("%s seed %d: R_product=%.3f p=%.4f R_store=%.3f explained=%.3f enrich=%.2f unmarked=%.2f", name, seed, row["R_product"], row["p_product"], row["R_store"], row["explained_fraction"], row["enrichment"], row["unmarked_event_fraction"])
            ev_tab = cell[cell.event].copy()
            ev_tab.insert(0, "seed", seed)
            ev_tab.insert(0, "set", name)
            event_tables.append(ev_tab)
            prof = date_profile(z_model, lay)
            for i, dte in enumerate(lay.dates):
                date_rows.append({"set": name, "seed": seed, "date": dte.strftime("%Y-%m-%d"), "mean_z": float(prof[i]),
                                  "holiday": float(np.mean(arrays["day_covariates"][:, i, COV_COLS.index("holiday_flag")])),
                                  "activity": float(np.mean(arrays["day_covariates"][:, i, COV_COLS.index("activity_flag")]))})
        seeds = cfg["seeds"]
        jac = [len(model_events[a] & model_events[b]) / max(len(model_events[a] | model_events[b]), 1) for i, a in enumerate(seeds) for b in seeds[i + 1 :]]
        for row in rows:
            if row["set"] == name:
                row["event_jaccard_across_seeds_mean"] = float(np.mean(jac))

    by_seed = pd.DataFrame(rows)
    by_seed.to_csv(fig_dir / "metrics_by_seed.csv", index=False)
    pd.concat(event_tables).to_csv(fig_dir / "events.csv", index=False)
    pd.DataFrame(date_rows).to_csv(fig_dir / "date_profile.csv", index=False)

    summary: dict[str, Any] = {}
    numeric = by_seed.select_dtypes(include=[np.number, bool]).columns.drop("seed")
    for name, grp in by_seed.groupby("set", sort=False):
        s: dict[str, Any] = {}
        for col in numeric:
            vals = grp[col].astype(float)
            s[col] = {"mean": float(vals.mean()), "sd": float(vals.std(ddof=1)), "min": float(vals.min()), "max": float(vals.max())}
        s["verdict"] = {
            "P1_all_seeds": bool(grp.P1_pass.all()),
            "P2_all_seeds": bool(grp.P2_pass.all()),
            "P3_below_half_seeds": int(grp.P3_below_half.sum()),
            "P4_enrichment_all_seeds": bool(grp.P4_enrichment_pass.all()),
            "P4_unmarked_majority_seeds": int(grp.P4_unmarked_majority.sum()),
        }
        summary[name] = s
    extract_checks = Path(cfg["output_dir"]) / "extract_checks.json"
    if extract_checks.exists():
        summary["extract_checks"] = load_json(extract_checks)
    with (fig_dir / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    LOGGER.info("verdicts: %s", {k: v["verdict"] for k, v in summary.items() if "verdict" in v})


# --------------------------------------------------------------------------- figures


INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]  # reference categorical slots 1-3 (validated all-pairs)


def _style(plt) -> None:
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.edgecolor": INK2,
            "axes.labelcolor": INK2,
            "xtick.color": INK2,
            "ytick.color": INK2,
            "axes.titlecolor": INK,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "lines.linewidth": 2.0,
            "figure.facecolor": "white",
        }
    )


def _profiles(arrays: dict[str, np.ndarray], idx: np.ndarray, day: int):
    """Per-series hourly profiles (sales normalised by the series' observed mean) for one day vs the others."""
    sales, obs, inter = arrays["sales"][idx], arrays["observed"][idx], arrays["interaction"][idx]
    scale = (sales * obs).sum((1, 2)) / np.maximum(obs.sum((1, 2)), 1)
    norm = sales / np.maximum(scale, 1e-6)[:, None, None]
    other = np.ones(sales.shape[1], bool)
    other[day] = False
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        ev_sales = np.nanmean(np.where(obs[:, day] > 0, norm[:, day], np.nan), 0)
        ot_sales = np.nanmean(np.where(obs[:, other] > 0, norm[:, other], np.nan), (0, 1))
    return ev_sales, ot_sales, inter[:, day].mean(0), inter[:, other].mean((0, 1)), 1 - obs[:, day].mean(0), 1 - obs[:, other].mean((0, 1))


def cmd_figures(cfg: dict[str, Any]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.dates  # noqa: F401 - used through matplotlib.dates
    import matplotlib.pyplot as plt

    _style(plt)
    fig_dir = Path(cfg["figure_dir"])
    events = pd.read_csv(fig_dir / "events.csv")
    hours = np.arange(24)

    # 1. case-study events
    cs = cfg["case_study"]
    arrays = load_set(cfg, cs["set"], int(cs["seed"]))
    sub = events[(events.set == cs["set"]) & (events.seed == int(cs["seed"]))].sort_values("mean_z", ascending=False)
    sub = sub.drop_duplicates("product_id").head(int(cs["n_events"]))
    fig, axes = plt.subplots(2, len(sub), figsize=(2.6 * len(sub), 4.6), sharex=True, squeeze=False)
    for j, (_, ev) in enumerate(sub.iterrows()):
        idx = np.where(arrays["static_ids"][:, 6] == ev.product_id)[0]
        day = int(ev.day)
        ev_s, ot_s, ev_i, ot_i, _, _ = _profiles(arrays, idx, day)
        ax = axes[0, j]
        ax.plot(hours, ot_s, color=INK2, lw=1.5, label="other days")
        ax.plot(hours, ev_s, color=SERIES[0], label="event day")
        mark = "marked" if ev.marked else "no campaign record"
        ax.set_title(
            f"product {int(ev.product_id)} · {ev.date[5:]}\n{int(round(ev.frac_fire * ev.n_valid))}/{int(ev.n_valid)} stores fire · {mark}\n"
            f"activity {ev.act:.2f} ({ev.act_window:.2f}) · discount {ev.disc:.2f} ({ev.disc_window_median:.2f})",
            fontsize=7.5,
            loc="left",
        )
        ax2 = axes[1, j]
        ax2.axhline(0, color=INK2, lw=0.8)
        ax2.plot(hours, ot_i, color=INK2, lw=1.5)
        ax2.plot(hours, ev_i, color=SERIES[0])
        ax2.set_xticks([0, 6, 12, 18, 23])
        ax2.set_xlabel("hour")
    axes[0, 0].set_ylabel("sales / series mean")
    axes[1, 0].set_ylabel("interaction component")
    fig.legend(*axes[0, 0].get_legend_handles_labels(), fontsize=8, frameon=False, loc="upper right", ncol=2)
    fig.suptitle(f"Top co-firing product-days ({cs['set']}, seed {cs['seed']}): store average; brackets = product's window average / median", fontsize=9, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(fig_dir / "case_events.png", dpi=160)
    plt.close(fig)

    # 2. date profile (city x date common part, before the removals)
    dp = pd.read_csv(fig_dir / "date_profile.csv")
    names = [s["name"] for s in cfg["sets"]]
    fig, axes = plt.subplots(len(names), 1, figsize=(8, 2.0 * len(names)), squeeze=False)
    for ax, name in zip(axes[:, 0], names):
        g = dp[dp.set == name].groupby("date").agg(m=("mean_z", "mean"), lo=("mean_z", "min"), hi=("mean_z", "max"), hol=("holiday", "mean")).reset_index()
        x = pd.to_datetime(g.date)
        for xi, h in zip(x, g.hol):
            if h > 0.5:
                ax.axvspan(xi - pd.Timedelta(hours=12), xi + pd.Timedelta(hours=12), color=GRID, lw=0)
        ax.fill_between(x, g.lo, g.hi, color=SERIES[0], alpha=0.2, lw=0)
        ax.plot(x, g.m, color=SERIES[0], marker="o", ms=3)
        ax.axhline(0, color=INK2, lw=0.8)
        for label, dte in (("618", "2024-06-18"), ("Dragon Boat", "2024-06-10"), ("May Day", "2024-05-01")):
            t = pd.Timestamp(dte)
            if x.min() <= t <= x.max():
                ax.annotate(label, (t, g.m.max()), fontsize=7, color=INK2, ha="center")
        ax.set_title(name, fontsize=9, loc="left")
        ax.set_ylabel("mean z")
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%m-%d"))
    axes[-1, 0].set_xlabel("date (shaded: holiday_flag = 1; band: seed min-max)")
    fig.tight_layout()
    fig.savefig(fig_dir / "date_profile.png", dpi=160)
    plt.close(fig)

    # 3. hour profile of events: marked vs unmarked, pooled over seeds
    confirm = [s["name"] for s in cfg["sets"] if s["role"] == "confirmatory"]
    fig, axes = plt.subplots(2, len(confirm), figsize=(4.2 * len(confirm), 5.0), sharex=True, squeeze=False)
    for j, name in enumerate(confirm):
        curves = {True: ([], []), False: ([], [])}
        for seed in cfg["seeds"]:
            arr = load_set(cfg, name, seed)
            prod = arr["static_ids"][:, 6]
            for _, ev in events[(events.set == name) & (events.seed == seed)].iterrows():
                idx = np.where(prod == ev.product_id)[0]
                _, _, ev_i, ot_i, ev_so, ot_so = _profiles(arr, idx, int(ev.day))
                curves[bool(ev.marked)][0].append(ev_i - ot_i)
                curves[bool(ev.marked)][1].append(ev_so - ot_so)
        for k, (label, color) in enumerate(((True, SERIES[0]), (False, SERIES[1]))):
            inter, so = curves[label]
            if not inter:
                continue
            name_label = f"{'marked' if label else 'unmarked'} (n={len(inter)})"
            axes[0, j].plot(hours, np.mean(inter, 0), color=color, label=name_label)
            axes[1, j].plot(hours, np.mean(so, 0), color=color, label=name_label)
        for ax in axes[:, j]:
            ax.axhline(0, color=INK2, lw=0.8)
        axes[0, j].set_title(name, fontsize=9, loc="left")
        axes[1, j].set_xticks([0, 6, 12, 18, 23])
        axes[1, j].set_xlabel("hour")
        axes[0, j].legend(fontsize=7, frameon=False)
    axes[0, 0].set_ylabel("interaction: event day − other days")
    axes[1, 0].set_ylabel("stockout share: event − other")
    fig.suptitle("Event-day hourly shape, pooled over 5 seeds", fontsize=9, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(fig_dir / "event_hour_profile.png", dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["extract", "analyze", "figures"])
    parser.add_argument("--config", required=True)
    parser.add_argument("--sets", nargs="*", help="restrict analyze to these set names (debugging only)")
    parser.add_argument("--figure-dir", help="override figure_dir (debugging only)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = load_json(args.config)
    cfg["_only_sets"] = args.sets
    if args.figure_dir:
        cfg["figure_dir"] = args.figure_dir
    {"extract": cmd_extract, "analyze": cmd_analyze, "figures": cmd_figures}[args.command](cfg)


if __name__ == "__main__":
    main()
