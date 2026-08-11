#!/usr/bin/env python3
"""
Qatalyst-Q standalone feasibility benchmark.

Purpose:
- Construct small synthetic constrained asset-siting QUBO instances.
- Solve each instance exactly by enumeration for a certified classical reference.
- Run p=2 QAOA on a NumPy exact-statevector emulator.
- Emulate 5,000 measurement shots.
- Deterministically verify cardinality feasibility and original-objective quality.

This is a standalone submission-specific benchmark harness. It does not contain
Qatalyst Ltd proprietary engine implementation or solver-routing logic.
"""
from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path
import time

import numpy as np
from scipy.optimize import minimize

OUT_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_CSV = OUT_DIR / "qatalyst_q_emulator_results.csv"
RESULTS_JSON = OUT_DIR / "qatalyst_q_emulator_results.json"


def make_instance(n: int, seed: int):
    rng = np.random.default_rng(seed)
    values = rng.uniform(1.0, 3.0, size=n)
    conflicts = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < 0.22:
                conflicts[i, j] = conflicts[j, i] = rng.uniform(0.1, 0.6)
    k = max(2, n // 3)
    return values, conflicts, k


def original_score(bits, values, conflicts):
    x = np.asarray(bits, dtype=float)
    return float(values @ x - 0.5 * x @ conflicts @ x)


def exact_optimum(n, values, conflicts, k):
    best_score = -np.inf
    best_bits = None
    for comb in itertools.combinations(range(n), k):
        bits = np.zeros(n, dtype=int)
        bits[list(comb)] = 1
        score = original_score(bits, values, conflicts)
        if score > best_score:
            best_score = score
            best_bits = bits.copy()
    return best_bits, float(best_score)


def make_cost_diagonal(n, values, conflicts, k, penalty=8.0):
    states = np.arange(2**n, dtype=np.uint32)[:, None]
    bit_matrix = ((states >> np.arange(n, dtype=np.uint32)) & 1).astype(float)
    original = bit_matrix @ values - 0.5 * np.einsum(
        "bi,ij,bj->b", bit_matrix, conflicts, bit_matrix
    )
    penalized = original - penalty * (bit_matrix.sum(axis=1) - k) ** 2
    # QAOA minimizes energy, while the siting score is maximized.
    return -penalized, bit_matrix


def apply_x_mixer(state, beta, n):
    c = np.cos(beta)
    s = -1j * np.sin(beta)
    out = state
    for q in range(n):
        step = 1 << q
        arr = out.reshape(-1, 2, step)
        a = arr[:, 0, :].copy()
        b = arr[:, 1, :].copy()
        arr[:, 0, :] = c * a + s * b
        arr[:, 1, :] = s * a + c * b
    return out


def qaoa_state(params, cost_diag, n, p):
    state = np.ones(2**n, dtype=np.complex128) / np.sqrt(2**n)
    gammas = params[:p]
    betas = params[p:]
    for gamma, beta in zip(gammas, betas):
        state *= np.exp(-1j * gamma * cost_diag)
        state = apply_x_mixer(state, beta, n)
    return state


def expected_energy(params, cost_diag, n, p):
    state = qaoa_state(params, cost_diag, n, p)
    return float(np.dot(np.abs(state) ** 2, cost_diag))


def optimize_qaoa(cost_diag, n, p, seed, random_trials=100, maxiter=100):
    rng = np.random.default_rng(seed)
    candidates = []
    for _ in range(random_trials):
        x = np.concatenate(
            [rng.uniform(0, np.pi, size=p), rng.uniform(0, np.pi / 2, size=p)]
        )
        candidates.append((expected_energy(x, cost_diag, n, p), x))
    candidates.sort(key=lambda item: item[0])

    best = None
    for _, x0 in candidates[:3]:
        result = minimize(
            expected_energy,
            x0,
            args=(cost_diag, n, p),
            method="Nelder-Mead",
            options={"maxiter": maxiter, "xatol": 1e-4, "fatol": 1e-5},
        )
        if best is None or result.fun < best.fun:
            best = result
    return best


def benchmark(n, seed, p=2, shots=5000):
    values, conflicts, k = make_instance(n, seed)
    exact_bits, exact_score = exact_optimum(n, values, conflicts, k)
    cost_diag, bit_matrix = make_cost_diagonal(n, values, conflicts, k)

    start = time.perf_counter()
    opt = optimize_qaoa(cost_diag, n, p, seed + 999)
    emulator_seconds = time.perf_counter() - start

    state = qaoa_state(opt.x, cost_diag, n, p)
    probabilities = np.abs(state) ** 2
    rng = np.random.default_rng(seed + 12345)
    sampled_states = rng.choice(2**n, size=shots, p=probabilities)
    sampled_bits = bit_matrix[sampled_states].astype(int)

    feasible_mask = sampled_bits.sum(axis=1) == k
    scores = np.full(shots, -np.inf)
    feasible_bits = sampled_bits[feasible_mask]
    if len(feasible_bits):
        scores[feasible_mask] = feasible_bits @ values - 0.5 * np.einsum(
            "bi,ij,bj->b", feasible_bits, conflicts, feasible_bits
        )

    best_idx = int(np.argmax(scores))
    best_score = float(scores[best_idx])
    best_bits = sampled_bits[best_idx]
    optimum_hits = int(np.sum(np.isclose(scores, exact_score, atol=1e-9)))

    return {
        "data_qubits": n,
        "cardinality_k": k,
        "qaoa_depth_p": p,
        "shots": shots,
        "exact_objective": exact_score,
        "best_sampled_qaoa_objective": best_score,
        "best_sampled_ratio": best_score / exact_score,
        "feasible_sample_rate": float(feasible_mask.mean()),
        "optimum_hit_rate": optimum_hits / shots,
        "exact_solution": "".join(map(str, exact_bits[::-1])),
        "best_sampled_solution": "".join(map(str, best_bits[::-1])),
        "emulator_optimisation_seconds": emulator_seconds,
        "optimizer_evaluations": int(opt.nfev),
        "seed": seed,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [benchmark(n, 100 + n) for n in (6, 8, 10, 12)]
    with RESULTS_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    RESULTS_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    print("Qatalyst-Q statevector emulator benchmark")
    for row in rows:
        print(
            f"n={row['data_qubits']:2d} | exact={row['exact_objective']:.6f} | "
            f"best={row['best_sampled_qaoa_objective']:.6f} | "
            f"feasible={100*row['feasible_sample_rate']:.2f}% | "
            f"optimum hits={100*row['optimum_hit_rate']:.2f}%"
        )
    print(f"Wrote: {RESULTS_CSV}")
    print(f"Wrote: {RESULTS_JSON}")


if __name__ == "__main__":
    main()
