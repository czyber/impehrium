from enum import StrEnum


class HomeworkAssistanceRunState(StrEnum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class HomeworkAssistanceRunStepState(StrEnum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class HomeworkAssistanceRunStepName(StrEnum):
    LABELING = "LABELING"
    EXPLANATION = "EXPLANATION"
    EXTRACT_TASKS = "EXTRACT_TASKS"


class MediaUploadState(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
