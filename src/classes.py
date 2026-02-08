import configparser as cfg
import json
import os
from rich.layout import Layout
from rich.columns import Columns
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
import statistics as stat
import readchar as rc
from functools import partial

class Cache:
    def __init__(self):
        config_path = r"assets/config/config.cfg"
        self.config = cfg.ConfigParser()
        files_read = self.config.read(config_path)
        
        if not files_read:
            raise FileNotFoundError("Config was not found")
    
    def get_config(self):
        return self.config
            
class Subscription:
    def __init__(self, name: str, expense: int|float):
        self.name = name
        self.expense = expense
        self.delta_avg = None
    
    def __repr__(self):
        return self.name.title().strip().replace("_", " ")
    
    def __add__(self, other):
        return self.expense + other.expense
    
    def __sub__(self, other):
        return self.expense - other.expense
    
    def __mul__(self, other):
        return self.expense - other.expense
    
    def __truediv__(self, other):
        return self.expense / other.expense

    def set_delta_avg(self, value: int|float):
        self.delta_avg = value
    
    def get_delta_avg(self):
        return self.delta_avg
    
    def get_expense(self):
        return self.expense

class Database:
    def __init__(self, cache: Cache):
        self.cache = cache
        self.path = self.cache.get_config().get("general", "test_data")
        
        self.data: dict[str, Subscription] = {}
        self.statistics: dict = {}
        
        with open(self.path, "r") as file:
            self.raw: dict = json.load(file)
        
        self.init_subscriptions()
        self.init_stats()
    
    def init_subscriptions(self):
        for name in self.raw:
            expense = float(self.raw[name]["expense"])
            self.data[name] = Subscription(name, expense)
        
    def init_stats(self):
        numeric = [self.data[name].get_expense() for name in self.data]
        
        _max = self.data[max(self.data, key=lambda key: self.data[key].get_expense())]
        _min = self.data[min(self.data, key=lambda key: self.data[key].get_expense())]
        
        self.statistics["max_subscription"] = f"[cyan]{_max.get_expense()}[/cyan] ([red]{_max}[/red])"
        self.statistics["min_subscription"] = f"[cyan]{_min.get_expense()}[/cyan] ([green]{_min}[/green])"
        
        self.statistics["average"] = round(stat.mean(numeric), 3)
        self.statistics["median"] = round(stat.median(numeric), 3)
        
        for name in self.data:
            subscription = self.data[name]
            expense = subscription.get_expense()
            
            subscription.set_delta_avg(round(expense - self.statistics["average"], 3))

    def display(self, console:Console, sort_mode=None):
        os.system("cls")
        data = self.data.items()

        if sort_mode == "expense":
            data = sorted(data, key=lambda item: item[1].get_expense())
        elif sort_mode == "delta":
            data = sorted(data, key=lambda item: item[1].get_delta_avg())
        elif sort_mode == "alphabet":
            data = sorted(data, key=lambda item: f"{item}")

        table = Table(
            box=box.SIMPLE_HEAD
        )
        
        table.add_column("Name")
        table.add_column("Expense")
        table.add_column("Delta Avg")
        
        for item in data:
            subscription = item[1]
            delta_avg = subscription.get_delta_avg()
            
            delta_avg_text = f"[red]{delta_avg}[/red]" if delta_avg > 0 else f"[green]{delta_avg}[/green]"
            
            table.add_row(f"[yellow]{subscription}[/yellow]", f"[cyan]{subscription.get_expense()}[/cyan]", delta_avg_text)
        
        left_panel = Panel(table, title="Subscriptions")
        
        stat_table = Table(
            box=None,
            show_header=False
        )
        
        stat_table.add_column("Stat")
        stat_table.add_column("Value")
        
        stat_table.add_row("", "")
        for name in self.statistics:
            stat_table.add_row(f"[yellow]{name.title().replace("_", " ")}[/yellow]:", f"{self.statistics[name]}")
        
        right_panel = Panel(stat_table, title="Statistics")
        
        layout = Layout()
        
        layout.split_row(
            Layout(left_panel, name="left"),
            Layout(right_panel, name="right",)
        )
        
        console.print(layout)
    
class Manager:
    def __init__(self):
        self.cache = Cache()
        self.database = Database(self.cache)
        self.console = Console()
        
        self.actions = {
            "q": {
                "name": "Quit",
                "function": self.quit
            },
            "s": {
                "name": "Sort By Expense",
                "function": partial(self.database.display, self.console, sort_mode="expense")
            },
            "a": {
                "name": "Sort by Name",
                "function": partial(self.database.display, self.console, sort_mode="alphabet")
            },
            "d": {
                "name": "Sort by Delta Average",
                "function": partial(self.database.display, self.console, sort_mode="delta")
            },
        }
    
    def run(self):
        self.database.display(self.console)
        
        while True:
            response = None
            key = rc.readchar()
            
            if key in self.actions:
                response = self.actions[key]["function"]()
            else:
                continue
        
            if response == "quit":
                break
    
    def quit(self):
        return "quit"
            
        