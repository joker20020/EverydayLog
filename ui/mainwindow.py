# -*- UTF-8 -*-
# @author   : 40599
# @time     : 2026/1/4 17:16
# @version  : V1
import datetime
import os

from PySide6.QtWidgets import (
    QFrame,
    QApplication,
    QHBoxLayout,
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
from qfluentwidgets import NavigationItemPosition, FluentWindow, SubtitleLabel, setFont, CommandBar, Action, RoundMenu,  MenuAnimationType
from qfluentwidgets import FluentIcon
from qfluentwidgets import Theme, setTheme
from widgets import RecordWidgetList

from database import Record, User
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()


class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignmentFlag.AlignCenter)

        # 必须给子界面设置全局唯一的对象名
        self.setObjectName(text.replace(' ', '-'))


class Window(FluentWindow):
    """ 主界面 """

    def __init__(self):
        super().__init__()

        # database
        self.username = "admin"
        self.engine = create_engine(os.environ["DATABASE_URL"])
        User.metadata.create_all(self.engine)
        with Session(self.engine) as session:
            user = session.query(User).filter(User.username == self.username).first()
            if user is None:
                user = User(
                    username=self.username,
                    password="admin",
                    last_login=datetime.datetime.now(),
                )
                session.add(user)
                session.commit()
            else:
                user.last_login = datetime.datetime.now()
                session.commit()

        # create record interface
        self.recordsInterface = RecordWidgetList()
        self.recordsInterface.delete_widget.connect(self.delete_record_from_db)
        self.refresh_record()
        # for i in range(5):
        #     self.recordsInterface.addRecord(datetime.datetime.now(), datetime.datetime.now(), "# test2\n ## t", [])

        self.settingInterface = Widget(self.tr('Setting Interface'), self)

        self.initNavigation()
        self.initWindow()

    def refresh_record(self):
        with Session(self.engine) as session:
            user = session.query(User).filter(User.username == self.username).first()
            for record in session.query(Record).filter(Record.user_id == user.user_id).all():
                self.recordsInterface.add_record(record.start_time, record.end_time, record.content,
                                                 record.image_list.split(";"))

    def initNavigation(self):
        self.addSubInterface(self.recordsInterface, FluentIcon.HOME, self.tr('记录'))


        self.addSubInterface(self.settingInterface, FluentIcon.HOME, self.tr('任务'))

        self.navigationInterface.addSeparator()

        self.addSubInterface(self.settingInterface, FluentIcon.SETTING, self.tr('基本设置'), NavigationItemPosition.BOTTOM)

    def initWindow(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle(self.tr("EverydayLog"))

    def delete_record_from_db(self, start_datetime: datetime.datetime, end_datetime: datetime.datetime):
        with Session(self.engine) as session:
            record = session.query(Record).filter(Record.start_time == start_datetime, Record.end_time == end_datetime).first()
            for image in record.image_list.split(";"):
                if os.path.exists(image):
                    os.remove(image)
            session.delete(record)
            session.commit()



if __name__ == '__main__':
    app = QApplication()
    setTheme(Theme.AUTO)
    w = Window()
    w.show()
    app.exec()
