import unittest

from spaghetti_ai.camera import SnapshotClient


class Response:
    def __init__(self, content: bytes, error: Exception | None = None) -> None:
        self.content = content
        self._error = error

    def raise_for_status(self) -> None:
        if self._error:
            raise self._error


class SnapshotClientTest(unittest.TestCase):
    def test_next_loop_reconnects_after_a_failed_request(self) -> None:
        responses = iter(
            [
                Response(b"", ConnectionError("camera unavailable")),
                Response(b"jpeg"),
            ]
        )
        client = SnapshotClient("http://camera/snapshot", 4, getter=lambda *args, **kwargs: next(responses))

        with self.assertRaises(ConnectionError):
            client.fetch()
        self.assertEqual(client.fetch(), b"jpeg")

    def test_empty_camera_response_is_rejected(self) -> None:
        client = SnapshotClient("http://camera/snapshot", 4, getter=lambda *args, **kwargs: Response(b""))

        with self.assertRaisesRegex(ValueError, "empty"):
            client.fetch()
