source("recipe.R")
labels <- transform(mtcars[1:5, ], name = rownames(mtcars)[1:5])
p <- ggplot2::ggplot(mtcars, ggplot2::aes(wt, mpg)) + ggplot2::geom_point()
p <- add_repel_labels(p, labels, "wt", "mpg", "name")
