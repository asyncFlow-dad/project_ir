from unittest import TestCase

from ir_search.schema import COLLECTION_NAME, collection_config
from ir_search.streams import STREAM_INBOX, all_streams
from ir_search.swarm_routes import route_request


class SchemaStreamTests(TestCase):
    def test_collection_config_matches_report_shape(self) -> None:
        config = collection_config()
        self.assertEqual(config["collection"], COLLECTION_NAME)
        self.assertIn("text_dense", config["vectors"])
        self.assertIn("text_sparse", config["sparse_vectors"])

    def test_streams_include_inbox(self) -> None:
        self.assertIn(STREAM_INBOX, all_streams())

    def test_route_request_for_pm(self) -> None:
        self.assertEqual(route_request(requester_bot="pm", intent="plan sprint"), "pm-planner")
