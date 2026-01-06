# -*- UTF-8 -*-
# @author   : 40599
# @time     : 2026/1/4 18:29
# @version  : V1

import datetime
import rtoml
import task
import os

from PySide6.QtWidgets import (
    QWidget,
    QFileDialog,
    QHeaderView,
    QTableWidgetItem,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QSpacerItem,
    QApplication,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColorConstants
from qfluentwidgets import (
    TitleLabel,
    SubtitleLabel,
    IconWidget,
    ComboBox,
    SpinBox,
    PrimaryPushButton,
    PushButton,
    TextBrowser,
    HorizontalFlipView,
    CardWidget,
    HeaderCardWidget,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PasswordLineEdit,
    AvatarWidget,
    ScrollArea,
    TableWidget,
    ToolButton,
    PrimaryToolButton,
    MessageBox,
    FluentIcon,
    SmoothMode,
    setTheme,
    Theme
)

from typing import List, Dict
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()


class RecordWidget(CardWidget):
    delete_content = Signal(datetime.datetime, datetime.datetime)

    def __init__(self, name: str = None, parent=None):
        super().__init__(parent)

        self.from_datetime = None
        self.to_datetime = None

        if name:
            self.setObjectName(name.replace(" ", "_"))
        else:
            self.setObjectName("RecordWidget")
        self.setMaximumHeight(200)
        self.setBorderRadius(10)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.h_box_layout = QHBoxLayout(self)
        self.v_box_layout = QVBoxLayout()
        self.h_box_layout_datetime = QHBoxLayout()
        self.v_box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.start_datetime = TitleLabel("start time", self)
        self.datetime_icon = IconWidget(self)
        self.end_datetime = TitleLabel("end time", self)
        self.del_btn = ToolButton(FluentIcon.DELETE, self)

        self.start_datetime.setMinimumWidth(100)
        self.start_datetime.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.end_datetime.setMinimumWidth(100)
        self.end_datetime.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.datetime_icon.setIcon(FluentIcon.DATE_TIME)
        self.datetime_icon.setFixedSize(48, 48)

        self.content = TextBrowser(self)
        self.images = HorizontalFlipView(self)

        self.v_box_layout.addItem(QSpacerItem(5, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.v_box_layout.addWidget(self.start_datetime)

        # add icon
        self.h_box_layout_datetime.addItem(QSpacerItem(20, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.h_box_layout_datetime.addWidget(self.datetime_icon)
        self.h_box_layout_datetime.addItem(QSpacerItem(20, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.v_box_layout.addLayout(self.h_box_layout_datetime)

        self.v_box_layout.addWidget(self.end_datetime)
        self.v_box_layout.addItem(QSpacerItem(5, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.v_box_layout.addWidget(self.del_btn)

        self.h_box_layout.addLayout(self.v_box_layout)
        self.h_box_layout.addWidget(self.content)
        self.h_box_layout.addWidget(self.images)

        self.bind()

    def bind(self):
        self.del_btn.clicked.connect(self.delete_clicked)

    def setContent(self, start_datetime: datetime.datetime, end_datetime: datetime.datetime, content: str, image_list: List[str]):
        self.from_datetime = start_datetime
        self.to_datetime = end_datetime
        self.start_datetime.setText(start_datetime.strftime("%Y-%m-%d %H:%M:%S"))
        self.end_datetime.setText(end_datetime.strftime("%Y-%m-%d %H:%M:%S"))
        self.content.setMarkdown(content)
        self.images.clear()
        if len(image_list):
            self.images.addImages(image_list)

    def delete_clicked(self):
        self.delete_content.emit(self.from_datetime, self.to_datetime)


class RecordWidgetList(ScrollArea):

    delete_widget = Signal(datetime.datetime, datetime.datetime)

    def __init__(self, name: str = None, parent=None):
        super().__init__(parent)
        if name:
            self.setObjectName(name.replace(" ", "_"))
        else:
            self.setObjectName("RecordWidgetList")
        self.setSmoothMode(SmoothMode.NO_SMOOTH, Qt.Orientation.Vertical)

        self.records_container = QWidget(self)
        self.v_box_layout = QVBoxLayout(self.records_container)

        self.setWidget(self.records_container)
        self.setWidgetResizable(True)

        # self.resize(500, 500)
        self.bind()

    def add_record(self, start_datetime: datetime.datetime, end_datetime: datetime.datetime, content: str, image_list: List[str]):
        record_widget = RecordWidget()
        record_widget.setContent(start_datetime, end_datetime, content, image_list)
        record_widget.delete_content.connect(self.delete_record)
        self.v_box_layout.addWidget(record_widget)
        self.records_container.adjustSize()

    def clear_records(self):
        for i in range(self.v_box_layout.count()):
            widget = self.v_box_layout.itemAt(0).widget()
            if isinstance(widget, RecordWidget):
                self.v_box_layout.removeWidget(widget)
                widget.deleteLater()

    def bind(self):
        pass

    def delete_record(self, start_datetime: datetime.datetime, end_datetime: datetime.datetime):
        confirm = MessageBox(self.tr("删除记录"), self.tr("确定要删除当前记录吗？"), self)
        confirm.yesButton.setText(self.tr("确定"))
        confirm.cancelButton.setText(self.tr("取消"))
        if not confirm.exec():
            return

        for i in range(self.v_box_layout.count()):
            widget = self.v_box_layout.itemAt(i).widget()
            if isinstance(widget, RecordWidget):
                if widget.from_datetime == start_datetime and widget.to_datetime == end_datetime:
                    self.v_box_layout.removeWidget(widget)
                    widget.deleteLater()
                    break
        self.delete_widget.emit(start_datetime, end_datetime)


class TaskWidget(ScrollArea):
    def __init__(self, username: str, name: str = None, tasks: Dict[str, str] = None, parent=None):
        super().__init__(parent)
        if name:
            self.setObjectName(name.replace(" ", "_"))
        else:
            self.setObjectName("TaskWidget")
        if not tasks:
            tasks = {}

        self.current_task = None
        self.username = username

        self.container = QWidget(self)
        self.grid_layout = QGridLayout()
        self.v_box_layout = QVBoxLayout(self.container)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.task_label = TitleLabel(self.tr("任务名称"), self)
        self.task_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.task_choice = ComboBox(self)
        self.task_choice.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        for k, v in tasks.items():
            self.task_choice.addItem(k, userData=v)
        if len(tasks) > 1:
            self.task_choice.setPlaceholderText(self.tr("请选择任务"))

        self.task_state_icon = IconWidget(self)
        self.task_state_icon.setIcon(FluentIcon.PAUSE_BOLD)
        self.task_state_icon.setFixedSize(48, 48)

        self.shot_freq_label = SubtitleLabel(self.tr("截屏频率/s"), self)
        self.shot_freq_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shot_freq_num = SpinBox(self)
        self.shot_freq_num.setValue(10)

        self.summary_freq_label = SubtitleLabel(self.tr("总结频率/s"), self)
        self.summary_freq_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.summary_freq_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_freq_num = SpinBox(self)
        self.summary_freq_num.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.summary_freq_num.setValue(60)

        self.force_width_label = SubtitleLabel(self.tr("缩放图像宽度"), self)
        self.force_width_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.force_width_num = SpinBox(self)
        self.force_width_num.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.force_width_num.setRange(0, 9999)
        self.force_width_num.setValue(1280)

        self.force_height_label = SubtitleLabel(self.tr("缩放图像高度"), self)
        self.force_height_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.force_height_num = SpinBox(self)
        self.force_height_num.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.force_height_num.setRange(0, 9999)
        self.force_height_num.setValue(720)

        self.start_btn = PrimaryPushButton(self.tr("开始"), self)
        self.stop_btn = PushButton(self.tr("停止"), self)
        self.stop_btn.setEnabled(False)

        self.log_table = TableWidget(self)
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.log_table.horizontalHeader().stretchLastSection()
        self.log_table.setBorderVisible(True)
        self.log_table.setBorderRadius(8)
        self.log_table.setWordWrap(False)
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels([self.tr("时间"), self.tr("级别"), self.tr("内容")])


        # init layout
        self.grid_layout.addWidget(self.task_label, 0, 0, 1, 1)
        self.grid_layout.addWidget(self.task_choice, 0, 1, 1, 1)
        self.grid_layout.addWidget(self.task_state_icon, 0, 3, 1, 1)
        self.grid_layout.addWidget(self.shot_freq_label, 1, 0, 1, 1)
        self.grid_layout.addWidget(self.shot_freq_num, 1, 1, 1, 1)
        self.grid_layout.addWidget(self.summary_freq_label, 1, 2, 1, 1)
        self.grid_layout.addWidget(self.summary_freq_num, 1, 3, 1, 1)
        self.grid_layout.addWidget(self.force_width_label, 2, 0, 1, 1)
        self.grid_layout.addWidget(self.force_width_num, 2, 1, 1, 1)
        self.grid_layout.addWidget(self.force_height_label, 2, 2, 1, 1)
        self.grid_layout.addWidget(self.force_height_num, 2, 3, 1, 1)
        self.grid_layout.addWidget(self.start_btn, 3, 0, 1, 2)
        self.grid_layout.addWidget(self.stop_btn, 3, 2, 1, 2)

        self.v_box_layout.addLayout(self.grid_layout)
        self.v_box_layout.addWidget(self.log_table)

        self.setWidget(self.container)
        self.setWidgetResizable(True)

        self.resize(500, 500)
        self.bind()

    def bind(self):
        self.start_btn.clicked.connect(self.start_task)
        self.stop_btn.clicked.connect(self.stop_task)

    def start_task(self):
        task_name = self.task_choice.currentText()
        shot_freq = self.shot_freq_num.value()
        if shot_freq <= 0:
            InfoBar.warning(
                title=self.tr("截屏频率有误"),
                content=self.tr("截屏频率必须大于0"),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        summary_freq = self.summary_freq_num.value()
        if summary_freq <= 0:
            InfoBar.warning(
                title=self.tr("总结频率有误"),
                content=self.tr("总结频率必须大于0"),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        force_width = self.force_width_num.value()
        if force_width <= 0:
            InfoBar.warning(
                title=self.tr("缩放图像宽度有误"),
                content=self.tr("缩放图像宽度必须大于0"),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        force_height = self.force_height_num.value()
        if force_height <= 0:
            InfoBar.warning(
                title=self.tr("缩放图像高度有误"),
                content=self.tr("缩放图像高度必须大于0"),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        self.current_task = getattr(task, task_name)(username=self.username,
                                                     shot_freq=shot_freq,
                                                     summary_freq=summary_freq,
                                                     force_size=(force_width, force_height),
                                                     )
        if hasattr(self.current_task, "take_shot"):
            self.current_task.take_shot.connect(self.shot_log)
        if hasattr(self.current_task, "summary"):
            self.current_task.summary.connect(self.summary_log)
        if hasattr(self.current_task, "task_start"):
            self.current_task.task_start.connect(self.start_log)
        if hasattr(self.current_task, "task_end"):
            self.current_task.task_end.connect(self.end_log)
        self.current_task.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.task_state_icon.setIcon(FluentIcon.PLAY_SOLID.colored(QColorConstants.Green, QColorConstants.Green))

    def stop_task(self):
        self.current_task.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.task_state_icon.setIcon(FluentIcon.PAUSE_BOLD)

    def write_log(self, level: str, content: str):
        self.log_table.insertRow(self.log_table.rowCount())
        self.log_table.setItem(self.log_table.rowCount() - 1, 0, QTableWidgetItem(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.log_table.setItem(self.log_table.rowCount() - 1, 1, QTableWidgetItem(level))
        self.log_table.setItem(self.log_table.rowCount() - 1, 2, QTableWidgetItem(content))

    def shot_log(self):
        self.write_log("INFO", self.tr("Take a shot"))

    def summary_log(self):
        self.write_log("INFO", self.tr("Summary"))

    def start_log(self):
        self.write_log("INFO", self.tr("Start"))

    def end_log(self):
        self.write_log("INFO", self.tr("End"))


class SettingWidget(QWidget):
    change_profile_clicked = Signal(str, str)

    def __init__(self, username: str, password: str, name: str = None, parent=None):
        super().__init__(parent)
        self.username = username
        self.password = password
        if name:
            self.setObjectName(name.replace(" ", "_"))
        else:
            self.setObjectName("SettingWidget")
        with open(os.environ["EVERYDAY_LOG_CONFIG_PATH"]) as f:
            self.config = rtoml.load(f)

        self.v_box_layout = QVBoxLayout(self)

        self.info_card = CardWidget(self)
        self.info_card_grid_layout = QGridLayout(self.info_card)
        self.info_card_grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.username_label = TitleLabel(self.tr("用户名"), self)
        self.username_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.username_editor = LineEdit(self)
        self.username_editor.setText(self.username)
        self.username_editor.setEnabled(False)

        self.passwd_label = TitleLabel(self.tr("密码"), self)
        self.passwd_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.passwd_editor = PasswordLineEdit(self)
        self.passwd_editor.setText(self.password)

        self.avatar = AvatarWidget(self)
        self.avatar.setText(self.username)

        self.change_profile_btn = PrimaryPushButton(self.tr("修改"), self)

        self.setting_scroll = ScrollArea(self)
        self.setting_scroll.setSmoothMode(SmoothMode.NO_SMOOTH, Qt.Orientation.Vertical)
        self.setting_scroll_widget = QWidget(self.setting_scroll)
        self.setting_scroll.setWidgetResizable(True)
        self.setting_scroll_layout = QVBoxLayout(self.setting_scroll_widget)
        self.setting_scroll.setWidget(self.setting_scroll_widget)

        self.image_path_card = HeaderCardWidget(self.setting_scroll_widget)
        self.image_path_card.setTitle(self.tr("图片保存设置"))
        self.image_path_editor = LineEdit(self.image_path_card)
        self.image_choose_btn = ToolButton(FluentIcon.FOLDER, self.image_path_card)
        self.image_path_card.viewLayout.addWidget(self.image_path_editor)
        self.image_path_card.viewLayout.addWidget(self.image_choose_btn)
        self.image_path_card.setMaximumHeight(300)

        self.db_path_card = HeaderCardWidget(self.setting_scroll_widget)
        self.db_path_card.setTitle(self.tr("数据库保存设置"))
        self.db_path_editor = LineEdit(self.db_path_card)
        self.db_choose_btn = ToolButton(FluentIcon.FOLDER, self.db_path_card)
        self.db_path_card.viewLayout.addWidget(self.db_path_editor)
        self.db_path_card.viewLayout.addWidget(self.db_choose_btn)
        self.db_path_card.setMaximumHeight(300)

        self.btn_h_layout = QHBoxLayout()
        self.btn_h_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.confirm_btn = PrimaryToolButton(FluentIcon.CHECKBOX, self)
        # self.quit_btn = ToolButton(FluentIcon.CLOSE, self)

        self.info_card_grid_layout.addWidget(self.username_label, 0, 0, 1, 1)
        self.info_card_grid_layout.addWidget(self.username_editor, 0, 1, 1, 1)
        self.info_card_grid_layout.addWidget(self.passwd_label, 1, 0, 1, 1)
        self.info_card_grid_layout.addWidget(self.passwd_editor, 1, 1, 1, 1)
        self.info_card_grid_layout.addWidget(self.avatar, 0, 2, 1, 1)
        self.info_card_grid_layout.addWidget(self.change_profile_btn, 1, 2, 1, 1)

        self.setting_scroll_layout.addWidget(self.image_path_card)
        self.setting_scroll_layout.addWidget(self.db_path_card)

        # self.btn_h_layout.addWidget(self.quit_btn)
        self.btn_h_layout.addWidget(self.confirm_btn)

        self.v_box_layout.addWidget(self.info_card)
        self.v_box_layout.addWidget(self.setting_scroll)
        self.v_box_layout.addLayout(self.btn_h_layout)

        self.bind()

    def bind(self):
        self.change_profile_btn.clicked.connect(self.change_profile)
        self.image_choose_btn.clicked.connect(self.choose_image_path)
        self.db_choose_btn.clicked.connect(self.choose_db_path)
        self.confirm_btn.clicked.connect(self.change_config)

    def change_profile(self):
        w = MessageBox(self.tr("修改用户信息"), self.tr("是否要修改用户信息"), self)
        w.yesButton.setText(self.tr("确定"))
        w.cancelButton.setText(self.tr("取消"))
        if not w.exec():
            return
        self.change_profile_clicked.emit(self.username_editor.text(), self.passwd_editor.text())

    def choose_image_path(self):
        file_path = QFileDialog.getExistingDirectory(self, self.tr("选择图片保存路径"), self.config["IMAGE_TEMP_PATH"])
        if file_path:
            self.image_path_editor.setText(file_path)

    def choose_db_path(self):
        database_url = self.config["DATABASE_URL"]
        prefix = database_url.split(":///")[0]
        database_path = database_url.split(":///")[1]
        file_path, _ = QFileDialog.getOpenFileName(self, self.tr("选择数据库保存路径"), database_path, "DataBases (*.db *.sqlite *.sqlite3)")
        if file_path:
            self.db_path_editor.setText(prefix + ":///" + file_path)

    def change_config(self):
        w = MessageBox(self.tr("修改配置文件"), self.tr("是否要修改配置文件"), self)
        w.yesButton.setText(self.tr("确定"))
        w.cancelButton.setText(self.tr("取消"))
        if not w.exec():
            return
        self.config["IMAGE_TEMP_PATH"] = self.image_path_editor.text()
        self.config["DATABASE_URL"] = self.db_path_editor.text()
        with open(os.environ["EVERYDAY_LOG_CONFIG_PATH"], "w") as f:
            rtoml.dump(self.config, f)


if __name__ == '__main__':
    app = QApplication()
    # w = RecordWidgetList()
    # w = RecordWidget()
    # w = TaskWidget("admin", tasks={"react_task": "react_task_id", "react_task2": "react_task2_id"})
    w = SettingWidget("admin", "admin")
    setTheme(Theme.AUTO)
    # for i in range(5):
    #     w.add_record(datetime.datetime.now(), datetime.datetime.now(), "# test2\n ## t", [])

    w.show()
    app.exec()
