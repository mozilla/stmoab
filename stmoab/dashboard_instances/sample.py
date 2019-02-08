import os

from stmoab.StatisticalDashboard import StatisticalDashboard


if __name__ == '__main__':
  api_key = os.environ["REDASH_API_KEY"]
  aws_access_key = os.environ['AWS_ACCESS_KEY']
  aws_secret_key = os.environ['AWS_SECRET_KEY']
  s3_region = os.environ['S3_REGION']
  s3_bucket_id_stats = os.environ['S3_BUCKET_ID_STATS']

  # T-Table Names
  HOURLY_TTABLE_EXISTING_USERS = "[Existing Users] Statistical Analysis (Per Active Hour) - UT"
  HOURLY_TTABLE_NEW_USERS = "[New Users] Statistical Analysis (Per Active Hour) - UT"

  # Template Keywords
  POPULATION_TEMPLATE = 'UT Experiment Template: Population Size'
  SCALARS_TTEST_PER_ACTIVE_HOUR_EXISTING_USERS = "TTests Template Per Hour Scalars: [Existing Users]"
  MAPS_TTEST_PER_ACTIVE_HOUR_EXISTING_USERS = "TTests Template Per Hour Maps: [Existing Users]"
  SCALARS_TTEST_PER_ACTIVE_HOUR_NEW_USERS = "TTests Template Per Hour Scalars: [New Users]"
  MAPS_TTEST_PER_ACTIVE_HOUR_NEW_USERS = "TTests Template Per Hour Mapped: [New Users]"

  dash = StatisticalDashboard(
    api_key,
    aws_access_key,
    aws_secret_key,
    s3_region,
    s3_bucket_id_stats,
    "Pocket Experiment",
    "Release Sponsored Stories",
    "pref-flip-activity-stream-59-release-pocket-sponsored-stories-bug-1435822",
    start_date="2018-02-12"
  )

  dash.add_graph_templates(POPULATION_TEMPLATE)

  ###################################################
  ## All of the following is based on events per day.
  ###################################################

  # Average Events per Day UT
  #dash.add_graph_templates("AS Template UT One:", dash.UT_EVENTS)
  #dash.add_graph_templates("AS Template UT Mapped Two:", dash.MAPPED_UT_EVENTS)

  #dash.add_ttable_data("TTests Template UT Four:", UT_TTABLE, dash.UT_EVENTS)
  #dash.add_ttable_data("TTests Template Mapped UT Six:", UT_TTABLE, dash.MAPPED_UT_EVENTS)

  #dash.add_ttable(UT_TTABLE)

  ###########################################################
  ## All of the following is based on events per active tick.
  ###########################################################

  # Existing Users
  dash.add_graph_templates("Experiment Template Rate Scalars: [Existing Users]", dash.UT_HOURLY_EVENTS)
  dash.add_graph_templates("Experiment Template Rate Maps: [Existing Users]", dash.MAPPED_UT_EVENTS)

  dash.add_ttable_data(SCALARS_TTEST_PER_ACTIVE_HOUR_EXISTING_USERS, HOURLY_TTABLE_EXISTING_USERS, dash.UT_HOURLY_EVENTS)
  dash.add_ttable_data(MAPS_TTEST_PER_ACTIVE_HOUR_EXISTING_USERS, HOURLY_TTABLE_EXISTING_USERS, dash.MAPPED_UT_EVENTS)
  dash.add_ttable(HOURLY_TTABLE_EXISTING_USERS)

  # New Users
  dash.add_graph_templates("Experiment Template Rate Scalars: [New Users]", dash.UT_HOURLY_EVENTS)
  dash.add_graph_templates("Experiment Template Rate Maps: [New Users]", dash.MAPPED_UT_EVENTS)

  dash.add_ttable_data(SCALARS_TTEST_PER_ACTIVE_HOUR_NEW_USERS, HOURLY_TTABLE_NEW_USERS, dash.UT_HOURLY_EVENTS)
  dash.add_ttable_data(MAPS_TTEST_PER_ACTIVE_HOUR_NEW_USERS, HOURLY_TTABLE_NEW_USERS, dash.MAPPED_UT_EVENTS)
  dash.add_ttable(HOURLY_TTABLE_NEW_USERS)
