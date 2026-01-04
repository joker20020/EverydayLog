import asyncio
import os
import pyautogui
import datetime
import base64
import cv2
import numpy as np
import logging

from agentscope.agent import ReActAgent
from agentscope.formatter import OpenAIChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import (
    Msg,
    Base64Source,
    TextBlock,
    ImageBlock,)
from agentscope.model import OpenAIChatModel
from agentscope.tool import Toolkit

from dotenv import load_dotenv
from database import Record, User
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from typing import List

# log init
load_dotenv()
logger = logging.getLogger("agent_logger")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


async def creating_react_agent(content) -> List[Msg]:
    """create ReAct agent"""
    # 准备工具
    toolkit = Toolkit()

    agent = ReActAgent(
        name="Jarvis",
        sys_prompt="你是一个优秀的助手，你的任务是根据用户的屏幕截图，分析用户在一段时间内所进行的工作",
        model=OpenAIChatModel(
            model_name="qwen3-vl-8b-instruct",
            api_key=os.environ["OPENAI_API_KEY"],
            stream=True,
            enable_thinking=False,
            client_kwargs={"base_url": os.environ["OPENAI_BASE_HTTP_API_URL"]}
        ),
        formatter=OpenAIChatFormatter(),
        toolkit=toolkit,
        memory=InMemoryMemory(),
    )

    msg = Msg(
        name="user",
        content=content,
        role="user",
    )

    await agent(msg)

    return await agent.memory.get_memory()


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

    # init timer
    shot_start_time = datetime.datetime.now()
    summary_start_time = shot_start_time
    shot_end_time = shot_start_time
    summary_end_time = shot_start_time

    # init image content
    img_content = []
    img_paths = []
    if not os.path.exists("./temp/temp_screenshot"):
        logger.info("temp/temp_screenshot dir not find, creating...")
        os.mkdir("./temp/temp_screenshot")

    while True:
        if (shot_end_time - shot_start_time).seconds > shot_freq and len(img_content) < summary_freq // shot_freq:
            logger.info(f"Taking screenshot...\n{shot_end_time.isoformat()}")
            screen_img = np.asarray(pyautogui.screenshot())
            screen_img = cv2.resize(screen_img, (force_width, force_height))
            save_path = f"./temp/temp_screenshot/screenshot_{shot_end_time.timestamp()}.png"
            cv2.imwrite(save_path, screen_img)
            _, encode_img = cv2.imencode(".png", screen_img)
            img_content.append(
                ImageBlock(
                    type="image",
                    source=Base64Source(
                        type="base64",
                        media_type="image/png",
                        data=base64.b64encode(
                            encode_img.tobytes()
                        ).decode("utf-8"),
                    ),
                )
            )
            img_paths.append(save_path)

            shot_start_time = datetime.datetime.now()
            shot_end_time = datetime.datetime.now()
        if (summary_end_time - summary_start_time).seconds > summary_freq:
            logger.info(f"Analyzing...\n{summary_end_time.isoformat()}")
            content = [
                TextBlock(
                    type="text",
                    text=f"以下是我从{summary_start_time.isoformat()}到{summary_end_time.isoformat()}截屏的图片，截图间隔为{shot_freq}s,"
                         f"请根据图片内容，给出一个总结。"
                    ),
            ] + img_content
            summary_Msgs = asyncio.run(creating_react_agent(content))

            # add to database
            with Session(engine) as session:
                user = session.query(User).filter(User.username == username).first()
                record = Record(
                    start_time=summary_start_time,
                    end_time=summary_end_time,
                    content=summary_Msgs[-1].get_text_content(),
                    image_list=";".join(img_paths),
                    user_id=user.user_id,
                )
                session.add(record)
                session.commit()

            summary_start_time = datetime.datetime.now()
            summary_end_time = datetime.datetime.now()
            img_content.clear()

        shot_end_time = datetime.datetime.now()
        summary_end_time = datetime.datetime.now()
