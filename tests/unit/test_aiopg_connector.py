import psycopg2
import pytest

from procrastinate import aiopg_connector, exceptions


@pytest.mark.asyncio
async def test_adapt_pool_args_on_connect(mocker):
    called = []

    async def on_connect(connection):
        called.append(connection)

    args = aiopg_connector.AiopgConnector._adapt_pool_args(
        pool_args={"on_connect": on_connect}, json_loads=None
    )

    assert args["on_connect"] is not on_connect

    connection = mocker.Mock(_pool=None)
    await args["on_connect"](connection)

    assert called == [connection]


@pytest.mark.asyncio
async def test_wrap_exceptions_wraps():
    @aiopg_connector.wrap_exceptions
    async def corofunc():
        raise psycopg2.DatabaseError

    coro = corofunc()

    with pytest.raises(exceptions.ConnectorException):
        await coro


@pytest.mark.asyncio
async def test_wrap_exceptions_success():
    @aiopg_connector.wrap_exceptions
    async def corofunc(a, b):
        return a, b

    assert await corofunc(1, 2) == (1, 2)


@pytest.mark.asyncio
async def test_wrap_query_exceptions_reached_max_tries(mocker):
    called = []

    @aiopg_connector.wrap_query_exceptions
    async def corofunc(connector):
        called.append(True)
        raise psycopg2.errors.OperationalError(
            "server closed the connection unexpectedly"
        )

    connector = mocker.Mock(_pool=mocker.Mock(maxsize=5))
    coro = corofunc(connector)

    with pytest.raises(exceptions.ConnectorException) as excinfo:
        await coro

    assert len(called) == 6
    assert str(excinfo.value) == "Could not get a valid connection after 6 tries"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exception_class", [Exception, psycopg2.errors.OperationalError]
)
async def test_wrap_query_exceptions_unhandled_exception(mocker, exception_class):
    called = []

    @aiopg_connector.wrap_query_exceptions
    async def corofunc(connector):
        called.append(True)
        raise exception_class("foo")

    connector = mocker.Mock(_pool=mocker.Mock(maxsize=5))
    coro = corofunc(connector)

    with pytest.raises(exception_class):
        await coro

    assert len(called) == 1


@pytest.mark.asyncio
async def test_wrap_query_exceptions_success(mocker):
    called = []

    @aiopg_connector.wrap_query_exceptions
    async def corofunc(connector, a, b):
        if len(called) < 2:
            called.append(True)
            raise psycopg2.errors.OperationalError(
                "server closed the connection unexpectedly"
            )
        return a, b

    connector = mocker.Mock(_pool=mocker.Mock(maxsize=5))

    assert await corofunc(connector, 1, 2) == (1, 2)
    assert len(called) == 2


@pytest.mark.parametrize(
    "method_name",
    [
        "close_async",
        "_create_pool",
        "execute_query_async",
        "_execute_query_connection",
        "execute_query_one_async",
        "execute_query_all_async",
        "listen_notify",
        "_loop_notify",
    ],
)
def test_wrap_exceptions_applied(method_name):
    connector = aiopg_connector.AiopgConnector()
    assert getattr(connector, method_name)._exceptions_wrapped is True


def test_set_pool(mocker):
    pool = mocker.Mock()
    connector = aiopg_connector.AiopgConnector()

    connector.set_pool(pool)

    assert connector._pool is pool


def test_set_pool_already_set(mocker):
    pool = mocker.Mock()
    connector = aiopg_connector.AiopgConnector()
    connector.set_pool(pool)

    with pytest.raises(exceptions.PoolAlreadySet):
        connector.set_pool(pool)


@pytest.mark.asyncio
async def test_listen_notify_pool_one_connection(mocker, caplog):
    pool = mocker.Mock(maxsize=1)
    connector = aiopg_connector.AiopgConnector()
    connector.set_pool(pool)
    caplog.clear()

    await connector.listen_notify(None, None)

    assert {e.action for e in caplog.records} == {"listen_notify_disabled"}
