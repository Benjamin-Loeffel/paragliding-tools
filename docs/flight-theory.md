# Flight theory — a cookbook

A **cookbook for the theory exam**: one fixed procedure per question type, step by step.
No derivations you don't need — but every formula is explained once in plain words, so you
don't just memorise it.

!!! note "What this is and isn't"
    A personal summary, **not official exam material**. All drawings are original. The numbers
    are typical values of the kind that appear in exercises. What counts is always the current
    published material of SHV/FSVL and the Swiss FOCA.

**How to use it:** read chapter 1 first (the two formulas). After that you can jump straight to
the recipe that matches your question. The numbers worth memorising and the most common traps
are at the end.

---

## 1 · The two formulas — in plain words

Almost everything in flight theory hangs on **two formulas built the same way**. Understand one
and you understand both.

### How hard does the air brake a body?

Picture holding your hand out of a car window. What makes the pressure on your hand bigger?

1. **The shape.** A flat hand brakes harder than a narrow, edge-on hand. That shape property is
   the **c<sub>D</sub> value** (in German exam material: c<sub>W</sub>, *W* for *Widerstand*).
   Small value = good shape.
2. **The size.** The whole hand brakes harder than one finger. What counts is the area facing the
   airflow — the **frontal area**.
3. **How thick the air is.** Dense down in the valley, thin high up. Thin air brakes less. That
   "thickness" is the **air density**, written with the Greek letter **ρ** ("rho").
4. **How fast you go.** And this is the important one: at double the speed the pressure is
   **not double but four times** as large.

Together that gives the drag formula:

> **D  =  c<sub>D</sub> &middot; &frac12; &middot; &rho; &middot; v&sup2; &middot; A**

| Symbol | Name | In plain words |
|---|---|---|
| **D** | drag | how hard the air brakes (in newtons) |
| **c<sub>D</sub>** | drag coefficient | how good or bad the **shape** is |
| **ρ** | air density | how **thick** the air is |
| **v** | speed | how **fast** the air flows past |
| **A** | frontal area | how **big** the body looks from the front |

The `½` is only a conversion factor so the units work out. You never have to evaluate it — it
cancels in every exam question.

### And lift?

Exactly the same formula, with the **lift** coefficient c<sub>L</sub> and the **wing** area S:

> **L  =  c<sub>L</sub> &middot; &frac12; &middot; &rho; &middot; v&sup2; &middot; S**

!!! tip "The one sentence that answers 35 questions"
    **Only speed enters squared. Shape, area and air density enter linearly.**

| Double this | Drag (and lift) becomes |
|---|---|
| shape c<sub>D</sub> | double |
| area | double |
| air density ρ | double |
| **speed v** | **four times** |

Keep this little table in your head:

| v becomes | ×2 | ×3 | ×4 | ÷2 |
|---|---|---|---|---|
| drag becomes | **×4** | **×9** | **×16** | **÷4** |

---

## 2 · Recipes for numerical questions

### Recipe 1 — "what happens to drag if …"

Typical question: *A body produces 300 N of drag at 30 km/h. How much at 60 km/h?*

**Procedure**

1. Identify **what changes**: speed, area or air density?
2. Form the ratio **new ÷ old** of that one quantity.
3. If it is the **speed** → **square** the ratio. Otherwise → leave it.
4. **Multiply** the old drag by it.

**Example:** 30 → 60 km/h. Ratio = 2. Speed ⇒ square it: 2² = 4. So 300 N × 4 = **1,200 N**.

**Second example:** area 2 m² → 4 m². Ratio = 2. Area ⇒ **don't** square. So 300 N × 2 = **600 N**.

!!! warning "The trap"
    Data such as "frontal area 0.75 m²" or "at sea level" is often pure **distraction**. If it
    doesn't change, it cancels — it never appears in the arithmetic.

### Recipe 2 — comparing c<sub>D</sub> values

Typical question: *Compared with a body of c<sub>D</sub> 1, a body with c<sub>D</sub> 0.33 produces …*

**Procedure**

1. **Divide**, never subtract: 1 ÷ 0.33 = 3.
2. The **smaller** c<sub>D</sub> has **less** drag.
3. Read off: three times less drag.

| Comparison | how the answer is phrased |
|---|---|
| 0.5 vs 1 | 2 times less |
| **0.33** vs 1 | **3 times less** |
| 0.2 vs 1 | 5 times less |
| 0.05 vs 1 | 20 times less |
| **1.3** vs 1 | **30 % more** |

!!! warning "The trap"
    0.33 is **not** "30 % less" — that would be 0.7. Values **close to 1** call for percentages,
    values **far below 1** for factors.

**The four bodies that appear in the exam figure** — learn once, score several times:

| Shape | c<sub>D</sub> |
|---|---|
| hollow shell, opening **facing** the wind (like a rescue parachute) | **1.3** |
| flat plate perpendicular to the flow | **1.0** |
| teardrop **reversed** (point first) | **0.17** |
| teardrop **correct** (round nose first, point aft) | **0.08** |

Mnemonic: *parachute > board ≫ teardrop reversed > teardrop correct.*

And the insight behind it: **the same teardrop turned around has twice the drag.** Drag arises
mostly **at the back** — the flow has to close cleanly again at the tail. That is why a tail
fairing on a harness helps more than a nose fairing.

### Recipe 3 — drag at altitude

The higher you go, the thinner the air, the less drag. One memorised row is enough:
**about 10 % less per 1,000 m.**

| Altitude | drag / air density |
|---|---|
| 1,100 m | **90 %** |
| 2,200 m | **81 %** |
| 3,300 m | **72 %** |
| 4,400 m | **64 %** |
| ~5,500 m | **50 %** (density halved) |

**Procedure:** round the altitude to the nearest 1,000 m step, read the row. Done.

Two related questions:

- *The decrease is not linear.* Density drops **faster low down** than high up — which is why
  half density is reached at 5,500 m and not at 20 km.
- *What does it mean in flight?* Lift and drag drop **equally** ⇒ the **glide ratio stays the
  same**, but you fly **faster**. Take-off, landing and stall speeds are higher at altitude
  (and in heat), and the take-off run is longer.

### Recipe 4 — the glide-ratio triangle

Three quantities, three possible questions. Always the same formula:

> **glide ratio  =  forward speed  &divide;  sink speed**

**Procedure**

1. Write the formula down.
2. Rearrange for the **unknown**.
3. Substitute — both speeds in the **same unit** (m/s is easiest).

| given | wanted | arithmetic | result |
|---|---|---|---|
| 9 m/s forward, 1.5 m/s sink | glide ratio | 9 ÷ 1.5 | **6.0** |
| glide ratio 9, sink 1 m/s | forward speed | 9 × 1 | **9 m/s = 32.4 km/h** |
| glide ratio 10, 12 m/s forward | sink | 12 ÷ 10 | **1.2 m/s** |

**The glide ratio means four things at once** — pick whichever appears in the answers:

| Reading | ratio |
|---|---|
| forces | lift ÷ drag |
| coefficients | c<sub>L</sub> ÷ c<sub>D</sub> |
| speeds | forward ÷ sink |
| distance | distance ÷ height lost |

!!! tip "Two free points"
    **There is no "thrust" on a paraglider or hang glider** — we have no engine. Any answer
    containing *thrust* is automatically wrong.

    And: **glide ratio and glide angle run in opposite directions.** Large glide ratio =
    **small** (flat) angle. More drag ⇒ smaller glide ratio ⇒ larger angle.

### Recipe 5 — how far can I get?

> **distance  =  glide ratio  &times;  height**

**Procedure**

1. Convert everything to **metres**.
2. Rearrange as needed:
   distance = GR × height · height = distance ÷ GR · GR = distance ÷ height
3. Convert to km at the end (÷ 1000).

| Task | arithmetic | result |
|---|---|---|
| glide ratio 12, 2,400 m up | 12 × 2,400 | **28.8 km** |
| glide ratio 8, 800 m up | 8 × 800 | **6.4 km** |
| glide ratio 8, 1,600 m distance | 1,600 ÷ 8 | **200 m height lost** |
| 7.0 km from 1,400 m | 7,000 ÷ 1,400 | **glide ratio 5** |

Mental rule of thumb: **glide ratio 10 ⇒ 1 km of distance per 100 m of height.**

!!! warning "Reality"
    These numbers assume **still air, best-glide speed, no reserve**. In practice you plan with
    a glide ratio of 6–7 instead of 10–12, plus arrival height over the landing field.

### Recipe 6 — adding wind and lift/sink

The wing always flies **relative to the air**. The air itself can move — you simply **add** that,
and you add it **separately**:

| The air moves … | changes | does **not** change |
|---|---|---|
| **horizontally** (wind) | forward speed over the ground | the sink |
| **vertically** (lift/sink) | sink over the ground | the forward speed |

> **glide ratio over ground  =  (forward &plusmn; wind)  &divide;  (sink &plusmn; air's vertical speed)**

**Procedure**

1. Write two lines: *forward* and *sink*.
2. **Subtract** headwind (add tailwind) — only in the *forward* line.
3. **Add** sinking air (subtract rising air) — only in the *sink* line.
4. Divide.

**Sinking-air example:** 10 m/s forward, 1 m/s own sink, air sinking at 1 m/s.
forward: 10 (unchanged) · sink: 1 + 1 = 2 ⇒ glide ratio **10 → 5**.

**Headwind example:** 15 m/s forward, 2 m/s sink, 5 m/s headwind.
forward: 15 − 5 = 10 · sink: 2 (unchanged) ⇒ glide ratio **7.5 → 5**.

!!! danger "Get a feel for this"
    Just **1 m/s of sinking air halves** the glide ratio of a 10:1 wing. That is why you cross
    sink **fast** instead of gliding "economically".

### Recipe 7 — m/s and km/h

> **m/s  &times; 3.6  =  km/h**  &nbsp;&nbsp;&middot;&nbsp;&nbsp;  **km/h  &divide; 3.6  =  m/s**

Anchors: 5 m/s = 18 km/h · 7 m/s = 25 km/h · 9 m/s = 32.4 km/h · 10 m/s = 36 km/h ·
15 m/s = 54 km/h · 20 m/s = 72 km/h.

---

## 3 · Recipe: reading the polar curve

The **speed polar** is the performance curve of the wing: forward speed horizontally, sink
vertically (downwards!). Every point on the curve is one flight state.

<figure markdown="span">
<svg viewBox="0 0 470 200" role="img" aria-label="Speed polar with the minimum-sink and best-glide points" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color--lightest)" stroke-width="1">
    <line x1="158" y1="25" x2="158" y2="185"/><line x1="204" y1="25" x2="204" y2="185"/>
    <line x1="249" y1="25" x2="249" y2="185"/><line x1="294" y1="25" x2="294" y2="185"/>
    <line x1="340" y1="25" x2="340" y2="185"/>
    <line x1="45" y1="55" x2="395" y2="55"/><line x1="45" y1="85" x2="395" y2="85"/>
    <line x1="45" y1="115" x2="395" y2="115"/><line x1="45" y1="145" x2="395" y2="145"/>
  </g>
  <g stroke="var(--md-default-fg-color--light)" stroke-width="2" fill="none">
    <line x1="45" y1="25" x2="392" y2="25"/>
    <line x1="45" y1="25" x2="45" y2="182"/>
  </g>
  <path d="M392,25 l-8,-4 v8 z" fill="var(--md-default-fg-color--light)"/>
  <path d="M45,182 l-4,-8 h8 z" fill="var(--md-default-fg-color--light)"/>
  <line x1="45" y1="25" x2="395" y2="112" stroke="var(--md-default-fg-color)" stroke-width="1.5" stroke-dasharray="6 4"/>
  <line x1="45" y1="70" x2="395" y2="70" stroke="var(--md-default-fg-color)" stroke-width="1.5" stroke-dasharray="2 4"/>
  <path d="M158,100 C 175,80 190,72 204,70 C 220,68 235,71 249,76 C 265,82 280,88 294,97 C 310,108 326,120 340,130"
        fill="none" stroke="var(--md-primary-fg-color)" stroke-width="2.5" stroke-linecap="round"/>
  <g fill="var(--md-default-fg-color--light)">
    <circle cx="158" cy="100" r="3"/><circle cx="294" cy="97" r="3"/><circle cx="340" cy="130" r="3"/>
  </g>
  <g fill="var(--md-primary-fg-color)" stroke="var(--md-default-bg-color)" stroke-width="2">
    <circle cx="204" cy="70" r="5.5"/><circle cx="249" cy="76" r="5.5"/>
  </g>
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1" fill="none">
    <path d="M196,68 L150,60"/><path d="M253,82 L272,116"/>
  </g>
  <g style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="147" y="57" text-anchor="end">minimum sink</text>
    <text x="276" y="120">best glide</text>
    <text x="158" y="18" text-anchor="middle">5</text><text x="204" y="18" text-anchor="middle">7</text>
    <text x="249" y="18" text-anchor="middle">9</text><text x="294" y="18" text-anchor="middle">11</text>
    <text x="340" y="18" text-anchor="middle">13</text>
    <text x="38" y="59" text-anchor="end">1</text><text x="38" y="89" text-anchor="end">2</text>
    <text x="38" y="119" text-anchor="end">3</text><text x="38" y="149" text-anchor="end">4</text>
  </g>
  <g style="font:400 11px system-ui,sans-serif" fill="var(--md-default-fg-color--light)">
    <text x="396" y="40">forward (m/s)</text>
    <text x="52" y="180">sink (m/s)</text>
  </g>
</svg>
<figcaption>The exam polar. Long dashed line: <b>tangent from the origin</b> — it touches the curve at <b>best glide</b>. Dotted horizontal line: the <b>lowest point</b> of the curve is <b>minimum sink</b>.</figcaption>
</figure>

This table belongs to the curve and is worth a large part of the exam:

| forward | sink | glide ratio | This is … |
|---|---|---|---|
| 5 m/s | 2.5 m/s | **2.0** | **minimum speed** (stall limit) |
| 7 m/s | 1.5 m/s | **4.6** | **minimum sink** — longest flight time |
| 9 m/s | 1.7 m/s | **5.3** | **best glide** — greatest distance |
| 11 m/s | 2.4 m/s | 4.6 | fast cruise |
| 13 m/s | 3.5 m/s | **3.7** | **maximum speed** (full bar) |

**Procedure for any polar question**

1. **Which row?**
   *minimum sink* = smallest sink figure (1.5) · *best glide* = largest glide ratio (5.3) ·
   *minimum* = first row · *maximum* = last row.
2. **What is asked?**
   *glide ratio* → read the third column.
   *forward speed* → read the first column.
   ***airspeed*** → **calculate** (see step 3).
3. If "airspeed" is asked, that is the speed **along the flight path**, i.e. the diagonal of
   forward speed and sink:

> **airspeed  =  &radic;( forward&sup2; + sink&sup2; )**

| Row | arithmetic | airspeed |
|---|---|---|
| 5 / 2.5 | √(25 + 6.25) | **5.6 m/s** (20 km/h) |
| 7 / 1.5 | √(49 + 2.25) | **7.2 m/s** (26 km/h) |
| 9 / 1.7 | √(81 + 2.89) | **9.2 m/s** (33 km/h) |

!!! warning "Exactly what the question targets"
    If the answers offer **9.0 and 9.2**, the question is testing whether you distinguish
    forward speed from airspeed. If the word "airspeed" appears → **take the square root**.

**Two sentences that go with it:**

- **Minimum sink is not best glide.** Best glide is **always faster**.
- **Too slow costs more than too fast:** at the slow end the glide ratio is 2.0, at full bar
  still 3.7.

---

## 4 · Recipe: speed to fly — when faster, when slower?

The rule in one sentence:

!!! tip "Speed to fly"
    **Headwind and sinking air ⇒ fly faster. Tailwind and rising air ⇒ fly slower.**

Why? Because the tangent no longer starts at the origin but at a **shifted point**. The further
that point is shifted, the further right (= faster) the tangent touches the curve.

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:1rem;align-items:start">

<figure markdown="span" style="margin:0">
<svg viewBox="0 -30 215 175" role="img" aria-label="Tangent from the origin in still air" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1.5" fill="none">
    <line x1="30" y1="20" x2="200" y2="20"/><line x1="30" y1="20" x2="30" y2="130"/>
  </g>
  <path d="M83,70 C 92,56 98,51 105,50 C 112,49 119,51 126,54 C 133,58 141,62 147,68 C 155,76 162,84 169,90"
        fill="none" stroke="var(--md-primary-fg-color)" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="30" y1="20" x2="200" y2="80" stroke="var(--md-default-fg-color)" stroke-width="1.5" stroke-dasharray="6 4"/>
  <circle cx="30" cy="20" r="4" fill="var(--md-default-fg-color)"/>
  <circle cx="126" cy="54" r="5" fill="var(--md-primary-fg-color)" stroke="var(--md-default-bg-color)" stroke-width="2"/>
  <text x="126" y="44" text-anchor="middle" style="font:600 11px system-ui,sans-serif" fill="var(--md-default-fg-color)">9 m/s</text>
</svg>
<figcaption><b>1 · Still air.</b> Tangent from the origin ⇒ best glide at 9 m/s.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 -30 215 175" role="img" aria-label="In a headwind the reference point moves to the right" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1.5" fill="none">
    <line x1="30" y1="20" x2="200" y2="20"/><line x1="30" y1="20" x2="30" y2="130"/>
  </g>
  <path d="M83,70 C 92,56 98,51 105,50 C 112,49 119,51 126,54 C 133,58 141,62 147,68 C 155,76 162,84 169,90"
        fill="none" stroke="var(--md-primary-fg-color)" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="115" y1="20" x2="190" y2="118" stroke="var(--md-default-fg-color)" stroke-width="1.5" stroke-dasharray="6 4"/>
  <g stroke="var(--md-default-fg-color)" stroke-width="2" fill="none">
    <line x1="34" y1="8" x2="108" y2="8"/>
  </g>
  <path d="M113,8 l-8,-4 v8 z" fill="var(--md-default-fg-color)"/>
  <text x="70" y="0" text-anchor="middle" style="font:600 11px system-ui,sans-serif" fill="var(--md-default-fg-color)">wind</text>
  <circle cx="115" cy="20" r="4" fill="var(--md-default-fg-color)"/>
  <circle cx="169" cy="90" r="5" fill="var(--md-primary-fg-color)" stroke="var(--md-default-bg-color)" stroke-width="2"/>
  <text x="169" y="106" text-anchor="middle" style="font:600 11px system-ui,sans-serif" fill="var(--md-default-fg-color)">full bar</text>
</svg>
<figcaption><b>2 · Headwind.</b> Reference point moves <b>right</b> ⇒ touch point faster. At 8 m/s of headwind, all the way to maximum speed.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 -30 215 175" role="img" aria-label="In sinking air the reference point moves upwards" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1.5" fill="none">
    <line x1="30" y1="20" x2="200" y2="20"/><line x1="30" y1="20" x2="30" y2="130"/>
  </g>
  <path d="M83,70 C 92,56 98,51 105,50 C 112,49 119,51 126,54 C 133,58 141,62 147,68 C 155,76 162,84 169,90"
        fill="none" stroke="var(--md-primary-fg-color)" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="30" y1="-20" x2="190" y2="103" stroke="var(--md-default-fg-color)" stroke-width="1.5" stroke-dasharray="6 4"/>
  <g stroke="var(--md-default-fg-color)" stroke-width="2" fill="none">
    <line x1="14" y1="16" x2="14" y2="-14"/>
  </g>
  <path d="M14,-19 l-4,8 h8 z" fill="var(--md-default-fg-color)"/>
  <text x="22" y="-8" style="font:600 11px system-ui,sans-serif" fill="var(--md-default-fg-color)">sink</text>
  <circle cx="30" cy="-20" r="4" fill="var(--md-default-fg-color)"/>
  <circle cx="147" cy="68" r="5" fill="var(--md-primary-fg-color)" stroke="var(--md-default-bg-color)" stroke-width="2"/>
  <text x="147" y="84" text-anchor="middle" style="font:600 11px system-ui,sans-serif" fill="var(--md-default-fg-color)">11 m/s</text>
</svg>
<figcaption><b>3 · Sinking air.</b> Reference point moves <b>up</b> ⇒ touch point also faster.</figcaption>
</figure>

</div>

!!! warning "The exception that gets tested"
    The **speed for minimum sink does not change** with wind or with rising/sinking air. Only
    the **best-glide** speed moves. Reason: the **lowest point** of the curve stays at the same
    forward speed, no matter where you put the reference point.

---

## 5 · Recipe: vector addition (adding forces)

This is the most important picture-question type, and it has a recipe that **always** works.

!!! tip "The recipe in one sentence"
    **Hold the first arrow. Re-attach the second arrow at the tip of the first. Then look from
    the held start to the tip of the second — that is the resultant.**

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:1rem;align-items:start">

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 190 160" role="img" aria-label="Step 1: two forces at the same point of application" style="max-width:100%;height:auto">
  <defs><pattern id="vea" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="translate(10,0)">
    <path d="M20 0H0V20" fill="none" stroke="var(--md-default-fg-color--lighter)" stroke-width="1"/></pattern></defs>
  <rect width="190" height="160" fill="url(#vea)"/>
  <g stroke="var(--md-default-fg-color)" stroke-width="2.5" fill="none" stroke-linecap="round">
    <line x1="30" y1="120" x2="86" y2="120"/><line x1="30" y1="120" x2="66" y2="84"/>
  </g>
  <path d="M90,120 l-9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <path d="M70,80 l-1,-10 l-9,1 z" fill="var(--md-default-fg-color)"/>
  <circle cx="30" cy="120" r="4" fill="var(--md-default-fg-color)"/>
  <g style="font:600 13px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="58" y="138" text-anchor="middle">F₁</text><text x="34" y="80">F₂</text>
  </g>
</svg>
<figcaption><b>1 · Given.</b> Two forces, same point of application.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 190 160" role="img" aria-label="Step 2: hold the first arrow" style="max-width:100%;height:auto">
  <defs><pattern id="veb" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="translate(10,0)">
    <path d="M20 0H0V20" fill="none" stroke="var(--md-default-fg-color--lighter)" stroke-width="1"/></pattern></defs>
  <rect width="190" height="160" fill="url(#veb)"/>
  <g stroke="var(--md-default-fg-color--lightest)" stroke-width="2" fill="none">
    <line x1="30" y1="120" x2="66" y2="84"/>
  </g>
  <line x1="30" y1="120" x2="86" y2="120" stroke="var(--md-default-fg-color)" stroke-width="3" stroke-linecap="round"/>
  <path d="M90,120 l-9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <circle cx="30" cy="120" r="6" fill="none" stroke="var(--md-primary-fg-color)" stroke-width="2.5"/>
  <circle cx="30" cy="120" r="4" fill="var(--md-default-fg-color)"/>
  <g style="font:600 13px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="58" y="138" text-anchor="middle">F₁</text>
  </g>
  <text x="8" y="146" style="font:400 11px system-ui,sans-serif" fill="var(--md-primary-fg-color)">hold</text>
</svg>
<figcaption><b>2 · Hold the first.</b> Remember the start point — everything is measured from there.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 190 160" role="img" aria-label="Step 3: attach the second arrow at the tip of the first" style="max-width:100%;height:auto">
  <defs><pattern id="vec" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="translate(10,0)">
    <path d="M20 0H0V20" fill="none" stroke="var(--md-default-fg-color--lighter)" stroke-width="1"/></pattern></defs>
  <rect width="190" height="160" fill="url(#vec)"/>
  <line x1="30" y1="120" x2="86" y2="120" stroke="var(--md-default-fg-color)" stroke-width="2.5" stroke-linecap="round"/>
  <path d="M90,120 l-9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <line x1="90" y1="120" x2="126" y2="84" stroke="var(--md-default-fg-color)" stroke-width="2.5" stroke-dasharray="5 4" stroke-linecap="round"/>
  <path d="M130,80 l-1,-10 l-9,1 z" fill="var(--md-default-fg-color)"/>
  <circle cx="30" cy="120" r="4" fill="var(--md-default-fg-color)"/>
  <g style="font:600 13px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="58" y="138" text-anchor="middle">F₁</text><text x="132" y="104">F₂</text>
  </g>
</svg>
<figcaption><b>3 · Attach the second.</b> Move F₂ unchanged — same length, same direction.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 190 160" role="img" aria-label="Step 4: draw the resultant from start to tip" style="max-width:100%;height:auto">
  <defs><pattern id="ved" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="translate(10,0)">
    <path d="M20 0H0V20" fill="none" stroke="var(--md-default-fg-color--lighter)" stroke-width="1"/></pattern></defs>
  <rect width="190" height="160" fill="url(#ved)"/>
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1.5" fill="none">
    <line x1="30" y1="120" x2="86" y2="120"/>
    <line x1="90" y1="120" x2="126" y2="84" stroke-dasharray="5 4"/>
  </g>
  <line x1="30" y1="120" x2="124" y2="86" stroke="var(--md-primary-fg-color)" stroke-width="3.5" stroke-linecap="round"/>
  <path d="M130,80 l-11,0 l3,9 z" fill="var(--md-primary-fg-color)"/>
  <circle cx="30" cy="120" r="4" fill="var(--md-default-fg-color)"/>
  <g style="font:700 14px system-ui,sans-serif" fill="var(--md-primary-fg-color)">
    <text x="72" y="96">R</text>
  </g>
</svg>
<figcaption><b>4 · Read it off.</b> From the held start to the tip of the second: <b>R</b> is the resultant.</figcaption>
</figure>

</div>

### The three special cases

If both arrows lie on **the same line** or are **at right angles**, it's even quicker:

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:1rem;align-items:start">

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 190 120" role="img" aria-label="Forces in the same direction add up" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color)" stroke-width="2.5" fill="none" stroke-linecap="round">
    <line x1="20" y1="30" x2="76" y2="30"/><line x1="84" y1="30" x2="120" y2="30" stroke-dasharray="5 4"/>
  </g>
  <path d="M80,30 l-9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <path d="M124,30 l-9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <line x1="20" y1="80" x2="118" y2="80" stroke="var(--md-primary-fg-color)" stroke-width="3.5" stroke-linecap="round"/>
  <path d="M124,80 l-10,-5 v10 z" fill="var(--md-primary-fg-color)"/>
  <g style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="46" y="22" text-anchor="middle">F₁</text><text x="100" y="22" text-anchor="middle">F₂</text>
  </g>
  <text x="66" y="102" text-anchor="middle" style="font:700 13px system-ui,sans-serif" fill="var(--md-primary-fg-color)">R</text>
</svg>
<figcaption><b>Same direction:</b> <b>add</b> the lengths, direction unchanged.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 190 120" role="img" aria-label="Opposing forces subtract" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color)" stroke-width="2.5" fill="none" stroke-linecap="round">
    <line x1="20" y1="30" x2="126" y2="30"/><line x1="130" y1="52" x2="74" y2="52" stroke-dasharray="5 4"/>
  </g>
  <path d="M130,30 l-9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <path d="M70,52 l9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <line x1="20" y1="86" x2="64" y2="86" stroke="var(--md-primary-fg-color)" stroke-width="3.5" stroke-linecap="round"/>
  <path d="M70,86 l-10,-5 v10 z" fill="var(--md-primary-fg-color)"/>
  <g style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="72" y="22" text-anchor="middle">F₁</text><text x="102" y="70" text-anchor="middle">F₂</text>
  </g>
  <text x="42" y="108" text-anchor="middle" style="font:700 13px system-ui,sans-serif" fill="var(--md-primary-fg-color)">R</text>
</svg>
<figcaption><b>Opposite directions:</b> <b>subtract</b> the lengths, direction of the larger force.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 190 120" role="img" aria-label="Perpendicular forces give a diagonal" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color)" stroke-width="2.5" fill="none" stroke-linecap="round">
    <line x1="30" y1="95" x2="96" y2="95"/><line x1="100" y1="95" x2="100" y2="45" stroke-dasharray="5 4"/>
  </g>
  <path d="M100,95 l-9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <path d="M100,40 l-4.5,9 h9 z" fill="var(--md-default-fg-color)"/>
  <line x1="30" y1="95" x2="97" y2="46" stroke="var(--md-primary-fg-color)" stroke-width="3.5" stroke-linecap="round"/>
  <path d="M102,40 l-10,2 l5,8 z" fill="var(--md-primary-fg-color)"/>
  <path d="M92,95 v-8 h8" fill="none" stroke="var(--md-default-fg-color--light)" stroke-width="1.5"/>
  <g style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="60" y="112" text-anchor="middle">F₁</text><text x="108" y="72">F₂</text>
  </g>
  <text x="52" y="60" style="font:700 13px system-ui,sans-serif" fill="var(--md-primary-fg-color)">R</text>
</svg>
<figcaption><b>Right angle:</b> <b>diagonal</b> of the rectangle (Pythagoras).</figcaption>
</figure>

</div>

### And when it is slanted and opposing?

Then split each arrow into **horizontal** and **vertical** and add the two directions
**separately**:

1. Count squares: F₁ = 3 to the right, 0 vertical.
2. Count squares: F₂ = 3 to the left, 2 downwards.
3. Horizontal: 3 right − 3 left = **0**. Vertical: **2 down**.
4. Result: an arrow pointing **straight down**, 2 squares long.

!!! danger "The most expensive trap"
    A slanted line tells you **nothing** about the direction. **Always find the arrowhead.**
    An arrow whose line looks like it goes "up and to the right" may well point **down and to
    the left** — and then a completely different resultant comes out.

**Exam tactic:** determine only the **direction** of the resultant first. That usually
eliminates 3 of 4 answers. Only if two candidates share a direction do you need to count squares.

---

## 6 · Recipe: picture questions about the aerofoil

### The terms

<figure markdown="span">
<svg viewBox="0 0 440 210" role="img" aria-label="Aerofoil with nose, trailing edge, chord line, chord length, thickness and mean line" style="max-width:100%;height:auto">
  <line x1="20" y1="105" x2="330" y2="105" stroke="var(--md-default-fg-color--light)" stroke-width="1.5" stroke-dasharray="14 4 3 4"/>
  <path d="M40,105 C 60,77 120,67 180,73 C 225,78 262,93 300,105 C 260,112 200,116 140,114 C 90,112 55,109 40,105 Z"
        fill="var(--md-primary-fg-color)" fill-opacity="0.08" stroke="var(--md-default-fg-color)" stroke-width="2.5"/>
  <path d="M40,105 C 90,89 170,86 300,105" fill="none" stroke="var(--md-primary-fg-color)" stroke-width="2" stroke-dasharray="4 3"/>
  <g stroke="var(--md-default-fg-color)" stroke-width="1.5" fill="none">
    <line x1="40" y1="150" x2="300" y2="150"/>
    <line x1="180" y1="73" x2="180" y2="115"/>
  </g>
  <path d="M40,150 l9,-4 v8 z M300,150 l-9,-4 v8 z" fill="var(--md-default-fg-color)"/>
  <path d="M180,73 l-4,9 h8 z M180,115 l-4,-9 h8 z" fill="var(--md-default-fg-color)"/>
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1" fill="none">
    <path d="M40,105 L28,62"/><path d="M300,105 L340,72"/><path d="M120,92 L120,40"/><path d="M330,105 L360,128"/>
  </g>
  <g style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="26" y="56" text-anchor="middle">nose</text>
    <text x="344" y="68">trailing edge</text>
    <text x="120" y="34" text-anchor="middle" fill="var(--md-primary-fg-color)">mean line</text>
    <text x="364" y="132">chord line</text>
    <text x="170" y="167" text-anchor="end">chord length</text>
    <text x="192" y="98">thickness</text>
  </g>
</svg>
<figcaption>The <b>chord line</b> is the dash-dot <b>line</b> from nose to trailing edge — in drawings it sticks out past the aerofoil at both ends. The <b>chord length</b> is the <b>length</b> of that line. The gap between chord line and mean line is the <b>camber</b>.</figcaption>
</figure>

| Term | In plain words |
|---|---|
| **chord line** | the imaginary **line** from nose to trailing edge |
| **chord length** | the **length** of that line (a number, in metres) |
| **thickness** | largest distance between upper and lower surface |
| **mean line** | centre line between upper and lower surface |
| **camber** | how far the mean line sits away from the chord line |
| relative thickness | thickness ÷ chord, on a paraglider **15–18 %** (a "thick" aerofoil) |

!!! danger "The most expensive trap in the whole subject"
    **The exam uses different aerofoil drawings for different questions — with different
    numbering.** Two figures can look almost identical and still assign the numbers 1–4
    differently.

    **Recipe: read the drawing afresh for every picture question.** Never carry a number over
    from another question. The drawing itself tells you everything:

    - **double-headed arrow** = a measured **length** (chord or thickness)
    - **horizontal** = chord length · **vertical** = thickness
    - **dash-dot line sticking out past the aerofoil** = **chord line** (in technical drawings
      that is always a reference axis)
    - **dot or arrow pointing at a spot on the outline** = nose or trailing edge
    - **thin curve inside** = mean line

### Why is a paraglider aerofoil thick and cambered?

Because we fly **slowly**. The lift formula contains v² — little speed has to be compensated by a
**high c<sub>L</sub>**, and that comes from a thick, strongly cambered (**asymmetric**) aerofoil.
Thick aerofoils also stall more gently.

Symmetric aerofoils exist only in aerobatics — a symmetric aerofoil produces **no** lift at 0°
angle of attack. A cambered one does; its zero-lift angle is around −3° to −5°.

---

## 7 · Recipe: the four points on the aerofoil

<figure markdown="span">
<svg viewBox="0 0 420 220" role="img" aria-label="Aerofoil at a large angle of attack with stagnation point, transition point, separation point, centre of pressure and wake" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1.5" fill="none">
    <path d="M10,40 C 90,40 130,30 200,26 C 270,22 330,26 410,30"/>
    <path d="M10,72 C 90,72 120,54 190,48"/>
    <path d="M10,150 C 90,150 140,152 200,158 C 270,164 340,170 410,174"/>
    <path d="M10,182 C 100,182 150,186 220,190 C 290,194 350,196 410,198"/>
  </g>
  <path d="M100,127 C 118,96 150,78 196,72 C 236,68 268,84 300,128 C 258,132 180,134 100,127 Z"
        fill="var(--md-primary-fg-color)" fill-opacity="0.08" stroke="var(--md-default-fg-color)" stroke-width="2.5"/>
  <line x1="100" y1="127" x2="300" y2="128" stroke="var(--md-default-fg-color--light)" stroke-width="1.5" stroke-dasharray="6 4"/>
  <g fill="none" stroke="var(--md-default-fg-color--light)" stroke-width="1.5">
    <path d="M312,60 a7,7 0 1,1 -0.1,0"/><path d="M336,76 a7,7 0 1,1 -0.1,0"/>
    <path d="M330,50 a6,6 0 1,1 -0.1,0"/><path d="M360,66 a8,8 0 1,1 -0.1,0"/>
    <path d="M356,92 a7,7 0 1,1 -0.1,0"/><path d="M384,54 a7,7 0 1,1 -0.1,0"/>
    <path d="M382,82 a6,6 0 1,1 -0.1,0"/>
  </g>
  <g fill="var(--md-primary-fg-color)" stroke="var(--md-default-bg-color)" stroke-width="2">
    <circle cx="104" cy="124" r="5.5"/><circle cx="160" cy="86" r="5.5"/>
    <circle cx="215" cy="70" r="5.5"/><circle cx="163" cy="128" r="5.5"/>
  </g>
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1" fill="none">
    <path d="M104,124 L52,156"/><path d="M160,86 L142,32"/><path d="M215,70 L268,34"/><path d="M163,128 L150,182"/>
  </g>
  <g style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="48" y="170" text-anchor="middle">stagnation pt.</text>
    <text x="140" y="26" text-anchor="middle">transition pt.</text>
    <text x="272" y="28">separation pt.</text>
    <text x="146" y="196" text-anchor="middle">centre of pressure</text>
    <text x="352" y="118" text-anchor="middle" fill="var(--md-default-fg-color--light)">wake</text>
  </g>
</svg>
<figcaption>From front to back: <b>stagnation point</b> → laminar boundary layer → <b>transition point</b> → turbulent boundary layer → <b>separation point</b> → eddies. The <b>centre of pressure</b> sits on the chord line, not on the surface.</figcaption>
</figure>

| Point | What happens there | How to spot it in the figure |
|---|---|---|
| **Stagnation point** | the air is brought to rest and **splits** into upper and lower flow | at the **nose**, usually slightly on the **underside** |
| **Transition point** | the boundary layer changes from **laminar to turbulent** | on top, ahead of the separation point |
| **Separation point** | the **flow detaches** from the wing; eddies behind it | on top, where the eddies begin |
| **Centre of pressure** | **point of action of the total air force** | on the **chord line** (the dashed line **inside** the aerofoil) |

There is also a **rear stagnation point**: at the trailing edge, where the upper and lower flows
meet again. That is exactly why some questions ask about the "front" stagnation point.

**How the points migrate** — stagnation point and centre of pressure move in **opposite**
directions:

| Angle of attack | Stagnation point | Centre of pressure | Separation point |
|---|---|---|---|
| **larger** (slow, brakes applied) | **aft** along the underside | **forward** | **forward** |
| **smaller** (accelerated) | **forward to the nose**, then onto the upper surface | **aft** | aft |

**What that means in practice:**

- If at a very small angle of attack the stagnation point moves past the nose onto the upper
  surface, the cell openings are no longer fed → internal pressure collapses → **frontal
  collapse**. Hence: ease off the speed bar in turbulence.
- If the separation point reaches the nose, the whole wing is separated → **stall**.

---

## 8 · Recipe: reading pressure-distribution figures

In these figures small arrows stand perpendicular to the aerofoil surface.

!!! tip "The two rules"
    **Arrow pointing away from the aerofoil = suction (low pressure).**
    **Arrow pointing towards the aerofoil = overpressure.**

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:1rem;align-items:start">

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 200 140" role="img" aria-label="Negative angle of attack: overpressure on top, suction below" style="max-width:100%;height:auto">
  <path d="M30,70 C 46,55 90,49 130,53 C 158,56 180,64 196,70 C 168,75 120,78 78,77 C 52,76 36,73 30,70 Z"
        fill="var(--md-primary-fg-color)" fill-opacity="0.08" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <g stroke="var(--md-default-fg-color)" stroke-width="1.6" fill="none">
    <line x1="60" y1="34" x2="60" y2="56"/><line x1="90" y1="30" x2="90" y2="51"/>
    <line x1="120" y1="31" x2="120" y2="52"/><line x1="150" y1="38" x2="150" y2="58"/>
    <line x1="70" y1="78" x2="70" y2="102"/><line x1="100" y1="79" x2="100" y2="106"/>
    <line x1="130" y1="77" x2="130" y2="100"/>
  </g>
  <g fill="var(--md-default-fg-color)">
    <path d="M60,60 l-4,-8 h8 z"/><path d="M90,55 l-4,-8 h8 z"/><path d="M120,56 l-4,-8 h8 z"/><path d="M150,62 l-4,-8 h8 z"/>
    <path d="M70,106 l-4,-8 h8 z"/><path d="M100,110 l-4,-8 h8 z"/><path d="M130,104 l-4,-8 h8 z"/>
  </g>
  <text x="100" y="20" text-anchor="middle" style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">pressure on top</text>
  <text x="100" y="130" text-anchor="middle" style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">suction below</text>
</svg>
<figcaption><b>Negative</b> angle of attack (e.g. −10°): picture <b>inverted</b>, the wing is pushed <b>down</b>.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 200 140" role="img" aria-label="Angle of attack about zero" style="max-width:100%;height:auto">
  <path d="M30,80 C 46,63 90,55 130,59 C 158,62 180,72 196,80 C 168,85 120,88 78,87 C 52,86 36,83 30,80 Z"
        fill="var(--md-primary-fg-color)" fill-opacity="0.08" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M34,74 C 60,44 120,36 176,60 C 190,66 196,74 196,80" fill="none" stroke="var(--md-primary-fg-color)" stroke-width="1.5" stroke-dasharray="4 3"/>
  <g stroke="var(--md-default-fg-color)" stroke-width="1.6" fill="none">
    <line x1="60" y1="62" x2="60" y2="46"/><line x1="90" y1="55" x2="90" y2="40"/>
    <line x1="120" y1="56" x2="120" y2="42"/><line x1="150" y1="66" x2="150" y2="54"/>
    <line x1="70" y1="96" x2="70" y2="104"/><line x1="100" y1="97" x2="100" y2="105"/>
    <line x1="130" y1="95" x2="130" y2="103"/>
  </g>
  <g fill="var(--md-default-fg-color)">
    <path d="M60,42 l-4,8 h8 z"/><path d="M90,36 l-4,8 h8 z"/><path d="M120,38 l-4,8 h8 z"/><path d="M150,50 l-4,8 h8 z"/>
    <path d="M70,92 l-4,8 h8 z"/><path d="M100,93 l-4,8 h8 z"/><path d="M130,91 l-4,8 h8 z"/>
  </g>
  <text x="100" y="26" text-anchor="middle" style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">suction on top</text>
  <text x="100" y="130" text-anchor="middle" style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">thin below</text>
</svg>
<figcaption><b>About 0°:</b> suction on top already present, but the overpressure zone below is only <b>flat and thin</b>.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 200 140" role="img" aria-label="Large angle of attack" style="max-width:100%;height:auto">
  <path d="M30,92 C 50,70 92,58 132,60 C 160,62 180,74 196,86 C 166,92 118,96 76,96 C 50,96 36,95 30,92 Z"
        fill="var(--md-primary-fg-color)" fill-opacity="0.08" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M18,86 C 30,34 110,20 176,52 C 190,60 196,76 196,86" fill="none" stroke="var(--md-primary-fg-color)" stroke-width="1.5" stroke-dasharray="4 3"/>
  <g stroke="var(--md-default-fg-color)" stroke-width="1.6" fill="none">
    <line x1="40" y1="80" x2="30" y2="52"/><line x1="62" y1="66" x2="58" y2="34"/>
    <line x1="92" y1="59" x2="92" y2="26"/><line x1="122" y1="59" x2="126" y2="28"/>
    <line x1="152" y1="68" x2="158" y2="44"/>
    <line x1="70" y1="98" x2="70" y2="118"/><line x1="100" y1="98" x2="100" y2="122"/>
    <line x1="130" y1="96" x2="130" y2="118"/>
  </g>
  <g fill="var(--md-default-fg-color)">
    <path d="M29,47 l-3,9 l8,-2 z"/><path d="M57,29 l-4,9 l8,-1 z"/><path d="M92,22 l-4,8 h8 z"/>
    <path d="M127,23 l-5,8 l8,1 z"/><path d="M159,39 l-5,8 l8,1 z"/>
    <path d="M70,122 l-4,-8 h8 z"/><path d="M100,126 l-4,-8 h8 z"/><path d="M130,122 l-4,-8 h8 z"/>
  </g>
  <text x="100" y="16" text-anchor="middle" style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">suction reaches forward</text>
  <text x="100" y="136" text-anchor="middle" style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">thick below</text>
</svg>
<figcaption><b>Large</b> angle of attack: the suction zone reaches <b>ahead of the nose</b>, with a <b>thick</b> overpressure zone below.</figcaption>
</figure>

</div>

**Procedure**

1. **Where is the suction?** On top ⇒ positive angle of attack. Below (with overpressure on top)
   ⇒ **negative** angle of attack.
2. **How large is the angle of attack?** Don't judge by the height of the suction area! The two
   reliable markers are:
   - **how far the suction zone reaches forward past the nose** (further forward = larger)
   - **how thick the overpressure zone below is** (thicker = larger)
3. For "about 0°": suction on top is present, but below it is **flat and thin**.

### Where does lift arise?

Two numbers, two different statements — don't mix them up:

| Direction | Distribution |
|---|---|
| top ↔ bottom | **2/3 upper surface (suction)**, 1/3 lower surface |
| front ↔ back | **2/3 in the foremost third** |

So lift sits **at the front, on top**: the wing is **sucked** up, not pushed. That is why the
centre of pressure sits at ~25–30 % of the chord, why the **A-lines** carry the main load, why
the **upper surface** is the critical area, and why frontal collapses start at the front.

---

## 9 · Recipe: forces in the glide

<figure markdown="span">
<svg viewBox="0 0 420 280" role="img" aria-label="Force equilibrium in steady glide with lift, drag, resultant, weight, angle of attack and glide angle" style="max-width:100%;height:auto">
  <line x1="20" y1="258" x2="400" y2="258" stroke="var(--md-default-fg-color--light)" stroke-width="2"/>
  <text x="396" y="272" text-anchor="end" style="font:400 11px system-ui,sans-serif" fill="var(--md-default-fg-color--light)">horizon</text>
  <line x1="50" y1="70" x2="200" y2="70" stroke="var(--md-default-fg-color--light)" stroke-width="1.5" stroke-dasharray="6 4"/>
  <line x1="50" y1="70" x2="350" y2="180" stroke="var(--md-default-fg-color--light)" stroke-width="1.5" stroke-dasharray="6 4"/>
  <path d="M50,70 m40,0 a40,40 0 0,1 -2.9,14.6" fill="none" stroke="var(--md-default-fg-color)" stroke-width="1.5"/>
  <text x="98" y="86" style="font:italic 600 13px system-ui,sans-serif" fill="var(--md-default-fg-color)">γ</text>
  <text x="120" y="62" style="font:400 11px system-ui,sans-serif" fill="var(--md-default-fg-color--light)">horizontal</text>
  <text x="248" y="168" style="font:400 11px system-ui,sans-serif" fill="var(--md-default-fg-color--light)">flight path = airflow</text>
  <g transform="translate(230,150) rotate(20)">
    <path d="M28,0 C 12,-10 -34,-13 -66,-5 C -44,5 -6,8 28,0 Z"
          fill="var(--md-primary-fg-color)" fill-opacity="0.12" stroke="var(--md-default-fg-color)" stroke-width="2"/>
    <line x1="-72" y1="-2" x2="40" y2="-2" stroke="var(--md-default-fg-color--light)" stroke-width="1.2" stroke-dasharray="8 3 2 3"/>
  </g>
  <path d="M230,150 m34,0 a34,34 0 0,0 -2,-11" fill="none" stroke="var(--md-default-fg-color)" stroke-width="1.5"/>
  <text x="272" y="146" style="font:italic 600 13px system-ui,sans-serif" fill="var(--md-default-fg-color)">α</text>
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1.2" stroke-dasharray="4 3" fill="none">
    <line x1="259" y1="71" x2="230" y2="60"/><line x1="201" y1="139" x2="230" y2="60"/>
  </g>
  <g stroke-width="3" fill="none" stroke-linecap="round">
    <line x1="230" y1="150" x2="255" y2="76" stroke="var(--md-default-fg-color)"/>
    <line x1="230" y1="150" x2="205" y2="140" stroke="var(--md-default-fg-color)"/>
    <line x1="230" y1="150" x2="230" y2="66" stroke="var(--md-primary-fg-color)" stroke-width="3.5"/>
    <line x1="230" y1="150" x2="230" y2="232" stroke="var(--md-default-fg-color)"/>
  </g>
  <path d="M259,68 l-9,3 l6,7 z" fill="var(--md-default-fg-color)"/>
  <path d="M199,138 l8,-5 l1,9 z" fill="var(--md-default-fg-color)"/>
  <path d="M230,60 l-5,10 h10 z" fill="var(--md-primary-fg-color)"/>
  <path d="M230,240 l-5,-10 h10 z" fill="var(--md-default-fg-color)"/>
  <g style="font:700 15px system-ui,sans-serif">
    <text x="266" y="66" fill="var(--md-default-fg-color)">L</text>
    <text x="182" y="132" fill="var(--md-default-fg-color)">D</text>
    <text x="238" y="72" fill="var(--md-primary-fg-color)">R</text>
    <text x="238" y="228" fill="var(--md-default-fg-color)">G</text>
  </g>
</svg>
<figcaption><b>L</b> lift (perpendicular to the airflow) · <b>D</b> drag (along the airflow, rearwards) · <b>R</b> resultant air force = L ⊕ D · <b>G</b> weight. <b>α</b> angle of attack (airflow ↔ chord line) · <b>γ</b> glide angle (flight path ↔ horizontal).</figcaption>
</figure>

**The rules that answer every question on this**

1. **Lift is perpendicular to the airflow**, **drag lies along the airflow** pointing rearwards.
   So they are **at right angles** to each other.
2. Together (as vectors) they give the **resultant air force R**.
3. In **steady** glide (i.e. whenever nothing is accelerating), **R is exactly as large as the
   weight G** and points the opposite way.
4. Therefore **R does not change** when you accelerate — only the **split** into L and D, and
   with it the glide angle.

!!! warning "Three fine distinctions that get tested"
    - **Not** "lift = weight". Lift alone is somewhat **smaller** than G. Only L **and** D
      together give G.
    - **Weight is not an air force** — it is a mass force. The air force consists of lift and
      drag only.
    - The reference frame is always the **airflow**, not the horizon. Lift points straight up
      only in level flight.

### Keeping the three angles apart

| Angle | between | What it is |
|---|---|---|
| **angle of attack** (α) | chord line ↔ **airflow** | a **flight state** — changes in flight |
| **glide angle** (γ) | flight path ↔ **horizontal** | the **performance measure** |
| **rigging/incidence angle** | chord line ↔ airframe axis | **built in, fixed** |

### Angle of attack and speed are coupled

!!! tip "The sentence that answers four questions"
    **Larger angle of attack ⇒ larger c<sub>L</sub> ⇒ slower** (brakes applied).
    **Smaller angle of attack ⇒ smaller c<sub>L</sub> ⇒ faster** (speed bar).

So you don't steer "throttle", you steer the **angle of attack**. And c<sub>L</sub> rises
**steadily** with the angle of attack — **up to the critical angle** (about 15–18°). There it
collapses: **stall**.

### Stall and loading

> **mean chord  =  area  &divide;  span**

| Loading | stall speed | angle of attack at the stall |
|---|---|---|
| minimum | **lower** | **the same** |
| maximum | **higher** | **the same** |

!!! warning "The half-right answer"
    "Independent of loading, always at the same speed **and** the same angle of attack" is half
    right and therefore dangerous. Correct: **same angle of attack, different speed.**

### Tip vortices

**Why they form:** overpressure below, low pressure above. At the **wing tips** the wing ends —
there the air escapes from below to above and rolls up into a vortex. That is not poor
workmanship but an **unavoidable consequence of lift**.

**Where they are:** **behind the trailing edge**.

**What they cost:** the **induced drag** — the one drag component that **increases** in **slow**
flight. A high aspect ratio reduces its share; that is the real reason for long, slender wings.

---

## 10 · Recipes: geometry and weight

### Recipe — mean chord

> **aspect ratio  =  span&sup2;  &divide;  area  =  span  &divide;  mean chord**

Example: 25 m² ÷ 10 m = **2.50 m**. · 12.5 m² ÷ 10 m = **1.25 m**.

### Recipe — aspect ratio

> **wing loading  =  (payload + glider weight)  &divide;  area**

**Procedure**

1. **Square** the span.
2. Divide by the area.

Example: 10² ÷ 25 = **4.0**. · 12² ÷ 24 = **6.0**. · 8² ÷ 32 = **2.0**.

**Spotting it without arithmetic:** the *largest* aspect ratio = **large span with small area**;
the *smallest* = **short and broad**.

In words, aspect ratio 5 means: **"the span is 5 times larger than the mean chord."**

| Wing | typical aspect ratio |
|---|---|
| school / beginner paraglider | 4.5 – 5 |
| **intermediate paraglider** | **5 – 6** |
| high performance / competition | 6.5 – 7.5 |
| **intermediate hang glider** | **about 7** |
| sailplane | 20 – 30 |

!!! warning "Two traps"
    - **Don't forget to square the span** — the most common arithmetic slip.
    - **Paraglider 5–6, hang glider 7.** Both questions occur.

**What aspect ratio does:** high aspect ratio ⇒ less induced drag ⇒ **better glide ratio**, but
**more collapse-prone** and sharper reactions. Glide performance is bought with collapse
sensitivity — which is what the EN classification is all about.

**Projected area** = the shadow the wing casts from above in flight. Because the wing is
**arched** in flight it is **smaller than or equal to** the flat (design) area — on a paraglider
about 80–85 %. The direction is the **same** for hang gliders and paragliders, only the magnitude
differs.

### Recipe — wing loading

> **load factor  =  load in flight  &divide;  all-up weight on the ground**

**Procedure**

1. **Add the glider's own weight!** "Payload" is pilot plus equipment **without** the glider.
2. Does the question ask for **minimum** or **maximum** payload? Read it twice.
3. Divide by the area. Unit **kg/m²**.

| Wing | payload | + glider | ÷ area | result |
|---|---|---|---|---|
| paraglider | 70 kg | + 5 kg = 75 | 25 m² | **3.0 kg/m²** |
| paraglider | 95 kg | + 5 kg = 100 | 25 m² | **4.0 kg/m²** |
| hang glider | 65 kg | + 35 kg = 100 | 12.5 m² | **8 kg/m²** |
| hang glider | 90 kg | + 35 kg = 125 | 12.5 m² | **10 kg/m²** |

!!! danger "The two certain traps"
    1. **Forgetting the glider's weight** — on a hang glider that is 35 kg, which changes
       everything.
    2. **min instead of max** (or the other way round) — **both** results appear among the
       answers.

**What wing loading does:** all speeds grow with **√(wing loading)** — trim, top and stall speeds
higher, sink higher, **glide ratio unchanged**. Upside: more stable in turbulence and wind.
Downside: weak thermals harder to use, faster landing, longer take-off run.

### Recipe — load factor

> **stall speed  grows with  &radic;(all-up weight)**

Example: 250 kg ÷ 100 kg = **2.5**. The result is a **pure number with no unit** — which is why
"25", "250" and "0.25" are the classic decimal-point distractors.

| Situation | load factor |
|---|---|
| straight flight | **1.0** |
| 30° bank | about 1.15 |
| 45° bank | about 1.4 |
| 60° bank | **2.0** |
| steep bank / spiral dive | **2.5 – 4+** |

**Going from straight flight into a turn increases BOTH the wing loading AND the minimum
airspeed.** Because v<sub>stall</sub> grows with √(load factor), a wing stalls about **58 %**
faster at 2.5 g than in straight flight — the physical cause of stalling while thermalling too
slowly in a tight turn.

Don't confuse: **load factor** (a number) · **wing loading** (kg/m²) · **ultimate/test load**
(paraglider 8 g).

### The four definitions that serve as each other's distractors

| Term | Definition |
|---|---|
| **span** | distance between the left and right wing tip |
| **mean chord** | average distance from nose to trailing edge |
| **wing loading** | all-up weight ÷ wing area |
| **twist / washout** | **differences in angle of attack** between wing sections |

These questions always offer **the same four answers**; only the question changes. Learn the four
rows and you collect several points for almost no effort.

---

## 11 · Axes and stability — free points

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;align-items:start">

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 150 150" role="img" aria-label="Longitudinal axis: roll" style="max-width:100%;height:auto">
  <line x1="75" y1="14" x2="75" y2="140" stroke="var(--md-primary-fg-color)" stroke-width="2" stroke-dasharray="7 4"/>
  <ellipse cx="75" cy="68" rx="54" ry="11" fill="var(--md-primary-fg-color)" fill-opacity="0.10" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <rect x="71" y="60" width="8" height="46" rx="4" fill="var(--md-primary-fg-color)" fill-opacity="0.10" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M112,110 a30,30 0 0,1 -46,10" fill="none" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M66,120 l10,-4 l-1,9 z" fill="var(--md-default-fg-color)"/>
</svg>
<figcaption><b>Longitudinal axis</b> — along the flight direction.<br>Motion: <b>roll</b>.<br>Stability: <b>roll-stable</b>.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 150 150" role="img" aria-label="Lateral axis: pitch" style="max-width:100%;height:auto">
  <line x1="10" y1="68" x2="140" y2="68" stroke="var(--md-primary-fg-color)" stroke-width="2" stroke-dasharray="7 4"/>
  <ellipse cx="75" cy="68" rx="54" ry="11" fill="var(--md-primary-fg-color)" fill-opacity="0.10" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <rect x="71" y="60" width="8" height="46" rx="4" fill="var(--md-primary-fg-color)" fill-opacity="0.10" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M112,40 a30,30 0 0,0 -8,-20" fill="none" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M104,16 l8,6 l-9,4 z" fill="var(--md-default-fg-color)"/>
  <path d="M112,96 a30,30 0 0,1 -8,20" fill="none" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M104,120 l8,-6 l-9,-4 z" fill="var(--md-default-fg-color)"/>
</svg>
<figcaption><b>Lateral axis</b> — across the flight direction.<br>Motion: <b>pitch</b>.<br>Stability: <b>pitch-stable</b>.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 150 150" role="img" aria-label="Vertical axis: yaw" style="max-width:100%;height:auto">
  <circle cx="75" cy="68" r="9" fill="none" stroke="var(--md-primary-fg-color)" stroke-width="2" stroke-dasharray="5 3"/>
  <line x1="75" y1="59" x2="75" y2="77" stroke="var(--md-primary-fg-color)" stroke-width="1.5"/>
  <line x1="66" y1="68" x2="84" y2="68" stroke="var(--md-primary-fg-color)" stroke-width="1.5"/>
  <ellipse cx="75" cy="68" rx="54" ry="11" fill="var(--md-primary-fg-color)" fill-opacity="0.10" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <rect x="71" y="60" width="8" height="46" rx="4" fill="var(--md-primary-fg-color)" fill-opacity="0.10" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M75,124 a42,42 0 0,0 40,-30" fill="none" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M117,90 l-1,10 l-8,-5 z" fill="var(--md-default-fg-color)"/>
</svg>
<figcaption><b>Vertical axis</b> — upright.<br>Motion: <b>yaw</b>.<br>Stability: <b>directionally stable</b>.</figcaption>
</figure>

</div>

Mnemonic: **vertical** axis = turning like a **carousel** = **yaw**.

!!! warning "Words that don't exist in this scheme"
    In the German exam wording: *trudeln, pendeln, höhenstabil, querstabil, längsstabil* — all
    pure distractors.

### Stable, unstable, neutral

| What the wing does after a disturbance | Term |
|---|---|
| returns **by itself** (e.g. after releasing the speed bar) | **stable** |
| moves **ever further away** (e.g. keeps accelerating) | **unstable (labile)** |
| **stays** in the new attitude | **neutral (indifferent)** |
| "inverse" | does not exist |

Mental image: **stable = ball in a bowl** · unstable = ball on a dome · neutral = ball on a table.

The **angle of attack** belongs to the **pitch axis**. A wing that changes it by itself is
therefore not **pitch-stable**. It is exactly this stability that makes a certified paraglider
swing back into trim by itself after a disturbance.

---

## 12 · Don't confuse the four diagrams

| Diagram | Axes | Belongs to |
|---|---|---|
| **speed polar** | forward ↔ sink | flight theory — performance of the **wing** |
| **aerofoil polar** (Lilienthal) | c<sub>D</sub> ↔ c<sub>L</sub> | flight theory — property of the **aerofoil** |
| **barogram** | time ↔ altitude | flight recording |
| **emagram** | temperature ↔ pressure/height | **meteorology** |

The **emagram** is a favourite distractor in flight-theory questions — it belongs to meteorology
and says nothing about the wing.

---

## 13 · Numbers worth memorising

Four tables carry most of the points:

**1 · c<sub>D</sub> values:** 1.3 (hollow shell) · 1.0 (flat plate) · 0.17 (teardrop reversed) ·
0.08 (teardrop correct)

**2 · Polar:** 5/2.5 → GR 2.0 · 7/1.5 → **4.6** · 9/1.7 → **5.3** · 11/2.4 → 4.6 · 13/3.5 → 3.7

**3 · Altitude row:** 1,100 m → 90 % · 2,200 m → 81 % · 3,300 m → 72 % · 4,400 m → 64 % ·
5,500 m → 50 %

**4 · Force diagram:** lift ⊥ airflow · drag ∥ airflow · R = L ⊕ D = G · α at the nose ·
γ at the ground

And:

| Quantity | Formula |
|---|---|
| lift | c<sub>L</sub> · ½ρv² · wing area |
| drag | c<sub>D</sub> · ½ρv² · frontal area |
| glide ratio | L/D = c<sub>L</sub>/c<sub>D</sub> = forward/sink = distance/height |
| aspect ratio | span² / area |
| mean chord | area / span |
| wing loading | (payload + glider weight) / area |
| load factor | load in flight / all-up weight |
| range | glide ratio × height |
| units | m/s × 3.6 = km/h |

---

## 14 · The most common traps — pre-exam checklist

1. **v enters squared, everything else linearly.**
2. **Add the glider's own weight** for wing loading.
3. **Minimum or maximum payload?** Read it twice.
4. **Square the span** for aspect ratio.
5. **Airspeed = square root** of forward² + sink² (9.0 vs 9.2).
6. **Divide c<sub>D</sub> values**, don't subtract.
7. **Glide ratio and glide angle run in opposite directions.**
8. **Minimum sink ≠ best glide** — and the minimum-sink speed does **not** change with
   wind or rising/sinking air.
9. **Stall: same angle of attack, different speed.**
10. **There is no "thrust"** on an unpowered wing.
11. **R (the whole air force) = weight** — not lift alone.
12. **The reference frame is the airflow**, not the horizon.
13. **Paraglider aspect ratio 5–6, hang glider 7.**
14. **Read every drawing afresh** — the numbering changes from figure to figure.
15. **In vector figures, find the arrowhead**, not the line's slope.
16. **Only infer what necessarily follows.** The glide ratio alone tells you nothing about sink
    or speed.
