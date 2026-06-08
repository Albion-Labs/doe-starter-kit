"""Synthetic fixture app — clean baseline, no defects."""


def add(a, b):
    return a + b


def is_even(n):
    return n % 2 == 0


def greet(name):
    return f"Hello, {name}!"
