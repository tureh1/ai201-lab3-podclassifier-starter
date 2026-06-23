
import json
import os
import re
from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_LABELS, DATA_PATH, TRAIN_FILE, LABELS_FILE

_client = Groq(api_key=GROQ_API_KEY)


def load_labeled_examples() -> list[dict]:
    """
    Load the training episodes and merge them with the student's labels.

    Returns a list of dicts, each with:
      - "id"          : episode ID
      - "title"       : episode title
      - "podcast"     : podcast name
      - "description" : episode description
      - "label"       : the label from my_labels.json (may be None if not yet annotated)

    Only returns episodes where the label is a valid, non-null string.
    Episodes with null labels are silently skipped.
    """
    train_path = os.path.join(DATA_PATH, TRAIN_FILE)
    labels_path = os.path.join(DATA_PATH, LABELS_FILE)

    with open(train_path, encoding="utf-8") as f:
        episodes = {ep["id"]: ep for ep in json.load(f)}

    with open(labels_path, encoding="utf-8") as f:
        labels = {entry["id"]: entry["label"] for entry in json.load(f)}

    labeled = []
    for ep_id, ep in episodes.items():
        label = labels.get(ep_id)
        if label in VALID_LABELS:
            labeled.append({**ep, "label": label})

    return labeled


def build_few_shot_prompt(labeled_examples: list[dict], description: str) -> str:
    """
    Build a few-shot classification prompt using the student's labeled training examples.

    The prompt includes:
      1. The task instructions and valid labels
      2. The labeled examples from Milestone 1
      3. The new episode description to classify
      4. A strict output format that classify_episode() can parse
    """
    instructions = """
You are a podcast episode format classifier.

Classify the episode by its structural format, not by topic, tone, or production quality.

Use exactly one of these four labels:

interview:
A host speaks with one or more guests. The episode is structured around questions and responses.
Key signal: there is a clear host-guest dynamic.

solo:
One host speaks alone, without guests. The host shares personal experience, opinion, reflection, analysis, or instruction.
Key signal: one main voice, no guest, and no assembled external sources as the structure.

panel:
Three or more speakers discuss a topic together without a clear host-guest dynamic.
Key signal: multiple voices with roughly equal standing.

narrative:
A story is told over the course of the episode, usually with reporting, production, or multiple sources woven together.
Key signal: documentary-style or reported story with a clear arc.

Important edge-case rules:
- If the episode is structured as Q&A with a guest, label it interview, even if the guest tells long stories.
- If one host tells a first-person story from memory or personal reflection, label it solo.
- If three or more speakers discuss as rough equals, label it panel.
- If the episode is assembled from outside sources, documents, archives, recordings, or interview excerpts into a story, label it narrative.

Return your answer in exactly this format:

LABEL: <interview | solo | panel | narrative>
REASONING: <one brief explanation>
""".strip()

    example_blocks = []

    for example in labeled_examples:
        example_blocks.append(
            f"""
Title: {example.get("title", "")}
Description: {example.get("description", "")}
Label: {example.get("label", "")}
""".strip()
        )

    if example_blocks:
        examples_text = "\n\n---\n\n".join(example_blocks)
    else:
        examples_text = "No labeled examples were provided. Use the taxonomy rules above."

    prompt = f"""
{instructions}

Here are labeled examples:

{examples_text}

---

Now classify this new episode.

Description: {description}

Return only:

LABEL: <interview | solo | panel | narrative>
REASONING: <one brief explanation>
""".strip()

    return prompt


def _parse_label_and_reasoning(response_text: str) -> tuple[str, str]:
    """
    Parse the LLM response into a label and reasoning.

    Expected format:
    LABEL: interview
    REASONING: This is a host-guest conversation.
    """
    label = "unknown"
    reasoning = "No reasoning provided."

    label_match = re.search(r"(?im)^label\s*:\s*(.+)$", response_text)
    reasoning_match = re.search(r"(?ims)^reasoning\s*:\s*(.+)$", response_text)

    if label_match:
        parsed_label = label_match.group(1).strip()
        parsed_label = parsed_label.replace("*", "").replace("`", "").strip()
        parsed_label = parsed_label.lower()

        # If the model returns something like "interview - because..."
        # keep only the first word for validation.
        parsed_label = re.split(r"[\s,.;:-]+", parsed_label)[0]

        if parsed_label in VALID_LABELS:
            label = parsed_label

    if reasoning_match:
        reasoning = reasoning_match.group(1).strip()

    return label, reasoning


def classify_episode(description: str, labeled_examples: list[dict]) -> dict:
    """
    Classify a single podcast episode description using the few-shot LLM classifier.

    Steps:
      1. Build the few-shot prompt
      2. Send it to the LLM
      3. Parse the response
      4. Validate the label
      5. Return a dict with "label" and "reasoning"
    """
    try:
        prompt = build_few_shot_prompt(labeled_examples, description)

        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a careful podcast format classifier. Follow the requested output format exactly."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=250,
        )

        response_text = response.choices[0].message.content or ""

        label, reasoning = _parse_label_and_reasoning(response_text)

        if label not in VALID_LABELS:
            return {
                "label": "unknown",
                "reasoning": f"Could not parse a valid label from the LLM response. Raw response: {response_text}"
            }

        return {
            "label": label,
            "reasoning": reasoning
        }

    except Exception as e:
        return {
            "label": "unknown",
            "reasoning": f"Classification failed: {e}"
        }