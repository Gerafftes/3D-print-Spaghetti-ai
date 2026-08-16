from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Detection:
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float


class ObicoOnnxDetector:
    """CPU-only implementation compatible with Obico's pinned ONNX model."""

    def __init__(self, model_path: Path, threshold: float, nms_threshold: float = 0.4) -> None:
        import onnxruntime

        session_options = onnxruntime.SessionOptions()
        session_options.intra_op_num_threads = 1
        session_options.inter_op_num_threads = 1
        session_options.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
        session_options.enable_cpu_mem_arena = False
        self._session = onnxruntime.InferenceSession(
            str(model_path),
            sess_options=session_options,
            providers=["CPUExecutionProvider"],
        )
        self._threshold = threshold
        self._nms_threshold = nms_threshold

    def detect(self, image) -> list[Detection]:
        import cv2
        import numpy as np

        input_spec = self._session.get_inputs()[0]
        input_height = int(input_spec.shape[2])
        input_width = int(input_spec.shape[3])
        image_height, image_width = image.shape[:2]

        resized = cv2.resize(image, (input_width, input_height), interpolation=cv2.INTER_LINEAR)
        tensor = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        tensor = np.transpose(tensor, (2, 0, 1)).astype(np.float32)[None, ...] / 255.0
        boxes_output, confidences_output = self._session.run(
            None,
            {input_spec.name: tensor},
        )
        boxes = boxes_output[:, :, 0][0]
        confidences = confidences_output[0, :, 0]
        selected = confidences > self._threshold
        boxes = boxes[selected]
        confidences = confidences[selected]
        if len(boxes) == 0:
            return []

        pixel_boxes = []
        for box in boxes:
            pixel_boxes.append(
                [
                    float(box[0] * image_width),
                    float(box[1] * image_height),
                    float(box[2] * image_width),
                    float(box[3] * image_height),
                ]
            )
        keep = cv2.dnn.NMSBoxes(
            [
                [x1, y1, max(0.0, x2 - x1), max(0.0, y2 - y1)]
                for x1, y1, x2, y2 in pixel_boxes
            ],
            confidences.tolist(),
            self._threshold,
            self._nms_threshold,
        )
        indices = [int(index) for index in keep]
        return [Detection(float(confidences[index]), *pixel_boxes[index]) for index in indices]
