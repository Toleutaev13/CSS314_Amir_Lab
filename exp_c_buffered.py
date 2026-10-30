"""Experiment C: remediation via local buffer aggregation."""
import time
from multiprocessing import Process, Queue


def buffered_worker(out_queue, items_per_worker, batch_size=10_000):
    buffer = []
    for i in range(items_per_worker):
        buffer.append(i % 7)
        if len(buffer) >= batch_size:
            out_queue.put(sum(buffer))
            buffer.clear()
    if buffer:
        out_queue.put(sum(buffer))
    out_queue.put(None)  # sentinel


def run_buffered(p, total_items=10_000_000):
    q = Queue()
    items_per_worker = total_items // p
    workers = [Process(target=buffered_worker, args=(q, items_per_worker))
               for _ in range(p)]
    t0 = time.perf_counter()
    for w in workers:
        w.start()
    total_sum, active = 0, p
    while active > 0:
        val = q.get()
        if val is None:
            active -= 1
        else:
            total_sum += val
    for w in workers:
        w.join()
    return time.perf_counter() - t0, total_sum


if __name__ == "__main__":
    runtimes, sums = {}, {}
    for p in (1, 2, 4, 8):
        runtimes[p], sums[p] = run_buffered(p)
        print(f"  done: P={p}, {runtimes[p]:.2f}s", flush=True)

    t1 = runtimes[1]
    print("\n--- Buffered Karp-Flatt Analysis (10M items) ---")
    print("P |  Time(s) | Speedup | Eff(%) | Karp-Flatt e | sum")
    for p in (1, 2, 4, 8):
        tp = runtimes[p]
        sp = t1 / tp
        e = "   --  " if p == 1 else f"{((p * tp / t1) - 1.0) / (p - 1.0):7.3f}"
        print(f"{p} | {tp:8.3f} | {sp:7.2f} | {sp/p*100:6.1f} | {e} | {sums[p]}")

    e2 = (2 * runtimes[2] / t1) - 1.0
    e8 = ((8 * runtimes[8] / t1) - 1.0) / 7.0
    print(f"\nmarkdown: | {t1:.2f} | {runtimes[2]:.2f} | {runtimes[4]:.2f} | "
          f"{runtimes[8]:.2f} | {t1/runtimes[8]:.2f} | {e2:.3f} | {e8:.3f} |")
    print(f"Throughput at P=8: {10_000_000 / runtimes[8]:,.0f} items/s")
