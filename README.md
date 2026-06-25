# YOLOv11 Corrosion Severity Grading

<p align="center">
  <img src="https://img.shields.io/badge/Model-YOLOv11-ff6b35?style=for-the-badge&logo=pytorch" />
  <img src="https://img.shields.io/badge/Backend-Flask-000000?style=for-the-badge&logo=flask" />
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/Inference-Local%20%2F%20Offline-22c55e?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Frontend-HTML%20%2F%20CSS%20%2F%20JS-f59e0b?style=for-the-badge" />
</p>

An AI-powered corrosion detection and severity grading system built on **YOLOv11**. The system accepts an image of a metal surface and returns detection results, severity grading, coverage percentage, and model confidence scores. Everything runs fully offline — no internet connection or cloud service is required after setup.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Web Interface](#web-interface)
- [REST API Reference](#rest-api-reference)
- [Detection Classes and Severity Logic](#detection-classes-and-severity-logic)
- [CLI Usage](#cli-usage)
- [Model Training](#model-training)
- [Dependencies](#dependencies)
- [License](#license)

---

## Features

| Feature | Description |
|---|---|
| Real-Time Detection | Detects corrosion using YOLOv11 at 640 x 640 pixel resolution |
| 4-Class Recognition | Identifies `corrosion`, `moderate corrosion`, `rust`, and `severe corrosion` |
| Severity Grading | Grades results as NONE, MILD, MODERATE, or CRITICAL |
| Coverage Analysis | Calculates the percentage of the image area affected by corrosion |
| Confidence Scoring | Reports per-detection and average model confidence |
| Side-by-Side View | Displays the original image alongside the annotated output |
| Severity Bar | Visual gradient bar with animated marker from Mild to Critical |
| Confidence Ring | Animated circular gauge showing average model confidence |
| Fully Offline | No data is uploaded anywhere — all processing happens on your machine |

---

## Project Structure

```
.
├── best.pt                  # YOLOv11 trained model weights (~40 MB)
├── app.py                   # Flask REST API backend
├── detect_and_grade.py      # Standalone command-line inference script
├── index.html               # Web UI (open directly in a browser)
├── style.css                # Dark-theme stylesheet
├── app.js                   # Frontend logic and API integration
├── graded_output/           # Saved annotated images and reports (auto-created)
├── dataset/                 # Training dataset
├── pt files & onnx/         # Alternative model formats (ONNX export)
└── kaggle_training.ipynb    # Model training notebook (Kaggle)
```

> **Note:** The `graded_output/` directory is created automatically the first time you run inference.

---

## Requirements

- Python 3.8 or higher
- A modern browser (Chrome, Edge, Firefox, or Safari)
- `best.pt` model file present in the project root

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yashasb05/YOLOv11-Corrosion-Severity-Grading.git
cd YOLOv11-Corrosion-Severity-Grading
```

### 2. Install Python dependencies

```bash
pip install flask flask-cors ultralytics opencv-python
```

If you are on a network-restricted environment, use a mirror:

```bash
pip install flask flask-cors ultralytics opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. Start the Flask backend

```bash
python app.py
```

You should see the following output once the server is ready:

```
[INFO] Loading model from best.pt ...
[INFO] Model ready.
 * Running on http://127.0.0.1:5000
```

Keep this terminal window open while using the application.

### 4. Open the web interface

Open `index.html` in your browser (double-click the file or drag it into a browser window).

The status indicator in the top-right corner will turn green when the backend is connected. Upload or drop any image to begin analysis.

---

## Web Interface

The frontend is a single-page application built with plain HTML, CSS, and vanilla JavaScript. It has no external framework dependencies and works by opening the file directly in a browser.

**What happens when you upload an image:**

1. An animated loading sequence runs through the stages: Preprocessing, Detecting, and Grading.
2. The original image and the annotated output are displayed side by side.
3. An overall grade badge is shown: NONE, MILD, MODERATE, or CRITICAL.
4. The severity bar animates its marker based on the computed severity score.
5. The confidence ring displays the average, maximum, and minimum per-bounding-box confidence.
6. A detection breakdown table lists every detected region with its class, grade, and confidence.

---

https://github.com/user-attachments/assets/e0a63df5-d2aa-44fc-a7e9-33c89dcb7440

---

<img width="1887" height="883" alt="Screenshot 2026-06-22 192932" src="https://github.com/user-attachments/assets/c30d29ad-b878-4ee0-af6e-2685181d8f80" />

---

<img width="1884" height="895" alt="Screenshot 2026-06-22 192959" src="https://github.com/user-attachments/assets/7480b891-530b-401e-aaf9-e41d8f22147c" />

---

## REST API Reference

The Flask backend exposes two endpoints.

### GET /api/health

Checks whether the server is running and the model is loaded.

**Response:**

```json
{
  "status": "ok",
  "model": "path/to/best.pt"
}
```

---

### POST /api/analyze

Analyzes an uploaded image for corrosion and returns structured results.

**Request:**

`multipart/form-data` with a field named `image`. Accepted formats: JPEG, PNG, BMP, WebP.

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

**Response fields explained:**

| Field | Description |
|---|---|
| `original_image` | Base64-encoded JPEG of the input image |
| `annotated_image` | Base64-encoded JPEG with bounding boxes and labels drawn |
| `avg_confidence` | Average detection confidence across all detections (0–100) |
| `overall.grade` | Integer grade: 0 = NONE, 1 = MILD, 2 = MODERATE, 3 = CRITICAL |
| `overall.coverage_pct` | Percentage of the image area covered by detected corrosion |
| `overall.severity_pct` | Normalized severity score for the UI gauge (0–100) |
| `detections` | Array of individual detection objects |

---

## Detection Classes and Severity Logic

### Class Definitions

| Class ID | Class Name | Severity Grade | Label |
|---|---|---|---|
| 0 | `corrosion` | 1 | MILD |
| 1 | `moderate corrosion` | 2 | MODERATE |
| 2 | `rust` | 1 | MILD |
| 3 | `severe corrosion` | 3 | SEVERE |

### Overall Grade Logic

The overall grade is determined after evaluating all detections together:

| Condition | Grade | Label |
|---|---|---|
| Max severity = 3, OR coverage > 50% | 3 | CRITICAL |
| Max severity = 2, OR coverage > 25%, OR more than 5 detections | 2 | MODERATE |
| Any detections below the above thresholds | 1 | MILD |
| No detections found | 0 | NONE |

The default confidence threshold for detections is **0.25** (25%). Detections below this score are discarded.

---

## CLI Usage

You can run inference directly from the command line without starting the web interface.

**Single image:**

```bash
python detect_and_grade.py --source path/to/image.jpg --weights best.pt
```

**Entire folder of images:**

```bash
python detect_and_grade.py --source path/to/images/ --weights best.pt
```

**Custom confidence threshold and output directory:**

```bash
python detect_and_grade.py --source images/ --weights best.pt --conf 0.35 --output results/
```

**Available arguments:**

| Argument | Default | Description |
|---|---|---|
| `--source` | (required) | Path to a single image file or a directory of images |
| `--weights` | (required) | Path to the YOLOv11 model weights file (`best.pt`) |
| `--conf` | `0.25` | Minimum confidence threshold for detections |
| `--output` | `graded_output` | Directory where annotated images and reports are saved |

**Output files saved to the output directory:**

| File | Description |
|---|---|
| `graded_<filename>.jpg` | Annotated image with bounding boxes and grade banner |
| `severity_report.csv` | Summary table — one row per image |
| `severity_report.json` | Full detection data including bounding boxes and per-image grades |

---

## Model Training

The model was trained on Kaggle using a custom-labeled corrosion dataset. The full training pipeline is documented in [`kaggle_training.ipynb`](kaggle_training.ipynb).

The dataset used for this model is : https://universe.roboflow.com/averkios/rust-corrosion-detection.

Credits: averkios

| Property | Value |
|---|---|
| Architecture | YOLOv11 |
| Input resolution | 640 x 640 pixels |
| Number of classes | 4 |
| Weight file | `best.pt` (~40 MB) |
| ONNX export | `pt files & onnx/best.onnx` (~80 MB) |

The ONNX export can be used for deployment in environments that do not support PyTorch, such as embedded systems or browser-based inference with ONNX Runtime Web.

---

## Dependencies

| Package | Purpose |
|---|---|
| `ultralytics` | YOLOv11 model loading and inference |
| `opencv-python` | Image reading, bounding box drawing, and JPEG encoding |
| `flask` | REST API backend server |
| `flask-cors` | Allows the browser frontend to call the local API (CORS headers) |
| `numpy` | Numerical array operations |

---

## License

This project is intended for academic and research purposes. See [LICENSE](LICENSE) for details.
