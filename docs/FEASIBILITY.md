# Qatalyst-Q Technical Feasibility Note

## Scope

This note documents the standalone emulator benchmark used as feasibility evidence for the Qatalyst-Q EuroHPC Quantum Access Pilot application. It is intentionally separate from the proprietary Qatalyst Engine.

## Experimental question

Can a controlled constrained-optimisation workflow be formulated, emulated, sampled, decoded, and independently verified before moving to physical quantum hardware?

## Method

For each benchmark size, the harness:

1. generates a synthetic constrained asset-siting instance with a fixed random seed;
2. establishes the exact classical optimum by enumerating all feasible cardinality-constrained selections;
3. constructs a penalised QUBO/Ising cost diagonal;
4. runs depth-2 QAOA using an exact NumPy statevector emulator;
5. optimises the QAOA parameters classically with a fixed-seed multistart procedure;
6. samples 5,000 emulated measurements; and
7. independently evaluates sampled bitstrings against the original feasibility constraint and original objective.

The deterministic check is outside the QAOA optimisation loop and does not rely on the quantum workflow to certify its own result.

## Results

| Data qubits | Cardinality k | QAOA p | Shots | Exact objective | Best sampled objective | Feasible sample rate | Optimum hit rate |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 6 | 2 | 2 | 5,000 | 5.306150 | 5.306150 | 67.14% | 62.00% |
| 8 | 2 | 2 | 5,000 | 5.226895 | 5.226895 | 59.52% | 3.48% |
| 10 | 3 | 2 | 5,000 | 8.038742 | 8.038742 | 44.20% | 0.48% |
| 12 | 4 | 2 | 5,000 | 10.340303 | 10.340303 | 33.42% | 5.14% |

For all four feasibility cases, at least one sampled candidate matched the independently established exact optimum. These results demonstrate end-to-end workflow feasibility at small scale. They are **not** evidence of quantum advantage and are not intended to establish superiority over classical optimisation.

## Why physical hardware is still required

Exact-statevector emulation is valuable for development but does not reproduce all effects that determine physical-QPU performance. The next stage requires real hardware to measure, among other factors:

- device noise and sampling variability;
- hardware-native compilation and circuit expansion;
- gate and readout errors;
- repeatability across independent QPU executions; and
- how solution feasibility and objective quality change with physical implementation.

The planned EuroHPC study will begin by reproducing the validated small cases, then increase problem size and interaction complexity within the capabilities of the selected system.

## Reproducibility

The benchmark script uses fixed seeds. Objective values, sampled solutions, feasibility rates, and optimum-hit rates should reproduce under the pinned numerical dependencies in `requirements.txt`. Wall-clock optimisation times are machine dependent and should not be treated as invariant evidence.

## IP boundary

This repository contains only the submission-specific benchmark harness and evidence. It does not contain Qatalyst Ltd's commercial engine, internal solver-routing logic, agent architecture, proprietary orchestration, or broader product verification implementation.
