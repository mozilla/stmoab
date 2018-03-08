import time
from datetime import datetime
from dateutil.parser import parse

from redash_client.client import RedashClient
from redash_client.constants import (
    VizWidth, VizType, ChartType, TimeInterval)


class SummaryDashboard(object):
  TILES_DATA_SOURCE_ID = 5

  class ExternalAPIError(Exception):
    pass

  def __init__(self, api_key, dash_name, events_table_name,
               start_date, end_date=None):
    self._dash_name = dash_name
    self._events_table = events_table_name
    self._start_date = start_date
    self._end_date = end_date if end_date else time.strftime("%Y-%m-%d")
    self._params = {
        "start_date": self._start_date,
        "end_date": self._end_date
    }

    try:
      self.redash = RedashClient(api_key)
      self._dash_id = self.redash.create_new_dashboard(self._dash_name)
      self.redash.publish_dashboard(self._dash_id)
      self.public_url = self.redash.get_public_url(self._dash_id)
    except self.redash.RedashClientException as e:
      raise self.ExternalAPIError(
          "Unable to create new dashboard: {error}".format(error=e), e)

  def _create_new_query(self, query_title, query_string,
                        data_source, description=""):
    try:
      query_id, table_id = self.redash.create_new_query(
        query_title, query_string, data_source, description=None)
      return query_id, table_id
    except self.redash.RedashClientException as e:
      raise self.ExternalAPIError(
          "Unable to create query titled '{title}': {error}".format(
              title=query_title, error=e))

  def _add_visualization_to_dashboard(self, viz_id, visualization_width):
    try:
      self.redash.add_visualization_to_dashboard(
        self._dash_id, viz_id, visualization_width)
    except self.redash.RedashClientException as e:
      raise self.ExternalAPIError(
          ("Unable to add visualization '{id}' to "
           "dashboard '{title}': {error}").format(
              id=viz_id, title=self._dash_name, error=e))

  def _get_query_results(self, query_string, data_source_id, query_name=""):
    try:
      data = self.redash.get_query_results(
          query_string, data_source_id)
      return data
    except self.redash.RedashClientException as e:
      raise self.ExternalAPIError(
        "Unable to fetch query results: '{query_name}' "
        " {error}".format(query_name=query_name, error=e))

  def _create_new_visualization(self, query_id, visualization_type,
                                visualization_name, chart_type,
                                column_mapping, series_options,
                                time_interval, stacking):
    try:
      viz_id = self.redash.create_new_visualization(
          query_id,
          visualization_type,
          visualization_name,
          chart_type,
          column_mapping,
          series_options,
          time_interval,
          stacking,
      )
      return viz_id
    except self.redash.RedashClientException as e:
      raise self.ExternalAPIError(
          "Unable to create visualization titled '{title}': {error}".format(
              title=visualization_name, error=e))

  def _get_widgets_from_dash(self, dash_name):
    try:
      return self.redash.get_widget_from_dash(dash_name)
    except self.redash.RedashClientException as e:
      raise self.ExternalAPIError(
          "Unable to access dashboard widgets: {error}".format(error=e), e)

  def _update_query(self, query_id, query_title, sql,
                    data_source_id, description="", options=""):
    try:
      self.redash.update_query(
          query_id,
          query_title,
          sql,
          data_source_id,
          description,
          options,
      )
    except self.redash.RedashClientException as e:
      raise self.ExternalAPIError(
          "Unable to update query {title}: {error}".format(
              title=query_title, error=e))

  def update_refresh_schedule(self, seconds_to_refresh):
    widgets = self._get_widgets_from_dash(self._dash_name)

    for widget in widgets:
      widget_id = widget.get(
          "visualization", {}).get("query", {}).get("id", None)

      if not widget_id:
        continue

      try:
        self.redash.update_query_schedule(widget_id, seconds_to_refresh)
      except self.redash.RedashClientException as e:
        raise self.ExternalAPIError(
          "Unable to update schedule for widget {widget_id}: {error}".format(
              widget_id=widget_id, error=e))

  def get_update_range(self):
    query_data = self.get_query_ids_and_names()

    if len(query_data) < 1:
      return {}

    dates = [parse(query_data[graph]["updated_at"]) for graph in query_data]
    update_range = {
        "min": min(dates),
        "max": max(dates)
    }
    return update_range

  def get_query_ids_and_names(self):
    widgets = self._get_widgets_from_dash(self._dash_name)

    data = {}
    for widget in widgets:
      widget_id = widget.get("id", None)

      query_id = widget.get(
          "visualization", {}).get("query", {}).get("id", None)

      widget_name = widget.get(
          "visualization", {}).get("query", {}).get("name", None)

      widget_query = widget.get(
          "visualization", {}).get("query", {}).get("query", None)

      updated_at = widget.get(
          "visualization", {}).get("query", {}).get("updated_at", None)

      if not widget_name:
        continue

      data[widget_name] = {
          "query_id": query_id,
          "widget_id": widget_id,
          "query": widget_query,
          "updated_at": updated_at
      }

    return data

  def remove_graph_from_dashboard(self, widget_id, query_id):
    try:
      if widget_id is not None:
        self.redash.remove_visualization(widget_id)

      if query_id is not None:
        self.redash.delete_query(query_id)
    except self.redash.RedashClientException as e:
      raise self.ExternalAPIError(
        "Unable to remove widget {widget_id} with query ID "
        "{query_id} from dashboard: {error}".format(
            widget_id=widget_id, query_id=query_id, error=e))

  def remove_all_graphs(self):
    widgets = self.get_query_ids_and_names()

    for widget_name in widgets:
      widget = widgets[widget_name]
      widget_id = widget.get("widget_id", None)
      query_id = widget.get("query_id", None)

      self.remove_graph_from_dashboard(widget_id, query_id)

  def _populate_sql_string_with_variables(self, template_sql, query_params):
    adjusted_string = template_sql.replace("{{{", "{").replace("}}}", "}")
    sql_query = adjusted_string.format(**query_params)
    return sql_query

  def _add_copied_query_to_dashboard(
      self, template, query_title, query_params, visualization_width,
      visualization_name="Chart"
  ):
    query_string = self._populate_sql_string_with_variables(
        template["query"], query_params)

    query_id, table_id = self._create_new_query(
        query_title, query_string, template["data_source_id"])
    try:
      viz_id = self.redash.make_new_visualization_request(
          query_id,
          template["type"],
          template["options"],
          visualization_name,
      )
      self._add_visualization_to_dashboard(viz_id, visualization_width)

      public_url = self.redash.get_visualization_public_url(query_id, viz_id)

      return public_url
    except self.redash.RedashClientException as e:
      raise self.ExternalAPIError(
        "Unable to add copied query {query_id} to "
        "dashboard: {error}".format(query_id=query_id, error=e))

  def _template_copy_results_exist(
      self, query_title, template_sql, data_source_id, query_params
  ):
    sql_query = self._populate_sql_string_with_variables(template_sql, query_params)
    data = self._get_query_results(sql_query, data_source_id, query_title)

    if data is None or len(data) == 0:
      self._logger.info((
          "Dashboard: Query '{name}' is still updating and will "
          "not be displayed.".format(name=query_title)))
      return False

    return True

  def _add_query_to_dashboard(self, query_title, query_string,
                              data_source, visualization_width,
                              visualization_type=VizType.CHART,
                              visualization_name="", chart_type=None,
                              column_mapping=None, series_options=None,
                              time_interval=None, stacking=True):

    query_id, table_id = self._create_new_query(
        query_title, query_string, data_source)
    viz_id = self._create_new_visualization(
        query_id,
        visualization_type,
        visualization_name,
        chart_type,
        column_mapping,
        series_options,
        time_interval,
        stacking,
    )
    self._add_visualization_to_dashboard(viz_id, visualization_width)
