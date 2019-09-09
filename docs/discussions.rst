.. _discussions:

Discussions
===========

How does this all work ?
------------------------

Procrastinate is based on several things:

- PostgreSQL's top notch ability to manage locks, thanks to its ACID_ properties.
  This ensures that when a worker starts executing a job, it's the only one.
  Procrastinate does this by executing a ``SELECT FOR UPDATE`` that will lock the
  jobs table. This might not scale to billions of simultaneous tables, but we don't
  expect to reach that level.
- PostgreSQL's LISTEN_ allows us to be notified whenever a task is available.

.. _ACID: https://en.wikipedia.org/wiki/ACID
.. _LISTEN: https://www.postgresql.org/docs/current/sql-listen.html

Why are you doing a task queue in PostgreSQL ?
----------------------------------------------

Because while maintaining a large Postgres_ database in good shape in
our infrastructure is no small feat, also maintaining a RabbitMQ_/Redis_/...
service is double the trouble. It introduces plenty of problems around backups,
high availability, monitoring, etc. If you already have a stable robust
database, and this database gives you all the tooling you need to build
a message queue on top of it, then it's always an option you have.

Another nice thing is the ability to easily browse (and possibly edit) jobs in
the queue, because interacting with data in a standard database a lot easier
than implementing a new specific protocol (say, AMQP).

This makes the building of tools around Procrastinate quite easier.

Finally, the idea that the core operations around tasks are handled by the
database itself using stored procedures eases the possibility of porting
Procrastinate to another language, while staying compatible with Python-based jobs.

.. _Postgres: https://www.postgresql.org/
.. _RabbitMQ: https://www.rabbitmq.com/
.. _Redis: https://redis.io/

There are 14 standards...
-------------------------

.. figure:: https://imgs.xkcd.com/comics/standards.png
    :alt: https://xkcd.com/927/

    https://xkcd.com/927/

We are aware that Procrastinate is an addition to an already crowded market of
Python task queues, and the aim is not to replace them all, but to provide
an alternative that fits our need, as we could not find one we were
completely satisfied with.

Nevertheless, we acknowledge the impressive Open Source work accomplished by
some projects that really stand out, to name a few:

- Celery_: Is really big and supports a whole variety of cases, but not using
  PostgreSQL as a message queue. We could have tried to add this, but it
  really feels like Celery is doing a lot already, and every addition to it is
  a lot of compromises, and would probably have been a lot harder.
- Dramatiq_ + dramatiq-pg_: Dramatiq is another very nice Python task queue
  that does things quite well, and it happens that there is a third party
  addition for using PostgreSQL as a backend. In fact, it was built around the
  same time as we started Procrastinate, and the paradigm it uses makes it hard to
  integrate a few of the feature we really wanted to use Procrastinate for, namely
  locks.


.. _Celery: https://docs.celeryproject.org
.. _Dramatiq: https://dramatiq.io/
.. _dramatiq-pg: https://pypi.org/project/dramatiq-pg/


How stable is Procrastinate ?
-----------------------------

Not quite stable. There a lot of things we would like to do before we start
advertising the project, and so far, it's not used anywhere.

We'd love if you were to try out Procrastinate in a non-production non-critical
project of yours and provide us with feedback.


Wasn't this project named "Cabbage" ?
-------------------------------------

Yes, in early development, we planned to call this "cabbage" in reference to
celery, but even if the name was available on PyPI, by the time we stopped
procrastinating and wanted to register it, it had been taken. Given this project
is all about "launching tasks in an undetermined moment in the future", the new
name felt quite adapted too. Also, now you know why the project is named this way.

Thanks PeopleDoc
----------------

This project was almost entirely created by PeopleDoc employees on their
working time. Let's take this opportunity to thank PeopleDoc for funding
an Open Source projects like this!

If this makes you want to know more about this company, check our website_
or our `job offerings`_ !

.. _website: https://www.people-doc.com/
.. _`job offerings`: https://www.people-doc.com/company/careers
