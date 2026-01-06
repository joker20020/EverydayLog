# -*- UTF-8 -*-
# @author   : 40599
# @time     : 2026/1/4 17:16
# @version  : V1
import datetime
import os
import rtoml
import task

from PySide6.QtWidgets import (
    QWidget,
    QApplication,
    QHBoxLayout,
    QFormLayout
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (
    NavigationItemPosition,
    FluentWindow,
    SubtitleLabel,
    LineEdit,
    PasswordLineEdit,
    PushButton,
    PrimaryPushButton,
    NavigationToolButton,
    MessageBox
)
from qfluentwidgets import FluentIcon
from qfluentwidgets import Theme, setTheme
from dotenv import load_dotenv
if __name__ == '__main__':
    from widgets import RecordWidgetList, TaskWidget, SettingWidget
    load_dotenv()
else:
    from .widgets import RecordWidgetList, TaskWidget, SettingWidget

from database import Record, User
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


class Window(FluentWindow):
    """ 主界面 """

    logout_clicked = Signal()

    def __init__(self, username: str):
        super().__init__()

        with open(os.environ["EVERYDAY_LOG_CONFIG_PATH"]) as f:
            self.config = rtoml.load(f)

        # database
        self.username = username
        self.engine = create_engine(self.config["DATABASE_URL"])
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
            self.password = user.password

        # create record interface
        self.records_interface = RecordWidgetList()
        self.records_interface.delete_widget.connect(self.delete_record_from_db)
        self.refresh_record()

        tasks = task.get_tasks()
        self.task_setting_interface = TaskWidget(self.username, tasks=tasks)

        self.base_setting_interface = SettingWidget(self.username, self.password)
        self.base_setting_interface.change_profile_clicked.connect(self.change_user_profile)

        self.initNavigation()
        self.initWindow()

        self.resize(1200, 800)

    def refresh_record(self):
        with Session(self.engine) as session:
            user = session.query(User).filter(User.username == self.username).first()
            for record in session.query(Record).filter(Record.user_id == user.user_id).all():
                self.records_interface.add_record(record.start_time, record.end_time, record.content,
                                                  record.image_list.split(";"))

    def initNavigation(self):
        self.addSubInterface(self.records_interface, FluentIcon.HOME, self.tr('记录'))

        self.addSubInterface(self.task_setting_interface, FluentIcon.ADD_TO, self.tr('任务'))

        self.navigationInterface.addSeparator()

        self.addSubInterface(self.base_setting_interface, FluentIcon.SETTING, self.tr('基本设置'), NavigationItemPosition.BOTTOM)

        self.navigationInterface.addWidget(
            routeKey="logout",
            widget=NavigationToolButton(FluentIcon.CLOSE),
            onClick=self.logout,
            position=NavigationItemPosition.BOTTOM,
            tooltip=self.tr("退出登录")
        )

    def initWindow(self):
        self.resize(900, 700)
        self.setWindowTitle(self.tr("EverydayLog"))

    def delete_record_from_db(self, start_datetime: datetime.datetime, end_datetime: datetime.datetime):
        with Session(self.engine) as session:
            record = session.query(Record).filter(Record.start_time == start_datetime, Record.end_time == end_datetime).first()
            for image in record.image_list.split(";"):
                if os.path.exists(image):
                    os.remove(image)
            session.delete(record)
            session.commit()

    def change_user_profile(self, username: str, password: str):
        with Session(self.engine) as session:
            user = session.query(User).filter(User.username == self.username).first()
            user.username = username
            user.password = password
            session.commit()

    def logout(self):
        self.logout_clicked.emit()


class StartWindow(QWidget):
    """登录界面"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        with open(os.environ["EVERYDAY_LOG_CONFIG_PATH"]) as f:
            self.config = rtoml.load(f)

        self.engin = create_engine(self.config["DATABASE_URL"])

        self.main_window = None

        self.form_layout = QFormLayout(self)

        self.username_label = SubtitleLabel(self.tr("用户名"), self)
        self.username_edit = LineEdit(self)
        self.password_label = SubtitleLabel(self.tr("密码"), self)
        self.password_edit = PasswordLineEdit(self)
        self.register_btn = PushButton(self.tr("注册"), self)
        self.login_btn = PrimaryPushButton(self.tr("登录"), self)

        self.form_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.username_label)
        self.form_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.username_edit)
        self.form_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.password_label)
        self.form_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.password_edit)
        self.form_layout.setWidget(2, QFormLayout.ItemRole.SpanningRole, self.register_btn)
        self.form_layout.setWidget(3, QFormLayout.ItemRole.SpanningRole, self.login_btn)

        self.bind()
        self.resize(400, 200)

    def bind(self):
        self.register_btn.clicked.connect(self.register)
        self.login_btn.clicked.connect(self.login)

    def register(self):
        if self.username_edit.text() == "" or self.password_edit.text() == "":
            MessageBox(self.tr("注册用户"), self.tr("用户名和密码不能为空"), self).exec()
            return
        confirm = MessageBox(self.tr("注册用户"), self.tr("确定要进行注册吗"), self)
        confirm.yesButton.setText(self.tr("确定"))
        confirm.cancelButton.setText(self.tr("取消"))
        if not confirm.exec():
            return
        with Session(self.engin) as session:
            user = User(username=self.username_edit.text(), password=self.password_edit.text(), last_login=datetime.datetime.now())
            session.add(user)
            session.commit()

    def login(self):
        with Session(self.engin) as session:
            user = session.query(User).filter(User.username == self.username_edit.text()).first()
            if user is not None and user.password == self.password_edit.text():
                user.last_login = datetime.datetime.now()
                self.main_window = Window(self.username_edit.text())
                self.main_window.logout_clicked.connect(self.logout)
                self.main_window.show()
                self.hide()
            else:
                MessageBox(self.tr("登录失败"), self.tr("用户名或密码错误"), self).exec()

    def logout(self):
        self.main_window.hide()
        self.main_window.destroy()
        self.username_edit.setText("")
        self.password_edit.setText("")
        self.show()


if __name__ == '__main__':
    app = QApplication()
    setTheme(Theme.AUTO)
    w = Window("admin")
    w.show()
    app.exec()
