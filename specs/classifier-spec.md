# Classifier Spec — Pod Classifier

Complete this spec **before** writing any code for Milestone 2.

Use Plan or Ask mode to think through each blank field. When you're done,
your answers here become the blueprint for `build_few_shot_prompt()` and
`classify_episode()` in `classifier.py`.

---

## build_few_shot_prompt(labeled_examples, description)

### What it does
Constructs a prompt string for the LLM that includes the task instructions,
all labeled training examples, and the new episode description to classify.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `labeled_examples` | `list[dict]` | Each dict has `"title"`, `"description"`, `"label"` (and others). These are the examples you labeled in Milestone 1. |
| `description` | `str` | The episode description to classify. |

### Output

| Return value | Type | Description |
|---|---|---|
| prompt | `str` | A complete prompt string ready to send to the LLM. |

---

### Spec fields — fill these in before writing code

**Task instruction (what should the LLM know about the task?):**

```
You are classifying podcast episodes by their format. Classify the episode
into exactly one of these four labels:

- interview: a conversation between a host and one or more guests
- solo: a single host speaking from memory, experience, or opinion — no guests,
  no assembled external sources
- panel: multiple guests with roughly equal speaking time, often debating or
  discussing a topic together
- narrative: a story assembled from external sources — interviews, archival
  audio, reporting — with a clear narrative arc

Return only the label and your reasoning. Do not explain the taxonomy.
```

---

**How should labeled examples be formatted in the prompt?**

```
Each example should include the episode title, a brief excerpt or the full
description, and the correct label. Separate examples with a blank line or
a delimiter like "---". Include all fields that help the model see why the
label was applied — title and description are both useful; other fields
(like episode ID) are not needed.
```

---

**Example block sketch (write one concrete example):**

```
Title: {title}
Description: {description}
Label: {label}
```

---

**How should the new episode (to be classified) be presented?**

```
Present it in the same format as the labeled examples, but omit the Label
line and replace it with an instruction to classify. For example:

Title: {title}
Description: {description}
Label: ?

Then add a line like: "Classify the episode above. Return your answer in
the format below:" followed by the output format you chose.
```

---

**What output format should you request from the LLM?**

```
LABEL: <interview | solo | panel | narrative>
REASONING: <one brief explanation>

I chose this format because it is structured enough to parse reliably, but still readable. The label appears after `LABEL:`, so `classify_episode()` can extract that line, normalize it to lowercase, and validate it against `VALID_LABELS`. The reasoning appears after `REASONING:`, so the app can display a short explanation without mixing it into the label.
```

---

**Edge cases to handle in the prompt:**

```
If `labeled_examples` is empty, the prompt should still include the taxonomy definitions and ask the model to classify using those rules. However, the classifier will be stronger when labeled examples are available because they show the model how the taxonomy is applied.

If the description is very short, the prompt should still ask for the best label based on the structural clues available. The model should classify by format, not topic or tone.

The prompt should also remind the model to return exactly one of the valid labels: `interview`, `solo`, `panel`, or `narrative`.
```

---

## classify_episode(description, labeled_examples)

### What it does
Classifies a single podcast episode description using the few-shot LLM classifier.
Returns a dict with a label and reasoning.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `description` | `str` | The episode description to classify. |
| `labeled_examples` | `list[dict]` | Labeled training examples from `load_labeled_examples()`. |

### Output

| Return value | Type | Description |
|---|---|---|
| result | `dict` | Must have keys `"label"` and `"reasoning"`. `"label"` must be one of `VALID_LABELS` or `"unknown"`. |

---

### Spec fields — fill these in before writing code

**Step 1 — Build the prompt:**

```
Call build_few_shot_prompt(labeled_examples, description) and store the
returned string in a variable (e.g., prompt). Pass through both arguments
exactly as received — no modification needed before calling.
```

---

**Step 2 — Send to the LLM:**

```
Call _client.chat.completions.create() with:
  - model: the model name from config (LLM_MODEL)
  - messages: a list with one dict — {"role": "user", "content": prompt}
    (system-design.md shows an optional system message too — either shape works)
  - max_tokens: a reasonable limit (e.g., 200–300) to keep responses concise

Extract the response text from:
  response.choices[0].message.content
```

---

**Step 3 — Parse the response:**

```
Because the requested output format is:

LABEL: <label>
REASONING: <reasoning>

I will split the response into lines and look for a line that starts with `LABEL:`. I will remove the `LABEL:` prefix, strip whitespace, remove simple markdown formatting like backticks or asterisks, and convert the result to lowercase.

For the reasoning, I will look for a line that starts with `REASONING:`. I will remove the prefix and keep the rest of the text as the explanation. If no reasoning line is found, I will use a fallback message like `"No reasoning provided."`
```

---

**Step 4 — Validate the label:**

```
After parsing the label, I will check whether it is in `VALID_LABELS`.

If the label is one of `interview`, `solo`, `panel`, or `narrative`, I will return it.

If the LLM returns something invalid, such as `story`, `conversation`, `Interview`, or a sentence instead of a label, I will normalize what I can. If it still does not match `VALID_LABELS`, I will set the label to `"unknown"` instead of crashing.
```

---

**Step 5 — Handle errors gracefully:**

```
Possible errors include a Groq API/network error, a missing API key, an empty response, or a response that does not follow the requested format.

If something fails, `classify_episode()` should return a dictionary with:

```python
{
    "label": "unknown",
    "reasoning": "Classification failed: <error message>"
}
```

---

### Return value structure

```python
{
    "label": str,      # one of VALID_LABELS, or "unknown" if invalid/error
    "reasoning": str,  # brief explanation from the LLM
}
```

---

## Notes on label quality

The classifier is only as good as your labels. If your training examples have
inconsistent or ambiguous labels, the LLM will learn the wrong pattern.

Before implementing the classifier, re-read `data/taxonomy.md` and double-check
any labels you're unsure about. Annotation quality is part of the lab.

---

## Implementation Notes

*Fill this in after implementing and testing both functions.*

**Test: what does the raw LLM response look like for one episode?**

```
Episode tested: The Aral Sea: A Disaster in Four Acts
Raw response text: 
LABEL: narrative
REASONING: The episode is structured as a reported story with a clear arc, using external sources and documentary-style production rather than a host-guest conversation.
```

**How did you parse the label out of the response?**

```
I searched for the line that starts with LABEL:, removed the prefix, stripped whitespace and simple markdown characters, converted the label to lowercase, and checked it against VALID_LABELS.
```

**Did any episodes return `"unknown"`? If so, why?**

```
No. The test examples returned valid labels after parsing and validation
```

**One thing about the output format that surprised you:**

```
The structured LABEL: and REASONING: format made parsing easier than trying to extract a label from a full paragraph. Even if the model adds extra explanation, the label line is still easy to locate.
```
