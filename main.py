import asyncio
import os
import datetime
import time

from dotenv import load_dotenv
from database import Record, User
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from task import ReActAgentTask
from typing import List
from util import logger

# env init
load_dotenv()


if __name__ == "__main__":

    # init db
    engine = create_engine(os.environ["DATABASE_URL"])
    User.metadata.create_all(engine)

    # debug
    username = "admin"
    with Session(engine) as session:
        user = session.query(User).filter(User.username == username).first()
        if user is None:
            user = User(
                username=username,
                password="admin",
                last_login=datetime.datetime.now(),
            )
            session.add(user)
            session.commit()
        else:
            user.last_login = datetime.datetime.now()
            session.commit()

    logger.info(user)
    # second
    shot_freq = 5
    summary_freq = 30
    force_width, force_height = (1280, 720)

    task = ReActAgentTask(username, shot_freq, summary_freq, force_size=(force_width, force_height))
    task.start()
    time.sleep(5)
    task.join()

