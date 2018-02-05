lint:
	flake8 stmoab/utils.py
	flake8 stmoab/dashboards/SummaryDashboard.py
	flake8 stmoab/dashboards/StatistcalDashboard.py
	flake8 stmoab/dashboards/ActivityStreamExperimentDashboard.py
	flake8 stmoab/tests/base.py
	flake8 stmoab/tests/test_summary_dashboard.py
	flake8 stmoab/test/test_utils.py
	flake8 stmoab/tests/test_activity_stream_experiment_dashboard.py
	flake8 stmoab/tests/test_statistical_dashboard.py

test: lint
	nosetests --with-coverage --cover-package=stmoab