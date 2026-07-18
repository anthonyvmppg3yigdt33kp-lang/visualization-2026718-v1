source("recipe.R")
p <- ggplot2::ggplot(mtcars, ggplot2::aes(wt, mpg)) + ggplot2::geom_point() + ggplot2::theme_classic()
p <- add_arrow_axes(p)
