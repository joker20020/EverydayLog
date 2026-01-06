# -*- UTF-8 -*-
# @author   : 40599
# @time     : 2026/1/5 20:39
# @version  : V1
import datetime
import os
import time

import cv2
import numpy as np
import base64
import pyautogui
import asyncio
import rtoml

from PySide6.QtCore import QThread, Signal
from agentscope.agent import ReActAgent
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg, ImageBlock, TextBlock, Base64Source
from agentscope.tool import Toolkit
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIChatFormatter
from typing import List, Tuple
from database import Record, User
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from util import logger
from abc import abstractmethod


class TaskBase(QThread):
    """任务基类"""
    task_start = Signal()
    task_end = Signal()

    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.is_running = False
        self.is_paused = False
        self.is_stopped = False
        self.is_finished = False

    def run(self):
        self.task_start.emit()
        self.before_run()
        self.is_running = True
        while self.is_running:
            if self.is_paused:
                self.msleep(100)
                continue
            if self.is_stopped:
                self.is_running = False
                self.end_time = datetime.datetime.now()
                self.task_end.emit()
                return
            # main loop
            self.main_fun()
        self.is_running = False
        self.is_finished = True
        self.end_time = datetime.datetime.now()
        self.after_run()
        self.task_end.emit()

    @abstractmethod
    def main_fun(self):
        pass

    @abstractmethod
    def before_run(self):
        pass

    @abstractmethod
    def after_run(self):
        pass

    # pause after a loop
    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    # pause after a loop
    def stop(self):
        self.is_stopped = True

    def join(self):
        while self.is_running:
            pass


class ReActAgentTask(TaskBase):
    """ReActAgentChatTask"""
    take_shot = Signal()
    summary = Signal()

    def __init__(self, username: str, shot_freq: float = 10, summary_freq: float = 60,
                 force_size: Tuple[int, int] = (1280, 720)
                 ):
        super().__init__(username)

        self.engine = None
        self.setTerminationEnabled(True)

        # as second
        self.shot_freq = shot_freq
        self.summary_freq = summary_freq
        self.force_width, self.force_height = force_size

        # pre define
        self.shot_start_time = datetime.datetime.now()
        self.summary_start_time = self.shot_start_time
        self.shot_end_time = self.shot_start_time
        self.summary_end_time = self.shot_start_time
        # init image content
        self.img_blocks = []
        self.img_paths = []
        self.img_datas = []

        with open(os.environ["EVERYDAY_LOG_CONFIG_PATH"]) as f:
            config = rtoml.load(f)
        self.img_save_dir = config["IMAGE_TEMP_PATH"]

        self.reset_cache()
        if not os.path.exists(self.img_save_dir):
            logger.info("temp screenshot dir not find, creating...")
            if "IMAGE_TEMP_PATH" in os.environ.keys():
                os.mkdir(self.img_save_dir)
            else:
                os.mkdir("temp/temp_screenshot")

    def reset_cache(self):
        # init timer
        self.shot_start_time = datetime.datetime.now()
        self.summary_start_time = self.shot_start_time
        self.shot_end_time = self.shot_start_time
        self.summary_end_time = self.shot_start_time
        # init image content
        self.img_blocks = []
        self.img_paths = []
        self.img_datas = []

    async def creating_react_agent(self, content: List[TextBlock | ImageBlock]) -> List[Msg]:
        """create ReAct agent"""
        # 准备工具
        toolkit = Toolkit()

        agent = ReActAgent(
            name="Jarvis",
            sys_prompt="你是一个优秀的助手，你的任务是根据用户的屏幕截图，分析用户在一段时间内所进行的工作，并以第二人称进行回答",
            model=OpenAIChatModel(
                model_name=os.environ["MODEL_NAME"],
                api_key=os.environ["OPENAI_API_KEY"],
                stream=True,
                # enable_thinking=False,
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

    def before_run(self):
        with open(os.environ["EVERYDAY_LOG_CONFIG_PATH"]) as f:
            config = rtoml.load(f)
        # init db
        self.engine = create_engine(config["DATABASE_URL"])
        User.metadata.create_all(self.engine)

    def main_fun(self):
        if ((self.shot_end_time - self.shot_start_time).seconds > self.shot_freq and
                len(self.img_blocks) < self.summary_freq // self.shot_freq
        ):
            logger.info(f"Taking screenshot...\n{self.shot_end_time.isoformat()}")
            self.take_shot.emit()
            screen_img = np.asarray(pyautogui.screenshot())
            screen_img = cv2.resize(screen_img, (self.force_width, self.force_height))
            save_path = os.path.abspath(f"{self.img_save_dir}/screenshot_{self.shot_end_time.timestamp()}.png")

            self.img_datas.append(screen_img)
            _, encode_img = cv2.imencode(".png", screen_img)
            self.img_blocks.append(
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
            self.img_paths.append(save_path)

            self.shot_start_time = datetime.datetime.now()
            self.shot_end_time = datetime.datetime.now()
        if (self.summary_end_time - self.summary_start_time).seconds > self.summary_freq:
            logger.info(f"Summarizing...\n{self.summary_end_time.isoformat()}")
            self.summary.emit()
            content = [
                TextBlock(
                    type="text",
                    text=f"以下是我从{self.summary_start_time.isoformat()}到{self.summary_end_time.isoformat()}截屏的图片，截图间隔为{self.shot_freq}s,"
                         f"请根据图片内容，给出一个总结。"
                    ),
            ] + self.img_blocks
            summary_Msgs = asyncio.run(self.creating_react_agent(content))

            # add to database
            with Session(self.engine) as session:
                user = session.query(User).filter(User.username == self.username).first()
                record = Record(
                    start_time=self.summary_start_time,
                    end_time=self.summary_end_time,
                    content=summary_Msgs[-1].get_text_content(),
                    image_list=";".join(self.img_paths),
                    user_id=user.user_id,
                )
                session.add(record)
                session.commit()
            # save img
            for img, save_path in zip(self.img_datas, self.img_paths):
                cv2.imwrite(save_path, img)

            self.summary_start_time = datetime.datetime.now()
            self.summary_end_time = datetime.datetime.now()
            self.img_blocks.clear()
            self.img_paths.clear()
            self.img_datas.clear()

        self.shot_end_time = datetime.datetime.now()
        self.summary_end_time = datetime.datetime.now()
        time.sleep(1)

    def resume(self):
        super().resume()
        self.reset_cache()

if __name__ == "__main__":
    # second
    shot_freq = 5
    summary_freq = 30
    force_width, force_height = (1280, 720)

    task = ReActAgentTask("admin", shot_freq, summary_freq, force_size=(force_width, force_height))
    task.start()
    time.sleep(5)
    task.join()
