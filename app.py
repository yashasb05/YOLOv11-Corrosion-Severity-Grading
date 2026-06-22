"""
Flask API Backend for Rust Detection & Severity Grading
========================================================
Exposes /api/analyze endpoint consumed by the frontend.

Run:  python app.py
"""

import base64
import io
import json
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from ultralytics import YOLO

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
WEIGHTS    = BASE_DIR / "best.pt"
CONF_THRES = 0.25

CLASS_NAMES = ['corrosion', 'moderate corrosion', 'rust', 'severe corrosion']

SEVERITY_MAP = {
    0: {'grade': 1, 'label': 'MILD',     'color': (76, 175, 80)},
    1: {'grade': 2, 'label': 'MODERATE', 'color': (0, 152, 255)},
    2: {'grade': 1, 'label': 'MILD',     'color': (74, 195, 139)},
    3: {'grade': 3, 'label': 'SEVERE',   'color': (54, 67, 244)},
}

app  = Flask(__name__)
CORS(app)

# Load model once at startup
print(f"[INFO] Loading model from {WEIGHTS} …")
model = YOLO(str(WEIGHTS))
print("[INFO] Model ready.")


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────
def compute_overall_grade(detections, img_area):
    if not detections:
        return {
            'grade': 0, 'label': 'NONE',
            'description': 'No corrosion detected',
            'coverage_pct': 0.0, 'num_detections': 0,
            'severity_pct': 0.0,
        }

    max_severity  = max(d['severity_grade'] for d in detections)
    total_area    = sum(d['area'] for d in detections)
    coverage_pct  = (total_area / img_area) * 100 if img_area > 0 else 0
    num_detections = len(detections)

    if max_severity == 3 or coverage_pct > 50:
        grade, label, desc = 3, 'CRITICAL', 'Immediate maintenance required. Severe structural risk.'
        severity_pct = min(100.0, 75 + coverage_pct * 0.25)
    elif max_severity == 2 or coverage_pct > 25 or num_detections > 5:
        grade, label, desc = 2, 'MODERATE', 'Schedule maintenance. Progressive degradation detected.'
        severity_pct = min(74.9, 40 + coverage_pct * 0.7)
    else:
        grade, label, desc = 1, 'MILD', 'Monitor periodically. Minor surface corrosion.'
        severity_pct = min(39.9, max(5.0, coverage_pct * 0.8))

    return {
        'grade': grade,
        'label': label,
        'description': desc,
        'coverage_pct': round(coverage_pct, 1),
        'num_detections': num_detections,
        'severity_pct': round(severity_pct, 1),
    }


def draw_detections(img, detections, overall_grade):
    h, w = img.shape[:2]

    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        color    = det['color']
        severity = det['severity_label']
        conf     = det['confidence']
        cls_name = det['class_name']

        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        label = f"{cls_name} [{severity}] {conf:.0%}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)
        cv2.putText(img, label, (x1 + 3, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    grade_colors = {
        'NONE': (100, 100, 100), 'MILD': (76, 175, 80),
        'MODERATE': (0, 152, 255), 'CRITICAL': (54, 67, 244)
    }
    banner_color = grade_colors.get(overall_grade['label'], (100, 100, 100))
    banner_text  = f"Overall: {overall_grade['label']} (Grade {overall_grade['grade']})"
    if overall_grade.get('coverage_pct', 0) > 0:
        banner_text += f" | Coverage: {overall_grade['coverage_pct']}%"

    cv2.rectangle(img, (0, 0), (w, 36), banner_color, -1)
    cv2.putText(img, banner_text, (10, 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
    return img


def encode_image_to_b64(img_bgr):
    _, buf = cv2.imencode('.jpg', img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return base64.b64encode(buf).decode('utf-8')


# ──────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────
@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    # Read image from memory
    file_bytes = np.frombuffer(file.read(), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({'error': 'Cannot decode image'}), 400

    h, w = img.shape[:2]
    img_area = h * w

    # Save to temp file for YOLO (YOLO needs a path)
    suffix = Path(file.filename).suffix or '.jpg'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes.tobytes())
        tmp_path = tmp.name

    try:
        results = model.predict(tmp_path, imgsz=640, conf=CONF_THRES, verbose=False)
    finally:
        os.unlink(tmp_path)

    detections = []
    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        cls_id = int(box.cls[0])
        conf   = float(box.conf[0])
        sev    = SEVERITY_MAP.get(cls_id, SEVERITY_MAP[0])

        detections.append({
            'class_id':       cls_id,
            'class_name':     CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else f'class_{cls_id}',
            'confidence':     round(conf, 4),
            'bbox':           [x1, y1, x2, y2],
            'area':           (x2 - x1) * (y2 - y1),
            'severity_grade': sev['grade'],
            'severity_label': sev['label'],
            'color':          sev['color'],
        })

    overall   = compute_overall_grade(detections, img_area)
    annotated = draw_detections(img.copy(), detections, overall)

    # Average confidence across all detections
    avg_conf = round(
        sum(d['confidence'] for d in detections) / len(detections) * 100, 1
    ) if detections else 0.0

    # Strip color tuples before serialising
    clean_detections = [
        {k: v for k, v in d.items() if k != 'color'}
        for d in detections
    ]

    return jsonify({
        'original_image':  encode_image_to_b64(img),
        'annotated_image': encode_image_to_b64(annotated),
        'overall':         overall,
        'detections':      clean_detections,
        'avg_confidence':  avg_conf,
    })


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model': str(WEIGHTS)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
