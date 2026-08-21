import unittest

import numpy as np

from spaghetti_ai.detector import Detection
from spaghetti_ai.service import annotate_alert_image


class AlertAnnotationTest(unittest.TestCase):
    def test_marks_scaled_detection_in_original_image(self) -> None:
        image = np.zeros((100, 120, 3), dtype=np.uint8)
        detection = Detection(0.91, 10.0, 20.0, 30.0, 40.0)

        annotated = annotate_alert_image(image, [detection], (5, 7), 0.5)

        red = np.array([0, 0, 255], dtype=np.uint8)
        self.assertTrue(np.array_equal(annotated[47, 25], red))
        self.assertTrue(np.array_equal(annotated[87, 65], red))
        self.assertFalse(np.array_equal(annotated[60, 45], red))
        self.assertTrue(np.array_equal(image, np.zeros((100, 120, 3), dtype=np.uint8)))

    def test_clips_boxes_to_camera_boundaries(self) -> None:
        image = np.zeros((40, 40, 3), dtype=np.uint8)
        detection = Detection(0.80, -10.0, -10.0, 60.0, 60.0)

        annotated = annotate_alert_image(image, [detection], (0, 0), 1.0)

        self.assertTrue(np.array_equal(annotated[0, 0], np.array([0, 0, 255], dtype=np.uint8)))
        self.assertTrue(np.array_equal(annotated[39, 39], np.array([0, 0, 255], dtype=np.uint8)))


if __name__ == "__main__":
    unittest.main()
