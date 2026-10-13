# Prior art and how this skill differs

| Project | Approach | What we took | What we do differently |
|---|---|---|---|
| **Remotion** (+ its official agent skills) | React components, `useCurrentFrame()`, a frame-accurate renderer | The determinism-first mindset; time as the only input | Plain HTML/CSS/JS with no build step or React; a craft layer (grammar, rubric, critic) on top of the renderer. Check Remotion's licence for commercial use. |
| **HyperFrames** (HeyGen, Apache-2.0) | HTML compositions with data attributes, headless Chrome to MP4, a router of agent skills | HTML-first, so an LLM can write it directly; agent workflows by video type | A seekable pure `render(t)` (no timeline attributes); voice-word clock; sound design in code; an independent critic agent with instruments |
| **After Effects practice** | Graph editor, motion blur, expressions (`valueAtTime`, overshoot), precomps | Easing by intent, overshoot and follow-through, stagger offsets, 180° shutter, parallax precomps | Encoded as functions (`spring`, `kf`, `stagger`, `blurFrom`, `camera`) |
| **Animation principles skills** | The Disney 12 mapped to motion graphics | Timings for text (15–25 f), transitions (10–20 f), anticipation (2–4 f) and follow-through (4–8 f) | Measured and enforced in QC, not just suggested |

Positioning: **a studio, not just a renderer.** The renderer is about 400 lines. The value is the grammar, the agents and the gates.
