from kitsuyui.animal import Dog


def test_dog() -> None:
    dog = Dog("Pochi")
    assert dog.name == "Pochi"
    assert dog.speak() == "Bark"
