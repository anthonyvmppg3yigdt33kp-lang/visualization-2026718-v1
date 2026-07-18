import matplotlib.pyplot as plt
import pandas as pd

from recipe import add_repel_labels


labels = pd.DataFrame({"x": [0, 0.01, 0.02], "y": [0, 0.005, 0.01], "name": ["A", "B", "C"]})
figure, axes = plt.subplots()
axes.scatter(labels["x"], labels["y"])
add_repel_labels(axes, labels, "x", "y", "name", method="deterministic")
figure.canvas.draw()
assert axes._plot_code_retriever_label_engine == "deterministic_matplotlib"
assert len(axes.texts) == len(labels)
