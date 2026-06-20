# Releasing bincode-next v3.1.1 (v3 stabilization release!)

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

Original Post: https://users.rust-lang.org/t/releasing-bincode-next-v3-1-1-v3-stabilization-release/140842/
