import argparse

from dotenv import load_dotenv
from ui import StartWindow
from qfluentwidgets import (
    setTheme,
    Theme
)
from PySide6.QtWidgets import QApplication

# env init
load_dotenv()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--command-line", action="store_true",
                        help="use qt ui")
    parser.add_argument("-s", "--shot-freq", type=int, default=5,
                        help="screen shot frequency in seconds")
    parser.add_argument("-m", "--summary-freq", type=int, default=30,
                        help="summary frequency in seconds")
    parser.add_argument("-f", "--force-size", type=int, nargs=2, default=(1280, 720),
                        help="force screen shot size")
    args = parser.parse_args()

    if args.command_line:
        from task import ReActAgentTask
        import time
        import signal

        def KI_handler(signum, frame):
            print("Killed by user")
            exit(0)
        signal.signal(signal.SIGINT, KI_handler)

        shot_freq = args.shot_freq
        summary_freq = args.summary_freq
        force_width, force_height = args.force_size

        task = ReActAgentTask("admin", shot_freq, summary_freq, force_size=(force_width, force_height))
        task.start()
        time.sleep(5)
        task.join()
    else:
        app = QApplication()
        setTheme(Theme.AUTO)
        w = StartWindow()
        w.show()
        app.exec()

