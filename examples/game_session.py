from typing import List


class PlayerCharacter:
    """玩家角色类，保存HP和位置状态"""
    
    def __init__(self, name: str):
        self.name = name
        self.hp = 100
        self.position = [0, 0]
        self.inventory = []

    def move(self, x: int, y: int) -> str:
        """移动角色"""
        self.position[0] += x
        self.position[1] += y
        return f"{self.name} 移动到了 {self.position}"

    def take_damage(self, amount: int) -> int:
        """受到伤害"""
        self.hp -= amount
        return self.hp

    def add_item(self, item: str) -> List[str]:
        """添加物品到背包"""
        self.inventory.append(item)
        return self.inventory

# 工厂函数：这是 LLM 的入口点
def create_character(name: str) -> PlayerCharacter:
    """
    创建一个新的游戏角色。
    
    返回的是一个复杂对象，allbemcp 会自动将其存储在内存中，
    并返回一个 object_id 给 LLM。
    """
    return PlayerCharacter(name)