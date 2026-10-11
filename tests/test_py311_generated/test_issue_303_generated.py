from __future__ import annotations

from abc import ABC
from typing import Annotated, Generic, TypeVar

from helptext_utils import get_helptext_with_checks
from salix import Struct

import tyro


class Generator(ABC): ...


class VLLMGenerator(Generator): ...


OutT = TypeVar("OutT")


class BuilderConfig(Generic[OutT]): ...


class GeneratorConfig(Struct, BuilderConfig[Generator], frozen=False): ...


class VLLMSamplingConfig(Struct, frozen=False):
    n: int = 1

    temperature: float = 1.0


class VLLMGeneratorConfig(GeneratorConfig, frozen=False):
    _target: type[Generator] = VLLMGenerator

    sample: VLLMSamplingConfig = VLLMSamplingConfig()


class TorchProfilerConfig(Struct, frozen=False):
    skip_n_steps: int = 4

    wait_n_steps: int = 0

    num_warmup_steps: int = 1

    num_active_steps: int = 4

    repeat: int = 1


CLITorchProfilerConfig = Annotated[TorchProfilerConfig, tyro.conf.subcommand(name="on")]


class EvalConfig(Struct, frozen=False):
    generator: VLLMGeneratorConfig = VLLMGeneratorConfig()

    profiler: CLITorchProfilerConfig | None = None


def test_issue_303() -> None:
    assert "(default: profiler:none)" in get_helptext_with_checks(
        EvalConfig, use_underscores=True, config=(tyro.conf.CascadeSubcommandArgs,)
    )
    assert isinstance(
        tyro.cli(
            EvalConfig,
            use_underscores=False,
            args=[],
        ),
        EvalConfig,
    )
    assert isinstance(
        tyro.cli(
            EvalConfig,
            use_underscores=True,
            args=[],
        ),
        EvalConfig,
    )
    assert isinstance(
        tyro.cli(
            EvalConfig,
            use_underscores=False,
            config=(tyro.conf.CascadeSubcommandArgs,),
            args=[],
        ),
        EvalConfig,
    )
    assert isinstance(
        tyro.cli(
            EvalConfig,
            use_underscores=True,
            config=(tyro.conf.CascadeSubcommandArgs,),
            args=[],
        ),
        EvalConfig,
    )
