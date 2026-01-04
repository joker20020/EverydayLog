# -*- UTF-8 -*-
# @author   : 40599
# @time     : 2026/1/4 13:36
# @version  : V1
import datetime

from sqlalchemy import Integer, DateTime, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    username: Mapped[str] = mapped_column(String(32))
    password: Mapped[str] = mapped_column(String(32))
    last_login: Mapped[datetime.datetime] = mapped_column(DateTime)
    records: Mapped[List["Record"]] = relationship(back_populates="user")


class Record(Base):
    __tablename__ = "records"
    record_id: Mapped[int] = mapped_column(primary_key=True)
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime.datetime] = mapped_column(DateTime)
    content: Mapped[str] = mapped_column(String())
    image_list: Mapped[str] = mapped_column(String)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"))

    user: Mapped[User] = relationship(back_populates="records")
