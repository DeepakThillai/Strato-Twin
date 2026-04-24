from agents.common import BaseLayerAgent


class ComputeAgent(BaseLayerAgent):
    def __init__(self) -> None:
        super().__init__(name="ComputeAgent", focus_layer="L2")

