from .base_step import register_step
from .document_segmentation import DocumentSegmentation
from .segment_vectorization import SegmentVectorization
from .general_initialization import GeneralInitialization
from .servicenow_segmentation import ServiceNowSegmentation


register_step("14fc347b-aa19-4a2a-9d9b-3b3a630c9d5c", GeneralInitialization)
register_step("423a197c-7f5b-45bc-be1e-12667e95979e", GeneralInitialization)
register_step("19feed33-c233-44c4-83ea-8d5dd54e7ec1", SegmentVectorization)
register_step("647427ef-2654-4585-8aaa-e03c66915c91", DocumentSegmentation)
register_step("82d68b0d-f602-4643-ba38-fccb1b7410eb", ServiceNowSegmentation)
register_step("b3b65582-c792-438a-b0bf-f034f6585a8c", SegmentVectorization)
