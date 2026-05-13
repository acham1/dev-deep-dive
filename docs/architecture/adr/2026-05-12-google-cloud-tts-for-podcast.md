# ADR: Gemini 3.1 Flash TTS for Podcast Generation

## Date

2026-05-12

## Context

Weekly Deep Dive needs a TTS provider to convert written reports (~10-12K chars each) into podcast episodes. The project already runs on GCP. Options considered:

- **Gemini 3.1 Flash TTS** (Preview) — Newest model, prompt-controllable voice style/tone/emotion, token-based pricing (~$0.45/episode), no free tier
- **Chirp 3: HD** — Best quality in Cloud TTS, 1M chars/month free, $30/1M chars after, 30 voice presets but no prompt-based style control
- **Neural2** — Good quality, 1M chars/month free, $16/1M chars, now labeled "Legacy"
- **ElevenLabs** — Best voice quality overall, 10K chars/month free, separate billing/account
- **OpenAI TTS** — $15/1M chars, no free tier, separate API key

## Decision

Use Gemini 3.1 Flash TTS with a detailed voice style prompt.

## Consequences

- **Positive:** Prompt-controllable voice style lets us define a specific podcast persona ("conversational explainer, relaxed, intelligent, plainspoken, lightly skeptical") without being locked to preset voices. This is unique to the Gemini TTS models.
- **Positive:** Cost is ~$0.45/episode, ~$2/month at weekly cadence. Negligible for a hobby project.
- **Positive:** Uses the same Google Cloud auth — no additional API keys or providers.
- **Negative:** No free tier (Chirp 3: HD offers 1M free chars/month). Acceptable given the low absolute cost.
- **Negative:** Currently in Preview — API surface may change. Fallback to Chirp 3: HD if it breaks or is discontinued.
- **Negative:** Token-based pricing is less predictable than per-character, though at this volume the difference is immaterial.
