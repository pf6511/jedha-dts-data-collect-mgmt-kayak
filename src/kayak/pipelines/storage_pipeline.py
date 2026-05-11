from kayak.services import S3Service
from pathlib import Path

from dataclasses import dataclass

@dataclass
class StoragePipelineOutput:
    uploaded_keys: list[str]

class StoragePipeline:

    def __init__(self, s3_service:S3Service):
        self.s3 = s3_service

    def _build_s3_key(self, file: Path) -> str:
        ext = file.suffix.lstrip(".").lower() or "other"

        if "weather" in file.name:
            return f"{ext}/weather/{file.name}"
        elif "hotel" in file.name:
            return f"{ext}/hotels/{file.name}"

        return f"{ext}/{file.name}"

    def upload_files(self, files:list[Path]) -> StoragePipelineOutput:
        keys = []
        for file in filter(None, files):
            if file.exists():
                s3_key=self._build_s3_key(file)
                self.s3.upload_file(file, s3_key=s3_key)
                keys.append(s3_key)
        return StoragePipelineOutput(uploaded_keys=keys)
