def test_import():
    from kitsuyui.animal import Dog, Animal
    from kitsuyui.hello import print_hello_world
    assert Dog
    assert Animal
    assert print_hello_world
