**Hello Rustaceans!**

Today we are releasing dtact v0.2.2 and rssn-advanced v0.1.0, both of which are experimental, high-performance projects currently under development. Dtact is an async concurrent engine, and rssn-advanced is a new generation symbolic core for rssn. Both will be detailed below.

## Dtact

Dtact is a coordinative, truly lockless async runtime designed for maximum work coordination speed and the highest throughput. In short, we mainly utilized a P2P network, a Lock-Free Context Arena, and a Zero-Copy Future Migration to achieve this. For a detailed analysis of the architecture, please refer to https://dtact.apich.org/ and https://github.com/Apich-Organization/dtact. The website's UI was written by AI—because we really aren't that good at writing UI, so please forgive us for that. A detailed benchmark report and CI run links can also be found on the official website, but in short, we can see the following chart (CI run: https://github.com/Apich-Organization/dtact/actions/runs/26011780070/job/76453764923):

### Task Spawn Efficiency

This benchmark measures the time required to spawn and execute a batch of asynchronous tasks.

| Task Scale | Runtime | Min Bound | Mean | Max Bound | Dtact Speedup |
| --- | --- | --- | --- | --- | --- |
| **1M** | Dtact | 103.92 ms | 104.92 ms | 105.94 ms | <br>**6.31x faster** 
 |
|  | Tokio | 648.02 ms | 662.11 ms | 676.42 ms | Reference 
 |
| **100k** | Dtact | 11.667 ms | 11.807 ms | 11.954 ms | <br>**5.34x faster** 
 |
|  | Tokio | 61.064 ms | 63.067 ms | 65.043 ms | Reference 
 |
| **10k** | Dtact | 1.9672 ms | 2.0144 ms | 2.0620 ms | <br>**2.63x faster** 
 |
|  | Tokio | 5.1595 ms | 5.2986 ms | 5.4395 ms | Reference 
 |
| **1k** | Dtact | 152.301 µs| 157.731 µs | 163.311 µs | <br>**4.76x faster** 
 |
|  | Tokio | 719.65 µs | 750.891 µs | 783.411 µs | Reference 
 |

### Yield Efficiency

This test measures the time taken for 10 concurrent tasks to perform 100 cooperative `yield_now` operations each.

| Test Case | Runtime | Min Bound | Mean | Max Bound | Comparison |
| --- | --- | --- | --- | --- | --- |
| **10 tasks** | Dtact | 795.651 µs | 827.511 µs | 860.191 µs | ~4.41x slower 
 |
|  | Tokio | 179.981 µs | 187.731 µs | 195.651 µs | <br>**4.41x faster** 
 |

### Work Deflection (Hot Core) Performance

This benchmark simulates task dispatching and throttle coordination under heavy load imbalances across a multi-core scheduler.

| Task Scale | Runtime | Min Bound | Mean | Max Bound | Dtact Speedup |
| --- | --- | --- | --- | --- | --- |
| **10M** | Dtact | 1.6624 s | 1.6792 s | 1.6962 s | <br>**4.13x faster** 
 |
|  | Tokio | 6.8482 s | 6.9386 s | 7.0291 s | Reference 
 |
| **100k** | Dtact | 17.472 ms | 17.659 ms | 17.847 ms | <br>**2.84x faster** 
 |
|  | Tokio | 49.110 ms | 51.112 ms | 53.114 ms | Reference 
 |
| **10k** | Dtact | 2.4961 ms | 2.5315 ms | 2.5675 ms | <br>**2.31x faster** 
 |
|  | Tokio | 5.7240 ms | 5.8411 ms | 5.9605 ms | Reference 
 |
| **1k** | Dtact | 273.791 µs | 285.231 µs | 297.07 µs | <br>**2.70x faster** 
 |
|  | Tokio | 739.641 µs | 769.841 µs | 801.701 µs | Reference 
 |

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