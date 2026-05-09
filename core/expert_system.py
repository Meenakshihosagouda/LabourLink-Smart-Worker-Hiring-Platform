# ============================================================
# RULE-BASED AI EXPERT SYSTEM — Worker & Contractor Recommender
# ============================================================
# This module replaces the previous ML/RandomForest model with
# a transparent, explainable Rule-Based Expert System (RBES).
#
# No external libraries (numpy, sklearn) are required.
# All scoring is deterministic based on explicit domain rules
# and heuristic weights defined by subject-matter expertise.
#
# Public API (same as before — views.py needs zero changes):
#   predict_best_worker(rating, distance, success_rate, jobs_completed)  → float
#   predict_best_contractor(rating, success_rate, available_workers, total_projects, distance) → float
# ============================================================


# ─────────────────────────────────────────────
# HELPER: Safe normaliser  (clamp to [0, 1])
# ─────────────────────────────────────────────
def _clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


# ─────────────────────────────────────────────
# RULE SET 1 — Proximity Score
# Uses a linear decay from 0 → max_km.
# Anything beyond max_km scores 0.
# ─────────────────────────────────────────────
def _proximity_score(distance_km, max_km):
    """
    Expert Rule: Closer is always better.
    Score decays linearly from 1.0 (at 0 km) to 0.0 (at max_km).
    """
    return _clamp((max_km - distance_km) / max_km)


# ─────────────────────────────────────────────
# RULE SET 2 — Experience Tier Score (Workers)
# Domain knowledge: more completed jobs → more reliable.
# ─────────────────────────────────────────────
def _experience_tier_score(jobs_completed):
    """
    Expert Rule:
      Tier 0 (new, 0 jobs)          → 0.20  (unproven)
      Tier 1 (1–10 jobs)            → 0.50  (beginner)
      Tier 2 (11–50 jobs)           → 0.75  (competent)
      Tier 3 (51–150 jobs)          → 0.90  (experienced)
      Tier 4 (151+ jobs)            → 1.00  (expert)
    """
    if jobs_completed == 0:
        return 0.20
    elif jobs_completed <= 10:
        return 0.50
    elif jobs_completed <= 50:
        return 0.75
    elif jobs_completed <= 150:
        return 0.90
    else:
        return 1.00


# ─────────────────────────────────────────────
# RULE SET 3 — Fleet Capacity Score (Contractors)
# Domain knowledge: larger available workforce → better for bulk jobs.
# ─────────────────────────────────────────────
def _fleet_capacity_score(available_workers):
    """
    Expert Rule:
      0–4 workers   → 0.10  (very small, risky)
      5–14 workers  → 0.40  (small)
      15–29 workers → 0.70  (medium)
      30–49 workers → 0.90  (large)
      50+ workers   → 1.00  (enterprise)
    """
    if available_workers < 5:
        return 0.10
    elif available_workers < 15:
        return 0.40
    elif available_workers < 30:
        return 0.70
    elif available_workers < 50:
        return 0.90
    else:
        return 1.00


# ─────────────────────────────────────────────
# RULE SET 4 — Penalty Multipliers
# Hard domain rules that reduce scores for red-flag conditions.
# ─────────────────────────────────────────────
def _worker_penalty(rating, distance_km, jobs_completed):
    """
    Applies multiplicative penalty factors for known risk signals:
      - Very low rating (< 2.0): −20%  (quality risk)
      - Zero experience:         −15%  (reliability risk)
      - Very far (> 20 km):      −30%  (logistics risk)
    Penalties stack multiplicatively (they compound).
    """
    penalty = 1.0
    if rating < 2.0:
        penalty *= 0.80
    if jobs_completed == 0:
        penalty *= 0.85
    if distance_km > 20.0:
        penalty *= 0.70
    return penalty


def _contractor_penalty(rating, distance_km, total_projects):
    """
    Applies multiplicative penalty factors for contractors:
      - Very low rating (< 2.0): −20%
      - No track record (0 projects): −10%
      - Very far (> 25 km): −30%
    """
    penalty = 1.0
    if rating < 2.0:
        penalty *= 0.80
    if total_projects == 0:
        penalty *= 0.90
    if distance_km > 25.0:
        penalty *= 0.70
    return penalty


# ─────────────────────────────────────────────
# PUBLIC FUNCTION 1 — Worker Recommendation
# Weighted heuristic scoring for individual workers.
# ─────────────────────────────────────────────
def predict_best_worker(rating, distance, success_rate, jobs_completed):
    """
    Rule-Based Expert System score for a single worker.

    Inputs:
      rating         — float, 0.0–5.0 star rating
      distance       — float, km from user's location
      success_rate   — float, 0–100 (percentage of completed jobs)
      jobs_completed — int, total completed jobs

    Returns:
      float in [0.0, 1.0] — higher = better match

    Scoring weights (Expert Rule):
      Rating score      → 35%
      Success rate      → 30%
      Proximity score   → 25%
      Experience tier   → 10%
    Then multiplied by penalty factor.
    """
    # --- Component Scores ---
    # 1. Rating: normalize from [0, 5] to [0, 1]
    rating_score = _clamp(rating / 5.0)

    # 2. Success rate: normalize from [0, 100] to [0, 1]
    success_score = _clamp(success_rate / 100.0)

    # 3. Proximity: linear decay up to 15 km
    proximity_score = _proximity_score(distance, max_km=15.0)

    # 4. Experience tier
    experience_score = _experience_tier_score(jobs_completed)

    # --- Weighted Combination ---
    raw_score = (
        rating_score    * 0.35 +
        success_score   * 0.30 +
        proximity_score * 0.25 +
        experience_score * 0.10
    )

    # --- Apply Penalty Rules ---
    penalty = _worker_penalty(rating, distance, jobs_completed)
    final_score = _clamp(raw_score * penalty)

    return float("{:.3f}".format(final_score))


# ─────────────────────────────────────────────
# PUBLIC FUNCTION 2 — Contractor Recommendation
# Weighted heuristic scoring for bulk-hire contractors.
# ─────────────────────────────────────────────
def predict_best_contractor(rating, success_rate, available_workers, total_projects, distance):
    """
    Rule-Based Expert System score for a contractor (bulk hire).

    Inputs:
      rating            — float, 0.0–5.0 star rating
      success_rate      — float, 0–100
      available_workers — int, workers currently available
      total_projects    — int, total projects handled historically
      distance          — float, km from user's location

    Returns:
      float in [0.0, 1.0] — higher = better match

    Scoring weights (Expert Rule):
      Rating score          → 35%
      Success rate          → 30%
      Proximity score       → 20%
      Fleet capacity score  → 15%
    Then multiplied by penalty factor.
    """
    # --- Component Scores ---
    # 1. Rating
    rating_score = _clamp(rating / 5.0)

    # 2. Success rate
    success_score = _clamp(success_rate / 100.0)

    # 3. Proximity: linear decay up to 30 km (contractors serve wider area)
    proximity_score = _proximity_score(distance, max_km=30.0)

    # 4. Fleet capacity
    fleet_score = _fleet_capacity_score(available_workers)

    # --- Weighted Combination ---
    raw_score = (
        rating_score    * 0.35 +
        success_score   * 0.30 +
        proximity_score * 0.20 +
        fleet_score     * 0.15
    )

    # --- Apply Penalty Rules ---
    penalty = _contractor_penalty(rating, distance, total_projects)
    final_score = _clamp(raw_score * penalty)

    return float("{:.3f}".format(final_score))


# ─────────────────────────────────────────────
# SELF-TEST — run: python core/ml_model.py
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  Rule-Based Expert System - Self Test")
    print("=" * 55)

    # ── Worker Tests ──
    w_top  = predict_best_worker(4.9, 0.8, 99.0, 120)
    w_mid  = predict_best_worker(3.5, 8.0, 75.0, 25)
    w_new  = predict_best_worker(0.0, 3.0, 100.0, 0)
    w_poor = predict_best_worker(1.5, 18.0, 30.0, 2)

    print(f"\n[Worker] Top    (4.9*, 0.8km, 99%, 120 jobs) -> {w_top}")
    print(f"[Worker] Mid    (3.5*, 8.0km, 75%, 25 jobs)  -> {w_mid}")
    print(f"[Worker] New    (0.0*, 3.0km, 100%, 0 jobs)  -> {w_new}")
    print(f"[Worker] Poor   (1.5*, 18km, 30%, 2 jobs)    -> {w_poor}")

    assert w_top  > 0.70, f"Expected top worker > 0.70, got {w_top}"
    assert w_poor < 0.40, f"Expected poor worker < 0.40, got {w_poor}"
    assert w_top  > w_mid > w_poor, "Ordering check failed for workers"
    print("\n[OK] Worker score ordering validated.")

    # ── Contractor Tests ──
    c_top  = predict_best_contractor(4.8, 95.0, 40, 20, 1.5)
    c_mid  = predict_best_contractor(3.2, 70.0, 15, 8,  12.0)
    c_new  = predict_best_contractor(0.0, 100.0, 10, 0, 5.0)
    c_poor = predict_best_contractor(1.8, 40.0, 3,  1,  28.0)

    print(f"\n[Contractor] Top  (4.8*, 95%, 40w, 20proj, 1.5km)  -> {c_top}")
    print(f"[Contractor] Mid  (3.2*, 70%, 15w, 8proj,  12km)    -> {c_mid}")
    print(f"[Contractor] New  (0.0*, 100%, 10w, 0proj, 5km)     -> {c_new}")
    print(f"[Contractor] Poor (1.8*, 40%, 3w,  1proj,  28km)    -> {c_poor}")

    assert c_top  > 0.70, f"Expected top contractor > 0.70, got {c_top}"
    assert c_poor < 0.40, f"Expected poor contractor < 0.40, got {c_poor}"
    assert c_top  > c_mid > c_poor, "Ordering check failed for contractors"
    print("\n[OK] Contractor score ordering validated.")

    print("\n[OK] All assertions passed. Rule-Based Expert System is working correctly.")
    print("=" * 55)
