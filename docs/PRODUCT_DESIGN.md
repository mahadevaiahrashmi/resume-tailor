# Product Design — Resume Tailor

## Design principles

1. **One screen, one action.** Everything needed to generate is on a single
   page; the primary button is unmistakable.
2. **Honest by default.** Copy and prompt reinforce that the tool reframes real
   experience rather than inventing it.
3. **Show, don't surprise.** Engine detection, status, and a live preview keep
   the user informed at every step.
4. **Local & private, said plainly.** Privacy is stated in the UI, not buried.

## Layout

A two-panel responsive layout (collapses to one column under 860px):

```
┌─────────────────────────────┬─────────────────────────────┐
│  FORM PANEL                 │  RESULT PANEL               │
│  • AI engine + model        │  • Status banner            │
│  • Job description *         │  • Download (4 buttons)     │
│  • Your current resume *     │  • Preview (Resume | Cover) │
│  • Extra instructions       │                             │
│  • [ Generate documents ]   │                             │
└─────────────────────────────┴─────────────────────────────┘
```

- **Form panel (left):** inputs top-to-bottom in the order people think —
  engine, the job, their resume, then optional nuance.
- **Result panel (right):** status first, then downloads, then a tabbed preview
  (Resume / Cover letter).

## Visual language

A restrained, professional palette that mirrors the generated documents so the
preview feels like the real output:

| Token | Value | Use |
| --- | --- | --- |
| `--navy` | `#1F3B5B` | Headers, name, primary button, section titles |
| `--rule` | `#2E5A88` | Section underlines, focus ring |
| `--gray` | `#555` | Secondary/contact text |
| `--ok` | `#1D7A46` | Success status |
| `--err` | `#B3261E` | Error status, required-field marker |

Type is the system UI stack; documents use Helvetica/Arial for parity between
PDF and Word.

## Interaction states

The status banner is the single source of truth for "what's happening":

| State | Trigger | Appearance / copy |
| --- | --- | --- |
| **Idle** | Page load | Neutral: "Fill the form and click Generate." |
| **Working** | Submit | Amber, button disabled: "Generating… the first run on a local model can take a minute." |
| **Error** | 4xx / network | Red, pre-wrapped: the server's detail or "Network error: …". |
| **Done** | 200 | Green: "Done. Download your 1-page resume and cover letter below." |

Downloads and preview are hidden until a successful run, then revealed together.

## Engine selection UX

- Each option is labelled, and unavailable engines are suffixed
  "— not detected" both server-side (in the `<option>`) and in the live hint.
- On load, `app.js` fetches `/providers` and **auto-selects the first detected
  engine**, so a user is never pointed at something they haven't installed.
- A per-engine hint explains install steps and shows a ✓ when detected.
- An optional **model** box lets power users override the default model without
  touching environment variables.

## Preview design

- Two tabs (Resume / Cover letter) toggle visibility; the active tab uses the
  navy fill for a clear selected state.
- The preview is built with **DOM text nodes**, never `innerHTML`, so anything
  the model emits is shown as text and cannot inject markup (see
  [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md#security)).
- The preview styling echoes the PDF/DOCX (ruled section headings, right-aligned
  dates, bulleted achievements) so what users see matches what they download.

## Copy & tone

Short, plain, reassuring. Examples in the UI:

- "Nothing is uploaded to us — generation runs locally via the engine you pick."
- Required fields marked with a red `*`.
- Errors are shown verbatim from the server so the cause is actionable.

## Accessibility

- Labels are associated with every control via `for`/`id`.
- Visible focus ring (`outline: 2px solid --rule`) on inputs.
- Color is never the only signal — status also changes its text.
- Layout reflows to a single column on small screens.

## Future design ideas

- A diff view (original vs. tailored) to build trust.
- Selectable document themes/templates.
- Inline editing of the preview before download.
- Progress streaming for long local-model runs.
