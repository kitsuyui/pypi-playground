import abc


class Animal:
    def __init__(self, name):
        self.name = name

    @abc.abstractmethod
    def speak(self):
        raise NotImplementedError("Subclass must implement abstract method")


class Dog(Animal):
    def speak(self):
        return "Bark"


def example():
    dog = Dog("Rex")
    print(dog.speak())  # Bark
