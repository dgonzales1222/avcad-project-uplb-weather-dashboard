### Test result for clean and ingest (17 June 2026)
```python
================================================ test session starts =================================================
platform darwin -- Python 3.13.9, pytest-9.1.0, pluggy-1.6.0 -- /Users/dgonzales22/Documents/AVCAD Project/uplb-nas-dashboard/venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/dgonzales22/Documents/AVCAD Project/avcad-project-uplb-weather-dashboard
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.14.0
collected 13 items                                                                                                   

tests/test_clean.py::test_daily_from_hourly_means PASSED                                                       [  7%]
tests/test_clean.py::test_build_daily_columns_and_merge PASSED                                                 [ 15%]
tests/test_clean.py::test_validate_passes_clean_frame PASSED                                                   [ 23%]
tests/test_clean.py::test_validate_allows_nan_values PASSED                                                    [ 30%]
tests/test_clean.py::test_validate_rejects_rh_out_of_range PASSED                                              [ 38%]
tests/test_clean.py::test_validate_rejects_negative_precip PASSED                                              [ 46%]
tests/test_clean.py::test_validate_rejects_max_below_min PASSED                                                [ 53%]
tests/test_clean.py::test_validate_rejects_duplicate_dates PASSED                                              [ 61%]
tests/test_clean.py::test_validate_rejects_missing_calendar_date PASSED                                        [ 69%]
tests/test_ingest.py::test_to_long_shape_and_mapping PASSED                                                    [ 76%]
tests/test_ingest.py::test_to_long_maps_nan_to_none PASSED                                                     [ 84%]
tests/test_ingest.py::test_build_db_end_to_end PASSED                                                          [ 92%]
tests/test_ingest.py::test_build_db_is_idempotent PASSED                                                       [100%]
```