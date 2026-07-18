import matplotlib.pyplot as plt
from recipe import export_publication_figure

figure, axes = plt.subplots()
axes.scatter([0, 1], [0, 1])
# Explicit execution only: export_publication_figure(figure, "figure.pdf", 3.5, 3.0)
