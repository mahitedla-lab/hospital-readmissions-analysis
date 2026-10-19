"""Runs the whole pipeline on SYNTHETIC CMS-shaped data and checks the logic, not real findings."""
import pytest

from readmissions import common, export, hypothesis_tests, load, synthetic


@pytest.fixture(scope="module")
def con(tmp_path_factory):
    d = tmp_path_factory.mktemp("data")
    hrrp, info = synthetic.make_synthetic(d, n_hospitals=1200)
    c = common.connect(d / "t.duckdb")
    load.load_all(c, hrrp, info)
    common.run_sql_files(c)
    return c


def q(con, sql):
    return con.execute(sql).fetchall()


def test_six_conditions_and_states(con):
    assert q(con, "select count(distinct condition) from analysis.hospital_condition")[0][0] == 6
    assert q(con, "select count(distinct state) from analysis.hospital_condition")[0][0] >= 50


def test_ids_zero_padded_and_join_recovers_stripped_ids(con):
    assert q(con, "select count(*) from staging.hrrp_clean where length(facility_id) <> 6")[0][0] == 0
    # synthetic info file strips leading zeros on some ids; padding must still match them
    unmatched = q(con, "select count(distinct facility_id) from analysis.hospital_condition where not matched_hospital_info")[0][0]
    total = q(con, "select count(distinct facility_id) from analysis.hospital_condition")[0][0]
    assert 0 < unmatched < 0.06 * total          # only the ~2% deliberately dropped from General Info


def test_suppressed_values_are_excluded_not_zero(con):
    assert q(con, "select count(*) from analysis.hospital_condition where excess_readmission_ratio is null")[0][0] == 0
    assert q(con, "select value from analysis.data_checks where check_name='hrrp_rows_without_ratio'")[0][0] > 0


def test_no_duplicate_grain(con):
    assert q(con, "select count(*) from (select facility_id, measure_code from analysis.hospital_condition group by 1,2 having count(*)>1)")[0][0] == 0


def test_size_tiers_roughly_terciles(con):
    for _, n in q(con, "select size_tier, count(*) from analysis.hospital_summary group by 1 order by 1"):
        assert n > 200


def test_data_checks_clean(con):
    checks = dict(q(con, "select check_name, value from analysis.data_checks"))
    assert checks["err_out_of_range"] == 0
    assert checks["conditions_covered"] == 6


def test_hypothesis_tests_detect_planted_effects(con):
    tests, ols = hypothesis_tests.run_all(con)
    kw = tests[tests.test.str.startswith("Kruskal")].set_index("test")
    assert (kw.p_value < 0.001).all()            # planted ownership and size effects
    coef = ols.set_index("term")["coef"]
    assert coef[[t for t in coef.index if "For-profit" in t][0]] > 0
    assert coef[[t for t in coef.index if "Small" in t][0]] > 0


def test_exports(con, tmp_path):
    paths = export.export_tables(con, tmp_path)
    assert len(paths) == len(export.TABLES) and all(p.stat().st_size > 0 for p in paths)
