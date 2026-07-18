import matplotlib.pyplot as plt
from recipe import remove_axes_frame

figure, axes = plt.subplots()
axes.scatter([0, 1], [0, 1])
remove_axes_frame(axes)
