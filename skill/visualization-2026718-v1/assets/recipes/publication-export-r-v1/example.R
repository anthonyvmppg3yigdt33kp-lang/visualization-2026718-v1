source("recipe.R")
p <- ggplot2::ggplot(mtcars, ggplot2::aes(wt, mpg)) + ggplot2::geom_point()
# Explicit execution only: export_publication_plot(p, "figure.pdf", width = 3.5, height = 3.0)
