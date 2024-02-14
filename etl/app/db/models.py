from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.schemas.instance import InstanceStatus
from app.schemas.pipeline import PipelineStepStatus
from app.schemas.application import ApplicationType
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

    id = Column(String, primary_key=True)
    creator = Column(String)
    name = Column(String)
    comment = Column(String, nullable=True)
    startTime = Column(String, nullable=True)
    endTime = Column(String, nullable=True)
    status = Column(Enum(InstanceStatus))
    datasetId = Column(String, nullable=True)
    selected_pipeline_id = Column(String, ForeignKey("pipelines.id"), nullable=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)

    chartData = relationship("InstanceChartData", back_populates="instance")
    pipelineStepStatuses = relationship(
        "InstancePipelineStepStatus", back_populates="instance"
    )

    application = relationship("Application", back_populates="instances")


class InstanceChartData(Base):
    __tablename__ = "instance_chart_data"

    instance_id = Column(String, ForeignKey("instances.id"), primary_key=True)

    totalItems = Column(Integer, default=0)
    ingestedItems = Column(Integer, default=0)
    avgSize = Column(Integer, default=0)
    totalSize = Column(Integer, default=0)
    ingestedSize = Column(Integer, default=0)
    ingestedChunks = Column(Integer, default=0)

    instance = relationship("Instance", back_populates="chartData")


class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(String, primary_key=True)
    entry = Column(String, ForeignKey("pipeline_steps.id"))
    exit = Column(String, ForeignKey("pipeline_steps.id"))
    label = Column(String)

    steps = relationship("PipelineStep", back_populates="pipeline")


class PipelineStep(Base):
    __tablename__ = "pipeline_steps"
    id = Column(String, primary_key=True)
    title = Column(String)
    # parent_id = Column(String, ForeignKey("pipeline_steps.id"))

    data = relationship("PipelineStepData", back_populates="step")
    pipeline = relationship("Pipeline", back_populates="steps")
    dependsOn = relationship("PipelineStepDependencies", back_populates="source")
    dependedOn = relationship("PipelineStepDependencies", back_populates="target")


class PipelineStepData(Base):
    __tablename__ = "pipeline_step_data"

    step_id = Column(String, ForeignKey("pipeline_steps.id"), primary_key=True)
    title = Column(String)
    value = Column(String)


class PipelineStepDependencies(Base):
    __tablename__ = "pipeline_step_dependencies"

    source_id = Column(String, ForeignKey("pipeline_steps.id"), primary_key=True)
    target_id = Column(String, ForeignKey("pipeline_steps.id"), primary_key=True)

    source = relationship("PipelineStep", back_populates="dependsOn")
    target = relationship("PipelineStep", back_populates="dependedOn")


class InstancePipelineStepStatus(Base):
    __tablename__ = "instance_pipeline_step_statuses"

    instance_id = Column(String, ForeignKey("instances.id"), primary_key=True)
    step = Column(String, ForeignKey("pipeline_steps.id"), primary_key=True)
    status = Column(Enum(PipelineStepStatus))
    startTime = Column(String, nullable=True)
    endTime = Column(String, nullable=True)

    instance = relationship("Instance", back_populates="pipelineStepStatuses")
