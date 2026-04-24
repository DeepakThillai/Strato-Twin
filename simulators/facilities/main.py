import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from simulators.base_simulator import run_layer_simulator


if __name__ == "__main__":
    run_layer_simulator("L6")

