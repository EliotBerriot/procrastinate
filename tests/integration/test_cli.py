from collections import defaultdict

import pytest

from procrastinate import __version__, cli


@pytest.fixture
def entrypoint(cli_runner):
    def ep(args=""):
        return cli_runner.invoke(cli.cli, args.split(), catch_exceptions=False)

    return ep


@pytest.fixture
def click_app(mocker, app):
    mocker.patch("procrastinate.App.from_path", return_value=app)
    yield app


def test_cli(entrypoint):
    result = entrypoint()
    assert result.output.startswith("Usage:")


def test_version(entrypoint):
    result = entrypoint("--version")

    assert "procrastinate " + __version__ in result.output
    assert "License: MIT License" in result.output


def test_worker(entrypoint, click_app, mocker):
    click_app.run_worker = mocker.MagicMock()
    result = entrypoint("-a yay worker a b")

    assert result.output.strip() == "Launching a worker on a, b"
    assert result.exit_code == 0
    click_app.run_worker.assert_called_once_with(queues=["a", "b"])


def test_migrate(entrypoint, click_app, mocker, job_store):
    job_store.reverse_queries = defaultdict(lambda: "migrate")

    migrate = mocker.patch("procrastinate.migration.Migrator.migrate")
    result = entrypoint("-a yay migrate")

    assert result.output.strip() == "Launching migrations\nDone"
    assert result.exit_code == 0
    migrate.assert_called_once_with()


def test_migrate_text(entrypoint):
    result = entrypoint("migrate --text")

    assert result.output.startswith("CREATE")
    assert result.exit_code == 0


def test_no_app(entrypoint, mocker):
    click_app.run_worker = mocker.MagicMock()
    with pytest.raises(NotImplementedError):
        entrypoint("migrate")


def test_defer(entrypoint, click_app):
    @click_app.task(name="hello")
    def mytask(a):
        pass

    # No space in the json helps entrypoint() to simply split args
    result = entrypoint("""-a yay defer --lock=sherlock hello {"a":1}""")

    assert result.output == "Launching a job: hello(a=1)\n"
    assert result.exit_code == 0
    assert click_app.job_store.jobs == {
        1: {
            "args": {"a": 1},
            "attempts": 0,
            "id": 1,
            "lock": "sherlock",
            "queue_name": "default",
            "scheduled_at": None,
            "started_at": None,
            "status": "todo",
            "task_name": "hello",
        }
    }


def test_defer_unknown(entrypoint, click_app):
    # No space in the json helps entrypoint() to simply split args
    result = entrypoint("""-a yay defer --unknown --lock=sherlock hello {"a":1}""")

    assert result.output == "Launching a job: hello(a=1)\n"
    assert result.exit_code == 0
    assert click_app.job_store.jobs == {
        1: {
            "args": {"a": 1},
            "attempts": 0,
            "id": 1,
            "lock": "sherlock",
            "queue_name": "default",
            "scheduled_at": None,
            "started_at": None,
            "status": "todo",
            "task_name": "hello",
        }
    }


@pytest.mark.parametrize(
    "input",
    [
        # Unparsable at
        "defer --at=yay mytask",
        # Define both in and at
        "defer --in=3 --at=2000-01-01T00:00:00Z mytask",
        # Invalid Json
        "defer hello {",
        # Unknown task
        "defer hello",
    ],
)
def test_defer_error(entrypoint, input):
    result = entrypoint(input)
    assert result.exit_code != 0
