source("recipe.R")
p1 <- ggplot2::ggplot(mtcars, ggplot2::aes(wt, mpg, colour = factor(cyl))) + ggplot2::geom_point()
p2 <- ggplot2::ggplot(mtcars, ggplot2::aes(disp, hp, colour = factor(cyl))) + ggplot2::geom_point()
combined <- compose_shared_legend(list(p1, p2))
