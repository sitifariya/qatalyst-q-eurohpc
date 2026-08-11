# Qatalyst-Q EuroHPC Benchmark Harness

Private research benchmark harness supporting the Qatalyst-Q application to the EuroHPC Quantum Access Pilot (Proposal DRAFT-21045).

## Purpose

This repository contains a deliberately limited, standalone feasibility benchmark for verified quantum-optimisation experiments. It is separate from the proprietary Qatalyst Engine and does **not** contain Qatalyst's commercial solver-routing, agent, orchestration, or internal verifier implementation.

The benchmark is designed to establish a controlled path from classical reference solving and emulator testing to physical-QPU experiments on EuroHPC infrastructure.

## Current feasibility benchmark

The included benchmark:

- constructs small synthetic constrained asset-siting optimisation instances;
- establishes exact classical reference solutions by enumeration;
- maps the constrained objective to a penalised QUBO/Ising cost function;
- runs a depth-2 QAOA workflow on an exact-statevector emulator;
- samples 5,000 measurements per instance;
- independently checks cardinality feasibility and original-objective quality; and
- reports results for 6, 8, 10, and 12 data qubits.

Across the submitted feasibility cases, the best sampled QAOA candidate matched the independently established classical optimum. This is evidence of workflow feasibility only and is **not** presented as evidence of quantum advantage.

## Repository layout

```text
benchmark/
  qatalyst_q_emulator_benchmark.py   Standalone emulator feasibility benchmark
results/
  qatalyst_q_emulator_results.csv    Submitted benchmark results
  qatalyst_q_emulator_results.json   Machine-readable results
docs/
  FEASIBILITY.md                     Method and interpretation
requirements.txt                     Minimal Python dependencies
```

## Reproduce the emulator benchmark

```bash
python -m pip install -r requirements.txt
python benchmark/qatalyst_q_emulator_benchmark.py
```

The script uses fixed random seeds. Objective values, feasibility rates, optimum-hit rates, and sampled solutions are therefore reproducible. Runtime measurements may vary by machine.

## Planned EuroHPC extension

If access is awarded, the benchmark workflow will be extended to physical quantum hardware using Qiskit and/or PennyLane. Initial hardware runs will reproduce validated small instances before scaling toward the selected system's available qubit range. Physical-QPU outputs will be compared against emulator and classical reference results using independent deterministic checks.

## Confidentiality and IP

This repository is private and maintained by Qatalyst Ltd. It is a submission-specific benchmark harness, not the Qatalyst Engine. Qatalyst Ltd's proprietary product code, internal solver-selection logic, commercial interfaces, and broader verification architecture remain outside this repository.

No public licence is granted by this repository. Third-party dependencies remain subject to their respective licences.
