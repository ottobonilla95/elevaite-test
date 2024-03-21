from datetime import datetime, timezone
import uuid
from pydantic import UUID4
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Uuid,
    JSON,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property

from ..util.func import get_utc_datetime
from ..schemas.instance import InstanceStatus
from ..schemas.pipeline import PipelineStepStatus
from ..schemas.application import ApplicationType
from .database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    icon = Column(String)
    description = Column(String)
    version = Column(String)
    creator = Column(String)  # TODO: Check if this should be a relationship to the user
    applicationType = Column(Enum(ApplicationType))

    instances = relationship("Instance", back_populates="application")
    pipelines = relationship("Pipeline")


class Instance(Base):
    __tablename__ = "instances"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    creator = Column(String)
    name = Column(String)
    comment = Column(String, nullable=True)
    startTime = Column(String, nullable=True)
    endTime = Column(String, nullable=True)
    status = Column(Enum(InstanceStatus))
    datasetId = Column(Uuid, ForeignKey("datasets.id"), nullable=False)
    selectedPipelineId = Column(Uuid, ForeignKey("pipelines.id"), nullable=False)
    applicationId = Column(Integer, ForeignKey("applications.id"), nullable=False)
    configurationId = Column(Uuid, ForeignKey("configurations.id"), nullable=False)
    projectId = Column(Uuid, ForeignKey("projects.id"), nullable=False)
    configurationRaw = Column(JSON)

    chartData = relationship(
        "InstanceChartData", back_populates="instance", uselist=False
    )
    pipelineStepStatuses = relationship(
        "InstancePipelineStepStatus", back_populates="instance"
    )

    application = relationship("Application", back_populates="instances", uselist=False)
    project = relationship("Project", uselist=False)
    dataset = relationship("Dataset", uselist=False)
    configuration = relationship("Configuration", back_populates="instances")


class InstanceChartData(Base):
    __tablename__ = "instance_chart_data"

    instanceId = Column(Uuid, ForeignKey("instances.id"), primary_key=True)

    totalItems = Column(Integer, default=0)
    ingestedItems = Column(Integer, default=0)
    avgSize = Column(Integer, default=0)
    totalSize = Column(Integer, default=0)
    ingestedSize = Column(Integer, default=0)
    ingestedChunks = Column(Integer, default=0)

    instance = relationship("Instance", back_populates="chartData")


class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    entry = Column(Uuid, ForeignKey("pipeline_steps.id"))
    exit = Column(Uuid, ForeignKey("pipeline_steps.id"))
    label = Column(String)
    applicationId = Column(Integer, ForeignKey("applications.id"))

    steps = relationship(
        "PipelineStep",
        back_populates="pipeline",
        primaryjoin="Pipeline.id==PipelineStep.pipelineId",
    )


pipeline_step_deps = Table(
    "pipeline_step_deps",
    Base.metadata,
    Column("source_id", Uuid, ForeignKey("pipeline_steps.id")),
    Column("target_id", Uuid, ForeignKey("pipeline_steps.id")),
)


class PipelineStep(Base):
    __tablename__ = "pipeline_steps"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    title = Column(String)
    pipelineId = Column(Uuid, ForeignKey("pipelines.id"))
    # parent_id = Column(String, ForeignKey("pipeline_steps.id"))

    data = relationship("PipelineStepData", back_populates="step")
    pipeline = relationship(
        "Pipeline", back_populates="steps", foreign_keys=[pipelineId]
    )

    @hybrid_property
    def previousStepIds(self) -> list[UUID4]:
        return [x.id for x in self._dependsOn]

    @hybrid_property
    def nextStepIds(self) -> list[UUID4]:
        return [x.id for x in self._dependedOn]

    _dependsOn = relationship(
        "PipelineStep",
        secondary=pipeline_step_deps,
        primaryjoin=(pipeline_step_deps.c.target_id == id),
        secondaryjoin=(pipeline_step_deps.c.source_id == id),
        backref="_dependedOn",
    )
    # dependedOn = relationship("PipelineStepDependencies", back_populates="target")


class PipelineStepData(Base):
    __tablename__ = "pipeline_step_data"

    stepId = Column(Uuid, ForeignKey("pipeline_steps.id"), primary_key=True)
    title = Column(String)
    value = Column(String)

    step = relationship("PipelineStep")


# class PipelineStepDependencies(Base):
#     __tablename__ = "pipeline_step_dependencies"

#     source_id = Column(String, ForeignKey("pipeline_steps.id"), primary_key=True)
#     target_id = Column(String, ForeignKey("pipeline_steps.id"), primary_key=True)

#     source = relationship("PipelineStep", back_populates="dependsOn")
#     target = relationship("PipelineStep", back_populates="dependedOn")


class InstancePipelineStepStatus(Base):
    __tablename__ = "instance_pipeline_step_statuses"

    instanceId = Column(Uuid, ForeignKey("instances.id"), primary_key=True)
    stepId = Column(Uuid, ForeignKey("pipeline_steps.id"), primary_key=True)
    status = Column(Enum(PipelineStepStatus))
    startTime = Column(String, nullable=True)
    endTime = Column(String, nullable=True)

    instance = relationship("Instance", back_populates="pipelineStepStatuses")


class Configuration(Base):
    __tablename__ = "configurations"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    applicationId = Column(Integer, ForeignKey("applications.id"))
    name = Column(String, unique=True)
    createDate = Column(DateTime, default=get_utc_datetime)
    updateDate = Column(DateTime, nullable=True, onupdate=get_utc_datetime)
    isTemplate = Column(Boolean)
    raw = Column(JSON)

    instances = relationship("Instance", back_populates="configuration", uselist=True)
    application = relationship("Application")


class DatasetTag(Base):
    __tablename__ = "dataset_tags"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str]


dataset_dataset_tags = Table(
    "dataset_dataset_tags",
    Base.metadata,
    Column("dataset_id", Uuid, ForeignKey("datasets.id")),
    Column("tag_id", Uuid, ForeignKey("dataset_tags.id")),
)


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String)
    projectId = Column(Uuid, ForeignKey("projects.id"))
    createDate = Column(DateTime, default=get_utc_datetime)
    updateDate = Column(DateTime, nullable=True, onupdate=get_utc_datetime)

    project = relationship("Project", back_populates="datasets")
    versions = relationship("DatasetVersion", back_populates="dataset")
    tags: Mapped[list["DatasetTag"]] = relationship(secondary=dataset_dataset_tags)


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    commitId: Mapped[str] = mapped_column()
    version: Mapped[int] = mapped_column()
    datasetId = mapped_column(ForeignKey("datasets.id"))
    createDate = Column(DateTime, default=get_utc_datetime)

    dataset: Mapped[Dataset] = relationship(back_populates="versions")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String)

    datasets = relationship("Dataset", back_populates="project")
    collections = relationship("Collection", back_populates="project")


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    projectId = mapped_column(ForeignKey("projects.id"))

    project: Mapped[Project] = relationship(back_populates="collections")
