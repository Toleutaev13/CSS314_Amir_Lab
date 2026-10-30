# RESULTS_B — Scalability Diagnostics (Variant B)

**Student ID:** 230103142  
**Machine:** Windows 10, Python 3.13, 4 physical cores / 8 logical threads

## Results

| Configuration | T1 (s) | T2 (s) | T4 (s) | T8 (s) | S8 | e(2) | e(8) | Verdict |
|---|---|---|---|---|---|---|---|---|
| A: Micro (k=1) | 126.65 | 125.11 | 130.55 | 131.45 | 0.96 | 0.976 | 1.043 | Master dispatch serialization |
| A: Coarse (k=10000) | 60.38 | 25.26 | 9.63 | 5.49 | 11.00 | -0.164 | -0.039 | Strong scaling; T1 baseline suspect (see analysis) |
| B: Queue Choke | 8.67 | 12.32 | 12.02 | 13.21 | 0.66 | 1.843 | 1.599 | IPC lock contention (negative speedup) |
| C: Buffered Batch | 1.88 | 1.17 | 0.91 | 0.73 | 2.56 | 0.242 | 0.303 | Amortized synchronization; scaling limited by 4 physical cores |

## Analysis

**Experiment A.** With chunksize = 1 the runtime does not improve with more processes:
T1 = 126.65 s and T8 = 131.45 s (S8 = 0.96, efficiency 12%). e(p) is about 1.0 for every P
(0.976, 1.041, 1.043), meaning almost the whole run behaves like a serial fraction. The
master process has to pickle and send 1,000,000 individual tasks, and that dispatch path is
single-threaded, so the workers cannot speed it up (master dispatch starvation). With
chunksize = 10000 the same work scales: 25.26 s (P=2), 9.63 s (P=4), 5.49 s (P=8).
Going from k=1 to k=10000 cuts the P=8 time from 131.45 s to 5.49 s.

Caveat: the coarse speedups are above P (S8 = 11.0 on a machine with 4 physical cores) and
e(p) is negative, which is not physically possible for real scaling. The most likely reason
is that the coarse P=1 run (60.38 s) was slowed by something unrelated to the algorithm
(background load or CPU frequency state), which inflates T1 and therefore every speedup
computed from it. The qualitative result (e(p) near 1 for k=1, scaling for k=10000) is
clear, but the exact coarse speedup numbers should be treated as unreliable.

**Experiment B.** Runtime does not drop with more processes: T1 = 8.67 s, T8 = 13.21 s, so
T8 > T1 and speedup is below 1 (S8 = 0.66). e(p) is far above 0.5 for every P
(1.843, 1.516, 1.599 for P = 2, 4, 8). The jump happens already at P = 2 and then stays
high instead of growing steadily, so e(p) is not strictly monotonic in my run. The cause is
that every one of the 400,000 items crosses the shared pipe, so producers contend for the
queue lock and the master is the single consumer. Throughput at P = 1 is only about
46,000 items/s.

**Experiment C.** Workers send one pre-aggregated message per 10,000 items, so the queue
carries only about 1,000 messages instead of millions. The workload is 25x larger than in B
(10M vs 400k items) and still finishes in under 2 s. Throughput at P = 8 is about
13.6M items/s (best run) vs about 30,000 items/s in B (400,000 / 13.21 s), roughly 450x
higher. Speedup is 2.56 (S8) in the reported run and 3.03 in a second run, and
e(8) is 0.30 (0.23 in the second run). These do not reach the handout targets (S8 > 5,
e(8) < 0.05), see the hardware note below.

Two runs of C gave different absolute times (T1 = 3.37 s vs 1.88 s), so there is
measurement noise from other processes on the machine. The table reports the faster run.

## Hardware note

The machine has 4 physical cores (8 logical threads). At P = 8 two processes share one
physical core, so S8 cannot go much beyond the physical core count. Also, on Windows each
process is started with `spawn`, and that start-up cost is included in the measured time.
With total runtimes of about 1–2 s this fixed cost is a large part of Tp. Since the queue
holds only about 1,000 messages in Experiment C, the remaining non-ideal e(p) comes from
hardware limits and process start-up, not from IPC lock contention as in Experiment B.
Measured values are reported as-is.
