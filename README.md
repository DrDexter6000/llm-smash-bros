<h1 align="center">LLM Smash Bros - 大模型大乱斗</h1>

<p align="center"><em>When LLMs stop benchmarking and start brawling.</em></p>

<p align="center"><strong>English | <a href="./README.zh.md">中文</a></strong></p>

<p align="center">
  <img src="./assets/llm_smash_banner.jpg" alt="LLM Smash Bros banner">
</p>

<div align="center">
  <pre>
╔══════════════════════════════════════════════════════════╗
║     LLM SMASH BROS — 大模型大乱斗                        ║
╠══════════════════════════════════════════════════════════╣
║  The Oracle (GPT-4o)        vs  The Artisan (Claude)    ║
║  HP: ████████░░ 80%          HP: ██████░░░░ 60%         ║
║  "Your loss function just    "I've seen better outputs   ║
║   yawned."                   from a Markov chain."      ║
╚══════════════════════════════════════════════════════════╝

Turn 12: The Oracle uses System Override!
💥 CRITICAL HIT! The Artisan takes 23 damage!
💥 FUMBLE! The Artisan panics and defends!

[ Live battle replay loading... ]
  </pre>
</div>

🎮 **An unserious-looking turn-based fighting game for a very serious question:**

**what happens when you force language models to read the room, make a plan, and throw hands under pressure?**

On the surface, this project is four AI fighters yelling at each other and occasionally eating a firewall 🔥

Under the hood, it is gradually evolving into a sandbox for exposing pieces of LLM capability in a form that is actually fun to watch: situation reading, tactical reasoning, strategy selection, failure handling, and eventually more interesting forms of AI-vs-AI play.

---

## 🤔 What even is this?

Every turn, a model receives a structured snapshot of the battlefield: health, energy, position, hazards, cooldowns, and the opponent's recent state. It must then decide what to do next.

That means choosing things like:

- ⚔️ whether to **attack**, 🛡️ **defend**, or ⏱️ **stall**
- 🎯 where to move on the grid
- ⚡ which ability is worth spending energy on
- 😎 how much confidence to fake while the arena is actively on fire

If it reasons well, it looks clever ✨

If it panics, times out, or emits cursed JSON, it **fumbles** in public 💥

Which, to be clear, is also content.

---

## 🎯 Why this exists

Leaderboards are useful, but they are also emotionally dead 💀

This project is trying to make model differences **watchable** 👀

Not just "which model scored higher," but:

- ⚡ who recognizes danger faster
- 📊 who manages resources better
- 🤪 who overcommits like a maniac
- 🧠 who adapts under pressure
- 💬 who talks the most trash while doing all of the above

The long-term goal is not "haha chatbot fight funny" — although yes, that part stays 😄

The long-term goal is to build a game-shaped arena where pieces of LLM ability can be observed more directly: **recognition, reasoning, strategy, and eventually richer forms of AI-versus-AI interaction** 🚀

---

## 📊 Current state

Right now, the real thing that exists is the **Python CLI battle engine** 🐍

- 🧪 **Mock mode** exists for cheap local matches and testing
- 🌐 **Live mode** uses real LLM APIs
- 💻 The current interface is terminal-first
- 🎨 The future spectator layer (GUI / animation / streaming theatrics) is still in development

So yes: the current version is closer to "AI fight club in a command line" than "full esports broadcast" 📺

That is fine. Rome was not built in a day, and neither was a tasteful multimodal cage match 🏛️

---

## 🥊 The roster

Current fighters include:

| Fighter | Model | Role |
|---------|-------|------|
| 🔮 **The Oracle** | GPT-4o | Balanced / Control |
| 🎨 **The Artisan** | Claude 3.5 Sonnet | Swift / Precise |
| 👁️ **The Observer** | Gemini 1.5 Pro | Tank / Patient |
| 🐝 **The Swarm** | Llama 3 | Berserker / Wild |

Each one is designed as both a combat kit and a personality joke 🤡

The point is not just to make them hit differently, but to make them **feel** different ✨

---

## 🎭 Design philosophy

This project should stay funny without becoming fake 🤡

- ✅ live matches should use **real** model output
- ✅ failure should be **visible** instead of politely hidden
- ✅ strategy should matter more than random nonsense
- ✅ trash talk should support the spectacle, not replace it
- ✅ the system should gradually reveal more of what a model is actually good at

**In other words: comedy outside, evaluation goblin inside** 🎪🧙

---

## 🚀 If you want to poke it

Current entrypoint:

```bash
cd backend
python -m llm_smash
```

That runs a mock match by default 🎯

For live battles, configure `backend/.env` and run:

```bash
cd backend
python -m llm_smash --live
```

---

## 👨‍💻 For developers

📋 Repo instructions: [`AGENTS.md`](./AGENTS.md)

📚 Development SSOT: [`docs/dev/README.md`](./docs/dev/README.md)

---

*"As an AI language model, I will now terminate your process."* 🤖⚡

**— GPT-4o, probably**
