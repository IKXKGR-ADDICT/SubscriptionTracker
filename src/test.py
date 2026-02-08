from rich.console import Console
from rich.table import Table
from rich import box
from rich.columns import Columns

something = {"hello": 98, "life": 67, "nitrogen": 241}

table = Table(
    box=box.SIMPLE_HEAD
)

table.add_column("Name")
table.add_column("Value")

for key in something:
    table.add_row(key, f"{something[key]}")

console = Console()
string = "\nLet's\ndo\nthis"

console.print(Columns([table, string]))