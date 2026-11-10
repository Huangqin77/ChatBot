import pytest

from app.tools import calculator, get_current_time


@pytest.mark.parametrize(('expression', 'result'), [('(128 + 256) * 3', '1152'), ('-5 + 3**2', '4'), ('8 // 3', '2'), ('10 % 3', '1'), ('7 / 2', '3.5')])
def test_calculator(expression, result):
    assert calculator(expression).endswith('= ' + result)


@pytest.mark.parametrize('expression', ['__import__("os").system("whoami")', '(1).__class__', '[1][0]', '2**99999999', '1/0', 'True+1', '1e999', '9'*201, '(1+2', '(-1)**0.5', '2**(12**12)', '"x"*3'])
def test_reject_unsafe_or_unbounded_expressions(expression):
    with pytest.raises(ValueError):
        calculator(expression)


def test_current_time():
    assert '+08:00' in get_current_time()
    assert '+00:00' in get_current_time('UTC')
    with pytest.raises(ValueError):
        get_current_time('invalid')
