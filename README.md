![q*bert sprite](https://github.com/backwardspy/qbert/blob/master/docs/qbert.png)

# qbert

a dead simple task queue backed by postgres

very informal testing suggests a max performance around 100 jobs per second per worker on my machine.

## usage

add `qbert.piccolo_app` to your `APP_REGISTRY` as per [the documentation](https://piccolo-orm.readthedocs.io/en/latest/piccolo/projects_and_apps/piccolo_apps.html).

see [example.py](example.py) for queue interaction examples.
