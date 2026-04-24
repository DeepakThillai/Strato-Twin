from agents.common import BaseLayerAgent


class NetworkAgent(BaseLayerAgent):
    def __init__(self) -> None:
        super().__init__(name="NetworkAgent", focus_layer="L1")

