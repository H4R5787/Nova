"""
Targeted tests for Loop Scoping & Per-Iteration Frame Isolation.
Validates the fix for closure variable capture inside loop iterations.
"""
import pytest
import nova


def test_while_loop_closure_capture():
    """
    Test that each iteration of a while loop gets an isolated environment frame.
    Closures created inside the loop must capture the value of that iteration,
    not the final state of the mutated counter.
    """
    source = """
    let mut closures = [];
    let mut i = 0;
    while (i < 4) {
        let iteration = i;
        let c = fn() { return iteration; };
        push(closures, c);
        i = i + 1;
    }

    let f0 = closures[0];
    let f1 = closures[1];
    let f2 = closures[2];
    let f3 = closures[3];

    print(f0());
    print(f1());
    print(f2());
    print(f3());
    """
    stdout = []
    nova.run(source, stdout_capture=stdout)
    assert stdout == ["0", "1", "2", "3"]


def test_for_loop_closure_capture():
    """
    Test that each iteration of a for loop isolates local bindings.
    """
    source = """
    let mut funcs = [];
    for (let mut i = 0; i < 3; i = i + 1) {
        let x = i * 10;
        push(funcs, fn() { return x; });
    }

    let g0 = funcs[0];
    let g1 = funcs[1];
    let g2 = funcs[2];

    print(g0());
    print(g1());
    print(g2());
    """
    stdout = []
    nova.run(source, stdout_capture=stdout)
    assert stdout == ["0", "10", "20"]


def test_loop_mutation_bubbles_to_outer_scope():
    """
    Reassignments to mutable variables defined outside the loop must mutate the outer frame,
    while variables declared inside the loop remain iteration-local.
    """
    source = """
    let mut outer_sum = 0;
    let mut counter = 1;
    while (counter <= 4) {
        let step = counter * 2;
        outer_sum = outer_sum + step;
        counter = counter + 1;
    }
    print("outer_sum =", outer_sum);
    print("counter =", counter);
    """
    stdout = []
    nova.run(source, stdout_capture=stdout)
    assert stdout == ["outer_sum = 20", "counter = 5"]
