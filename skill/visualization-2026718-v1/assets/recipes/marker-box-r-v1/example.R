source("recipe.R")
p <- ggplot2::ggplot(mtcars, ggplot2::aes(factor(cyl), factor(gear))) + ggplot2::geom_point()
p <- add_marker_box(p, 0.5, 1.5, 0.5, 2.5)
