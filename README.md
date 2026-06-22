# 🔩 Rust Detection & Severity Grading

<p align="center">
  <img src="https://img.shields.io/badge/Model-YOLOv11-ff6b35?style=for-the-badge&logo=pytorch" />
  <img src="https://img.shields.io/badge/Backend-Flask-000000?style=for-the-badge&logo=flask" />
  <img src="https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/Inference-Local%20%2F%20Offline-22c55e?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Frontend-HTML%20%2F%20CSS%20%2F%20JS-f59e0b?style=for-the-badge" />
</p>

An AI-powered **rust and corrosion detection system** built on **YOLOv11**, featuring a local Flask backend and a premium web frontend. Upload any image of a metal surface and receive instant detection results, severity grading, coverage analysis, and model confidence scores — all running fully offline on your machine.

---

## Features

| Feature | Description |
|---|---|
| **Real-Time Detection** | Detects corrosion instantly using YOLOv11 at 640px resolution |
| **4-Class Recognition** | Identifies `corrosion`, `moderate corrosion`, `rust`, `severe corrosion` |
| **Severity Grading** | Grades results as **MILD**, **MODERATE**, or **CRITICAL** |
| **Coverage Analysis** | Calculates the % of image area affected by corrosion |
| **Confidence Scoring** | Reports per-detection and average model confidence |
| **Side-by-Side Comparison** | Original image vs. annotated output with bounding boxes |
| **Severity Bar** | Gradient bar from 🟢 Mild → 🔴 Critical with animated marker |
| **Confidence Ring** | Animated circular gauge showing model confidence |
| **100% Local / Offline** | No cloud, no data upload — everything runs on your machine |

---

## Project Structure

```
.
├── best.pt                  # YOLOv11 trained weights
├── app.py                   # Flask REST API backend
├── detect_and_grade.py      # Standalone CLI inference script
├── frontend/
│   ├── index.html           # Web UI (open in browser)
│   ├── style.css            # Dark-theme design system
│   └── app.js               # Frontend logic & API integration
├── graded_output/           # Saved annotated images & reports
├── dataset/                 # Training dataset
└── kaggle_training.ipynb    # Model training notebook
```

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-username/rust-detection.git
cd rust-detection
```

### 2. Install dependencies

```bash
pip install flask flask-cors ultralytics opencv-python
```

> **Network restricted?** Use a mirror:
> ```bash
> pip install flask flask-cors ultralytics opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple
> ```

### Train the Model Using Google Colab or Kaggle using Jyupter Notebook
### Dataset : https://universe.roboflow.com/averkios/rust-corrosion-detection

### If you need Trained Model: Email me at yb62406@gmail.com

### 3. Start the backend server

```bash
python app.py
```

You should see:
```
[INFO] Loading model from best.pt …
[INFO] Model ready.
 * Running on http://127.0.0.1:5000
```

### 4. Open the frontend

Simply open **`frontend/index.html`** in your browser (double-click the file).

The **green dot** in the top-right confirms the backend is connected. Drop any image and analysis begins immediately.

---

## Web Interface

The frontend is a single-page app with no framework dependencies — just HTML, CSS, and vanilla JavaScript.

**On image upload it:**
1. Shows animated loading steps (Preprocessing → Detecting → Grading)
2. Displays the **original vs. annotated** image side-by-side
3. Shows the **overall grade badge** (NONE / MILD / MODERATE / CRITICAL)
4. Animates the **severity bar** — marker moves from green to red based on score
5. Renders the **confidence ring** with average, max, and min per-box confidence
6. Lists every detected bounding box in a **detection breakdown** table

<img width="1887" height="883" alt="Screenshot 2026-06-22 192932" src="https://github.com/user-attachments/assets/6ae4eaa4-6376-4a5a-8c5a-f40076de8541" />

<img width="1884" height="895" alt="Screenshot 2026-06-22 192959" src="https://github.com/user-attachments/assets/43681fc1-c00d-4293-8eb4-29f4eb22979e" />

<img width="1874" height="882" alt="Screenshot 2026-06-22 193030" src="https://github.com/user-attachments/assets/5d6ad9a0-22c8-4e34-bd34-c9d9dfbe9d72" />

---

## REST API

The Flask backend exposes two endpoints:

### `GET /api/health`
Check if the server is running.

**Response:**
```json
{ "status": "ok", "model": "path/to/best.pt" }
```

---

### `POST /api/analyze`
Analyze an uploaded image for corrosion.

**Request:** `multipart/form-data` with field `image` (JPEG, PNG, BMP, WebP)

**Response:**
```json
{
  "original_image":  "<base64-encoded JPEG>",
  "annotated_image": "<base64-encoded JPEG>",
  "avg_confidence": 62.4,
  "overall": {
    "grade": 3,
    "label": "CRITICAL",
    "description": "Immediate maintenance required. Severe structural risk.",
    "coverage_pct": 88.3,
    "num_detections": 2,
    "severity_pct": 97.1
  },
  "detections": [
    {
      "class_id": 3,
      "class_name": "severe corrosion",
      "confidence": 0.7304,
      "bbox": [0, 447, 1598, 1264],
      "area": 1305566,
      "severity_grade": 3,
      "severity_label": "SEVERE"
    }
  ]
}
```

---

## Detection Classes & Severity

| Class ID | Class Name | Severity Grade | Label |
|---|---|---|---|
| 0 | `corrosion` | 1 | MILD |
| 1 | `moderate corrosion` | 2 | MODERATE |
| 2 | `rust` | 1 | MILD |
| 3 | `severe corrosion` | 3 | SEVERE |

### Overall Grade Logic

| Condition | Grade | Label |
|---|---|---|
| Max severity = 3 OR coverage > 50% | 3 | **CRITICAL** |
| Max severity = 2 OR coverage > 25% OR detections > 5 | 2 | **MODERATE** |
| Otherwise | 1 | **MILD** |
| No detections | 0 | **NONE** |

---

## 🖱️ CLI Usage

You can also run inference directly from the command line without the web interface:

```bash
# Single image
python detect_and_grade.py --source path/to/image.jpg --weights best.pt

# Entire folder
python detect_and_grade.py --source path/to/images/ --weights best.pt

# Custom confidence threshold & output directory
python detect_and_grade.py --source images/ --weights best.pt --conf 0.35 --output results/
```

**Outputs saved to `graded_output/`:**
- `graded_<filename>.jpg` — annotated images with bounding boxes
- `severity_report.csv` — grade summary per image
- `severity_report.json` — full detection data in JSON

---

## Dependencies

| Package | Purpose |
|---|---|
| `ultralytics` | YOLOv11 inference engine |
| `opencv-python` | Image reading, annotation, encoding |
| `flask` | REST API backend |
| `flask-cors` | Cross-origin requests from the browser frontend |
| `numpy` | Array operations |

---

## Model Training

The model was trained on Kaggle using a custom corrosion dataset. See [`kaggle_training.ipynb`](kaggle_training.ipynb) for the full training pipeline.

- **Architecture:** YOLOv11
- **Input size:** 640 × 640
- **Classes:** 4 (corrosion, moderate corrosion, rust, severe corrosion)
- **Weights:** `best.pt` (40 MB)
- **ONNX export:** `pt files & onnx/best.onnx` (80 MB)

---

## Requirements

- Python 3.8+
- A modern browser (Chrome, Edge, Firefox)
- `best.pt` model file in the project root

---

## License

This project is for academic and research purposes. See [LICENSE](LICENSE) for details.
