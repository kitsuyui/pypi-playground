from kitsuyui.hello import hello_world, print_hello_world


def test_hello_world() -> None:
    assert hello_world() == "Hello, World!"


def test_print_hello_world(capsys) -> None:
    print_hello_world()
    captured = capsys.readouterr()
    assert captured.out == "Hello, World!\n"
    assert captured.err == ""
