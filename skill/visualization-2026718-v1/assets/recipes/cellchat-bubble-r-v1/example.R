source("recipe.R")
communication <- utils::read.csv("cellchat_communication.csv", check.names = FALSE)
plot_cellchat_bubble(communication, top_n = 30, p_threshold = 0.05)
