# -*- UTF-8 -*-
# @author   : 40599
# @time     : 2026/1/4 18:29
# @version  : V1

import datetime

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QSpacerItem,
    QApplication,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (
    TitleLabel,
    SubtitleLabel,
    IconWidget,
    ComboBox,
    SpinBox,
    TextBrowser,
    HorizontalFlipView,
    CardWidget,
    ScrollArea,
    ToolButton,
    MessageBox,
    FluentIcon,
    setTheme,
    Theme
)
from qframelesswindow import AcrylicWindow
from typing import List, Dict


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
    def __init__(self, name: str = None, tasks: Dict[str, str] = None, parent=None):
        super().__init__(parent)
        if name:
            self.setObjectName(name.replace(" ", "_"))
        else:
            self.setObjectName("TaskWidget")
        if not tasks:
            tasks = {}

        self.container = QWidget(self)
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.task_label = TitleLabel(self.tr("任务名称"), self)
        self.task_choice = ComboBox(self)
        for k, v in tasks.items():
            self.task_choice.addItem(k, userData=v)
        self.task_choice.setPlaceholderText(self.tr("请选择任务"))
        self.task_state_icon = IconWidget(self)
        self.task_state_icon.setIcon(FluentIcon.UP)
        self.task_state_icon.setFixedSize(48, 48)
        self.shot_freq_label = SubtitleLabel(self.tr("截屏频率"), self)
        self.shot_freq_num = SpinBox(self)
        self.summary_freq_label = SubtitleLabel(self.tr("总结频率"), self)
        self.summary_freq_num = SpinBox(self)

        self.grid_layout.addWidget(self.task_label, 0, 0, 1, 1)
        self.grid_layout.addWidget(self.task_choice, 0, 1, 1, 1)
        self.grid_layout.addWidget(self.task_state_icon, 0, 3, 1, 1)
        self.grid_layout.addWidget(self.shot_freq_label, 1, 0, 1, 1)
        self.grid_layout.addWidget(self.shot_freq_num, 1, 1, 1, 1)
        self.grid_layout.addWidget(self.summary_freq_label, 1, 2, 1, 1)
        self.grid_layout.addWidget(self.summary_freq_num, 1, 3, 1, 1)



        self.setWidget(self.container)
        self.setWidgetResizable(True)

        self.resize(500, 500)
        self.bind()

    def bind(self):
        pass

if __name__ == '__main__':
    app = QApplication()
    # w = RecordWidgetList()
    # w = RecordWidget()
    w = TaskWidget(tasks={"react_task": "react_task_id"})
    setTheme(Theme.AUTO)
    # for i in range(5):
    #     w.add_record(datetime.datetime.now(), datetime.datetime.now(), "# test2\n ## t", [])

    w.show()
    app.exec()
