from agents.common import BaseLayerAgent


class ApplicationAgent(BaseLayerAgent):
    def __init__(self) -> None:
        super().__init__(name="ApplicationAgent", focus_layer="L3")

