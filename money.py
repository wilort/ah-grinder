from dataclasses import dataclass

@dataclass
class Money:
    """
    Example usage:
    money_obj = Money(value=12345)
    """
    value: int
    gold: int = 0
    silver: int = 0
    copper: int = 0

    def __post_init__(self):
        self.value = int(self.value)

        self.gold, remaining_value = divmod(abs(self.value), 10000)  # 1 gold = 10000 value
        self.silver, self.copper = divmod(remaining_value, 100)  # 1 silver = 100 value, 1 copper = 1 value

        if self.value < 0:
            self.gold = -self.gold
            self.silver = -self.silver
            self.copper = -self.copper

    def __str__(self):
        return f"{self.gold}g,{self.silver}s,{self.copper}c"