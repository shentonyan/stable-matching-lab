import numpy as np
import pytest

from paper.run_analysis import mean_interval


def test_identical_paired_difference_has_zero_uncertainty():
    result=mean_interval(np.full(30,.25),1000,7,family=6)
    assert result==dict(mean=.25,low=.25,high=.25,n=30)


def test_adjusted_interval_contains_ordinary_interval_same_draws():
    values=np.array([-2.,-1.,0.,.4,.6,1.,2.,3.])
    ordinary=mean_interval(values,4000,3)
    adjusted=mean_interval(values,4000,3,family=6)
    assert adjusted["low"]<=ordinary["low"]<=ordinary["high"]<=adjusted["high"]
    assert adjusted["mean"]==pytest.approx(values.mean())


def test_resampling_batches_do_not_change_seeded_result():
    values=np.arange(17.)
    first=mean_interval(values,1500,11,6)
    second=mean_interval(values,1500,11,6)
    assert first==second
