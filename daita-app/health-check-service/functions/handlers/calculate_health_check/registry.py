from typing import Callable, Dict


HEALTHCHECK: Dict[str, Callable] = {}


def register_healthcheck(name: str):
    def wrapper(healthcheck_function):
        HEALTHCHECK[name] = healthcheck_function
        return healthcheck_function

    return wrapper
