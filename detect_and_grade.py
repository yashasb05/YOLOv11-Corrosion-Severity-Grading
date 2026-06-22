"""
Rust & Corrosion Detection with Severity Grading
=================================================
Local inference script. Processes images, draws bounding boxes,
and generates severity reports.

Usage:
    python detect_and_grade.py --source path/to/images --weights best.pt
    python detect_and_grade.py --source single_image.jpg --weights best.pt
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

# ──────────────────────────────────────────────
# CLASS & SEVERITY DEFINITIONS
# ──────────────────────────────────────────────
CLASS_NAMES = ['corrosion', 'moderate corrosion', 'rust', 'severe corrosion']

SEVERITY_MAP = {
    0: {'grade': 1, 'label': 'MILD',     'color': (76, 175, 80)},    # Green
    1: {'grade': 2, 'label': 'MODERATE',  'color': (0, 152, 255)},    # Orange (BGR)
    2: {'grade': 1, 'label': 'MILD',      'color': (74, 195, 139)},   # Light green
    3: {'grade': 3, 'label': 'SEVERE',    'color': (54, 67, 244)},    # Red (BGR)
}


def compute_overall_grade(detections, img_area):
    """
    Compute overall severity grade based on:
    1. Maximum severity of any detection
    2. Total corrosion coverage area
    3. Number of detections
    """
    if not detections:
        return {'grade': 0, 'label': 'NONE', 'description': 'No corrosion detected'}

    max_severity = max(d['severity_grade'] for d in detections)
    total_area = sum(d['area'] for d in detections)
    coverage_pct = (total_area / img_area) * 100 if img_area > 0 else 0
    num_detections = len(detections)

    # Grade logic: severity + coverage + density
    if max_severity == 3 or coverage_pct > 50:
        grade = 3
        label = 'CRITICAL'
        desc = 'Immediate maintenance required. Severe structural risk.'
    elif max_severity == 2 or coverage_pct > 25 or num_detections > 5:
        grade = 2
        label = 'MODERATE'
        desc = 'Schedule maintenance. Progressive degradation detected.'
    else:
        grade = 1
        label = 'MILD'
        desc = 'Monitor periodically. Minor surface corrosion.'

    return {
        'grade': grade,
        'label': label,
        'description': desc,
        'coverage_pct': round(coverage_pct, 1),
        'num_detections': num_detections,
    }


def draw_detections(img, detections, overall_grade):
    """Draw bounding boxes and severity labels on the image."""
    h, w = img.shape[:2]

    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        color = det['color']
        severity = det['severity_label']
        conf = det['confidence']
        cls_name = det['class_name']

        # Draw box
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        # Label
        label = f"{cls_name} [{severity}] {conf:.0%}"
        (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)
        cv2.putText(img, label, (x1 + 3, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    # Overall grade banner
    grade_colors = {
        'NONE': (200, 200, 200), 'MILD': (76, 175, 80),
        'MODERATE': (0, 152, 255), 'CRITICAL': (54, 67, 244)
    }
    banner_color = grade_colors.get(overall_grade['label'], (200, 200, 200))
    banner_text = f"Overall: {overall_grade['label']} (Grade {overall_grade['grade']})"
    if 'coverage_pct' in overall_grade:
        banner_text += f" | Coverage: {overall_grade['coverage_pct']}%"

    cv2.rectangle(img, (0, 0), (w, 32), banner_color, -1)
    cv2.putText(img, banner_text, (10, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

    return img


def process_image(model, image_path, conf_threshold=0.25):
    """Process a single image: detect and grade."""
    img = cv2.imread(str(image_path))
    if img is None:
        print(f"  ⚠️ Cannot read: {image_path}")
        return None, None, None

    h, w = img.shape[:2]
    img_area = h * w

    # Run inference
    results = model.predict(str(image_path), imgsz=640, conf=conf_threshold, verbose=False)

    detections = []
    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        severity_info = SEVERITY_MAP[cls_id]

        detections.append({
            'class_id': cls_id,
            'class_name': CLASS_NAMES[cls_id],
            'confidence': conf,
            'bbox': [x1, y1, x2, y2],
            'area': (x2 - x1) * (y2 - y1),
            'severity_grade': severity_info['grade'],
            'severity_label': severity_info['label'],
            'color': severity_info['color'],
        })

    overall = compute_overall_grade(detections, img_area)
    annotated = draw_detections(img.copy(), detections, overall)

    return annotated, detections, overall


def main():
    parser = argparse.ArgumentParser(description='Rust/Corrosion Detection & Severity Grading')
    parser.add_argument('--source', required=True, help='Path to image or directory of images')
    parser.add_argument('--weights', required=True, help='Path to YOLOv11 weights (best.pt)')
    parser.add_argument('--conf', type=float, default=0.25, help='Confidence threshold')
    parser.add_argument('--output', default='graded_output', help='Output directory')
    args = parser.parse_args()

    # Load model
    print(f"Loading model: {args.weights}")
    model = YOLO(args.weights)

    # Collect images
    source = Path(args.source)
    if source.is_file():
        image_paths = [source]
    elif source.is_dir():
        image_paths = sorted(
            p for p in source.iterdir()
            if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        )
    else:
        print(f"❌ Source not found: {source}")
        sys.exit(1)

    print(f"Processing {len(image_paths)} images...")

    # Create output dir
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # CSV report
    csv_path = out_dir / 'severity_report.csv'
    csv_file = open(csv_path, 'w', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow([
        'Image', 'Overall_Grade', 'Grade_Level', 'Coverage_%',
        'Num_Detections', 'Description'
    ])

    all_reports = []

    for i, img_path in enumerate(image_paths, 1):
        print(f"  [{i}/{len(image_paths)}] {img_path.name}", end='')

        annotated, detections, overall = process_image(model, img_path, args.conf)
        if annotated is None:
            continue

        # Save annotated image
        out_path = out_dir / f"graded_{img_path.name}"
        cv2.imwrite(str(out_path), annotated)

        # Write CSV row
        csv_writer.writerow([
            img_path.name,
            overall['label'],
            overall['grade'],
            overall.get('coverage_pct', 0),
            overall.get('num_detections', 0),
            overall.get('description', '')
        ])

        all_reports.append({
            'image': img_path.name,
            'overall': overall,
            'detections': [
                {k: v for k, v in d.items() if k != 'color'}
                for d in detections
            ]
        })

        print(f" → {overall['label']} ({overall.get('num_detections', 0)} detections)")

    csv_file.close()

    # Save JSON report
    json_path = out_dir / 'severity_report.json'
    with open(json_path, 'w') as f:
        json.dump(all_reports, f, indent=2)

    # Summary
    print(f"\n{'='*50}")
    print(f"✅ COMPLETE — {len(all_reports)} images processed")
    print(f"   Output: {out_dir.resolve()}")
    print(f"   CSV:    {csv_path.name}")
    print(f"   JSON:   {json_path.name}")

    # Grade distribution
    from collections import Counter
    grade_dist = Counter(r['overall']['label'] for r in all_reports)
    print(f"\n   Grade Distribution:")
    for grade in ['CRITICAL', 'MODERATE', 'MILD', 'NONE']:
        if grade in grade_dist:
            print(f"     {grade}: {grade_dist[grade]} images")


if __name__ == '__main__':
    main()
