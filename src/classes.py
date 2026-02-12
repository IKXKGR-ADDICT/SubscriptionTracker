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
from rich.prompt import Prompt, FloatPrompt, Confirm
from time import sleep

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
    
    def get_name(self):
        return self.name
    
    def set_name(self, name):
        self.name = name
    
    def set_expense(self, expense):
        self.expense = expense

class Database:
    def __init__(self, cache: Cache, init_subscription: Subscription = None):
        self.cache = cache
        self.path = self.cache.get_config().get("general", "data")
        
        self.data: dict[str, Subscription] = {}
        self.statistics: dict = {}
        
        with open(self.path, "r") as file:
            self.raw: dict = json.load(file)
        
        self.empty = not bool(self.raw)
        self.valid = True
        
        if self.empty and not init_subscription:
            self.valid = False
            return
        elif self.empty:
            self.add_subscription(init_subscription.get_name(), init_subscription.get_expense())
            
        self.init_subscriptions()
        self.init_stats()
    
    def __bool__(self):
        return self.valid
    
    def init_subscriptions(self):
        pre_data = {}
        
        for name in self.raw:
            expense = float(self.raw[name]["expense"])
            
            pre_data[name] = Subscription(name, expense)
            self.data = pre_data
        
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
    
    def update_database(self):
        with open(self.cache.get_config().get("general", "data"), "w") as file:
            json.dump(self.raw, file)
        
        self.init_subscriptions()
        self.init_stats()
    
    def update_subscription(self, name, expense):
        if name in self.raw:
            self.raw[name] = {"expense": expense}
        else:
            raise IndexError
        
        self.update_database()
        
    def add_subscription(self, name, expense):
        if name in self.raw:
            return

        self.raw[name] = {"expense": expense}
        
        self.update_database()
    
    def remove_subscription(self, name):
        if name in self.raw:
            del self.raw[name]
        else:
            raise IndexError
        
        self.update_database()
        
    def get_subscription_names(self):
        return list(self.raw.keys())

    def get_subscription(self, name) -> Subscription:
        if name in self.data:
            return self.data[name]

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
        
        stat_table.add_column("Stat", justify="right")
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
        
        if not self.database:
            self.console.print("[red]Json file is empty. Asking user to fill initial details...[/red]")
            sleep(2)
            
            details = self.add_subscription(call_database=False)
            subscription = Subscription(details[0], details[1])
            
            self.database = Database(self.cache, subscription)
            
        self.actions_menu = []
        
        self.actions = {
            "q": {
                "name": "Quit",
                "function": self.quit
            },
            "s": {
                "name": "Sort By Expense",
                "function": partial(self.database.display, self.console, sort_mode="expense")
            },
            "n": {
                "name": "Sort by Name",
                "function": partial(self.database.display, self.console, sort_mode="alphabet")
            },
            "d": {
                "name": "Sort by Delta Average",
                "function": partial(self.database.display, self.console, sort_mode="delta")
            },
            "a": {
                "name": "Add Subscription",
                "function": partial(self.add_subscription, force_input=False)
            },
            "r": {
                "name": "Remove",
                "function": self.remove_subscription
            },
            "u": {
                "name": "Update",
                "function":self.update_subscription
            }
        }
        
        self.init_action_menu()
    
    def __prompt_name(self, choices:list[str] = None) -> str:
        name = None
        
        while not name:
            name = Prompt.ask("[yellow]Enter subscription name[/yellow]", console=self.console, choices=choices, show_choices=True, case_sensitive=False)
        
        return name.strip().lower().replace(" ", "_")

    def __prompt_expense(self) -> float:
        expense = None
        
        while True:
            expense = FloatPrompt.ask("[yellow]Enter expense[/yellow]", console=self.console, default=0,)
            
            if expense <= 0 or expense == None:
                continue
            else:
                break
        
        time_mul = {
            "daily": 30.4167,
            "yearly": 1/12,
            "monthly": 1
        }[Prompt.ask("Enter expense rate: ", choices=["daily", "yearly", "monthly"], show_choices=True, case_sensitive=False).lower().strip()]
        
        return round(time_mul * expense, 3)
    
    def validate_subscription_details(self, name, expense, force_input) -> tuple[str, float] | None:
        self_name = name
        self_expense = expense
        
        while True:
            self.console.print(f"[yellow]Name[/yellow]: {self_name.title().replace("_", " ")}")
            self.console.print(f"[yellow]Expense[/yellow]: {self_expense}")
            
            confirm = Prompt.ask(
                "Ensure the details are correct. Type the field you'd like to change, or type 'confirm' to confirm", 
                choices=["name", "confirm", "expense"] if force_input else ["name", "confirm", "expense", "cancel"],
                case_sensitive=False).lower().strip()
            
            os.system("cls")
            
            if confirm == "name":
                self_name = self.__prompt_name()
            elif confirm == "expense":
                self_expense = self.__prompt_expense()
            elif confirm == "cancel":
                return
            else:
                break
                
            os.system("cls")
        
        return (self_name, self_expense)
    
    def add_subscription(self, call_database: bool = True, force_input=True) -> tuple[str, float] | None:
        os.system("cls")
        
        name = self.__prompt_name()
        expense = self.__prompt_expense()
        
        os.system("cls")
        final_details = self.validate_subscription_details(name, expense, force_input)
        
        if not final_details:
            return
    
        if call_database:
            self.database.add_subscription(final_details[0], final_details[1])
            
        return final_details

    def remove_subscription(self):
        os.system("cls")
        confirm = False
        
        while not confirm:
            self.database.display(console=self.console)
            name = self.__prompt_name(self.database.get_subscription_names())
            
            confirm = Confirm.ask("Are these correct?")
        
        self.database.remove_subscription(name)
    
    def update_subscription(self):
        self.database.display(console=self.console)
        name = self.__prompt_name(choices=self.database.get_subscription_names()).strip().lower().replace(" ", "_")
        
        os.system("cls")
        details = self.validate_subscription_details(name, self.database.get_subscription(name).get_expense(), False)
        
        if not details:
            raise IndexError
        
        self.database.update_subscription(details[0], details[1])
        
    def init_action_menu(self):
        for key in self.actions:
            self.actions_menu.append(f"[bright cyan]({key.upper()})[/bright cyan] [yellow]{self.actions[key]["name"]}[/yellow]")
        
        self.actions_menu = Panel("   ".join(self.actions_menu), title="Keybinds")
        
    def run(self):
        while True:
            self.database.display(self.console)
            self.console.print(self.actions_menu)
            
            response = None
            key = rc.readchar()
            
            os.system("cls")
            if key in self.actions:
                response = self.actions[key]["function"]()
            else:
                continue
        
            if response == "quit":
                break
            os.system("cls")
    
    def quit(self):
        return "quit"