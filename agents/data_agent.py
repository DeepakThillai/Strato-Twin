from agents.common import BaseLayerAgent


class DataAgent(BaseLayerAgent):
    def __init__(self) -> None:
        super().__init__(name="DataAgent", focus_layer="L4")

