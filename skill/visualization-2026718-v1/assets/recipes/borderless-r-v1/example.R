source("recipe.R")
p <- ggplot2::ggplot(mtcars, ggplot2::aes(wt, mpg)) + ggplot2::geom_point()
p <- remove_plot_frame(p)
