"""Experiment A: The Granularity Trap.
Usage:  python exp_a_granularity.py            (full run, 1,000,000 items)
        python exp_a_granularity.py --items 200000   (quick test)
"""
import argparse
import time
from multiprocessing import Pool


def collatz_steps(n):
    steps = 0
    while n > 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    return steps


def run_granularity(workers, total_items=1_000_000, chunk_size=1):
    numbers = range(1, total_items + 1)
    t0 = time.perf_counter()
    with Pool(processes=workers) as pool:
        results = pool.map(collatz_steps, numbers, chunksize=chunk_size)
    return time.perf_counter() - t0, sum(results)


def karp_flatt(p, tp, t1):
    return ((p * tp / t1) - 1.0) / (p - 1.0)


def report(label, runtimes):
    t1 = runtimes[1]
    print(f"\n--- {label} ---")
    print("P |  Time(s) | Speedup | Eff(%) | Karp-Flatt e")
    for p in (1, 2, 4, 8):
        tp = runtimes[p]
        sp = t1 / tp
        eff = sp / p * 100
        e = "   --  " if p == 1 else f"{karp_flatt(p, tp, t1):7.3f}"
        print(f"{p} | {tp:8.3f} | {sp:7.2f} | {eff:6.1f} | {e}")
    print(f"markdown: | {t1:.2f} | {runtimes[2]:.2f} | {runtimes[4]:.2f} | "
          f"{runtimes[8]:.2f} | {t1/runtimes[8]:.2f} | "
          f"{karp_flatt(2, runtimes[2], t1):.3f} | {karp_flatt(8, runtimes[8], t1):.3f} |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", type=int, default=1_000_000)
    ap.add_argument("--only", choices=["micro", "coarse"],
                    help="run just one of the two configurations")
    args = ap.parse_args()

    configs = [("Micro-tasks (chunksize=1)", 1, "micro"),
               ("Coarse chunks (chunksize=10000)", 10_000, "coarse")]
    for label, chunk, key in configs:
        if args.only and args.only != key:
            continue
        runtimes, checks = {}, set()
        for p in (1, 2, 4, 8):
            t, s = run_granularity(p, args.items, chunk)
            runtimes[p] = t
            checks.add(s)
            print(f"  done: P={p}, chunk={chunk}, {t:.2f}s", flush=True)
        assert len(checks) == 1, "checksums differ between runs!"
        report(label, runtimes)
