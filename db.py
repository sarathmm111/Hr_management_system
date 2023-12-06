import datetime
import logging
from typing import List

from sqlalchemy import String, Integer,Date, create_engine, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column, sessionmaker, relationship



class HRDBBase(DeclarativeBase):
  def __repr__(self):
    return f"{self.__class__.__name__}(id={self.id})"

class employee(HRDBBase):
  __tablename__ = "employee"
  __table_args__= (UniqueConstraint('firstname','lastname','email'),)
  empid    : Mapped[int] = mapped_column(primary_key=True)
  firstname: Mapped[str] = mapped_column(String(50))
  lastname : Mapped[str] = mapped_column(String(50))
  title_id : Mapped[int] = mapped_column(ForeignKey("designation.jobid"))
  email    : Mapped[str] = mapped_column(String(150))
  ph_no    : Mapped[str] = mapped_column(String(50))
  title    : Mapped["designation"] = relationship(back_populates='employees')

class designation(HRDBBase):
  __tablename__ = "designation"
  __table_args__ = (UniqueConstraint('jobid','title'),)
  jobid      : Mapped[int] = mapped_column(primary_key=True)
  title      : Mapped[str] = mapped_column(String(100))
  max_leaves : Mapped[int] = mapped_column(Integer)
  employees  : Mapped[List["employee"]] = relationship(back_populates='title')

class leaves(HRDBBase):
  __tablename__ = "leaves"
  __table_args__ = (UniqueConstraint("empid","date"),)
  serial_num : Mapped[int] = mapped_column(primary_key=True)
  empid      : Mapped[str] = mapped_column(ForeignKey("employee.empid"))
  date       : Mapped[datetime.date] = mapped_column(Date())
  reason     : Mapped[str] = mapped_column(String(150))


def create_all(db_uri):
    logger = logging.getLogger("HR")
    engine = create_engine(db_uri)
    HRDBBase.metadata.create_all(engine)
    logger.info("Created database")

def get_session(db_uri):
    engine = create_engine(db_uri)
    Session = sessionmaker(bind = engine)
    session = Session()
    return session