"""Example app showing how to use the Queue class."""
import asyncio
import random

from asyncpg import DuplicateTableError
from loguru import logger
from piccolo.table import create_tables
from pydantic import BaseModel

from qbert import Queue, tables


class Echo(BaseModel):
    """Print a message out."""

    message: str


class Add(BaseModel):
    """Add two numbers and push the result."""

    a: int
    b: int


class SometimesFail(BaseModel):
    """Generic job that sometimes fails to execute."""


async def run_job(msg: BaseModel, queue: Queue) -> None:
    """Execute the required work for the given job."""
    match msg:
        case Echo():
            print(msg.message)
        case Add():
            await queue.push(
                Echo(message=f"Add result: {msg.a} + {msg.b} = {msg.a + msg.b}")
            )
        case SometimesFail():
            if random.choice([True, False]):
                raise RuntimeError("The job that sometimes failed has failed!")


async def run_worker(queue: Queue) -> None:
    """Consume the queue and run the jobs. Will return when no jobs remain."""
    while batch := await queue.pull():
        for job in batch:
            logger.debug(f"Got job: {job}")

            try:
                await run_job(job.message, queue)
            except Exception as ex:  # pylint: disable=broad-except
                logger.exception(ex)
                await queue.fail_job(job.id)
            else:
                await queue.delete_job(job.id)


async def main() -> None:
    """Run the example app."""

    # this would normally be done by running the migrations.
    try:
        create_tables(tables.Job)
    except DuplicateTableError:
        print("Database already setup, skipping table creation.")

    # push some jobs to the queue.
    queue = Queue([Echo, Add, SometimesFail])

    # await queue.push(SometimesFail())
    await queue.push(Echo(message="Hello, world!"))
    await queue.push(Add(a=1, b=2))

    while True:
        await run_worker(queue)

        # sleep when there's no jobs left to give the database a rest :)
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
