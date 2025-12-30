"""Tests for singleton metaclass."""

from src.core.types.singleton import SingletonMeta

# Test values for singleton tests
TEST_VALUE_FIRST = 42
TEST_VALUE_SECOND = 10
TEST_VALUE_THIRD = 20
TEST_KWARGS_COUNT = 5


class TestSingletonMeta:
    """Tests for SingletonMeta metaclass."""

    def setup_method(self) -> None:
        """Reset singleton instances before each test."""
        # Clear any existing instances from the shared dict
        SingletonMeta._instances.clear()  # noqa: SLF001

    def test_creates_instance_on_first_call(self) -> None:
        """Singleton creates instance on first instantiation."""

        class TestClass(metaclass=SingletonMeta):
            def __init__(self, value: int = 0) -> None:
                self.value = value

        instance = TestClass(TEST_VALUE_FIRST)

        assert instance is not None
        assert instance.value == TEST_VALUE_FIRST

    def test_returns_cached_instance_on_subsequent_calls(self) -> None:
        """Singleton returns same instance on subsequent instantiations."""

        class AnotherTestClass(metaclass=SingletonMeta):
            def __init__(self, value: int = 0) -> None:
                self.value = value

        instance1 = AnotherTestClass(TEST_VALUE_SECOND)
        instance2 = AnotherTestClass(TEST_VALUE_THIRD)

        assert instance1 is instance2
        # Value should be from first instantiation
        assert instance1.value == TEST_VALUE_SECOND
        assert instance2.value == TEST_VALUE_SECOND

    def test_different_classes_have_separate_instances(self) -> None:
        """Different singleton classes maintain separate instances."""

        class ClassA(metaclass=SingletonMeta):
            name = "A"

        class ClassB(metaclass=SingletonMeta):
            name = "B"

        instance_a = ClassA()
        instance_b = ClassB()

        assert instance_a is not instance_b  # type: ignore[comparison-overlap]
        assert instance_a.name == "A"
        assert instance_b.name == "B"

    def test_works_with_no_init_args(self) -> None:
        """Singleton works with classes that have no __init__ args."""

        class SimpleClass(metaclass=SingletonMeta):
            pass

        instance1 = SimpleClass()
        instance2 = SimpleClass()

        assert instance1 is instance2

    def test_works_with_kwargs(self) -> None:
        """Singleton works with keyword arguments."""

        class KwargsClass(metaclass=SingletonMeta):
            def __init__(self, name: str = "default", count: int = 0) -> None:
                self.name = name
                self.count = count

        instance = KwargsClass(name="test", count=TEST_KWARGS_COUNT)

        assert instance.name == "test"
        assert instance.count == TEST_KWARGS_COUNT

        # Second instantiation should return cached instance
        instance2 = KwargsClass(name="other", count=TEST_VALUE_SECOND)
        assert instance2.name == "test"  # Still original values
