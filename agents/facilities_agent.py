from agents.common import BaseLayerAgent


class FacilitiesAgent(BaseLayerAgent):
    def __init__(self) -> None:
        super().__init__(name="FacilitiesAgent", focus_layer="L6")

