from agents.common import BaseLayerAgent


class WorkforceAgent(BaseLayerAgent):
    def __init__(self) -> None:
        super().__init__(name="WorkforceAgent", focus_layer="L5")

