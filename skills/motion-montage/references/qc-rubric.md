# QC rubric: the critic's scoresheet

The critic scores the **finished render**, never the code. It uses instruments (`qc_video.py`, `render.mjs --qc`)
and eyes (the contact sheet, a still from every scene, the 2 s around every cut, the first and last frames).

## Hard fails (any one blocks delivery)

| # | Check | Instrument |
|---|---|---|
| H1 | Text off-frame or in an unsafe zone on a settled frame | `render.mjs --qc` + stills |
| H2 | Two text blocks colliding on a settled frame | `--qc` OVERLAP + stills |
| H3 | Dead air: frozen picture > 0.7 s (except the final hold ≤ 2 s) | `qc_video.py` DEAD AIR |
| H4 | Caption ≠ spoken words, or on-screen words nobody says (except labels/handle/logo) | timeline vs composition |
| H5 | Loudness outside −14 ±1 LUFS or true peak > −1 dBTP (social) | `qc_video.py` |
| H6 | Music audibly louder than the voice, or the voice muffled or robotic | listen + spectrum print |
| H7 | Broken RTL shaping, tofu boxes or a missing font | stills |
| H8 | An empty frame 0, or an empty mid-transition frame | stills at 0 and at each cut centre |
| H9 | Anything from the negative list in SKILL.md | eyes |
| H10 | Assets without rights, or a redrawn/generated logo | asset list |

## Scored categories (0–10, ship at ≥ 8 in every category)

| Category | 10 looks like | 5 looks like |
|---|---|---|
| **Composition** | Frame filled with intent, one focal point, consistent edges, balanced vertical centre | Small type in a corner, empty halves, things floating |
| **Typography** | Scale contrast 3–8×, fitted hero lines, 2 families, perfect tracking and optical alignment | Similar sizes, default tracking, three fonts |
| **Motion quality** | Eased, staggered and overlapping; springs settle once; motion blur on fast moves | Linear or simultaneous; bouncy; no blur on whips |
| **Sync** | Every accent within ±50 ms of its word or beat; cuts just ahead of the line | Highlights late, cuts mid-word |
| **Edit and transitions** | 3–5 transition types chosen by meaning, never two the same in a row; flow across cuts | One wipe repeated, or random novelty transitions |
| **Life** | Camera always alive, parallax, a secondary action per scene, no stillness without a reason | A slideshow of static cards |
| **Sound** | The bed supports, SFX are sparse and tight, ducking is invisible, the silence is used once | SFX on everything, music fighting the voice |
| **Brand and taste** | Consistent palette and style lock; it looks like a studio made it | Generic, template-y, "AI" |

## Output format

```
SCORE  composition 8 · type 9 · motion 7 · sync 9 · edit 8 · life 6 · sound 8 · brand 9
HARD   none   (or: H3 dead air 13.30–14.00s)
FIX    1. [motion] S04 headline rises with no stagger — each 0.06, add blur:6        → montage-motion
       2. [life]   S06 static for 1.1 s before the cut — add push-in 1.00→1.04          → montage-motion
       3. [edit]   cuts 3 and 4 are both `panel` — make cut 4 `push up`                 → montage-editor
VERDICT  LOOP (2 categories < 8)   |   SHIP
```

Each fix names the time, the problem, a concrete change and the owning agent. Vague notes like "make it pop" aren't allowed.
