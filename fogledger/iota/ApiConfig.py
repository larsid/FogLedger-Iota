from .NodeConfig import (NodeConfig)
from typing import Dict

class ApiConfig(NodeConfig):
    def __init__(self, name: str, port_bindings: Dict[str, str],  ip:str=None):
        super().__init__(name, port_bindings, ip)