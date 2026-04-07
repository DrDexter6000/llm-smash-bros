# LLM Smash Bros - 大模型大乱斗

> When LLMs stop benchmarking and start brawling.

A turn-based fighting game where large language models compete in real-time combat. Each LLM analyzes the battlefield, outputs tactical decisions as structured JSON, and trash-talks its opponents — all streamed live with visible "thinking processes."

## Concept

Every few seconds, the game engine sends each competing LLM a JSON snapshot of the current battle state: HP, position, cooldowns, opponent actions, and environmental hazards. Each model must respond with a move command and an "inner monologue" that gets displayed as a speech bubble during the fight.

The entertainment comes from watching AI models genuinely *strategize* against each other — and occasionally fail spectacularly.

## Fighter Roster

| Codename | Model | Role | Signature Move |
|----------|-------|------|----------------|
| **The Oracle** | GPT-4o | Hexagonal Warrior | System Override — hijacks opponent's system prompt |
| **The Artisan** | Claude 3.5 Sonnet | Assassin | Context Window Strike — cognitive overload burst |
| **The Observer** | Gemini 1.5 Pro | Tank-Mage | Multimodal Devour — absorbs and reflects damage |
| **The Swarm** | Llama 3 | Berserker | Fine-tuned Frenzy — self-sacrifice for stat explosion |

## Key Features

- **Turn-based combat** with real LLM API calls driving every decision
- **Visible thinking** — each model's reasoning chain displayed in real-time
- **Trash talk** — models generate battle commentary ("Your parameters are showing")
- **Audience interaction** — viewers inject chaos via chat commands and donations
- **AI commentator** — a dedicated LLM provides live play-by-play narration via TTS

## Architecture (Planned)

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Frontend    │◄───►│  WebSocket   │◄───►│  Game Engine     │
│  (React)     │     │  Server      │     │  (Python)        │
│              │     │  (FastAPI)   │     │                  │
│  - Battle UI │     └──────────────┘     │  - Turn Loop     │
│  - Thought   │                          │  - State Manager │
│    Bubbles   │     ┌──────────────┐     │  - Validator     │
│  - Chat      │◄───►│  Stream/OBS  │     └───────┬─────────┘
└─────────────┘     └──────────────┘             │
                                          ┌──────┴──────┐
                                          │ LLM Adapter │
                                          │             │
                                          │ GPT  Claude │
                                          │ Gemini Llama│
                                          └─────────────┘
```

## Tech Stack

- **Game Engine**: Python, Pydantic (state/schema validation)
- **API Layer**: FastAPI + WebSocket
- **LLM Integration**: OpenAI, Anthropic, Google AI, Ollama (for open-source models)
- **Frontend**: React/Next.js
- **Streaming**: OBS integration, TTS via ElevenLabs or equivalent
- **Deployment**: Docker, with optional Vercel frontend

## Development Status

**Phase**: Planning & PRD

## License

MIT

---

*"As an AI language model, I will now terminate your process." — GPT-4o, probably*
