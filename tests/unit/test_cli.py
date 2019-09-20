import datetime
import logging

import click
import pytest

from procrastinate import cli, exceptions


@pytest.mark.parametrize(
    "verbosity, log_level", [(0, "INFO"), (1, "DEBUG"), (2, "DEBUG")]
)
def test_get_log_level(verbosity, log_level):
    assert cli.get_log_level(verbosity=verbosity) == getattr(logging, log_level)


def test_set_verbosity(mocker, caplog):
    config = mocker.patch("logging.basicConfig")

    caplog.set_level("DEBUG")

    cli.set_verbosity(1)

    config.assert_called_once_with(level=logging.DEBUG)
    records = [record for record in caplog.records if record.action == "set_log_level"]
    assert len(records) == 1
    assert records[0].value == "DEBUG"


@pytest.mark.parametrize(
    "raised, expected",
    [
        # Procrastinate exceptions are caught
        (exceptions.ProcrastinateException, click.ClickException),
        # Other exceptions are not
        (ValueError, ValueError),
    ],
)
def test_handle_errors(raised, expected):
    @cli.handle_errors()
    def raise_exc():
        raise exceptions.ProcrastinateException

    with pytest.raises(click.ClickException):
        raise_exc()


def test_handle_errors_no_error():
    @cli.handle_errors()
    def raise_exc():
        assert True

    raise_exc()


def test_main(mocker):

    environ = mocker.patch("os.environ", {"LANG": "fr-FR.UTF-8"})
    mocker.patch("procrastinate.cli.cli")
    cli.main()

    assert environ == {"LANG": "fr-FR.UTF-8", "LC_ALL": "C.UTF-8"}


@pytest.mark.parametrize(
    "input, output", [(None, {}), ("{}", {}), ("""{"a": "b"}""", {"a": "b"})]
)
def test_load_json_args(input, output):
    assert cli.load_json_args(input) == output


@pytest.mark.parametrize("input", ["", "{", "[1, 2, 3]", '"yay"'])
def test_load_json_args_error(input):
    with pytest.raises(click.BadArgumentUsage):
        assert cli.load_json_args(input)


@pytest.mark.parametrize(
    "input, output",
    [
        (None, None),
        (
            "2000-01-01T00:00:00Z",
            datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc),
        ),
    ],
)
def test_get_schedule_at(input, output):
    assert cli.get_schedule_at(input) == output


@pytest.mark.parametrize("input", ["yay", "2000-01-34T00:00:00Z"])
def test_get_schedule_at_error(input):
    with pytest.raises(click.BadOptionUsage):
        assert cli.get_schedule_at(input)


@pytest.mark.parametrize("input, output", [(None, None), (12, {"seconds": 12})])
def test_get_schedule_in(input, output):
    assert cli.get_schedule_in(input) == output


def test_configure_job_known(app):
    @app.task(name="foobar", queue="marsupilami")
    def mytask():
        pass

    job = cli.configure_job(app, "foobar", {}, unknown=False).job
    assert job.task_name == "foobar"
    assert job.queue == "marsupilami"


def test_configure_job_unknown(app):
    job = cli.configure_job(app, "foobar", {}, unknown=True).job
    assert job.task_name == "foobar"
    assert job.queue == "default"


def test_test_configure_job_error(app):
    with pytest.raises(click.BadArgumentUsage):
        assert cli.configure_job(app, "foobar", {}, unknown=False)


def test_filter_none():
    assert cli.filter_none({"a": "b", "c": None}) == {"a": "b"}
