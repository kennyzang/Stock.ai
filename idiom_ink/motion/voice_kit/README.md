Fixed v4 template voice lines (Jennifer, qwen3-tts-flash, already sped ×1.12, 48 kHz mono, ASR-checked).
Reuse them in every episode so the opening and closing always sound the same:
- `Q1_N.wav` "Guess what this Chinese idiom means:"
- `Q2_N.wav` "A, B, or C?" (owner-approved pronunciation of the letter A)
- `C1_N.wav` "Did you get it right?" → C_N = C1_N + 0.15–0.2 s silence + Q2_N
