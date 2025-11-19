"""
Project service for the FAIR Metadata Enrichment API.
Handles project-related business logic.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, List, Optional

from models.pydantic_models import DatasetSummary, ProjectSummary
from app.core.config import DATASET_PREFIX, METADATA_SUBDIR, PROJECT_PREFIX, get_monitor_path
from app.core.cache import cached, get_project_cache
from app.services.metadata_generator import get_metadata_generator

logger = logging.getLogger(__name__)


class ProjectService:
    def __init__(self, metadata_generator: Optional[Any] = None) -> None:
        logger.debug("ProjectService: Initializing...")
        self.monitor_path = get_monitor_path()
        self.project_cache = get_project_cache()
        if metadata_generator is not None:
            self.metadata_generator = metadata_generator
        else:
            self.metadata_generator = get_metadata_generator()
        logger.debug("ProjectService: Initialization complete")

    @cached(ttl_seconds=60, cache_type="memory")  # Cache project list for 1 minute
    async def list_projects(self) -> List[ProjectSummary]:
        """List all available projects."""
        projects: List[ProjectSummary] = []

        logger.debug(f"ProjectService: monitor_path = {self.monitor_path}")
        logger.debug(f"ProjectService: monitor_path.exists() = {self.monitor_path.exists()}")
        logger.debug(f"ProjectService: PROJECT_PREFIX = {PROJECT_PREFIX}")

        if not self.monitor_path.exists():
            logger.warning("ProjectService: Monitor path does not exist!")
            return projects

        logger.debug(f"ProjectService: Scanning directory contents:")

        # Run directory scanning in thread pool for better performance
        loop = asyncio.get_event_loop()
        project_dirs = await loop.run_in_executor(
            None, self._scan_project_directories
        )

        for project_dir in project_dirs:
            project_id = project_dir.name
            project_path = project_dir
            logger.debug(f"ProjectService: Found project: {project_id}")

            # Try to get project title from metadata (run in thread pool)
            project_title = await loop.run_in_executor(
                None, self._get_project_title, project_path
            )

            # Count folders and datasets (run in thread pool)
            folder_count, dataset_count = await loop.run_in_executor(
               None, self._count_folders_and_datasets, project_path
            )

            project_summary = ProjectSummary(
                project_id=project_id,
                project_title=project_title,
                path=str(project_path.absolute()),
                folder_count=folder_count,
                dataset_count=dataset_count,
            )
            logger.debug(f"ProjectService: Adding project: {project_summary}")
            projects.append(project_summary)

        logger.debug(f"ProjectService: Returning {len(projects)} projects")
        return projects

    def _scan_project_directories(self) -> List[Path]:
        """Scan for project directories (sync function for thread pool)."""
        project_dirs = []
        for item in self.monitor_path.iterdir():
            if item.is_dir() and item.name.startswith(PROJECT_PREFIX):
                project_dirs.append(item)
        return project_dirs

    def _get_project_title(self, project_path: Path) -> Optional[str]:
        """Get project title from metadata file (sync function for thread pool)."""
        metadata_file = project_path / METADATA_SUBDIR / "project_descriptive.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                    return metadata.get("project_title")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"ProjectService: Error reading metadata: {e}")
        return None

    def _count_folders_and_datasets(self, project_path: Path) -> tuple[int, int]:
        """Return total non-hidden folder count and d_-prefixed dataset count."""
        folder_count = 0
        dataset_count = 0
        for subitem in project_path.iterdir():
            if not subitem.is_dir():
                continue
            # Exclude hidden folders
            if subitem.name.startswith('.'):
                continue
            folder_count += 1
            if subitem.name.startswith(DATASET_PREFIX):
                dataset_count += 1
        return folder_count, dataset_count

    @cached(ttl_seconds=120, cache_type="memory")  # Cache dataset list for 2 minutes
    async def get_project_datasets(self, project_id: str) -> List[DatasetSummary]:
        """List all datasets within a specific project."""
        datasets = []

        project_path = self.monitor_path / project_id
        if not project_path.exists() or not project_path.is_dir():
            raise ValueError(f"Project {project_id} not found")

        # Run dataset scanning in thread pool
        loop = asyncio.get_event_loop()
        dataset_dirs = await loop.run_in_executor(
            None, self._scan_dataset_directories, project_path
        )

        for dataset_dir in dataset_dirs:
            dataset_id = dataset_dir.name
            dataset_path = dataset_dir

            # Get dataset metadata (run in thread pool)
            dataset_title, metadata_status = await loop.run_in_executor(
                None, self._get_dataset_info, dataset_path
            )

            datasets.append(
                DatasetSummary(
                    dataset_id=dataset_id,
                    dataset_title=dataset_title,
                    path=str(dataset_path.absolute()),
                    metadata_status=metadata_status,
                )
            )

        return datasets

    def _scan_dataset_directories(self, project_path: Path) -> List[Path]:
        """Scan for dataset directories (sync function for thread pool)."""
        dataset_dirs = []
        for item in project_path.iterdir():
            if item.is_dir() and item.name.startswith(DATASET_PREFIX):
                dataset_dirs.append(item)
        return dataset_dirs

    def _get_dataset_info(self, dataset_path: Path) -> tuple[Optional[str], str]:
        """Get dataset title and metadata status (sync function for thread pool)."""
        # Try to get dataset title from metadata
        dataset_title = None
        metadata_file = dataset_path / METADATA_SUBDIR / "dataset_structural.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                    dataset_title = metadata.get("dataset_title")
            except (json.JSONDecodeError, KeyError):
                pass

        # Determine metadata status
        metadata_status = "V0_Initial"
        if (dataset_path / METADATA_SUBDIR / "dataset_structural.json").exists():
            metadata_status = "V1_Ingested"
        if (dataset_path / METADATA_SUBDIR / "complete_metadata.json").exists():
            metadata_status = "V2_Finalized"

        return dataset_title, metadata_status

    def get_dataset_path(self, dataset_id: str) -> Optional[Path]:
        """Get the path to a specific dataset by its ID."""
        # Search through all projects to find the dataset
        for project_dir in self.monitor_path.iterdir():
            if project_dir.is_dir() and project_dir.name.startswith(PROJECT_PREFIX):
                dataset_path = project_dir / dataset_id
                if dataset_path.exists() and dataset_path.is_dir():
                    return dataset_path
        return None
