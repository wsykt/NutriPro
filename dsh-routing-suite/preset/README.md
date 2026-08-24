# dsh-router-standard

> # ⚠️⚠️⚠️ 重要勘误与道歉（必读） ⚠️⚠️⚠️
>
> ## 我不需要被造神，也不配被造神
>
> 这篇 README 顶部必须放这段话：**我错了，而且错得很有代表性。**
>
> - **论文不撤回**，但其中**理论解释部分（双吸引子假设 A1–A4 及"god/ghost"、"自路由不可能"等强归因）已正式标注作废**。
> - **心路历程**：我最初把 "We need / Let me" 的差异当成"官方刻意设计的双模式"；后来才意识到那更可能是**一条原生深度路径 + 一条后压未收敛的极简路径**之间的**断层/断裂带**。这个断层**本身就像一层路由层**——我们实际做的是把它当路由层用，实现了 "Let me / We need" 自路由。
> - **我们做对了一件事，也请记住这件事**：**利用后训练的一个小缺陷（断层/断裂带），我们实现了 V4 Flash 能力的可复现提升**——这不是我聪明，是那个缺陷恰好可被工程利用。
> - **Pro 是另一场完全不同的硬仗**：雷霆大思考、工具面敏感、内部路由不稳定。**我已经找到方向**（黑盒 logprobs / 嵌入向量层逆向 / 语义锚点指纹），初步数据已在仓库。这条路我会继续用实测走，而不是用叙事走。
>
> 📄 完整勘误声明：[docs/statement.md](docs/statement.md) ｜ 道歉函：[docs/apology.md](docs/apology.md)

**Task-aware reasoning-mode router for DeepSeek Harness.** One preset, two
**routing modes** (v0.2.0 naming), plus the measured three-band axis behind them:

| routing mode | first request | thinking shape |
|---|---|---|
| **standard（标准路由预设）** | 分类 persona（spec/react/weak）+ 完整 prompt sections + 分带首轮工具面 | 按分类带行动：react 直接产出、spec 先读后改、weak 内路由（每轮近距离引导） |
| **spec（spec 路由预设）** | 分类 persona（spec/react/weak）+ 完整 prompt sections | **雷霆大思考**：首轮超长思维链（101K 推理 0 行动是其特征，不是缺陷） |

> 选择：安装两个预设之一（Router Standard / Router Spec，见 Usage）。
> `dev_router_status` 显示当前路由模式。

> This is a research artifact. It encodes a measured property of DeepSeek V4
> Pro / V4 Flash: model behavior along the persona axis is **not a continuum**
> — it collapses into a few stable regions separated by phase transitions.
> The router therefore quantizes to the stable regions instead of pretending
> the axis is continuously tunable.

## v0.3.0 — real-assembly-chain fixes

v0.2.x shipped routing logic that was validated against bare-API probes but
was broken on the REAL DeepSeek Harness assembly chain. v0.3.0 fixes all of it,
verified against `@deepseek-ai/dsh-agent-loop` (0.1.0-rc.7) event ordering:

- **First-turn routing actually works** (issue #13): the loop claims the inbox
  BEFORE assembling the system prompt, and `inbox.claim()` emits the
  agent-scoped `agent/inbox/claimed` event synchronously — the router captures
  the first REAL user message there (`source.kind === 'user'` only), so the
  first request is classified instead of unconditionally falling into weak.
  (The captured text is CLASSIFIED, not fed to bandOf raw — the old capture
  path silently mapped every captured message to the spec band.)
- **Near-field guidance moved to `agent/pre-step`** (issues #34/#36/#55):
  `session/event` never fires inside agent-plane presets (dsh-scope filters
  it out of entry-local realms), so the old inbox re-append never delivered
  guidance — and wherever it did fire, the `next-step` append forced a SECOND
  model request per user message (the 2× API-call spike). The guide is now
  inserted into `decision.messages` at `agent/pre-step`: same request as the
  user message, near-field, cache-neutral, zero extra round-trips.
- **Fixes**: missing `extractText`/`bandOf` imports in both bootstrap files
  (#11) — the `session/event` handlers crashed with ReferenceError whenever
  they did fire; `sessionMode` ignoring plugin-origin messages when pinning
  the band; `router.test.mjs` import path; preset.yml YAML quoting (#53);
  subagent-session skip (#5); session-selected model from
  `assembled.variables` (#9); the RL-standard mode of the spec preset now
  returns the assembly untouched after the first tool/call (#44).
- **New**: `router.integration.test.mjs` replays the real claim → assemble →
  pre-step ordering against the actual bootstrap code.

## What it does

**router-standard**: reads the session's first REAL user message, classifies
the task (build → react / fix → spec / ambiguous → weak), and on the first
model request injects the matching persona while keeping the full prompt
sections; the first-turn core tool surface follows the band
(spec=read/edit/glob/grep, react=read/write/edit, weak=read/write/edit, each
plus the platform shell). Weak-band sessions also get a near-field routing
guide in the SAME request as every real user message.

**router-spec**: same routing core with the deep-think-first branding; keeps
the v0.2.0 dual-mode code path (`routerMode`), so a copy configured with
`routerMode: standard` still gets the RL-interface first turn (RL sentence +
shell/str_replace_editor) with full sections restored after the first durable
tool/call.

After the first durable tool call the full Standard catalog is exposed and the
router stops touching anything. The mode is derived from durable session
events, so resume/reload keeps it. The plan-mode prompt section is preserved,
so plan boundaries do not reset the model's focus.

## The three measured behavior bands

Fine-grained probing (21 mode points × n=2, official API, reasoning_effort=max)
on V4 Pro shows behavior along the persona axis collapses into **three bands**:

| band | mode | measured behavior |
|---|---|---|
| `spec` | 0 – 0.19 | stable plan-collective (`We` trajectories, let-me ≈ 0) |
| `mixed` | 0.2 – 0.49 | **transition trap**: unstable mixing of `We`/`The`/`Let` |
| `react` | 0.5 – 1.0 | stable doer (`The`/`Let` first-person, we ≈ 0) — 11 mode values behave alike |

V4 Flash is threshold-like (0–0.5 all spec side, jumps at 0.75+). The numeric
`dev_router_mode` interface is kept, but it quantizes to the three bands — the
transition band is never selected automatically.

## Why: dual-attractor RL policy

Evidence across projects (see `docs/paper.md` and `docs/experiments.md`):

- The **same model** reaches top-band scores under spec conditions on a
  maintenance benchmark (Project2: minimal 99/96, anchored 98/99) and under
  react/code conditions on a greenfield build task (Mario: 10/10), while the
  wrong mode scores 91 / 6 respectively — a ~10-point swing from prompt
  conditioning alone ("god/ghost duality").
- Persona is the dominant trigger (one-sentence swap flips the trajectory);
  tool-schema surface is a secondary condition; catalog text in a user message
  has no effect.
- Behavior is path-committed: once anchored, expanding the tool catalog
  perturbs at most one reasoning block and never flips the mode.
- Intermediate personas are **out-of-distribution** (training-distribution
  gap), which is the measured unstable band.

The model cannot self-route: P3 (same persona, task swap → trajectory
unchanged), P5 (router personas → doer attractor absorbs the instruction) and
P8 (domain-overlap scan) show the only internal-routing window is a WEAK
persona + few-shot routing instruction (lean, not flip; discrimination
+2.3..+3.3). There is no reward signal for switching modes mid session, and
the behavior phase transition means the model commits on the first request.
**Mode selection must come from outside** — a human (the "streamer"), a
heuristic classifier, or a learned router. This preset is the automated
version of that external routing.

## Usage

**Two presets** (v0.2.0): install one or both under `~/.dsh/.agent-presets/`:

```powershell
# 标准路由预设（RL 接口还原，默认推荐）
$target = Join-Path $env:USERPROFILE '.dsh\.agent-presets\router-standard'
Copy-Item -Recurse .\preset\router-standard $target

# spec 路由预设（深度思考优先）
$target = Join-Path $env:USERPROFILE '.dsh\.agent-presets\router-spec'
Copy-Item -Recurse .\preset\router-spec $target
# NOTE: installed copies must keep unique module filenames
# (the loader caches ESM modules by URL; do not overwrite in place)
```

Restart DSH, start a new session, pick **Router Standard (experimental)**
(RL-interface, think-act loops) or **Router Spec (experimental)**
(deep-think-first, the long first-turn chain is the point).

- `dev_router_status` — current mode, band, persona, core tools, override state
- `dev_router_mode <spec|weak|mixed|react|0-100|0.0-1.0|auto>` — explicit mode
  (numeric inputs quantize to the three bands)
- `dev_mode_subagent <spec|react|balanced> <task>` — run one task in a
  DIFFERENT reasoning mode inside a fresh isolated context (its own system
  prompt), leaving the current trajectory untouched. Mode isolation is the
  only reliable way to change modes mid-session: mid-session persona switches
  invalidate the whole prefix cache, tail personas are ineffective (P6), and
  the native subagent inherits this persona.

**One preset, auto-matched per model.** There is no Pro/Flash split to
configure: `personaFor(mode, modelId)` reads the session's model route and
selects the measured optimum automatically — Pro → w6c (spec sentence +
classify instruction, no anchors; 24/24 = 100% routing, P24), Flash → w7 +
recall/anti-runaway anchors (96% routing; 100% single-task completion, P23).
The model is fixed at the first request (path commitment), so the persona is
locked for the session; switching the GUI model starts a new session with the
matching configuration.

**Depth-adaptive guidance (v20, thinking efficiency).** Per-message guidance
is dispatched by task complexity (`isComplexTask`: length or architecture
keywords):
- **simple tasks** → fast-convergence guide (P30: 1 step, zero waste);
- **complex tasks** → decision-closure deep guide: "Think deeply about the
  architecture, edge cases, and integration points. Do not spend reasoning
  on the environment or tooling. Produce when your information is complete.
  End each reasoning block with a decision or an information need." —
  P30: depth +12% AND faster convergence (8.0 vs 8.3 steps), 3/3 completion.
- Rumination (environment suspicion / re-confirmation) is suppressed by the
  anti-runaway anchor: measured 0.0-0.3% of reasoning tokens.

## Tests

```sh
node --test router.test.mjs   # 11 tests: classification, bands, personas, plan-section survival
```

## Files

- `preset/agent.cordis.yml` — full rc.6 Standard composition + router row
- `preset/router-core.mjs` — pure routing logic (zero deps, unit-testable)
- `preset/router-bootstrap.mjs` — Cordis plugin (zero external imports)
- `router.test.mjs` — unit tests
- `docs/paper.md` — the theory + experiments write-up
- `docs/experiments.md` — full data tables

## Evidence & attribution

- Trajectory trigger matrix, dual-model matrices, and the 21-point phase probe:
  `dsh-probe` (this repo's sibling scripts live in the paper's appendix tables).
- Project2 evaluation data: [xiaobright/modeltest](https://github.com/xiaobright/modeltest)
  (V4.1b, frozen) — minimal 99/96, standard 91, PTC 92, anchored-standard 98/99.
- Two-phase anchoring preset: [xiaobright/dsh-anchored-standard](https://github.com/xiaobright/dsh-anchored-standard)
  (MIT). The router's first-turn anchoring is a plugin-level port of its
  `tool-bootstrap` mechanism.
- DeepSeek Harness official `minimal` preset snapshot
  (`sends the exact RL prompt and schemas` test) — the spec persona and the
  RL-alignment claim.

## License

MIT. `preset/agent.cordis.yml` derives from the DeepSeek Harness Standard
preset (MIT); original attribution in `NOTICE`.
