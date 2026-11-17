import pytest

from ai_intelligence_lab.fairtriage.benchmark.stats import paired_summary


def test_no_differences_give_a_zero_interval():
    summary = paired_summary([0.0] * 50)

    assert (summary.mean, summary.low, summary.high) == (0.0, 0.0, 0.0)
    assert summary.share_positive == summary.share_negative == 0.0


def test_a_constant_difference_has_no_spread():
    summary = paired_summary([2.0] * 40)

    assert (summary.low, summary.high) == (2.0, 2.0)


def test_the_same_seed_gives_the_same_interval():
    data = [float(i % 7 - 3) for i in range(60)]

    assert paired_summary(data, seed=3) == paired_summary(data, seed=3)


def test_the_interval_contains_the_mean_and_the_signs_are_counted():
    data = [1.0] * 20 + [-1.0] * 10 + [0.0] * 30

    summary = paired_summary(data)

    assert summary.n == 60
    assert summary.low <= summary.mean <= summary.high
    assert summary.mean == pytest.approx(1 / 6)
    assert summary.share_positive == pytest.approx(1 / 3)
    assert summary.share_negative == pytest.approx(1 / 6)


def test_a_clear_effect_excludes_zero():
    summary = paired_summary([1.0] * 55 + [0.0] * 5)

    assert summary.low > 0


def test_too_few_pairs_are_refused():
    with pytest.raises(ValueError, match="at least"):
        paired_summary([1.0] * 5)


@pytest.mark.parametrize(
    "settings", [{"confidence": 1.0}, {"confidence": 0.0}, {"resamples": 10}]
)
def test_bad_settings_are_refused(settings):
    with pytest.raises(ValueError):
        paired_summary([1.0] * 40, **settings)


def test_a_non_finite_difference_is_refused():
    with pytest.raises(ValueError, match="finite"):
        paired_summary([1.0] * 39 + [float("nan")])
