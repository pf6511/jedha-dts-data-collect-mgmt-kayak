from pathlib import Path
import pandas as pd
from kayak.services import S3Service

class LoadPipeline:

    def __init__(self, s3_service:S3Service, base_dir:Path, logger=None):
        self.s3=s3_service
        self.base_dir=base_dir
        self.logger=logger

    def _download_files(self, s3_keys:list[str]) -> list[Path]:
        local_files=[]
        for key in s3_keys:
            local_path=self.base_dir / key

            downloaded_file = self.s3.download_file(s3_key=key,local_path=local_path,overwrite=False)
            local_files.append(downloaded_file)
        return local_files


    def run(self, s3_keys: list[str]) -> list[Path]:
        self.logger.info("Starting LoadPipeline...")

        local_files = self._download_files(s3_keys)
        self.logger.info("LoadPipeline completed")
        return local_files