# Sentry

## YOLO Training Metrics Guide

Understanding the metrics generated during YOLO training is crucial for evaluating and improving your object detection model. The results are split into **Losses** (training errors) and **Metrics** (validation performance).

### 1. Losses (Lower is Better)
Loss functions measure how "wrong" the model is. During training, the model tries to minimize these values.

#### **`box_loss` (Box Regression Loss)**
- **What it is:** Measures the error in the predicted bounding box coordinates (center, width, height) compared to the ground truth box.
- **What it does:** Tells the model to draw boxes that tighter fit the object.
- **Goal:** **Lower is Better**.
- **Interpretation:**
    - **High:** The predicted boxes are far off from the real objects (too big, too small, or shifted).
    - **Low:** The boxes are very accurate and tight around the objects.
    - **Consistent Decrease:** The model is successfully learning where objects are located.
    - **Inconsistent / Spiking:** The learning rate might be too high, or the data has bad labels (e.g., boxes cutting off part of the object).

#### **`cls_loss` (Classification Loss)**
- **What it is:** Measures the error in identifying the class of the object (e.g., misclassifying a "person" as a "car").
- **What it does:** Tells the model to learn the specific features that distinguish one object type from another.
- **Goal:** **Lower is Better**.
- **Interpretation:**
    - **High:** The model is confused about what the objects are.
    - **Low:** The model effectively recognizes object categories.
    - **Consistent Decrease:** The model is learning the visual features of your classes.
    - **Inconsistent:** The dataset might have confusing images (e.g., objects look too similar) or class imbalance (too many of one type, too few of another).

#### **`dfl_loss` (Distribution Focal Loss)**
- **What it is:** Measures the certainty of the model regarding the boundaries of the bounding box.
- **What it does:** Helps refine the box edges, especially when valid boundaries are not clear (e.g., occluded objects or blurry edges).
- **Goal:** **Lower is Better**.
- **Interpretation:**
    - **High:** The model is "uncertain" about exactly where the object starts and ends.
    - **Low:** The model is confident about the precise edges of the object.
    - **Consistent Decrease:** The model is fine-tuning its ability to handle difficult or obscured edges.

---

### 2. Performance Metrics (Higher is Better)
These metrics evaluate how well the model performs on unseen (validation) data.

#### **`Precision` (P)**
- **What it is:** The accuracy of positive predictions. Formula: `True Positives / (True Positives + False Positives)`.
- **What it does:** Answers: "When the model claims it found an object, how often is it right?"
- **Goal:** **Higher is Better** (1.0 = 100% accurate).
- **Interpretation:**
    - **High:** Few false alarms. If it detects something, it's likely real.
    - **Low:** Many false positives. The model is "hallucinating" objects that aren't there.
    - **Inconsistent:** Often a tradeoff with Recall. Tuning confidence thresholds can affect this.

#### **`Recall` (R)**
- **What it is:** The ability to find all actual objects. Formula: `True Positives / (True Positives + False Negatives)`.
- **What it does:** Answers: "Out of all the objects that actually exist, how many did the model find?"
- **Goal:** **Higher is Better** (1.0 = found everything).
- **Interpretation:**
    - **High:** The model finds almost every object, rarely missing one.
    - **Low:** The model misses many objects (false negatives).
    - **Inconsistent:** High recall but low precision means the model is spamming boxes just to catch everything.

#### **`mAP50` (mean Average Precision @ IoU 0.5)**
- **What it is:** The average precision calculated at an Intersection over Union (IoU) threshold of 0.50.
- **What it does:** Checks if the predicted box overlaps with the ground truth box by at least 50%. This is the standard "did you find it?" metric.
- **Goal:** **Higher is Better**.
- **Interpretation:**
    - **High (>0.8):** Excellent detection capabilities for general purposes.
    - **Low (<0.5):** The model often misses objects or places boxes poorly.
    - **Consistent Increase:** The model is generalizing well to new data.

#### **`mAP50-95` (mean Average Precision @ IoU 0.50:0.95)**
- **What it is:** The average precision averaged over multiple IoU thresholds (from 0.50 to 0.95 in steps of 0.05).
- **What it does:** A much stricter metric that rewards high-precision localization. It requires the box to match the ground truth almost perfectly.
- **Goal:** **Higher is Better**.
- **Interpretation:**
    - **High (>0.6):** State-of-the-art performance. The boxes are extremely tight and accurate.
    - **Low:** The model finds objects (high mAP50) but the boxes are sloppy (loose fit).
    - **Gap between mAP50 and mAP50-95:** A large gap is normal, but if mAP50-95 is very low while mAP50 is high, your model finds objects but struggles with precise sizing.