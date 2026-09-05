"""
Unit tests for Nova Evaluator and Runtime.
"""
import pytest
import nova
from nova.errors import NovaRuntimeError


def run_code(source: str):
    stdout = []
    nova.run(source, stdout_capture=stdout)
    return stdout


def test_eval_arithmetic():
    stdout = run_code("print(10 + 20 * 3 - 5 / 5);")
    assert stdout == ["69"]


def test_eval_string_concatenation():
    stdout = run_code('print("Hello " + "Nova!");')
    assert stdout == ["Hello Nova!"]


def test_eval_immutability_enforcement():
    # Attempting to mutate an immutable variable must raise NovaRuntimeError
    source = """
    let x = 10;
    x = 20;
    """
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source)
    assert "Cannot reassign immutable variable 'x'" in str(exc_info.value)


def test_eval_mutable_reassignment():
    source = """
    let mut x = 10;
    x = 25;
    print(x);
    """
    stdout = run_code(source)
    assert stdout == ["25"]


def test_eval_if_else():
    source = """
    let mut result = 0;
    let val = 42;
    if (val > 50) {
        result = 1;
    } else {
        result = 2;
    }
    print(result);
    """
    stdout = run_code(source)
    assert stdout == ["2"]


def test_eval_while_loop():
    source = """
    let mut sum = 0;
    let mut i = 1;
    while (i <= 5) {
        sum = sum + i;
        i = i + 1;
    }
    print(sum);
    """
    stdout = run_code(source)
    assert stdout == ["15"]


def test_eval_for_loop():
    source = """
    let mut total = 0;
    for (let mut k = 0; k < 5; k = k + 1) {
        total = total + k;
    }
    print(total);
    """
    stdout = run_code(source)
    assert stdout == ["10"]


def test_eval_functions_and_recursion():
    source = """
    fn factorial(n) {
        if (n <= 1) {
            return 1;
        }
        return n * factorial(n - 1);
    }
    print(factorial(5));
    """
    stdout = run_code(source)
    assert stdout == ["120"]


def test_eval_closures():
    source = """
    fn make_multiplier(factor) {
        return fn(val) {
            return val * factor;
        };
    }
    let times3 = make_multiplier(3);
    print(times3(7));
    """
    stdout = run_code(source)
    assert stdout == ["21"]


def test_eval_lists():
    source = """
    let mut arr = [1, 2, 3];
    push(arr, 4);
    print(len(arr));
    print(arr[0]);
    print(arr[3]);
    arr[1] = 99;
    print(arr[1]);
    """
    stdout = run_code(source)
    assert stdout == ["4", "1", "4", "99"]


def test_eval_division_by_zero():
    source = "let x = 10 / 0;"
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source)
    assert "Division by zero" in str(exc_info.value)
