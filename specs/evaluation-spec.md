# Evaluation Spec — Pod Classifier

Complete this spec **before** writing any code for Milestone 3.

Use Plan or Ask mode to think through each blank field. When you're done,
your answers here become the blueprint for `compute_accuracy()` and
`compute_per_class_accuracy()` in `evaluate.py`.

---

## Background: What is evaluation?

After building a classifier, we need to know how well it works. Evaluation answers:
- **Overall:** What fraction of episodes did we classify correctly?
- **Per-class:** Are we better at some labels than others?

Both functions take the same inputs: a list of predicted labels and a list of
ground-truth labels, in the same order.

---

## compute_accuracy(predictions, ground_truth)

### What it does
Returns the fraction of predictions that exactly match the ground truth.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `predictions` | `list[str]` | Labels predicted by `classify_episode()`, one per episode. |
| `ground_truth` | `list[str]` | The correct labels, in the same order as `predictions`. |

### Output

| Return value | Type | Description |
|---|---|---|
| accuracy | `float` | A value between 0.0 and 1.0. |

---

### Spec fields — fill these in before writing code

**Formula:**

```
Accuracy = number of correct predictions divided by the total number of predictions.

A prediction counts as correct when the predicted label exactly matches the ground-truth label at the same index.
```

---

**Step-by-step logic:**

```
1. If the input lists are empty, return 0.0.
2. Loop through predictions and ground_truth together using zip().
3. Count how many predicted labels exactly match the corresponding ground-truth labels.
4. Divide the number of correct predictions by the total number of ground-truth labels.
5. Return the result as a float between 0.0 and 1.0.
```

---

**Edge case — what if both lists are empty?**

```
Return 0.0.

If there are no examples to evaluate, there is no meaningful accuracy score. Returning 0.0 avoids dividing by zero and keeps the evaluation report from crashing.
```

---

**Worked example:**

```
predictions  = ["interview", "solo", "panel", "interview"]
ground_truth = ["interview", "solo", "solo",  "narrative"]

Compare each pair:
1. interview == interview → correct
2. solo == solo → correct
3. panel != solo → incorrect
4. interview != narrative → incorrect

Correct predictions = 2
Total predictions = 4

compute_accuracy() returns 2 / 4 = 0.5
```

---

## compute_per_class_accuracy(predictions, ground_truth)

### What it does
Returns accuracy broken down by each label. For each label in `VALID_LABELS`,
reports how many episodes with that ground-truth label were classified correctly.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `predictions` | `list[str]` | Labels predicted by `classify_episode()`. |
| `ground_truth` | `list[str]` | Correct labels, in the same order. |

### Output

A `dict` keyed by label. Each value is a dict with three keys:

```python
{
    "interview": {"correct": int, "total": int, "accuracy": float},
    "solo":      {"correct": int, "total": int, "accuracy": float},
    "panel":     {"correct": int, "total": int, "accuracy": float},
    "narrative": {"correct": int, "total": int, "accuracy": float},
}
```

---

### Spec fields — fill these in before writing code

**What does "correct" mean for a given class?**

```
For a given class, an episode counts as correct only if its ground-truth label is that class and the predicted label matches it exactly.

For example, for the "interview" class, an episode is correct only when ground_truth is "interview" and prediction is also "interview".
```

---

**What does "total" mean for a given class?**

```
Total means the number of episodes whose ground-truth label is that class.

It is not the total number of predictions overall. For example, the total for "panel" is only the number of test episodes that are actually labeled "panel" in the ground truth.
```

---

**Step-by-step logic:**

```
1. Initialize a results dictionary with one entry for each label in VALID_LABELS.
2. Each label starts with correct = 0, total = 0, and accuracy = 0.0.
3. Loop through predictions and ground_truth together.
4. For each pair, use the ground-truth label to decide which class bucket to update.
5. Add 1 to that class's total.
6. If the prediction exactly matches the ground-truth label, also add 1 to that class's correct count.
7. After the loop, compute accuracy for each class as correct / total.
8. If a class has total == 0, leave its accuracy as 0.0.
9. Return the full results dictionary.
```

---

**Edge case — what if a class has no examples in ground_truth (total == 0)?**

```
Set that class's accuracy to 0.0.

If total == 0, there is no denominator, so the function should not divide by zero. Returning 0.0 keeps the evaluation report stable and makes it clear that there were no examples for that class.
```

---

**Worked example:**

```
predictions  = ["interview", "interview", "solo", "panel", "panel"]
ground_truth = ["interview", "solo",      "solo", "panel", "narrative"]

label       correct  total  accuracy
----------  -------  -----  --------
interview   1        1      1.0
solo        1        2      0.5
panel       1        1      1.0
narrative   0        1      0.0
```

---

## Reflection questions (discuss at the checkpoint)

1. Overall accuracy can hide weak classes because one class may be doing very well while another is doing badly. Per-class accuracy is more informative because it shows whether the classifier understands each label boundary separately. For example, a classifier could have decent overall accuracy but still fail on most panel episodes.

2. If `panel` episodes consistently get misclassified as `interview`, that suggests the prompt or training labels are not clearly showing the difference between multi-guest roundtables and host-guest conversations. I would add or improve examples that clearly show panel episodes as speakers discussing as equals.

3. If I labeled 100 training episodes, the classifier might improve because the few-shot prompt would have more examples of edge cases and a stronger signal for each label. If I had 200 test episodes, the evaluation would be more reliable because the accuracy would be based on a larger and more diverse held-out set.

   
