from rich.console import Console
from rich.table import Table
from rich import box
from rich.columns import Columns

class Example:
    def __init__(self, value):
        self.value = value

something = {
    "first": Example(3),
    "second": Example(0),
    "third": Example(5)
}

print(something[max(something, key=lambda key: something[key].value)])