# SPDX-FileCopyrightText: 2024-2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
import os
import subprocess
import sys
import typing as t

from dynamic_pipelines.constants import BINARY_SIZE_METRIC_NAME
from idf_build_apps import App
from idf_build_apps import CMakeApp
from idf_build_apps.utils import rmdir

if t.TYPE_CHECKING:
    pass


class IdfCMakeApp(CMakeApp):
    build_system: t.Literal['idf_cmake'] = 'idf_cmake'

    def _initialize_hook(self, **kwargs: t.Any) -> None:
        # ensure this env var exists
        os.environ['IDF_TARGET'] = self.target

        super()._initialize_hook(**kwargs)

    def _post_build(self) -> None:
        super()._post_build()

        # only upload in CI
        if os.getenv('CI_JOB_ID'):
            subprocess.run(
                [
                    'idf-ci',
                    'gitlab',
                    'upload-artifacts',
                    self.app_dir,
                ],
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            rmdir(
                self.build_path,
                exclude_file_patterns=[
                    'build_log.txt',
                ],
            )


class Metrics:
    """
    Represents a metric and its values for source, target, and the differences.
    """

    def __init__(
        self,
        source_value: t.Optional[float] = None,
        target_value: t.Optional[float] = None,
        difference: t.Optional[float] = None,
        difference_percentage: t.Optional[float] = None,
    ) -> None:
        self.source_value = source_value or 0.0
        self.target_value = target_value or 0.0
        self.difference = difference or 0.0
        self.difference_percentage = difference_percentage or 0.0

    def to_dict(self) -> t.Dict[str, t.Any]:
        """
        Converts the Metrics object to a dictionary.
        """
        return {
            'source_value': self.source_value,
            'target_value': self.target_value,
            'difference': self.difference,
            'difference_percentage': self.difference_percentage,
        }


class AppWithMetricsInfo(IdfCMakeApp):
    metrics: t.Dict[str, Metrics]
    is_new_app: bool

    def __init__(self, **kwargs: t.Any) -> None:
        super().__init__(**kwargs)

        self.metrics = {metric_name: metric_data for metric_name, metric_data in kwargs.get('metrics', {}).items()}
        self.is_new_app = kwargs.get('is_new_app', False)

    class Config:
        arbitrary_types_allowed = True


def enrich_apps_with_metrics_info(
    app_metrics_info_map: t.Dict[str, t.Dict[str, t.Any]], apps: t.List[App]
) -> t.List[AppWithMetricsInfo]:
    def _get_full_attributes(obj: App) -> t.Dict[str, t.Any]:
        """
        Retrieves all attributes of an object, including properties and computed fields.
        """
        attributes: t.Dict[str, t.Any] = obj.__dict__.copy()
        for attr in dir(obj):
            if not attr.startswith('_'):  # Skip private/internal attributes
                try:
                    value = getattr(obj, attr)
                    # Include only if it's not already in __dict__
                    if attr not in attributes:
                        attributes[attr] = value
                except Exception:
                    # Skip attributes that raise exceptions (e.g., methods needing args)
                    pass
        return attributes

    default_metrics_structure = {
        BINARY_SIZE_METRIC_NAME: Metrics(
            source_value=0,
            target_value=0,
            difference=0,
            difference_percentage=0.0,
        ),
    }

    apps_with_metrics_info = []
    for app in apps:
        key = f'{app.app_dir}_{app.config_name}_{app.target}'
        app_attributes = _get_full_attributes(app)

        metrics = {metric_name: default_metric for metric_name, default_metric in default_metrics_structure.items()}
        is_new_app = False

        if key in app_metrics_info_map:
            info = app_metrics_info_map[key]
            for metric_name, metric_data in info.get('metrics', {}).items():
                metrics[metric_name] = Metrics(
                    source_value=metric_data.get('source_value', 0),
                    target_value=metric_data.get('target_value', 0),
                    difference=metric_data.get('difference', 0),
                    difference_percentage=metric_data.get('difference_percentage', 0.0),
                )

            is_new_app = info.get('is_new_app', False)

        app_attributes.update({'metrics': metrics, 'is_new_app': is_new_app})

        apps_with_metrics_info.append(AppWithMetricsInfo(**app_attributes))

    return apps_with_metrics_info
