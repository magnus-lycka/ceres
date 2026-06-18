# Traveller Task Mechanics

This document details the core resolution mechanics of the Traveller RPG ruleset, specifically focusing on how tasks, checks, and modifiers work in play and how they overlap with character creation and design preparation tools.

---

## 1. The Core Check

Most uncertain actions in Traveller are resolved using a **Check**. To perform a check, a Traveller rolls **2D** (two six-sided dice), adds their characteristic modifier, their skill level, and any other relevant dice modifiers (DMs). If the total is equal to or greater than the target number, the check succeeds.

$$\text{Check Total} = 2\text{D} + \text{Characteristic DM} + \text{Skill Level} + \text{Other DMs}$$

### Characteristic Dice Modifier (DM)
A Traveller's raw characteristic score determines the DM applied to checks using that characteristic. It is computed as:

$$\text{DM} = \lfloor \frac{\text{Value}}{3} \rfloor - 2$$

| Characteristic Score | Dice Modifier (DM) |
| :--- | :--- |
| 0 | -3 (Inflicted or disabled) |
| 1–2 | -2 |
| 3–5 | -1 |
| 6–8 | +0 |
| 9–11 | +1 |
| 12–14 | +2 |
| 15+ | +3 |

### Skill Levels
- **Level 0 (Basic training)**: Allows checks without penalty. Gained from basic career training or background.
- **Level 1+**: Added directly to the check total.
- **Unskilled Penalty**: Attempting a check without having the skill (not even at level 0) inflicts a **DM-3** penalty. Some highly specialized checks cannot be attempted unskilled at all.

---

## 2. Task Difficulties

The referee sets the baseline difficulty of a task. The target number (the score required to succeed) changes accordingly. If no difficulty is specified, the task defaults to **Average (8+)**.

| Difficulty | Target Number | Description & Examples |
| :--- | :--- | :--- |
| **Simple** | 2+ | Trivial for everyone. Ordering a meal, requesting basic weather data. |
| **Easy** | 4+ | Trivial for a professional. Activating J-drive, simple navigation. |
| **Routine** | 6+ | Trivial for a professional, easy for amateur. Landing at a starport. |
| **Average** | 8+ | Moderate obstacle. Standard Gun Combat, plotting a jump, first aid. |
| **Difficult** | 10+ | Tough even for a professional. Hacking basic security, extreme stunts. |
| **Very Difficult** | 12+ | Hard for a professional, nearly impossible for an amateur. |
| **Formidable** | 14+ | Exceptionally hard. Hacking military networks, alien surgery. |
| **Impossible** | 16+ | Requires near-miraculous effort. Rebuilding mainframe from scratch. |

---

## 3. Boon and Bane

Boons and Banes represent external circumstances (such as high-quality tools, poor lighting, helper drones, or hazardous environments) that make a check easier or harder.
- **Boon**: Roll **3D** and discard the **lowest** die before summing.
- **Bane**: Roll **3D** and discard the **highest** die before summing.
- *Rule*: Multiple Boons or Banes do not stack. If you have both a Boon and a Bane, they cancel each other out, resulting in a normal 2D roll.

---

## 4. Effect (Success Margin)

The **Effect** is the difference between the total check roll (after modifiers) and the target number.

$$\text{Effect} = \text{Check Total} - \text{Target Number}$$

- **Non-negative Effect (0 or more)**: Success. A higher effect yields better quality, faster resolution, or extra damage.
  - *Medic Example*: The patient regains characteristic points equal to the check's Effect.
  - *Explosives Example*: The damage of the charge is multiplied by the Effect.
- **Negative Effect (-1 or worse)**: Failure.
  - *Exceptional Failure (-6 or worse)*: Severe complications, equipment damage, or injury.

---

## 5. Task Chains

When a sequence of actions is interlinked, or when a group of Travellers works together on a single complex task, they use a **Task Chain**. The Effect of a previous check determines a positive or negative DM applied to the subsequent check.

### Task Chain DM Table
| Previous Check Result | Effect Range | DM to Next Check |
| :--- | :--- | :--- |
| **Failed** (Exceptional) | -6 or less | **-3** |
| **Failed** | -2 to -5 | **-2** |
| **Failed** (Marginal) | -1 | **-1** |
| **Succeeded** (Marginal) | 0 | **+1** |
| **Succeeded** | 1 to 5 | **+2** |
| **Succeeded** (Exceptional) | 6 or more | **+3** |

### Patterns of Task Chains
1. **Sequential Tasks**: One Traveller performs a series of interlinked skills (e.g., Recon check $\rightarrow$ Tactics check $\rightarrow$ Stealth check).
2. **Working Together (Assisting)**: Multiple Travellers work on the same task simultaneously. One Traveller is designated the leader and performs the "final" check. The assistants perform helping checks and apply their resulting Task Chain DMs to the leader's final roll.

---

## 6. Timeframes & Going Faster or Slower

Tasks have a default timeframe (e.g., 1D seconds, 1D x 10 minutes, 1D hours). Travellers can often choose to rush or take their time to shift the timeframe:
- **Going Faster**: Shift timeframe one step up (shorter). Inflicts a **DM-2** penalty on the check.
- **Going Slower**: Shift timeframe one step down (longer). Grants a **DM+2** bonus on the check.
