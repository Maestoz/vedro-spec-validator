import json
import os
import shutil
from pathlib import Path
from typing import Any, Type

from vedro.core import Dispatcher, Plugin, PluginConfig
from vedro.events import CleanupEvent, ScenarioReportedEvent, StartupEvent
from .jj_spec_validator import Config as jj_sv_Config

jj_sv_Config.IS_ENABLED = False


__all__ = ("SpecValidator", "SpecValidatorPlugin")


class SpecValidatorPlugin(Plugin):
    def __init__(self, config: Type["SpecValidator"]) -> None:
        super().__init__(config)
        self.main_artifact_dir_path = Path(jj_sv_Config.MAIN_DIRECTORY) / "validation_results"
        self.buffer_structure: dict[str, Any] = {}
        jj_sv_Config.IS_RAISES = config.is_raised
        jj_sv_Config.IS_STRICT = config.is_strict
        jj_sv_Config.IS_ENABLED = True
        jj_sv_Config.SKIP_IF_FAILED_TO_GET_SPEC = config.skip_if_failed_to_get_spec
        jj_sv_Config.OUTPUT_FUNCTION = self._custom_output

    def subscribe(self, dispatcher: Dispatcher) -> None:
        dispatcher.listen(ScenarioReportedEvent, self.on_scenario_reported) \
                  .listen(StartupEvent, self.on_startup) \
                  .listen(CleanupEvent, self.finish_run)

    def on_startup(self, event: StartupEvent) -> None:
        self._scheduler = event.scheduler
        if self.main_artifact_dir_path.exists():
            shutil.rmtree(self.main_artifact_dir_path)

    async def on_scenario_reported(self, event: ScenarioReportedEvent) -> None:
        scenario_rel_path = event.aggregated_result.scenario.rel_path.parent
        scenario_name = event.aggregated_result.scenario.rel_path.name
        scenario_paramsed_subject = event.aggregated_result.scenario.subject

        for elem in self.buffer_structure:
            mocked_dir_path = self.main_artifact_dir_path / Path(elem)
            scenario_path_for_mocked = mocked_dir_path / scenario_rel_path
            scenario_path_for_mocked.mkdir(exist_ok=True, parents=True)
            file_path = scenario_path_for_mocked / f"{str(scenario_name)}.txt"
            with file_path.open('a') as file:
                file.write('\n' + 'subject: ' + scenario_paramsed_subject + '\n' + self.buffer_structure[elem] + '\n')
        self.buffer_structure = {}

    async def finish_run(self, event: CleanupEvent) -> None:
        output: dict[str, Any] = {}

        for dirpath, dirnames, filenames in os.walk(self.main_artifact_dir_path):
            relative_path = os.path.relpath(dirpath, self.main_artifact_dir_path)

            if relative_path == ".":
                current_dict = output
            else:
                parts = relative_path.split(os.sep)
                current_dict = output
                for part in parts:
                    if part not in current_dict:
                        current_dict[part] = {}
                    current_dict = current_dict[part]

            for filename in filenames:
                subject_without_extension = os.path.splitext(filename)[0]
                filepath = os.path.join(dirpath, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    current_dict[subject_without_extension] = f.read()

            output_file = self.main_artifact_dir_path / "results.json"

            with output_file.open('w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=4)

    def _custom_output(self, func_name: str, e: Exception, text: str = None):
        if text:
            self.buffer_structure[func_name] = text
        else:
            self.buffer_structure[func_name] = str(e)



class SpecValidator(PluginConfig):
    plugin = SpecValidatorPlugin

    is_raised = False  # If True - raises error when validation is failes. False for disable throwing error.

    is_strict = False  # If True - validate exact structure in given mocked. False - allow to mock incomplete body.

    skip_if_failed_to_get_spec = False # If True - validation will be skipped if failed to get spec.
