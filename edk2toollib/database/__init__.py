# @file __init__.py
# The core classes and methods used to interact with the database portion of edk2-pytool-library
# This prevents needing to do deeply nested imports and can simply `from edk2toollib.database import``
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Core classes and methods used to interact with the database module inside edk2-pytool-library."""
import datetime
from typing import List, Optional

from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint, func
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship  # noqa: F401

from .edk2_db import Edk2DB  # noqa: F401

# Association tables. Should not be used directly. Only for relationships
_source_association = Table(
    'source_association', Edk2DB.Base.metadata,
    Column('left_id', Integer, ForeignKey('inf.id')),
    Column('right_id', Integer, ForeignKey('source.id')),
)

_instance_source_association = Table(
    'instance_source_association', Edk2DB.Base.metadata,
    Column('left_id', Integer, ForeignKey('instancedinf.id')),
    Column('right_id', Integer, ForeignKey('source.id')),
)

_fv_association = Table(
    'fv_association', Edk2DB.Base.metadata,
    Column('left_id', Integer, ForeignKey('fv.id')),
    Column('right_id', Integer, ForeignKey('instancedinf.id')),
)
_library_association = Table(
    'library_association', Edk2DB.Base.metadata,
    Column('left_id', Integer, ForeignKey('inf.id')),
    Column('right_id', Integer, ForeignKey('library.id')),
)

_inf_association = Table(
    'inf_association', Edk2DB.Base.metadata,
    Column('left_id', Integer, ForeignKey('instancedinf.id')),
    Column('right_id', Integer, ForeignKey('instancedinf.id')),
)

class Environment(Edk2DB.Base):
    """A class to represent an environment in the database."""
    __tablename__ = "environment"

    id: Mapped[str] = mapped_column(primary_key=True)
    date: Mapped[datetime.datetime] = mapped_column(insert_default=func.now())
    version: Mapped[str] = mapped_column(String(40))
    values: Mapped[List["Value"]] = relationship(back_populates="env", cascade="all, delete-orphan")

class Value(Edk2DB.Base):
    """A class to represent a key-value pair in the database."""
    __tablename__ = "value"

    env_id: Mapped[str] = mapped_column(ForeignKey("environment.id"), primary_key=True, index=True)
    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str]
    env: Mapped["Environment"] = relationship(back_populates="values")

class Inf(Edk2DB.Base):
    """A class to represent an INF file in the database."""
    __tablename__ = "inf"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(unique=True)
    guid: Mapped[str]
    library_class: Mapped[Optional[str]]
    package_name: Mapped[Optional[str]] = mapped_column(ForeignKey("package.name"))
    module_type: Mapped[Optional[str]]
    sources: Mapped[List["Source"]] = relationship(secondary=_source_association)
    libraries:  Mapped[List["Library"]] = relationship(secondary=_library_association)

class InstancedInf(Edk2DB.Base):
    """A class to represent an instanced INF file in the database."""
    __tablename__ = "instancedinf"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    env: Mapped[str] = mapped_column(ForeignKey("environment.id"), index=True)
    path: Mapped[str] = mapped_column(ForeignKey("inf.path"))
    arch: Mapped[str]
    name: Mapped[str]
    package: Mapped[Optional["Package"]] = relationship()
    package_id: Mapped[Optional[int]] = mapped_column(ForeignKey("package.id"))
    repository: Mapped["Repository"] = relationship()
    repository_id: Mapped[Optional[int]] = mapped_column(ForeignKey("repository.id"))
    dsc: Mapped[str]
    cls: Mapped[Optional[str]]
    component: Mapped[str] = mapped_column(ForeignKey("inf.path"))
    libraries: Mapped[List["InstancedInf"]] = relationship(
        secondary=_inf_association,
        primaryjoin=(id == _inf_association.c.left_id),
        secondaryjoin=(id == _inf_association.c.right_id),
    )
    sources: Mapped[List["Source"]] = relationship(
        secondary=_instance_source_association,
    )

class Source(Edk2DB.Base):
    """A class to represent a source file in the database."""
    __tablename__ = "source"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(unique=True)
    license: Mapped[Optional[str]]
    total_lines: Mapped[Optional[int]]
    code_lines: Mapped[Optional[int]]
    comment_lines: Mapped[Optional[int]]
    blank_lines: Mapped[Optional[int]]

class Library(Edk2DB.Base):
    """A class to represent a library in the database."""
    __tablename__ = "library"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True)

class Repository(Edk2DB.Base):
    """A class to represent a repository in the database."""
    __tablename__ = "repository"
    __table_args__ = (UniqueConstraint("name", "path"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    path: Mapped[Optional[str]]
    packages: Mapped[List["Package"]] = relationship("Package", back_populates="repository")


class Package(Edk2DB.Base):
    """A class to represent a package in the database."""
    __tablename__ = "package"
    __table_args__ = (UniqueConstraint("name", "path"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    path: Mapped[str]
    repository: Mapped["Repository"] = relationship("Repository", back_populates="packages")
    repository_id: Mapped[int] = mapped_column(ForeignKey("repository.id"))

class Fv(Edk2DB.Base):
    """A class to represent an FV in the database."""
    __tablename__ = "fv"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    env: Mapped[str] = mapped_column(ForeignKey("environment.id"), index=True)
    name: Mapped[str]
    fdf: Mapped[str]
    infs: Mapped[List["InstancedInf"]] = relationship(secondary=_fv_association)
