"""Salix Struct reading: Structs parse wherever dataclasses do."""

from __future__ import annotations

import pytest

import tyro
from salix import Struct


class Optimizer(Struct):
    learning_rate: float = 1e-3
    weight_decay: float = 0.0


class Train(Struct):
    optimizer: Optimizer = Optimizer()
    steps: int = 10
    name: str = "base"


def train(config: Train) -> Train:
    return config


def test_basic_struct_parse() -> None:
    config = tyro.cli(
        train,
        args=["--config.steps", "42", "--config.optimizer.learning-rate", "0.5"],
    )
    assert isinstance(config, Train)
    assert config.steps == 42
    assert config.optimizer.learning_rate == 0.5


def test_struct_defaults() -> None:
    config = tyro.cli(train, args=[])
    assert config.steps == 10
    assert config.optimizer.weight_decay == 0.0


class TrainSub(Struct):
    steps: int = 1


class EvalSub(Struct):
    batches: int = 2


def union_main(sub: TrainSub | EvalSub) -> TrainSub | EvalSub:
    return sub


def test_struct_union_subparser() -> None:
    config = tyro.cli(union_main, args=["sub:eval-sub", "--sub.batches", "7"])
    assert isinstance(config, EvalSub)
    assert config.batches == 7


def test_struct_field_names_preserved() -> None:
    config = tyro.cli(train, args=["--config.name", "custom"])
    assert config.name == "custom"


class DocumentedBase(Struct):
    """Base.

    Args:
        inherited: help from the base class docstring.
    """

    inherited: int = 1


class DocumentedChild(DocumentedBase):
    own: int = 2
    """Help from an attribute docstring."""


def test_struct_field_help_resolves_through_user_bases(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        tyro.cli(DocumentedChild, args=["--help"])
    output = capsys.readouterr().out
    assert "help from the base class docstring." in output
    assert "Help from an attribute docstring." in output
