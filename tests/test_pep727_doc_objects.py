from helptext_utils import get_helptext_with_checks
from salix import Struct
from typing_extensions import Annotated, Doc


class SomeOtherMarker:
    pass


def test_basic() -> None:
    class SimpleDoc(Struct, frozen=False):
        x: Annotated[int, Doc("Simple documentation")]

    assert "Simple documentation" in get_helptext_with_checks(SimpleDoc)


def test_basic_function() -> None:
    def main(x: Annotated[int, Doc("Simple documentation")]) -> None:
        del x

    assert "Simple documentation" in get_helptext_with_checks(main)


def test_multiple_annotations() -> None:
    class MultipleAnnotations(Struct, frozen=False):
        x: Annotated[int, SomeOtherMarker(), Doc("Doc with other markers")]

    assert "Doc with other markers" in get_helptext_with_checks(MultipleAnnotations)


def test_multiline_to_dedent() -> None:
    class MultilineDoc(Struct, frozen=False):
        x: Annotated[
            int,
            Doc(
                """
            This is a multiline
            documentation string
            that should be dedented.
        """
            ),
        ]

    assert "multiline documentation" in get_helptext_with_checks(MultilineDoc)
    assert "string that" in get_helptext_with_checks(MultilineDoc)
