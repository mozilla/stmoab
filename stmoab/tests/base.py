import mock
import json
import unittest

from stmoab.SummaryDashboard import SummaryDashboard


class AppTest(unittest.TestCase):

  def _setupMockRedashClientException(self, functionToPatch,
                                      newFunction=None):
    mock_function_patcher = mock.patch(
        "stmoab.SummaryDashboard.RedashClient.{patchable}".format(
            patchable=functionToPatch))
    self.mock_function = mock_function_patcher.start()
    self.addCleanup(mock_function_patcher.stop)

    def redash_client_exception_raiser(*args, **kwargs):
      raise self.dash.redash.RedashClientException

    mockFunctionality = redash_client_exception_raiser
    if newFunction is not None:
        mockFunctionality = newFunction

    self.mock_function.side_effect = mockFunctionality

  def post_server(self, url, data):
    EXPECTED_QUERY_ID = "query_id123"
    QUERY_ID_RESPONSE = {
        "id": EXPECTED_QUERY_ID
    }

    response = self.get_mock_response(
        content=json.dumps(QUERY_ID_RESPONSE))

    self.server_calls += 1
    return response

  def get_dashboard(self, api_key):
    DASH_NAME = "Firefox iOS: Metrics Summary"
    EXPECTED_QUERY_ID = "query_id123"
    EXPECTED_SLUG = "some_slug_it_made"
    QUERY_ID_RESPONSE = {
        "id": EXPECTED_QUERY_ID,
        "slug": EXPECTED_SLUG
    }

    self.mock_requests_get.return_value = self.get_mock_response(
        content=json.dumps(QUERY_ID_RESPONSE))
    self.mock_requests_post.return_value = self.get_mock_response()

    dashboard = SummaryDashboard(
        self.API_KEY,
        DASH_NAME,
    )
    return dashboard

  def setUp(self):
    self.API_KEY = "test_key"

    mock_requests_post_patcher = mock.patch(
        "redash_client.client.requests.post")
    self.mock_requests_post = mock_requests_post_patcher.start()
    self.addCleanup(mock_requests_post_patcher.stop)

    mock_requests_get_patcher = mock.patch(
        "redash_client.client.requests.get")
    self.mock_requests_get = mock_requests_get_patcher.start()
    self.addCleanup(mock_requests_get_patcher.stop)

    mock_requests_delete_patcher = mock.patch(
        "redash_client.client.requests.delete")
    self.mock_requests_delete = mock_requests_delete_patcher.start()
    self.addCleanup(mock_requests_delete_patcher.stop)

    self.dash = self.get_dashboard(self.API_KEY)

  def get_mock_response(self, status=200, content='{}'):
    mock_response = mock.Mock()
    mock_response.status_code = status
    mock_response.content = content

    return mock_response
