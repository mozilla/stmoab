import json
from dateutil.parser import parse

from redash_client.constants import VizWidth, ChartType

from stmoab.tests.base import AppTest
from stmoab.SummaryDashboard import SummaryDashboard


class TestSummaryDashboard(AppTest):

  def test_init_exception_thrown(self):
    self._setupMockRedashClientException("create_new_dashboard")

    self.assertRaisesRegexp(
        self.dash.ExternalAPIError,
        "Unable to create new dashboard",
        lambda: SummaryDashboard("a", "b", "c", "d",))

  def test_add_visualization_to_dash_exception_thrown(self):
    self._setupMockRedashClientException("add_visualization_to_dashboard")

    self.assertRaisesRegexp(
        self.dash.ExternalAPIError,
        "Unable to add visualization",
        lambda: self.dash._add_visualization_to_dashboard("a", "b"))

  def test_get_query_results_exception_thrown(self):
    self._setupMockRedashClientException("get_query_results")

    self.assertRaisesRegexp(
        self.dash.ExternalAPIError,
        "Unable to fetch query results",
        lambda: self.dash._get_query_results("a", "b"))

  def test_update_query_exception_thrown(self):
    self._setupMockRedashClientException("update_query")

    self.assertRaisesRegexp(
        self.dash.ExternalAPIError,
        "Unable to update query",
        lambda: self.dash._update_query("a", "b", "c", "d",))

  def test_create_new_query_exception_thrown(self):
    self._setupMockRedashClientException("create_new_query")

    self.assertRaisesRegexp(
        self.dash.ExternalAPIError,
        "Unable to create query titled",
        lambda: self.dash._create_new_query("a", "b", "c"))

  def test_create_new_visualization_exception_thrown(self):
    self._setupMockRedashClientException("create_new_visualization")

    self.assertRaisesRegexp(
        self.dash.ExternalAPIError,
        "Unable to create visualization titled",
        lambda: self.dash._create_new_visualization(
            "a", "b", "c", "d", "e", "f", "g", "h"))

  def test_get_widgets_from_dash_exception_thrown(self):
    self._setupMockRedashClientException("get_widget_from_dash")

    self.assertRaisesRegexp(
        self.dash.ExternalAPIError,
        "Unable to access dashboard widgets",
        lambda: self.dash._get_widgets_from_dash("dash_name"))

  def test_remove_graph_from_dashboard_exception_thrown(self):
    self._setupMockRedashClientException("remove_visualization")

    self.assertRaisesRegexp(
        self.dash.ExternalAPIError,
        "Unable to remove widget",
        lambda: self.dash.remove_graph_from_dashboard(123, 456))

  def test_add_copied_query_exception_thrown(self):
    MOCK_WIDGET = {
        "query": "SELECT thing FROM table",
        "data_source_id": 5,
        "type": "meep",
        "options": "boop",
        "id": 123
    }
    QUERY_PARAMS = {"a": "b"}

    self._setupMockRedashClientException("make_new_visualization_request")

    self.assertRaisesRegexp(
        self.dash.ExternalAPIError,
        "Unable to add copied query",
        lambda: self.dash._add_copied_query_to_dashboard(
            MOCK_WIDGET, "query_id", QUERY_PARAMS, None, None))

  def test_update_refresh_schedule_exception_thrown(self):
    MOCK_WIDGET = [{
        "visualization": {
            "query": {
                "name": "query_name",
                "id": 1
            }
        },
        "id": 4}]

    def get_widget_from_dash_mock(self):
      return MOCK_WIDGET

    self._setupMockRedashClientException(
        "get_widget_from_dash", get_widget_from_dash_mock)
    self._setupMockRedashClientException("update_query_schedule")

    self.assertRaisesRegexp(
        self.dash.ExternalAPIError,
        "Unable to update schedule for widget",
        lambda: self.dash.update_refresh_schedule(1000))

  def test_update_refresh_schedule_success(self):
    EXPECTED_QUERY_ID = "query_id123"
    WIDGETS_RESPONSE = {
        "widgets": [
            {
                "visualization": {
                    "query": {
                        "nope": "fail"
                    }
                }
            }, {
                "visualization": {
                    "query": {
                        "id": EXPECTED_QUERY_ID
                    }
                }
            }, {
                "visualization": {
                    "query": {
                        "muhahaha": "you can't catch me!"
                    }
                }
            }
        ]
    }

    self.mock_requests_get.return_value = self.get_mock_response(
        content=json.dumps(WIDGETS_RESPONSE))
    self.mock_requests_post.return_value = self.get_mock_response()

    self.dash.update_refresh_schedule(86400)

    # 2 posts to create the dashboard and make it public
    # 1 post for refreshing the one valid visualization ID
    # 2 gets for creating the dashboard and looking up chart names
    self.assertEqual(self.mock_requests_post.call_count, 3)
    self.assertEqual(self.mock_requests_get.call_count, 2)
    self.assertEqual(self.mock_requests_delete.call_count, 0)

  def test_get_chart_data_success(self):
    EXPECTED_QUERY_NAME = "query_name123"
    EXPECTED_QUERY_NAME2 = "query_name456"
    EXPECTED_QUERY_NAME3 = "query_name789"
    EXPECTED_UPDATED_AT = "2018-02-27T18:45:01.995651+00:00"
    WIDGETS_RESPONSE = {
        "widgets": [
            {
                "visualization": {
                    "query": {
                        "updated_at": EXPECTED_UPDATED_AT,
                        "name": EXPECTED_QUERY_NAME,
                        "id": 1
                    }
                },
                "id": 4
            }, {
                "visualization": {
                    "query": {
                        "updated_at": EXPECTED_UPDATED_AT,
                        "not_a_name": EXPECTED_QUERY_NAME2,
                        "id": 2
                    }
                },
                "id": 5
            }, {
                "visualization": {
                    "query": {
                        "updated_at": EXPECTED_UPDATED_AT,
                        "name": EXPECTED_QUERY_NAME3,
                        "id": 3
                    }
                },
                "id": 6
            }
        ]
    }
    EXPECTED_NAMES = [EXPECTED_QUERY_NAME, EXPECTED_QUERY_NAME3]
    EXPECTED_QUERY_IDS = [1, 3]
    EXPECTED_WIDGET_IDS = [4, 6]

    self.mock_requests_get.return_value = self.get_mock_response(
        content=json.dumps(WIDGETS_RESPONSE))

    data_dict = self.dash.get_query_ids_and_names()

    self.assertEqual(len(data_dict), 2)
    for name in data_dict:
      self.assertEqual(len(data_dict[name]), 4)
      self.assertTrue(name in EXPECTED_NAMES)
      self.assertTrue(data_dict[name]["query_id"] in EXPECTED_QUERY_IDS)
      self.assertTrue(data_dict[name]["widget_id"] in EXPECTED_WIDGET_IDS)
      self.assertEqual(data_dict[name]["updated_at"], EXPECTED_UPDATED_AT)

  def test_get_update_range_empty(self):
    update_range = self.dash.get_update_range()
    self.assertEqual(len(update_range), 0)
    self.assertEqual(update_range, {})

  def test_get_update_range_correct_range(self):
    EXPECTED_MIN_UPDATE = "2018-02-27T18:47:41.932017+00:00"
    EXPECTED_MID_UPDATE = "2018-02-27T18:48:11.295060+00:00"
    EXPECTED_MAX_UPDATE = "2018-02-27T18:59:05.862722+00:00"
    WIDGETS_RESPONSE = {
        "widgets": [
            {
                "visualization": {
                    "query": {
                        "updated_at": EXPECTED_MIN_UPDATE,
                        "name": "name1",
                        "id": 1
                    }
                },
                "id": 4
            }, {
                "visualization": {
                    "query": {
                        "updated_at": EXPECTED_MID_UPDATE,
                        "name": "name2",
                        "id": 2
                    }
                },
                "id": 5
            }, {
                "visualization": {
                    "query": {
                        "updated_at": EXPECTED_MAX_UPDATE,
                        "name": "name3",
                        "id": 3
                    }
                },
                "id": 6
            }
        ]
    }
    self.mock_requests_get.return_value = self.get_mock_response(
        content=json.dumps(WIDGETS_RESPONSE))

    update_range = self.dash.get_update_range()
    self.assertEqual(len(update_range), 2)
    self.assertTrue("min" in update_range)
    self.assertTrue("max" in update_range)
    self.assertEqual(update_range["min"], parse(EXPECTED_MIN_UPDATE))
    self.assertEqual(update_range["max"], parse(EXPECTED_MAX_UPDATE))

  def test_remove_all_graphs_success(self):
    EXPECTED_QUERY_ID = "query_id123"
    EXPECTED_QUERY_ID2 = "query_id456"
    EXPECTED_QUERY_ID3 = "query_id789"
    WIDGETS_RESPONSE = {
        "widgets": [
            {
                "id": EXPECTED_QUERY_ID,
                "visualization": {
                    "query": {
                        "id": EXPECTED_QUERY_ID,
                        "name": "A"
                    }
                }
            }, {
                "id": EXPECTED_QUERY_ID2,
                "visualization": {
                    "query": {
                        "id": EXPECTED_QUERY_ID2,
                        "name": "B"
                    }
                }
            }, {
                "id": EXPECTED_QUERY_ID3,
                "visualization": {
                    "query": {
                        "id": EXPECTED_QUERY_ID3,
                        "name": "C"
                    }
                }
            }
        ]
    }

    self.mock_requests_delete.return_value = self.get_mock_response()
    self.mock_requests_get.return_value = self.get_mock_response(
        content=json.dumps(WIDGETS_RESPONSE))

    self.dash.remove_all_graphs()

    # 2 posts to create the dashboard and make it public
    # 2 gets for creating the dashboard and looking up chart names
    self.assertEqual(self.mock_requests_post.call_count, 2)
    self.assertEqual(self.mock_requests_get.call_count, 2)
    self.assertEqual(self.mock_requests_delete.call_count, 6)

  def test_add_query_to_dashboard_makes_expected_calls(self):
    QUERY_TITLE = "title"
    QUERY_STRING = "SELECT * FROM test"

    MAU_DAU_COLUMN_MAPPING = {
        "a": "x",
        "b": "y",
        "c": "y",
        "d": "y"
    }

    self.dash._add_query_to_dashboard(
        QUERY_TITLE,
        QUERY_STRING,
        5,
        VizWidth.WIDE,
        column_mapping=MAU_DAU_COLUMN_MAPPING,
        chart_type=ChartType.BAR
    )

    # POST calls:
    #     1) Create dashboard
    #     2) Create new query
    #     3) Create new visualization
    #     4) Add visualization to dashboard
    #     5) Make dashboard public
    # GET calls:
    #     1) Create dashboard
    self.assertEqual(self.mock_requests_post.call_count, 5)
    self.assertEqual(self.mock_requests_get.call_count, 1)
