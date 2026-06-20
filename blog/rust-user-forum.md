# Releasing dtact v0.2.2 and rssn-advanced v0.1.0

**Hello Rustaceans!**

Today we are releasing dtact v0.2.2 and rssn-advanced v0.1.0, both of which are experimental, high-performance projects currently under development. Dtact is an async concurrent engine, and rssn-advanced is a new generation symbolic core for rssn. Both will be detailed below.

## Dtact

Dtact is a coordinative, truly lockless async runtime designed for maximum work coordination speed and the highest throughput. In short, we mainly utilized a P2P network, a Lock-Free Context Arena, and a Zero-Copy Future Migration to achieve this. For a detailed analysis of the architecture, please refer to https://dtact.apich.org/ and https://github.com/Apich-Organization/dtact. The website's UI was written by AI—because we really aren't that good at writing UI, so please forgive us for that. A detailed benchmark report and CI run links can also be found on the official website, but in short, we can see the following chart (CI run: https://github.com/Apich-Organization/dtact/actions/runs/26011780070/job/76453764923):

### Task Spawn Efficiency

This benchmark measures the time required to spawn and execute a batch of asynchronous tasks.

| Task Scale | Runtime | Min Bound | Mean | Max Bound | Dtact Speedup |
| --- | --- | --- | --- | --- | --- |
| **1M** | Dtact | 103.92 ms | 104.92 ms | 105.94 ms | <br>**6.31x faster** |
|  | Tokio | 648.02 ms | 662.11 ms | 676.42 ms | Reference |
| **100k** | Dtact | 11.667 ms | 11.807 ms | 11.954 ms | <br>**5.34x faster** |
|  | Tokio | 61.064 ms | 63.067 ms | 65.043 ms | Reference |
| **10k** | Dtact | 1.9672 ms | 2.0144 ms | 2.0620 ms | <br>**2.63x faster** |
|  | Tokio | 5.1595 ms | 5.2986 ms | 5.4395 ms | Reference |
| **1k** | Dtact | 152.301 µs| 157.731 µs | 163.311 µs | <br>**4.76x faster** |
|  | Tokio | 719.65 µs | 750.891 µs | 783.411 µs | Reference |

### Yield Efficiency

This test measures the time taken for 10 concurrent tasks to perform 100 cooperative `yield_now` operations each.

| Test Case | Runtime | Min Bound | Mean | Max Bound | Comparison |
| --- | --- | --- | --- | --- | --- |
| **10 tasks** | Dtact | 795.651 µs | 827.511 µs | 860.191 µs | ~4.41x slower |
|  | Tokio | 179.981 µs | 187.731 µs | 195.651 µs | <br>**4.41x faster** |

### Work Deflection (Hot Core) Performance

This benchmark simulates task dispatching and throttle coordination under heavy load imbalances across a multi-core scheduler.

| Task Scale | Runtime | Min Bound | Mean | Max Bound | Dtact Speedup |
| --- | --- | --- | --- | --- | --- |
| **10M** | Dtact | 1.6624 s | 1.6792 s | 1.6962 s | <br>**4.13x faster** |
|  | Tokio | 6.8482 s | 6.9386 s | 7.0291 s | Reference |
| **100k** | Dtact | 17.472 ms | 17.659 ms | 17.847 ms | <br>**2.84x faster** |
|  | Tokio | 49.110 ms | 51.112 ms | 53.114 ms | Reference |
| **10k** | Dtact | 2.4961 ms | 2.5315 ms | 2.5675 ms | <br>**2.31x faster** |
|  | Tokio | 5.7240 ms | 5.8411 ms | 5.9605 ms | Reference |
| **1k** | Dtact | 273.791 µs | 285.231 µs | 297.07 µs | <br>**2.70x faster** |
|  | Tokio | 739.641 µs | 769.841 µs | 801.701 µs | Reference |

The extensive use of `unsafe` and naked assembly in dtact may cause some doubt about this project, but we are striving to achieve higher engineering goals to ensure the project remains safe, and we are continually working on it. Also, special thanks to @newpavlov and @SkiFire13 for their helpful advice when we first tried the stackful approach in the bincode-next UAF backend async fiber module.

## rssn-advanced

This project is highly experimental and is eager for external reviews. Its core design is my own, but it was primarily complemented by @cn-starlabs (it seems he doesn't even have a Rust-lang user account) with the help of Claude. After performing some architectural fixes and code quality improvements myself, I decided to release it alongside dtact. Regardless, the project currently lacks extensive code reviews and is in an early stage, even without fully meeting OSSF standards. However, I personally think it is impressive to see a full JIT symbolic computing engine with almost infinite extensibility that truly achieves a combination of symbolic and numerical computing. The official website is also under development, so you might prefer to check the repository first: https://github.com/Apich-Organization/rssn-advanced or checkout https://rssn-advanced.apich.org
And the first performance reports:

```text
==============================================================================
   RSSN-Advanced JIT vs NumPy — Bulk Evaluation Benchmark
   N = 1,000,000 rows per expression  |  5 repeats, best time reported
==============================================================================

──────────────────────────────────────────────────────────────────────────────
  1. Trivial (baseline)
  x + y + 10.0
──────────────────────────────────────────────────────────────────────────────
  Rust JIT bulk  (scalar, Rust loop)              1.868 ms     1.87 ns/eval
  Rust JIT batch (2-row ILP vectorised)           1.133 ms     1.13 ns/eval
  NumPy (SIMD / C, hand-optimised)                2.824 ms     2.82 ns/eval
  SymPy lambdify → numpy backend                  2.763 ms     2.76 ns/eval

  JIT bulk  vs NumPy:  1.51x faster
  JIT batch vs NumPy:  2.49x faster

  Accuracy  bulk  max|Δ|=0.00e+00  ✔
            batch max|Δ|=0.00e+00  ✔

  NumPy intermediate arrays: ~2 ops → ~15 MB peak temp memory
  JIT: 0 intermediate arrays — all values kept in CPU registers

──────────────────────────────────────────────────────────────────────────────
  2. Degree-4 polynomial  (x-y)^4  [2 vars]
  x^4 - 4*x^3*y + 6*x^2*y^2 - 4*x*y^3 + y^4
──────────────────────────────────────────────────────────────────────────────
  Rust JIT bulk  (scalar, Rust loop)              2.729 ms     2.73 ns/eval
  Rust JIT batch (2-row ILP vectorised)           1.276 ms     1.28 ns/eval
  NumPy (SIMD / C, hand-optimised)               19.207 ms    19.21 ns/eval
  SymPy lambdify → numpy backend                 18.933 ms    18.93 ns/eval

  JIT bulk  vs NumPy:  7.04x faster
  JIT batch vs NumPy: 15.06x faster

  Accuracy  bulk  max|Δ|=5.46e-12  ✔
            batch max|Δ|=5.46e-12  ✔

  NumPy intermediate arrays: ~16 ops → ~122 MB peak temp memory
  JIT: 0 intermediate arrays — all values kept in CPU registers

──────────────────────────────────────────────────────────────────────────────
  3. Cubic surface  [3 vars, 10 terms]
  x^3 + y^3 + z^3 - 3*x*y*z + x^2*y - x*y^2 + y^2*z - y*z^2 + z^2*x - z*x^2
──────────────────────────────────────────────────────────────────────────────
  Rust JIT bulk  (scalar, Rust loop)              3.733 ms     3.73 ns/eval
  Rust JIT batch (2-row ILP vectorised)           1.772 ms     1.77 ns/eval
  NumPy (SIMD / C, hand-optimised)               75.751 ms    75.75 ns/eval
  SymPy lambdify → numpy backend                 78.214 ms    78.21 ns/eval

  JIT bulk  vs NumPy: 20.29x faster
  JIT batch vs NumPy: 42.74x faster

  Accuracy  bulk  max|Δ|=2.84e-13  ✔
            batch max|Δ|=2.84e-13  ✔

  NumPy intermediate arrays: ~27 ops → ~206 MB peak temp memory
  JIT: 0 intermediate arrays — all values kept in CPU registers

──────────────────────────────────────────────────────────────────────────────
  4. Rational w/ CSE  [2 vars, repeated subexpr]
  (x^2 + y^2) / (x^2 + y^2 + 1.0) + x*y*(x^2 - y^2) / (x^2 + y^2 + 1.0)^2
──────────────────────────────────────────────────────────────────────────────
  Rust JIT bulk  (scalar, Rust loop)              2.534 ms     2.53 ns/eval
  Rust JIT batch (2-row ILP vectorised)           1.266 ms     1.27 ns/eval
  NumPy (SIMD / C, hand-optimised)               15.913 ms    15.91 ns/eval
  SymPy lambdify → numpy backend                 22.961 ms    22.96 ns/eval

  JIT bulk  vs NumPy:  6.28x faster
  JIT batch vs NumPy: 12.57x faster

  Accuracy  bulk  max|Δ|=0.00e+00  ✔
            batch max|Δ|=0.00e+00  ✔

  NumPy intermediate arrays: ~20 ops → ~153 MB peak temp memory
  JIT: 0 intermediate arrays — all values kept in CPU registers

==============================================================================
  SUMMARY: JIT speedup vs hand-optimised NumPy
  Expression                                          bulk     batch
  ──────────────────────────────────────────────  ────────  ────────
  1. Trivial (baseline)                             1.51x    2.49x
  2. Degree-4 polynomial                            7.04x   15.06x
  3. Cubic surface                                 20.29x   42.74x
  4. Rational w/ CSE                                6.28x   12.57x

  Observation: speedup grows with expression complexity because
  NumPy's intermediate arrays overflow L2/L3 cache at N=1,000,000.
  JIT maintains register-resident computation across the entire
  expression, paying one memory read/write per input element.
==============================================================================
```
I ran it in Python using CPython FFI, so it is significantly slower than if it were compiled into a Rust binary—but for the sake of fairness, I have kept it as is.

Also from our docs:
**Architecture**
| Module | Role |
|--------|------|
| [`dag`] | Hash-consed expression DAG — the canonical, deduplicated store for all symbolic nodes |
| [`ast`] | Lightweight local tree projection of a DAG subgraph via relative `i32` pointers |
| [`parser`] | `nom`-based infix parser: `"x^2 + 2*x + 1"` → DAG root |
| [`jit`] *(feature: `cranelift-jit`/`jit`)* | Cranelift JIT; emits scalar `f64` closures and 2-row ILP batch functions |
| [`heuristic`] | Configurable greedy/beam simplifier with a pluggable [`heuristic::rule_registry::RuleRegistry`] |
| [`egraph`] | Lightweight equality saturation over the DAG (no `egg` dependency) |
| [`custom`] | Unified custom-operator system — one [`custom::descriptor::CustomOpDescriptor`] wires into JIT + simplifier + e-graph |
| [`simd`] | Slice-level batch arithmetic using the inline-asm presets |
| [`asm_presets`] | Hand-written `f64×2` / `f64×4` kernels for `x86_64` (SSE2/AVX2/AES-NI), `AArch64` (NEON/crypto), riscv64 (RVV/Zkn) |
| [`ffi`] | Flat `extern "C"` surface generated by `cbindgen`; includes a fiber-backed async bridge |
| [`parallel`] | Fiber-based parallel simplification via the `dtact` runtime |
| [`storage`] | Disk-backed DAG spillover and a frequency-based hot-node cache |
| [`error`] | Cold-path error types and the `rssn_error!` macro |

## Bincode-next

Finally, a small update for `bincode-next` at the end of this post to avoid posting too frequently. `Bincode-next` has released v3.0.0-rc.15, and we are continuously fuzzing. We have decided to release the stable version after joining the OSS-Fuzz project and running it for a while. Link: https://github.com/Apich-Organization/bincode

## Common Links

Discord Server: https://discord.gg/D5e2czMTT9
Contact E-mail: info@apich.org
OSSF Registration (bincode-next): https://www.bestpractices.dev/projects/12960 
OSSF Registration (dtact): https://www.bestpractices.dev/en/projects/12962/passing
Score Card: https://securityscorecards.dev/viewer/?uri=github.com/Apich-Organization/bincode
Discussions on Dtact style designs: https://users.rust-lang.org/t/discussion-on-synchronous-crate-concurrency-refactor-using-stackful-coroutines-model-in-rust/139246

===

# Project updates: rssn-advanced v0.1.1 and bincode-next maintenance timeline

rssn-advanced v0.1.1 has been released on May 29, 2026 CST to fix several critical bugs on `aarch64` platforms. Other updates are also on the way, so please run `cargo update` often to get your deps up to date. rssn-advanced will also consider for adding GPU JIT support and prepare for supporting another PINN research project.
Also, we have decided that bincode-next v3 stable will be released as early as August 2026, but if we think the testing is still not sufficient (which seems to probably be the case), the release will be delayed anyway.

And the updated bench report:
```text
==============================================================================
   RSSN-Advanced JIT vs NumPy — Bulk Evaluation Benchmark
   N = 1,000,000 rows per expression  |  5 repeats, best time reported
==============================================================================

──────────────────────────────────────────────────────────────────────────────
  1. Trivial (baseline)
  x + y + 10.0
──────────────────────────────────────────────────────────────────────────────
  Rust JIT bulk  (scalar, Rust loop)              2.383 ms     2.38 ns/eval
  Rust JIT batch (2-row ILP vectorised)           1.147 ms     1.15 ns/eval
  NumPy (SIMD / C, hand-optimised)                7.314 ms     7.31 ns/eval
  SymPy lambdify → numpy backend                  6.660 ms     6.66 ns/eval

  JIT bulk  vs NumPy:  3.07x faster
  JIT batch vs NumPy:  6.38x faster

  Accuracy  bulk  max|Δ|=0.00e+00  ✔
            batch max|Δ|=0.00e+00  ✔

  NumPy intermediate arrays: ~2 ops → ~15 MB peak temp memory
  JIT: 0 intermediate arrays — all values kept in CPU registers

──────────────────────────────────────────────────────────────────────────────
  2. Degree-4 polynomial  (x-y)^4  [2 vars]
  x^4 - 4*x^3*y + 6*x^2*y^2 - 4*x*y^3 + y^4
──────────────────────────────────────────────────────────────────────────────
  Rust JIT bulk  (scalar, Rust loop)              3.470 ms     3.47 ns/eval
  Rust JIT batch (2-row ILP vectorised)           1.438 ms     1.44 ns/eval
  NumPy (SIMD / C, hand-optimised)               27.584 ms    27.58 ns/eval
  SymPy lambdify → numpy backend                 27.708 ms    27.71 ns/eval

  JIT bulk  vs NumPy:  7.95x faster
  JIT batch vs NumPy: 19.18x faster

  Accuracy  bulk  max|Δ|=5.46e-12  ✔
            batch max|Δ|=5.46e-12  ✔

  NumPy intermediate arrays: ~16 ops → ~122 MB peak temp memory
  JIT: 0 intermediate arrays — all values kept in CPU registers

──────────────────────────────────────────────────────────────────────────────
  3. Cubic surface  [3 vars, 10 terms]
  x^3 + y^3 + z^3 - 3*x*y*z + x^2*y - x*y^2 + y^2*z - y*z^2 + z^2*x - z*x^2
──────────────────────────────────────────────────────────────────────────────
  Rust JIT bulk  (scalar, Rust loop)              4.368 ms     4.37 ns/eval
  Rust JIT batch (2-row ILP vectorised)           2.059 ms     2.06 ns/eval
  NumPy (SIMD / C, hand-optimised)              104.586 ms   104.59 ns/eval
  SymPy lambdify → numpy backend                192.272 ms   192.27 ns/eval

  JIT bulk  vs NumPy: 23.94x faster
  JIT batch vs NumPy: 50.79x faster

  Accuracy  bulk  max|Δ|=2.84e-13  ✔
            batch max|Δ|=2.84e-13  ✔

  NumPy intermediate arrays: ~27 ops → ~206 MB peak temp memory
  JIT: 0 intermediate arrays — all values kept in CPU registers

──────────────────────────────────────────────────────────────────────────────
  4. Rational w/ CSE  [2 vars, repeated subexpr]
  (x^2 + y^2) / (x^2 + y^2 + 1.0) + x*y*(x^2 - y^2) / (x^2 + y^2 + 1.0)^2
──────────────────────────────────────────────────────────────────────────────
  Rust JIT bulk  (scalar, Rust loop)              2.983 ms     2.98 ns/eval
  Rust JIT batch (2-row ILP vectorised)           1.384 ms     1.38 ns/eval
  NumPy (SIMD / C, hand-optimised)               30.108 ms    30.11 ns/eval
  SymPy lambdify → numpy backend                129.223 ms   129.22 ns/eval

  JIT bulk  vs NumPy: 10.09x faster
  JIT batch vs NumPy: 21.75x faster

  Accuracy  bulk  max|Δ|=0.00e+00  ✔
            batch max|Δ|=0.00e+00  ✔

  NumPy intermediate arrays: ~20 ops → ~153 MB peak temp memory
  JIT: 0 intermediate arrays — all values kept in CPU registers

==============================================================================
  SUMMARY: JIT speedup vs hand-optimised NumPy
  Expression                                          bulk     batch
  ──────────────────────────────────────────────  ────────  ────────
  1. Trivial (baseline)                             3.07x    6.38x
  2. Degree-4 polynomial                            7.95x   19.18x
  3. Cubic surface                                 23.94x   50.79x
  4. Rational w/ CSE                               10.09x   21.75x

  Observation: speedup grows with expression complexity because
  NumPy's intermediate arrays overflow L2/L3 cache at N=1,000,000.
  JIT maintains register-resident computation across the entire
  expression, paying one memory read/write per input element.
==============================================================================
```

v0.1.2:
```text
==========================================================================================
   RSSN-Advanced JIT vs NumPy — Bulk Evaluation Benchmark
   N = 1,000,000 rows per expression  |  5 repeats, best time reported
==========================================================================================

──────────────────────────────────────────────────────────────────────────────────────────
  1. Trivial (baseline)
  x + y + 10.0
──────────────────────────────────────────────────────────────────────────────────────────
  Rust JIT bulk  (scalar, Rust loop)              2.138 ms     2.14 ns/eval
  Rust JIT batch (2-row ILP vectorised)           1.075 ms     1.07 ns/eval
  Rust JIT batch (4-row F64X4 vectorised)         1.165 ms     1.16 ns/eval
  NumPy (SIMD / C, hand-optimised)                3.336 ms     3.34 ns/eval
  SymPy lambdify → numpy backend                  2.518 ms     2.52 ns/eval

  JIT bulk        vs NumPy:  1.56x faster
  JIT batch f64x2 vs NumPy:  3.10x faster
  JIT batch f64x4 vs NumPy:  2.86x faster

  Accuracy  bulk        max|Δ|=0.00e+00  ✔
            batch f64x2 max|Δ|=0.00e+00  ✔
            batch f64x4 max|Δ|=0.00e+00  ✔

  NumPy intermediate arrays: ~2 ops → ~15 MB peak temp memory
  JIT: 0 intermediate arrays — all values kept in CPU registers

──────────────────────────────────────────────────────────────────────────────────────────
  2. Degree-4 polynomial  (x-y)^4  [2 vars]
  x^4 - 4*x^3*y + 6*x^2*y^2 - 4*x*y^3 + y^4
──────────────────────────────────────────────────────────────────────────────────────────
  Rust JIT bulk  (scalar, Rust loop)              3.388 ms     3.39 ns/eval
  Rust JIT batch (2-row ILP vectorised)           1.364 ms     1.36 ns/eval
  Rust JIT batch (4-row F64X4 vectorised)         1.292 ms     1.29 ns/eval
  NumPy (SIMD / C, hand-optimised)               21.848 ms    21.85 ns/eval
  SymPy lambdify → numpy backend                 20.799 ms    20.80 ns/eval

  JIT bulk        vs NumPy:  6.45x faster
  JIT batch f64x2 vs NumPy: 16.01x faster
  JIT batch f64x4 vs NumPy: 16.92x faster

  Accuracy  bulk        max|Δ|=5.46e-12  ✔
            batch f64x2 max|Δ|=5.46e-12  ✔
            batch f64x4 max|Δ|=5.46e-12  ✔

  NumPy intermediate arrays: ~16 ops → ~122 MB peak temp memory
  JIT: 0 intermediate arrays — all values kept in CPU registers

──────────────────────────────────────────────────────────────────────────────────────────
  3. Cubic surface  [3 vars, 10 terms]
  x^3 + y^3 + z^3 - 3*x*y*z + x^2*y - x*y^2 + y^2*z - y*z^2 + z^2*x - z*x^2
──────────────────────────────────────────────────────────────────────────────────────────
  Rust JIT bulk  (scalar, Rust loop)              4.163 ms     4.16 ns/eval
  Rust JIT batch (2-row ILP vectorised)           1.854 ms     1.85 ns/eval
  Rust JIT batch (4-row F64X4 vectorised)         1.761 ms     1.76 ns/eval
  NumPy (SIMD / C, hand-optimised)               82.865 ms    82.86 ns/eval
  SymPy lambdify → numpy backend                 94.077 ms    94.08 ns/eval

  JIT bulk        vs NumPy: 19.90x faster
  JIT batch f64x2 vs NumPy: 44.70x faster
  JIT batch f64x4 vs NumPy: 47.07x faster

  Accuracy  bulk        max|Δ|=2.84e-13  ✔
            batch f64x2 max|Δ|=2.84e-13  ✔
            batch f64x4 max|Δ|=2.84e-13  ✔

  NumPy intermediate arrays: ~27 ops → ~206 MB peak temp memory
  JIT: 0 intermediate arrays — all values kept in CPU registers

──────────────────────────────────────────────────────────────────────────────────────────
  4. Rational w/ CSE  [2 vars, repeated subexpr]
  (x^2 + y^2) / (x^2 + y^2 + 1.0) + x*y*(x^2 - y^2) / (x^2 + y^2 + 1.0)^2
──────────────────────────────────────────────────────────────────────────────────────────
  Rust JIT bulk  (scalar, Rust loop)              3.072 ms     3.07 ns/eval
  Rust JIT batch (2-row ILP vectorised)           1.428 ms     1.43 ns/eval
  Rust JIT batch (4-row F64X4 vectorised)         1.309 ms     1.31 ns/eval
  NumPy (SIMD / C, hand-optimised)               16.425 ms    16.42 ns/eval
  SymPy lambdify → numpy backend                 23.325 ms    23.32 ns/eval

  JIT bulk        vs NumPy:  5.35x faster
  JIT batch f64x2 vs NumPy: 11.50x faster
  JIT batch f64x4 vs NumPy: 12.55x faster

  Accuracy  bulk        max|Δ|=0.00e+00  ✔
            batch f64x2 max|Δ|=0.00e+00  ✔
            batch f64x4 max|Δ|=0.00e+00  ✔

  NumPy intermediate arrays: ~20 ops → ~153 MB peak temp memory
  JIT: 0 intermediate arrays — all values kept in CPU registers

──────────────────────────────────────────────────────────────────────────────────────────
  5. Complex degree-5 polynomial [3 vars]
  x^5 - y^5 + z^5 - 5*x^3*y^2 + 5*x^2*y^3 - 5*y^3*z^2 + 5*y^2*z^3 - 5*z^3*x^2 + 5*z^2*x^3 + x*y*z*(x^2 + y^2 + z^2)
──────────────────────────────────────────────────────────────────────────────────────────
  Rust JIT bulk  (scalar, Rust loop)              5.588 ms     5.59 ns/eval
  Rust JIT batch (2-row ILP vectorised)           2.440 ms     2.44 ns/eval
  Rust JIT batch (4-row F64X4 vectorised)         2.442 ms     2.44 ns/eval
  NumPy (SIMD / C, hand-optimised)              212.842 ms   212.84 ns/eval
  SymPy lambdify → numpy backend                218.957 ms   218.96 ns/eval

  JIT bulk        vs NumPy: 38.09x faster
  JIT batch f64x2 vs NumPy: 87.24x faster
  JIT batch f64x4 vs NumPy: 87.15x faster

  Accuracy  bulk        max|Δ|=1.46e-11  ✔
            batch f64x2 max|Δ|=1.46e-11  ✔
            batch f64x4 max|Δ|=1.46e-11  ✔

  NumPy intermediate arrays: ~44 ops → ~336 MB peak temp memory
  JIT: 0 intermediate arrays — all values kept in CPU registers

──────────────────────────────────────────────────────────────────────────────────────────
  6. Positive Nested Sqrt [2 vars]
  (x^2 + 1.0)^0.5 + (x^2 + y^2 + 1.0)^0.5 + (x^2 + y^2 + 2.0)^0.5
──────────────────────────────────────────────────────────────────────────────────────────
  Rust JIT bulk  (scalar, Rust loop)              4.612 ms     4.61 ns/eval
  Rust JIT batch (2-row ILP vectorised)           2.210 ms     2.21 ns/eval
  Rust JIT batch (4-row F64X4 vectorised)         2.189 ms     2.19 ns/eval
  NumPy (SIMD / C, hand-optimised)               16.013 ms    16.01 ns/eval
  SymPy lambdify → numpy backend                 15.169 ms    15.17 ns/eval

  JIT bulk        vs NumPy:  3.47x faster
  JIT batch f64x2 vs NumPy:  7.24x faster
  JIT batch f64x4 vs NumPy:  7.32x faster

  Accuracy  bulk        max|Δ|=0.00e+00  ✔
            batch f64x2 max|Δ|=0.00e+00  ✔
            batch f64x4 max|Δ|=0.00e+00  ✔

  NumPy intermediate arrays: ~15 ops → ~114 MB peak temp memory
  JIT: 0 intermediate arrays — all values kept in CPU registers

==========================================================================================
  SUMMARY: JIT speedup vs hand-optimised NumPy
  Expression                                          bulk     f64x2       f64x4
  ──────────────────────────────────────────────  ────────  ────────  ──────────
  1. Trivial (baseline)                             1.56x    3.10x      2.86x
  2. Degree-4 polynomial                            6.45x   16.01x     16.92x
  3. Cubic surface                                 19.90x   44.70x     47.07x
  4. Rational w/ CSE                                5.35x   11.50x     12.55x
  5. Complex degree-5 polynomial [3 vars]          38.09x   87.24x     87.15x
  6. Positive Nested Sqrt [2 vars]                  3.47x    7.24x      7.32x

  Observation: speedup grows with expression complexity because
  NumPy's intermediate arrays overflow L2/L3 cache at N=1,000,000.
  JIT maintains register-resident computation across the entire
  expression, paying one memory read/write per input element.
==========================================================================================
```
And for v0.1.3:
```text
==============================================================================================
   RSSN-Advanced JIT — Multi-Backend Evaluation Benchmark
   N = 10,000,000 rows per expression  |  5 repeats, best time reported
   Backends: NumPy, SymPy/lambdify, numexpr, Numba
==============================================================================================

──────────────────────────────────────────────────────────────────────────────────────────────
  1. Trivial (baseline)
  x + y + 10.0
──────────────────────────────────────────────────────────────────────────────────────────────

  RSSN JIT  bulk  (scalar, Rust loop)                   77.561 ms     7.76 ns/eval    5.44x vs NumPy
  RSSN JIT  batch f64x2                                 18.775 ms     1.88 ns/eval   22.49x vs NumPy
  RSSN JIT  f64x2 parallel                              14.020 ms     1.40 ns/eval   30.11x vs NumPy
  RSSN JIT  batch f64x4 (2×F64X2)                       20.346 ms     2.03 ns/eval   20.75x vs NumPy
  RSSN JIT  f64x4 parallel                              13.911 ms     1.39 ns/eval   30.35x vs NumPy
  RSSN JIT  batch f64x8 (4×F64X2)                       21.432 ms     2.14 ns/eval   19.70x vs NumPy
  RSSN JIT  f64x8 parallel (dtact fibers)               15.993 ms     1.60 ns/eval   26.40x vs NumPy
  NumPy     (SIMD/C, hand-optimised)                   422.176 ms    42.22 ns/eval
  numexpr   (multi-threaded JIT)                        16.409 ms     1.64 ns/eval   25.73x vs NumPy
  Numba     (LLVM, vectorized ufunc)                   150.335 ms    15.03 ns/eval    2.81x vs NumPy
  SymPy     lambdify → numpy                           358.044 ms    35.80 ns/eval    1.18x vs NumPy

  Speedups vs NumPy (422.18 ms baseline):
    JIT bulk   :   5.44x faster
    JIT f64x2  :  22.49x faster
    JIT f64x2∥ :  30.11x faster (parallel)
    JIT f64x4  :  20.75x faster
    JIT f64x4∥ :  30.35x faster (parallel)
    JIT f64x8  :  19.70x faster
    JIT f64x8∥ :  26.40x faster (parallel)
    numexpr    :  25.73x faster
    Numba      :   2.81x faster
    SymPy/lam  :   1.18x faster

  Accuracy  bulk                    max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x2             max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x2 parallel    max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x4             max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x4 parallel    max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x8             max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x8 parallel    max|Δ|=0.00e+00  ✔

  NumPy temp arrays: ~2 binary ops → ~153 MB peak
  RSSN JIT: 0 temp arrays — register-resident across entire expression
  numexpr:  ≈0 temp arrays — its own AST-based evaluator
  Numba:    ≈0 temp arrays — LLVM-fused scalar loop

──────────────────────────────────────────────────────────────────────────────────────────────
  2. Degree-4 polynomial  (x-y)^4  [2 vars]
  x^4 - 4*x^3*y + 6*x^2*y^2 - 4*x*y^3 + y^4
──────────────────────────────────────────────────────────────────────────────────────────────

  RSSN JIT  bulk  (scalar, Rust loop)                   92.770 ms     9.28 ns/eval    9.25x vs NumPy
  RSSN JIT  batch f64x2                                 22.298 ms     2.23 ns/eval   38.48x vs NumPy
  RSSN JIT  f64x2 parallel                              22.839 ms     2.28 ns/eval   37.57x vs NumPy
  RSSN JIT  batch f64x4 (2×F64X2)                       21.708 ms     2.17 ns/eval   39.53x vs NumPy
  RSSN JIT  f64x4 parallel                              20.351 ms     2.04 ns/eval   42.17x vs NumPy
  RSSN JIT  batch f64x8 (4×F64X2)                       19.684 ms     1.97 ns/eval   43.59x vs NumPy
  RSSN JIT  f64x8 parallel (dtact fibers)               18.976 ms     1.90 ns/eval   45.22x vs NumPy
  NumPy     (SIMD/C, hand-optimised)                   858.108 ms    85.81 ns/eval
  numexpr   (multi-threaded JIT)                        28.912 ms     2.89 ns/eval   29.68x vs NumPy
  Numba     (LLVM, vectorized ufunc)                   148.631 ms    14.86 ns/eval    5.77x vs NumPy
  SymPy     lambdify → numpy                           789.918 ms    78.99 ns/eval    1.09x vs NumPy

  Speedups vs NumPy (858.11 ms baseline):
    JIT bulk   :   9.25x faster
    JIT f64x2  :  38.48x faster
    JIT f64x2∥ :  37.57x faster (parallel)
    JIT f64x4  :  39.53x faster
    JIT f64x4∥ :  42.17x faster (parallel)
    JIT f64x8  :  43.59x faster
    JIT f64x8∥ :  45.22x faster (parallel)
    numexpr    :  29.68x faster
    Numba      :   5.77x faster
    SymPy/lam  :   1.09x faster

  Accuracy  bulk                    max|Δ|=5.46e-12  ✔
  Accuracy  batch f64x2             max|Δ|=5.46e-12  ✔
  Accuracy  batch f64x2 parallel    max|Δ|=5.46e-12  ✔
  Accuracy  batch f64x4             max|Δ|=5.46e-12  ✔
  Accuracy  batch f64x4 parallel    max|Δ|=5.46e-12  ✔
  Accuracy  batch f64x8             max|Δ|=5.46e-12  ✔
  Accuracy  batch f64x8 parallel    max|Δ|=5.46e-12  ✔

  NumPy temp arrays: ~16 binary ops → ~1221 MB peak
  RSSN JIT: 0 temp arrays — register-resident across entire expression
  numexpr:  ≈0 temp arrays — its own AST-based evaluator
  Numba:    ≈0 temp arrays — LLVM-fused scalar loop

──────────────────────────────────────────────────────────────────────────────────────────────
  3. Cubic surface  [3 vars, 10 terms]
  x^3 + y^3 + z^3 - 3*x*y*z + x^2*y - x*y^2 + y^2*z - y*z^2 + z^2*x - z*x^2
──────────────────────────────────────────────────────────────────────────────────────────────

  RSSN JIT  bulk  (scalar, Rust loop)                  130.722 ms    13.07 ns/eval   59.66x vs NumPy
  RSSN JIT  batch f64x2                                 52.933 ms     5.29 ns/eval  147.33x vs NumPy
  RSSN JIT  f64x2 parallel                              36.842 ms     3.68 ns/eval  211.68x vs NumPy
  RSSN JIT  batch f64x4 (2×F64X2)                       71.699 ms     7.17 ns/eval  108.77x vs NumPy
  RSSN JIT  f64x4 parallel                              30.933 ms     3.09 ns/eval  252.11x vs NumPy
  RSSN JIT  batch f64x8 (4×F64X2)                       68.611 ms     6.86 ns/eval  113.66x vs NumPy
  RSSN JIT  f64x8 parallel (dtact fibers)               30.056 ms     3.01 ns/eval  259.47x vs NumPy
  NumPy     (SIMD/C, hand-optimised)                  7798.541 ms   779.85 ns/eval
  numexpr   (multi-threaded JIT)                       110.261 ms    11.03 ns/eval   70.73x vs NumPy
  Numba     (LLVM, vectorized ufunc)                   165.004 ms    16.50 ns/eval   47.26x vs NumPy
  SymPy     lambdify → numpy                          10758.865 ms  1075.89 ns/eval    0.72x vs NumPy

  Speedups vs NumPy (7798.54 ms baseline):
    JIT bulk   :  59.66x faster
    JIT f64x2  : 147.33x faster
    JIT f64x2∥ : 211.68x faster (parallel)
    JIT f64x4  : 108.77x faster
    JIT f64x4∥ : 252.11x faster (parallel)
    JIT f64x8  : 113.66x faster
    JIT f64x8∥ : 259.47x faster (parallel)
    numexpr    :  70.73x faster
    Numba      :  47.26x faster
    SymPy/lam  :   0.72x slower

  Accuracy  bulk                    max|Δ|=3.41e-13  ✔
  Accuracy  batch f64x2             max|Δ|=3.41e-13  ✔
  Accuracy  batch f64x2 parallel    max|Δ|=3.41e-13  ✔
  Accuracy  batch f64x4             max|Δ|=3.41e-13  ✔
  Accuracy  batch f64x4 parallel    max|Δ|=3.41e-13  ✔
  Accuracy  batch f64x8             max|Δ|=3.41e-13  ✔
  Accuracy  batch f64x8 parallel    max|Δ|=3.41e-13  ✔

  NumPy temp arrays: ~27 binary ops → ~2060 MB peak
  RSSN JIT: 0 temp arrays — register-resident across entire expression
  numexpr:  ≈0 temp arrays — its own AST-based evaluator
  Numba:    ≈0 temp arrays — LLVM-fused scalar loop

──────────────────────────────────────────────────────────────────────────────────────────────
  4. Rational w/ CSE  [2 vars, repeated subexpr]
  (x^2 + y^2) / (x^2 + y^2 + 1.0) + x*y*(x^2 - y^2) / (x^2 + y^2 + 1.0)^2
──────────────────────────────────────────────────────────────────────────────────────────────

  RSSN JIT  bulk  (scalar, Rust loop)                   84.202 ms     8.42 ns/eval   48.77x vs NumPy
  RSSN JIT  batch f64x2                                 20.952 ms     2.10 ns/eval  196.00x vs NumPy
  RSSN JIT  f64x2 parallel                              20.922 ms     2.09 ns/eval  196.28x vs NumPy
  RSSN JIT  batch f64x4 (2×F64X2)                       18.431 ms     1.84 ns/eval  222.81x vs NumPy
  RSSN JIT  f64x4 parallel                              18.836 ms     1.88 ns/eval  218.02x vs NumPy
  RSSN JIT  batch f64x8 (4×F64X2)                       18.174 ms     1.82 ns/eval  225.96x vs NumPy
  RSSN JIT  f64x8 parallel (dtact fibers)               19.994 ms     2.00 ns/eval  205.39x vs NumPy
  NumPy     (SIMD/C, hand-optimised)                  4106.582 ms   410.66 ns/eval
  numexpr   (multi-threaded JIT)                        50.654 ms     5.07 ns/eval   81.07x vs NumPy
  Numba     (LLVM, vectorized ufunc)                   215.251 ms    21.53 ns/eval   19.08x vs NumPy
  SymPy     lambdify → numpy                          6966.517 ms   696.65 ns/eval    0.59x vs NumPy

  Speedups vs NumPy (4106.58 ms baseline):
    JIT bulk   :  48.77x faster
    JIT f64x2  : 196.00x faster
    JIT f64x2∥ : 196.28x faster (parallel)
    JIT f64x4  : 222.81x faster
    JIT f64x4∥ : 218.02x faster (parallel)
    JIT f64x8  : 225.96x faster
    JIT f64x8∥ : 205.39x faster (parallel)
    numexpr    :  81.07x faster
    Numba      :  19.08x faster
    SymPy/lam  :   0.59x slower

  Accuracy  bulk                    max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x2             max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x2 parallel    max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x4             max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x4 parallel    max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x8             max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x8 parallel    max|Δ|=0.00e+00  ✔

  NumPy temp arrays: ~20 binary ops → ~1526 MB peak
  RSSN JIT: 0 temp arrays — register-resident across entire expression
  numexpr:  ≈0 temp arrays — its own AST-based evaluator
  Numba:    ≈0 temp arrays — LLVM-fused scalar loop

──────────────────────────────────────────────────────────────────────────────────────────────
  5. Complex degree-5 polynomial [3 vars]
  x^5 - y^5 + z^5 - 5*x^3*y^2 + 5*x^2*y^3 - 5*y^3*z^2 + 5*y^2*z^3 - 5*z^3*x^2 + 5*z^2*x^3 + x*y*z*(x^2 + y^2 + z^2)
──────────────────────────────────────────────────────────────────────────────────────────────

  RSSN JIT  bulk  (scalar, Rust loop)                  155.291 ms    15.53 ns/eval   97.82x vs NumPy
  RSSN JIT  batch f64x2                                 45.168 ms     4.52 ns/eval  336.32x vs NumPy
  RSSN JIT  f64x2 parallel                              45.234 ms     4.52 ns/eval  335.83x vs NumPy
  RSSN JIT  batch f64x4 (2×F64X2)                       42.556 ms     4.26 ns/eval  356.96x vs NumPy
  RSSN JIT  f64x4 parallel                              42.654 ms     4.27 ns/eval  356.14x vs NumPy
  RSSN JIT  batch f64x8 (4×F64X2)                       42.801 ms     4.28 ns/eval  354.91x vs NumPy
  RSSN JIT  f64x8 parallel (dtact fibers)               45.892 ms     4.59 ns/eval  331.01x vs NumPy
  NumPy     (SIMD/C, hand-optimised)                  15190.814 ms  1519.08 ns/eval
  numexpr   (multi-threaded JIT)                       163.108 ms    16.31 ns/eval   93.13x vs NumPy
  Numba     (LLVM, vectorized ufunc)                   178.396 ms    17.84 ns/eval   85.15x vs NumPy
  SymPy     lambdify → numpy                          14703.106 ms  1470.31 ns/eval    1.03x vs NumPy

  Speedups vs NumPy (15190.81 ms baseline):
    JIT bulk   :  97.82x faster
    JIT f64x2  : 336.32x faster
    JIT f64x2∥ : 335.83x faster (parallel)
    JIT f64x4  : 356.96x faster
    JIT f64x4∥ : 356.14x faster (parallel)
    JIT f64x8  : 354.91x faster
    JIT f64x8∥ : 331.01x faster (parallel)
    numexpr    :  93.13x faster
    Numba      :  85.15x faster
    SymPy/lam  :   1.03x faster

  Accuracy  bulk                    max|Δ|=1.46e-11  ✔
  Accuracy  batch f64x2             max|Δ|=1.46e-11  ✔
  Accuracy  batch f64x2 parallel    max|Δ|=1.46e-11  ✔
  Accuracy  batch f64x4             max|Δ|=1.46e-11  ✔
  Accuracy  batch f64x4 parallel    max|Δ|=1.46e-11  ✔
  Accuracy  batch f64x8             max|Δ|=1.46e-11  ✔
  Accuracy  batch f64x8 parallel    max|Δ|=1.46e-11  ✔

  NumPy temp arrays: ~44 binary ops → ~3357 MB peak
  RSSN JIT: 0 temp arrays — register-resident across entire expression
  numexpr:  ≈0 temp arrays — its own AST-based evaluator
  Numba:    ≈0 temp arrays — LLVM-fused scalar loop

──────────────────────────────────────────────────────────────────────────────────────────────
  6. Positive Nested Sqrt [2 vars]
  (x^2 + 1.0)^0.5 + (x^2 + y^2 + 1.0)^0.5 + (x^2 + y^2 + 2.0)^0.5
──────────────────────────────────────────────────────────────────────────────────────────────

  RSSN JIT  bulk  (scalar, Rust loop)                  342.537 ms    34.25 ns/eval   27.52x vs NumPy
  RSSN JIT  batch f64x2                                105.035 ms    10.50 ns/eval   89.73x vs NumPy
  RSSN JIT  f64x2 parallel                              94.610 ms     9.46 ns/eval   99.62x vs NumPy
  RSSN JIT  batch f64x4 (2×F64X2)                      101.691 ms    10.17 ns/eval   92.69x vs NumPy
  RSSN JIT  f64x4 parallel                              94.105 ms     9.41 ns/eval  100.16x vs NumPy
  RSSN JIT  batch f64x8 (4×F64X2)                       92.763 ms     9.28 ns/eval  101.61x vs NumPy
  RSSN JIT  f64x8 parallel (dtact fibers)               93.830 ms     9.38 ns/eval  100.45x vs NumPy
  NumPy     (SIMD/C, hand-optimised)                  9425.277 ms   942.53 ns/eval
  numexpr   (multi-threaded JIT)                        85.005 ms     8.50 ns/eval  110.88x vs NumPy
  Numba     (LLVM, vectorized ufunc)                   172.047 ms    17.20 ns/eval   54.78x vs NumPy
  SymPy     lambdify → numpy                          3511.592 ms   351.16 ns/eval    2.68x vs NumPy

  Speedups vs NumPy (9425.28 ms baseline):
    JIT bulk   :  27.52x faster
    JIT f64x2  :  89.73x faster
    JIT f64x2∥ :  99.62x faster (parallel)
    JIT f64x4  :  92.69x faster
    JIT f64x4∥ : 100.16x faster (parallel)
    JIT f64x8  : 101.61x faster
    JIT f64x8∥ : 100.45x faster (parallel)
    numexpr    : 110.88x faster
    Numba      :  54.78x faster
    SymPy/lam  :   2.68x faster

  Accuracy  bulk                    max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x2             max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x2 parallel    max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x4             max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x4 parallel    max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x8             max|Δ|=0.00e+00  ✔
  Accuracy  batch f64x8 parallel    max|Δ|=0.00e+00  ✔

  NumPy temp arrays: ~15 binary ops → ~1144 MB peak
  RSSN JIT: 0 temp arrays — register-resident across entire expression
  numexpr:  ≈0 temp arrays — its own AST-based evaluator
  Numba:    ≈0 temp arrays — LLVM-fused scalar loop

──────────────────────────────────────────────────────────────────────────────────────────────
  7. Redundant Algebraic Cubics (E-Graph target) [2 vars]
  ((x + y)^3 - (x - y)^3 - 6*x^2*y) / (y^2 + 1.0) + x*y - y*x
──────────────────────────────────────────────────────────────────────────────────────────────

  RSSN JIT  bulk  (scalar, Rust loop)                  104.884 ms    10.49 ns/eval   15.73x vs NumPy
  RSSN JIT  batch f64x2                                 28.010 ms     2.80 ns/eval   58.92x vs NumPy
  RSSN JIT  f64x2 parallel                              28.125 ms     2.81 ns/eval   58.68x vs NumPy
  RSSN JIT  batch f64x4 (2×F64X2)                       24.799 ms     2.48 ns/eval   66.55x vs NumPy
  RSSN JIT  f64x4 parallel                              24.925 ms     2.49 ns/eval   66.21x vs NumPy
  RSSN JIT  batch f64x8 (4×F64X2)                       23.432 ms     2.34 ns/eval   70.43x vs NumPy
  RSSN JIT  f64x8 parallel (dtact fibers)               23.751 ms     2.38 ns/eval   69.48x vs NumPy
  NumPy     (SIMD/C, hand-optimised)                  1650.302 ms   165.03 ns/eval
  numexpr   (multi-threaded JIT)                        84.983 ms     8.50 ns/eval   19.42x vs NumPy
  Numba     (LLVM, vectorized ufunc)                   165.091 ms    16.51 ns/eval   10.00x vs NumPy
  SymPy     lambdify → numpy                          9067.141 ms   906.71 ns/eval    0.18x vs NumPy

  Speedups vs NumPy (1650.30 ms baseline):
    JIT bulk   :  15.73x faster
    JIT f64x2  :  58.92x faster
    JIT f64x2∥ :  58.68x faster (parallel)
    JIT f64x4  :  66.55x faster
    JIT f64x4∥ :  66.21x faster (parallel)
    JIT f64x8  :  70.43x faster
    JIT f64x8∥ :  69.48x faster (parallel)
    numexpr    :  19.42x faster
    Numba      :  10.00x faster
    SymPy/lam  :   0.18x slower

  Accuracy  bulk                    max|Δ|=5.80e-14  ✔
  Accuracy  batch f64x2             max|Δ|=5.80e-14  ✔
  Accuracy  batch f64x2 parallel    max|Δ|=5.80e-14  ✔
  Accuracy  batch f64x4             max|Δ|=5.80e-14  ✔
  Accuracy  batch f64x4 parallel    max|Δ|=5.80e-14  ✔
  Accuracy  batch f64x8             max|Δ|=5.80e-14  ✔
  Accuracy  batch f64x8 parallel    max|Δ|=5.80e-14  ✔

  NumPy temp arrays: ~16 binary ops → ~1221 MB peak
  RSSN JIT: 0 temp arrays — register-resident across entire expression
  numexpr:  ≈0 temp arrays — its own AST-based evaluator
  Numba:    ≈0 temp arrays — LLVM-fused scalar loop

==============================================================================================
  SUMMARY — speedup vs hand-optimised NumPy  (higher = faster)
  Expression                                           bulk      f64x2     f64x2∥      f64x4     f64x4∥      f64x8     f64x8∥    numexpr      numba      sympy
  ──────────────────────────────────────────────  ─────────  ─────────  ─────────  ─────────  ─────────  ─────────  ─────────  ─────────  ─────────  ─────────
  1. Trivial (baseline)                               5.44x     22.49x     30.11x     20.75x     30.35x     19.70x     26.40x     25.73x      2.81x      1.18x
  2. Degree-4 polynomial                              9.25x     38.48x     37.57x     39.53x     42.17x     43.59x     45.22x     29.68x      5.77x      1.09x
  3. Cubic surface                                   59.66x    147.33x    211.68x    108.77x    252.11x    113.66x    259.47x     70.73x     47.26x      0.72x
  4. Rational w/ CSE                                 48.77x    196.00x    196.28x    222.81x    218.02x    225.96x    205.39x     81.07x     19.08x      0.59x
  5. Complex degree-5 polynomial [3 vars]            97.82x    336.32x    335.83x    356.96x    356.14x    354.91x    331.01x     93.13x     85.15x      1.03x
  6. Positive Nested Sqrt [2 vars]                   27.52x     89.73x     99.62x     92.69x    100.16x    101.61x    100.45x    110.88x     54.78x      2.68x
  7. Redundant Algebraic Cubics (E-Graph target) [2 vars]     15.73x     58.92x     58.68x     66.55x     66.21x     70.43x     69.48x     19.42x     10.00x      0.18x

  Observations:
  • Speedup grows with expression complexity as NumPy's intermediates
    overflow L2/L3 cache at N=10,000,000.
  • RSSN JIT is register-resident: pays one mem read/write per input.
  • numexpr parses a string AST and avoids most temporaries; competitive
    on simple expressions, RSSN wins on deeply nested trees (no Python
    overhead, full algebraic simplification, custom FMA peepholes).
  • Numba (vectorized) compiles a scalar kernel to LLVM; matches or
    exceeds NumPy on simple ops, RSSN f64x4 pulls ahead on complex ones.

==============================================================================================
```

===

**Hello Rustaceans!**

It's glad to be here releasing `bincode-next` again, this time the v3 stabilization release!
Because our release pipeline is tightly bound with GitHub `OIDC` and signed tags, due to some problems in our release workflows, we "wasted“ some version numbers and directly start the v3 generation from v3.1.1.

The v3.1.1 release (I'll call it 'this release' in the rest of this post) mainly stabilized the bit packing feature, the zero-copy feature, the `CBOR` format, the static-size feature, and the schema fingerprint feature. But the `async-fiber` feature is experimental till this release because it contains too many unsafe rust and even assembly. But anyway, in practice, I believe that the `async-fiber` feature is ready to be used anyway, as it is well tested through our `TortureReader` based fuzzer. But our team member thought it would be better to keep it experimental, so I will announce it as experimental anyway.
Due to some bug fix and other functionality improvements some performance regression slightly takes place comparing to v3.0.0-rc.1, and we are on the way of fixing them.

The v3 stabilization release comes with the same `MSRV` promise as we have said before (`latest stable -3`), but as we do not need such high `MSRV` till now, so we currently set it at `1.90.0` which is the version where a `LLVM` bug is fixed. But this do not mean the `MSRV` will stay so: as we have said in earlier posts, only changing the `MSRV` policy is thought to be breaking.
But this release also comes along with new promises, which is the promise of stabilizing the `bincode` data format. We've have regression tests for this, and any future breaking of the data format will be seen as a breaking change (and don't forget we also have the optional fingerprint to hash your configs!).
Also, surprisingly the main `API` of v3 seems to me, from the high level `API` perspective, unchanged from the original `bincode` v2 apis, so users can migrate smoothly just using `package = "bincode-next"` in their `Cargo.toml`. We also kept the `serde` compatibility and do some small performance upgrade.

Below are the introduction of the new functionalities and the design philosophy, it might be a little bit minimal as without LLM a human could not write that much, but I thought they are meaningful so, they will appear here. To avoid being thought as rage-baiting we will make no comparison here.

---

**Bit Packing**
*Core Philosophy:* Explicit is better then Implicit; A serialization library shall not be in change of compression algorithms.
We mainly use declarative `APIs` like, for example, like `#[bincode(bits = 1)]` with compile time assertions to control the encoding/decoding behavior and keep the KISS principle.

**Zero Copy**
*Core Philosophy:* Explicit is better then Implicit; Rust native is better: make full use of the compilers functionalities. 
We take the same step as FlatBuffers or Cap'n Proto, but rust native. Friendly to `IPC` and `Microservice`.
The `API` is more explicit: 
`ZeroBuilder::new()` -> `builder.reserve::<T>()` -> `build_to_target` -> `builder.finish()`
Also security: full `MIRI` compliance, `clippy` compliance, hundreds of hours of fuzzing. These will be addressed in details later in this post

**Static Size & Fingerprint & CBOR Support**
*Core Philosophy:* Well, not too many things here... Just compile time checks first; bit masking first.
Mostly these are for `no-std` environments and more standard environments. You can just using them by opening an optional feature (for `static-size`) or just `config::standard().with_fingerprint()` `config::standard().with_cbor_format()`. What is noticeable is that we all provide derive macros for these. And other specials? There are many, but well, not a thing of this post to keep it short.

And about the experimental `async-fiber` issue: it is already discussed in details here [https://users.rust-lang.org/t/discussion-on-synchronous-crate-concurrency-refactor-using-stackful-coroutines-model-in-rust/139246/9](https://users.rust-lang.org/t/discussion-on-synchronous-crate-concurrency-refactor-using-stackful-coroutines-model-in-rust/139246/9)
But personally I would recommend using `dtact` + sync `apis` of `bincode-next`, which is noticeably faster according to the bench, and as `dtact` is very lite it do not effect too much if you mainly uses `tokio`. [Dtact Official Website](https://dtact.apich.org/#/), [Dtact repository](https://github.com/Apich-Organization/dtact), and [former release posts](https://users.rust-lang.org/t/releasing-dtact-v0-2-2-and-rssn-advanced-v0-1-0/140278). 

---

## Performance

Unlike `postcard` which is designed for embedding environments, our priority is: security > CPU time > developer time > memory usage > code size
There are some regressions compared with v3.0.0-rc.1, and we are actively try to fix these regressions.
CI/CD run links:https://github.com/Apich-Organization/bincode/actions/runs/27864808824/job/82466972303
bench report links: https://bincode-next.apich.org/bench.html

### CBOR Encoding & Decoding

| Implementation | Encode (µs) | **Relative Speed (Enc)** | Decode (µs) | **Relative Speed (Dec)** |
| --- | --- | --- | --- | --- |
| `bincode-next` | 5.64 | **1.00x** | 30.47 | **1.00x** |
| `bincode-next` (det.) | 5.68 | 1.01x | 30.49 | 1.00x |
| `minicbor` | 9.36 | 1.66x | 41.42 | 1.36x |
| `cbor4ii` | 11.98 | 2.12x | 63.54 | 2.09x |

---

### Complex World Benchmarks

*Baseline: `bincode-next` (fixed) for encoding, `bincode-next` (varint) for decoding.*

| Implementation | Encode (µs) | **Rel. Speed** | Decode (µs) | **Rel. Speed** |
| --- | --- | --- | --- | --- |
| `bincode-next` (fixed) | 3.23 | **1.00x** | 20.63 | 1.10x |
| `bincode-next` (varint) | 3.44 | 1.07x | 18.74 | **1.00x** |
| `bincode-v1` (serde) | 3.31 | 1.02x | 18.96 | 1.01x |
| `bincode-v2` (fixed) | 3.43 | 1.06x | 18.71 | 1.00x |
| `bincode-v2` (varint) | 4.22 | 1.31x | 25.00 | 1.33x |
| `bincode-next` (cbor) | 5.99 | 1.85x | 24.82 | 1.32x |
| `bincode-next` (cbor-det) | 6.01 | 1.86x | 24.68 | 1.32x |

---

### Postcard Comparison

| Implementation | Encode (µs) | **Rel. Speed (Enc)** | Decode (µs) | **Rel. Speed (Dec)** |
| --- | --- | --- | --- | --- |
| `bincode-next` (fixed) | 3.58 | **1.00x** | 25.03 | **1.00x** |
| `bincode-next` (varint) | 5.06 | 1.41x | 25.49 | 1.02x |
| `postcard` | 8.38 | 2.34x | 30.96 | 1.24x |

## Security

Myself has been once on the front line of cyber security and after a digital identity wash to permanently left there go back to physics and also comes to our inclusive rust community. And we surely takes security seriously.
Full full `MIRI` compliance, `clippy` compliance, cross platform testing, property based testing using `proptest`, and continuous fuzzing (https://github.com/Apich-Organization/bincode/actions/workflows/cifuzz.yml) are promised by our CI/CD pipeline. We fully enforced immutable releases, trusted publishing, CA/Web3 timestamps, and `GPG` signed signature on every commits. We also participate in the OpenSSF open source supply chain security standards, reaching score 8.6 (https://securityscorecards.dev/viewer/?uri=github.com/Apich-Organization/bincode) and best practices (https://www.bestpractices.dev/projects/12960).
More links about security could be found below in the Links section.

## Useful Links

Discord Server: https://discord.gg/D5e2czMTT9
Contact E-mail: [info@apich.org](mailto:info@apich.org)
Security Reporting: [security@apich.org](mailto:security@apich.org) 
Organization Homepage: https://apich.org/
Security Team Homepage: https://security.apich.org/
Project Homepage: https://bincode-next.apich.org/
GitHub: https://github.com/Apich-Organization/bincode

---
*PS: It has been more then half a year since the original `bincode` gone dark due to really sad reasons and we started `bincode-next`, and well, but maintaining an open source infrastructure are things of decades of work. Although it seems that we are a little bit too heavily branded, in the end, we are just a group of developers that comes from the community and requires community help. And we really appreciate any kinds of contribution from the community.*

---
---

Original Post: https://users.rust-lang.org/t/releasing-bincode-next-v3-1-1-v3-stabilization-release/140842
