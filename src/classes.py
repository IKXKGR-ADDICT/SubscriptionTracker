import configparser as cfg
import json
import os
from rich.console import Console
from rich.table import Table
from rich import box
import statistics as stat

class Cache:
    def __init__(self):
        config_path = r"assets/config/config.cfg"
        
        with open(config_path, "r") as file:
            self.config = cfg.ConfigParser()
            
            files_read = self.config.read(file)
            
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
        return self.name.title().strip()
    
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
    
    def get_expense(self):
        return self.expense

class Database:
    def __init__(self, cache: Cache):
        self.cache = cache
        self.path = self.cache.get_config().get("general", "data")
        
        with open(self.path, "r") as file:
            self.data: dict[str, Subscription] = json.load(file)
        
    def init_data(self):
        self.max = max(self.data, key=lambda key: self.data[key].get_expense())
        self.min = min(self.data, key=lambda key: self.data[key].get_expense())
        self.avg = stat.mean(self.data)
    
        
    def display(self):
        os.system("cls")
        
        table = Table(
            box=box.SIMPLE_HEAD
        )
        
        table.add_column("Name")
        table.add_column("Expense")
        table.add_column("Delta Avg")

class Manager:
    def __init__(self):
        self.cache = Cache()
        self.database = Database(self.cache)
        self.console = Console()
            
            
        