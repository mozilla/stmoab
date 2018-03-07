import math
import statistics
from scipy import stats
import statsmodels.stats.power as smp

from redash_client.constants import VizWidth

from stmoab.utils import upload_as_json, create_boto_transfer
from stmoab.constants import TTableSchema
from stmoab.ExperimentDashboard import (
    ExperimentDashboard)


class StatisticalDashboard(ExperimentDashboard):
  TTABLE_DESCRIPTION = (
    "Smaller p-values (e.g. <= 0.05) indicate a high "
    "probability that the variants have different distributions. Alpha "
    "error indicates the probability a difference is observed when one "
    "does not exists. Larger power (e.g. >= 0.7) indicates a high "
    "probability that an observed difference is correct. Beta error "
    "(1 - power) indicates the probability that no difference is observed "
    "when indeed one exists.")
  ALPHA_ERROR = 0.005
  TTABLE_TEMPLATE = {"columns": TTableSchema, "rows": []}


  def __init__(
      self, api_key, aws_access_key, aws_secret_key, s3_region,
      s3_bucket_id, project_name, dash_name, exp_id,
      start_date=None, end_date=None
  ):
    super(StatisticalDashboard, self).__init__(
        api_key,
        project_name,
        dash_name,
        exp_id,
        start_date,
        end_date)

    self._ttables = {}
    self._s3_bucket = s3_bucket_id
    self._transfer = create_boto_transfer(
      aws_access_key, aws_secret_key, s3_region)

  def _copy_ttable_tempalte(self):
    template_copy = self.TTABLE_TEMPLATE.copy()
    template_copy["rows"] = []
    return template_copy

  def _compute_pooled_stddev(self, control_std, exp_std,
                             control_vals, exp_vals):

    control_len_sub_1 = len(control_vals) - 1
    exp_len_sub_1 = len(exp_vals) - 1

    pooled_stddev_num = (pow(control_std, 2) * control_len_sub_1 +
                         pow(exp_std, 2) * exp_len_sub_1)
    pooled_stddev_denom = control_len_sub_1 + exp_len_sub_1

    pooled_stddev = math.sqrt(pooled_stddev_num / float(pooled_stddev_denom))
    return pooled_stddev

  def _power_and_ttest(self, control_vals, exp_vals):
    control_mean = statistics.mean(control_vals)
    control_std = statistics.stdev(control_vals)
    exp_mean = statistics.mean(exp_vals)
    exp_std = statistics.stdev(exp_vals)

    pooled_stddev = self._compute_pooled_stddev(
        control_std, exp_std, control_vals, exp_vals)

    power = 0
    percent_diff = None
    if control_mean != 0 and pooled_stddev != 0:
      percent_diff = (control_mean - exp_mean) / float(control_mean)
      effect_size = (abs(percent_diff) * float(control_mean)) / float(pooled_stddev)
      power = smp.TTestIndPower().solve_power(
          effect_size,
          nobs1=len(control_vals),
          ratio=len(exp_vals) / float(len(control_vals)),
          alpha=self.ALPHA_ERROR, alternative='two-sided')

    ttest_result = stats.ttest_ind(control_vals, exp_vals, equal_var=False)
    p_val = ""
    if len(ttest_result) >= 2 and not math.isnan(ttest_result[1]):
      p_val = ttest_result[1]

    mean_diff = exp_mean - control_mean

    if p_val <= self.ALPHA_ERROR and mean_diff < 0:
      significance = "Negative"
    elif p_val <= self.ALPHA_ERROR and mean_diff > 0:
      significance = "Positive"
    else:
      significance = "Neutral"

    return {
        "power": power,
        "p_val": p_val,
        "control_mean": control_mean,
        "mean_diff": mean_diff,
        "percent_diff": 0 if percent_diff is None else percent_diff * -100,
        "significance": significance,
    }

  def _get_ttable_data_for_query(self, label, query_string,
                                 column_name, data_source_id):
    data = self._get_query_results(query_string, data_source_id, label)

    if data is None or len(data) <= 3 or (column_name not in data[0]):
      return []

    control_vals = []
    exp_vals = {}
    for row in data:
      if "type" in row and row["type"].lower().find("control") != -1:
        control_vals.append(row[column_name])
      elif "type" in row:
        if row["type"] not in exp_vals:
          exp_vals[row["type"]] = []

        exp_vals[row["type"]].append(row[column_name])
      else:
        return []

    ttable_results = []
    for variant in exp_vals:
      results = self._power_and_ttest(control_vals, exp_vals[variant])
      ttable_results.append({
          "Metric": "[control vs. {variant}] {metric}".format(variant=variant, metric=label),
          "Alpha Error": self.ALPHA_ERROR,
          "Power": results["power"],
          "Two-Tailed P-value (ttest)": results["p_val"],
          "Control Mean": results["control_mean"],
          "Experiment Mean - Control Mean": results["mean_diff"],
          "Percent Difference in Means": results["percent_diff"],
          "Significance": results["significance"]
      })
    return ttable_results

  def _apply_ttable_event_template(self, template, chart_data, events_list,
                                   events_table, title):

    if title not in self._ttables:
      self._ttables[title] = self._copy_ttable_tempalte()

    self._params["events_table"] = events_table
    for event in events_list:
      event_data = self._get_event_title_description(template, event)
      options = self._create_options()

      adjusted_string = template["query"].replace(
          "{{{", "{").replace("}}}", "}")
      query_string = adjusted_string.format(**self._params)

      self._update_query(
          template["id"],
          template["name"],
          template["query"],
          template["data_source_id"],
          event_data["description"],
          options
      )

      ttable_rows = self._get_ttable_data_for_query(
          event_data["title"],
          query_string,
          "count",
          template["data_source_id"])

      if len(ttable_rows) == 0:
        self._logger.info((
            "StatisticalDashboard: "
            "Query '{name}' has no relevant data and will not be "
            "included in T-Table.".format(name=event_data["title"])))
        continue

      self._ttables[title]["rows"] = self._ttables[title]["rows"] + ttable_rows

  def add_ttable_data(self, template_keyword, title,
                      events_list=None, events_table=None):
    self._logger.info((
        "StatisticalDashboard: Adding data for "
        "{keyword}").format(keyword=template_keyword))

    if events_list is None:
      events_list = self.DEFAULT_EVENTS
      events_table = self._events_table

    # Create the t-table
    self._apply_functions_to_templates(
        template_keyword,
        events_list,
        events_table,
        self._apply_ttable_event_template,
        None,
        title)

  def add_ttable(self, title):
    if title not in self._ttables or len(self._ttables[title]["rows"]) < 1:
      self._logger.info((
        "StatisticalDashboard: T-Table data for {title} is unavailable and "
        "will not be added to dashboard.").format(title=title))
      return

    chart_data = self.get_query_ids_and_names()
    num_rows_current_ttable = 0

    if title in chart_data:
      data = self._get_query_results(
          chart_data[title]["query"], self.URL_FETCHER_DATA_SOURCE_ID, title)
      num_rows_current_ttable = len(data)

    # Don't replace the existing T-Table unless we have at least an
    # equivalent number of rows.
    if len(self._ttables[title]["rows"]) < num_rows_current_ttable:
      self._logger.info((
        "StatisticalDashboard: T-Table data for {title} is incomplete and "
        "will not be added to dashboard.").format(title=title))
      return

    self._logger.info((
        "StatisticalDashboard: Creating a T-Table with "
        "title {title}").format(title=title))

    FILENAME = '{exp_id}_{title}'.format(exp_id=self._experiment_id, title=title)

    # Remove a table if it already exists
    if title in chart_data:
      self._logger.info((
          "StatisticalDashboard: "
          "Stale T-Table exists and will be removed"))
      query_id = chart_data[title]["query_id"]
      widget_id = chart_data[title]["widget_id"]
      self.remove_graph_from_dashboard(widget_id, query_id)

    query_string = upload_as_json(
        "experiments",
        FILENAME,
        self._transfer,
        self._s3_bucket,
        self._ttables[title],
    )
    query_id, table_id = self._create_new_query(
        title,
        query_string,
        self.URL_FETCHER_DATA_SOURCE_ID,
        self.TTABLE_DESCRIPTION,
    )
    self._add_visualization_to_dashboard(table_id, VizWidth.WIDE)
