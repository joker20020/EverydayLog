import asyncio
import os
import PIL.Image
import pyautogui
import datetime
import base64
import cv2
import numpy as np

from agentscope.agent import ReActAgent, AgentBase
from agentscope.formatter import DashScopeChatFormatter, OpenAIChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import (
    Msg,
    Base64Source,
    TextBlock,
    ThinkingBlock,
    ImageBlock,
    AudioBlock,
    VideoBlock,)
from agentscope.model import DashScopeChatModel, OpenAIChatModel
from agentscope.tool import Toolkit, execute_python_code
from dotenv import load_dotenv


load_dotenv()


async def creating_react_agent(content) -> None:
    """创建一个 ReAct 智能体并运行一个简单任务。"""
    # 准备工具
    toolkit = Toolkit()
    # toolkit.register_tool_function(execute_python_code)

    jarvis = ReActAgent(
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

    await jarvis(msg)


if __name__ == "__main__":
    # second
    shot_freq = 10
    summary_freq = 60
    force_width, force_height = (1280, 720)

    # init timer
    shot_start_time = datetime.datetime.now()
    summary_start_time = shot_start_time
    shot_end_time = shot_start_time
    summary_end_time = shot_start_time

    # init image content
    img_content = []

    while True:
        if (shot_end_time - shot_start_time).seconds > shot_freq and len(img_content) < summary_freq // shot_freq:
            print(f"截图中...\n{shot_end_time.isoformat()}")
            screen_img = np.asarray(pyautogui.screenshot())
            screen_img = cv2.resize(screen_img, (force_width, force_height))
            save_path = f"./temp_screenshot/screenshot_{shot_end_time.timestamp()}.png"
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

            shot_start_time = datetime.datetime.now()
            shot_end_time = datetime.datetime.now()
        if (summary_end_time - summary_start_time).seconds > summary_freq:
            print(f"分析中...\n{summary_end_time.isoformat()}")
            content = [
                TextBlock(
                    type="text",
                    text=f"以下是我从{summary_start_time.isoformat()}到{summary_end_time.isoformat()}截屏的图片，截图间隔为{shot_freq}s,"
                         f"请根据图片内容，给出一个总结。"
                    ),
            ] + img_content
            asyncio.run(creating_react_agent(content))

            summary_start_time = datetime.datetime.now()
            summary_end_time = datetime.datetime.now()
            img_content.clear()

        shot_end_time = datetime.datetime.now()
        summary_end_time = datetime.datetime.now()
