import pytest

from kitsuyui.animal import Animal, Dog


def test_dog() -> None:
    dog = Dog("Pochi")
    assert dog.name == "Pochi"
    assert dog.speak() == "Bark"


def test_animal_is_abstract() -> None:
    with pytest.raises(TypeError):
        Animal("test")  # type: ignore[abstract]
