# 基本功修炼：Chord diagram  和弦图的基础函数

- 专辑：绘图小技巧2025
- 公众号：生信技能树
- 发布时间：2025-07-24 22:58
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247544490&idx=1&sn=9a3e5918921f89126470514d7516094e&chksm=9b4b6e11ac3ce70784d404a3180d1a08986cc5e9fbdb995ff12141d37b8f6f139b8173d570c1)

---
> 前面我收集了一堆单细胞通讯结果可视化的美图：[cellchat细胞通讯绘制弦图函数的参数这么难搞定吗？](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247542658&idx=1&sn=adabcd404adc4cd33d3991909888ec76#wechat_redirect)。然后去绘制的时候，发现很多地方不能自如的调整细节，现在去修炼一下内功：学习Chord diagram  和弦图的绘制~ 来看看啊

此外，我们生信技能树**每个月都有一期带领初学者，0基础的生信入门培训，会有各种贴心的答疑，最新一期在8月4号**，感兴趣的可以去看看呀：[生信入门&数据挖掘线上直播课8月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247544311&idx=1&sn=d41b5838e799f52280e78703135bb603#wechat_redirect)。

绘制和弦图用的包是circlize，这个包是圈内的大佬做的，大家应该都认识：Zuguang Gu。包的官网给到你，网址

> https://jokergoo.github.io/circlize_book/book/

## Circos 介绍

Circos 可以用来将表格转换成图像。将枯燥的表格转换成信息丰富且视觉上引人入胜的数据图形！

在这种方法中，表格的列和行通过围绕圆周的线段来表示。单个单元格显示为带状物，它们连接相应的行和列线段：

![文章图片 1](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/001.png)

用于表示关系的数据格式有两种：

- 邻接矩阵：在邻接矩阵中，第 *i* 行第 *j* 列的值表示从第 *i* 行对象到第 *j* 列对象的关系，其绝对值衡量关系的强度。

- 邻接列表：在邻接列表中，关系表示为一个三列的数据框，其中第一列表示关系的起点，第二列表示关系的终点，第三列表示关系的强度。

以下是邻接矩阵的一个示例代码：

```r
rm(list=ls())
library(circlize)

mat = matrix(1:9, 3)
rownames(mat) = letters[1:3]
colnames(mat) = LETTERS[1:3]
mat
```

![文章图片 2](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/002.png)

下面的代码是一个邻接列表的示例：

```r
## 邻接列表
df = data.frame(from = letters[1:3], to = LETTERS[1:3], value = 1:3)
df
```

![文章图片 3](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/003.png)

和弦图可以从多个层面展示关系的信息：

- 1.链接直观地展示对象之间的关系；

- 2.链接的宽度与关系的强度成比例，这比其他图形映射更具表现力；

- 3.链接的颜色可以是关系的另一种图形映射；

- 4.扇区的宽度表示一个对象与其他对象连接的总强度，或者被其他对象连接的总强度。

在 circlize 包中，有一个 `chordDiagram()` 函数，它支持邻接矩阵和邻接列表这两种输入格式。对于不同格式的输入，相应的图形参数格式也会有所不同。

## 和弦图的基本用法

首先，生成一个随机矩阵及其对应的邻接列表：

```r
## 生成邻接矩阵
set.seed(999)
mat = matrix(sample(18, 18), 3, 6)
rownames(mat) = paste0("S", 1:3)
colnames(mat) = paste0("E", 1:6)
mat


# 转为邻接列表
df = data.frame(from = rep(rownames(mat), times = ncol(mat)),
                to = rep(colnames(mat), each = nrow(mat)),
                value = as.vector(mat),
                stringsAsFactors = FALSE)
df
```

![文章图片 4](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/004.png)

![文章图片 5](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/005.png)

最简单的绘图：

```r
# 绘图
chordDiagram(mat)
circos.clear()
```

![文章图片 6](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/006.png)

到这里其实就可以开始绘制细胞通讯的和弦图了，细胞通讯的结果很容易就可以转换成上面的邻接矩阵或者邻接列表。

但是为了让图更好看，我们再看学习一些细节调整~

## 修改扇区的顺序

默认的和弦图包括一个标签轨道、一个带有轴的网格轨道（或者你可以称其为线条、矩形）以及链接。与矩阵的行对应的扇区位于圆的下半部分。扇区的顺序是 `union(rownames(mat), colnames(mat))` 或者 `union(df[[1]], df[[2]])`（如果输入是一个数据框）。扇区的顺序可以通过 `order` 参数来控制（见图 14.2，左侧）。当然，`order` 向量的长度应该与扇区的数量相同。

```r
## 修改顺序
par(mfrow = c(1, 2))
mat
chordDiagram(mat, order = c("S2", "S1", "S3", "E4", "E1", "E5", "E2", "E6", "E3"))
circos.clear()

chordDiagram(mat, order = c("S2", "S1", "E4", "E1", "S3", "E5", "E2", "E6", "E3"))
circos.clear()
```

![文章图片 7](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/007.png)

从圆的右中心开始，扇区按顺时针方向排列！

## circos.par()参数调整

由于和弦图是通过 circlize 的基础函数实现的，就像普通的圆形图一样，其布局可以通过 `circos.par()` 来自定义。

可以通过 `circos.par(gap.after = ...)` 设置扇区之间的间隙。当需要区分行和列对应的扇区时，这非常有用。请注意，由于你更改了默认的图形设置，因此在绘图结束时需要使用 `circos.clear()` 来重置它。

```r
## 修改间隔
gap <-  c(rep(5, nrow(mat)-1), 15, rep(5, ncol(mat)-1), 15)
gap
circos.par(gap.after = gap)
chordDiagram(mat)
circos.clear()
```

![文章图片 8](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/008.png)

gap也可以通过指定向量的名字来指定：

```r
## 指定名字对应的gap
circos.par(gap.after = c("S1" = 5, "S2" = 5, "S3" = 15, "E1" = 5, "E2" = 5,
                         "E3" = 5, "E4" = 5, "E5" = 5, "E6" = 15))
chordDiagram(mat)
circos.clear()
```

这个貌似更清晰：

![文章图片 9](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/009.png)

### `big.gap` 参数

为了简化操作，用户可以直接在 `chordDiagram()` 函数中设置 `big.gap` 参数。`big.gap` 的值对应于行扇区和列扇区之间的间隙（或者在输入是数据框时，对应于第一列扇区和第二列扇区之间的间隙）。在内部，`chordDiagram()` 会为 `circos.par()` 分配一个合适的 `gap.after` 参数。

> 请注意，只有当行扇区和列扇区之间没有重叠时，或者换句话说，矩阵的行和列（或数据框的第一列和第二列）代表两个不同的组时，`big.gap` 才会起作用。

```r
## big.gap参数
chordDiagram(mat, big.gap = 30)
circos.clear()
```

![文章图片 10](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/010.png)

### `small.gap` 参数

`small.gap` 参数控制对应于矩阵行或列的扇区之间的间隙。默认值是 1 度，通常你不需要设置它。在组数大于两个的情况下，也可以设置 `big.gap` 和 `small.gap`。

类似于普通的圆形图，第一个扇区（即邻接矩阵的第一行或邻接列表的第一行）从圆的右中心开始，扇区按顺时针方向排列。第一个扇区的起始角度可以通过 `circos.par(start.degree = ...)` 设置，方向可以通过 `circos.par(clock.wise = ...)` 设置。

```r
## small.gap参数
par(mfrow = c(1, 2))
circos.par(start.degree = 85, clock.wise = FALSE)
chordDiagram(mat)
circos.clear()

circos.par(start.degree = 85)
chordDiagram(mat, order = c(rev(colnames(mat)), rev(rownames(mat)))) # 设置所有扇区的逆序
circos.clear()
```

![文章图片 11](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/011.png)

在图 左侧，设置 `circos.par(clock.wise = FALSE)` 使链接变得非常扭曲。实际上，通过设置所有扇区的逆序，也可以实现方向的逆时针反转（见图 右侧）。正如我们所见，左侧图中的链接非常扭曲，而右侧图仍然看起来不错。原因是 `chordDiagram()` 会根据扇区的排列自动优化链接的位置。

## Colors设置

网格有不同的颜色来代表不同的扇区。通常，扇区被分为两组。一组包含矩阵的行或数据框的第一列中定义的扇区，另一组包含矩阵的列或数据框的第二列中定义的扇区。因此，链接连接了这两组中的对象。默认情况下，链接的颜色与第一组中对应扇区的颜色相同。

更改网格的颜色也可能会改变链接的颜色。可以通过 `grid.col` 参数设置网格的颜色。`grid.col` 的值最好是一个命名向量，其名称与扇区名称相对应。

```r
## 修改颜色
grid.col = c(S1 = "red", S2 = "green", S3 = "blue",
             E1 = "grey", E2 = "grey", E3 = "grey", E4 = "grey", E5 = "grey", E6 = "grey")
chordDiagram(mat, grid.col = grid.col)
chordDiagram(t(mat), grid.col = grid.col)
circos.clear()
```

![文章图片 12](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/012.png)

如果它没有名称索引，则假设 `grid.col` 的顺序与扇区的顺序相同。如果你想让颜色与矩阵的列或数据框的第二列中的扇区相同，只需转置矩阵（见图 右侧）。

### 设置连接线的颜色

链接颜色的透明度可以通过 `transparency` 参数来设置。其值应在 0 到 1 之间，其中 0 表示完全不透明，1 表示完全透明。默认的透明度值为 0.5。

```r
## 设置连接线的颜色
grid.col
chordDiagram(mat, grid.col = grid.col, transparency = 0)
circos.clear()
```

![文章图片 13](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/013.png)

对于邻接矩阵，可以通过提供一个颜色矩阵来自定义链接的颜色。在下面的示例中，我们使用 `rand_color()` 函数生成一个随机颜色矩阵。

```r
col_mat = rand_color(length(mat), transparency = 0.5)
dim(col_mat) = dim(mat)  # to make sure it is a matrix
col_mat
chordDiagram(mat, grid.col = grid.col, col = col_mat)
circos.clear()
```

![文章图片 14](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/014.png)

当关系的强度（例如相关性）表示为连续值时，`col` 也可以被指定为一个自定义的颜色映射函数。`chordDiagram()` 接受由 `colorRamp2()` 生成的颜色映射：

```r
## 连续值映射
col_fun = colorRamp2(range(mat), c("#FFEEEE", "#FF0000"), transparency = 0.5)
chordDiagram(mat, grid.col = grid.col, col = col_fun)
circos.clear()
```

![文章图片 15](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/015.png)

有时不需要生成整个颜色矩阵。只需提供与行或列对应的颜色，这样来自同一行/列的链接将具有相同的颜色：

```r
chordDiagram(mat, grid.col = grid.col, row.col = 1:3)
chordDiagram(mat, grid.col = grid.col, column.col = 1:6)
circos.clear()
```

![文章图片 16](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/016.png)

## 连接线的边界

`link.lwd`、`link.lty` 和 `link.border` 控制链接的线宽、线型和链接边框的颜色。如果输入是邻接矩阵，所有这三个参数既可以设置为单个标量值，也可以设置为矩阵。

### 如果设置为单个标量值，则表示所有链接共享相同的样式：

```r
chordDiagram(mat, grid.col = grid.col, link.lwd = 2, link.lty = 2, link.border = "red")
circos.clear()
```

![文章图片 17](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/017.png)

### 如果将其设置为一个矩阵，那么它的维度应该与 `mat` 相同：

```r
lwd_mat = matrix(1, nrow = nrow(mat), ncol = ncol(mat))
lwd_mat[mat > 12] = 2
border_mat = matrix(NA, nrow = nrow(mat), ncol = ncol(mat))
border_mat[mat > 12] = "red"
chordDiagram(mat, grid.col = grid.col, link.lwd = lwd_mat, link.border = border_mat)
circos.clear()
```

![文章图片 18](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/018.png)

它也可以是一个子矩阵（见图 14.13）。对于那些在矩阵中未指定对应值的行或列，将填充默认值。它必须具有行名称和列名称，以便能够将设置映射到正确的链接：

```r
border_mat2 = matrix("black", nrow = 1, ncol = ncol(mat))
rownames(border_mat2) = rownames(mat)[2]
colnames(border_mat2) = colnames(mat)
chordDiagram(mat, grid.col = grid.col, link.lwd = 2, link.border = border_mat2)
circos.clear()
```

![文章图片 19](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/019.png)

为了更加方便，图形参数可以设置为一个三列的数据框，其中前两列对应矩阵中的行名和列名，第三列对应图形参数：

```r
lty_df = data.frame(c("S1", "S2", "S3"), c("E5", "E6", "E4"), c(1, 2, 3))
lwd_df = data.frame(c("S1", "S2", "S3"), c("E5", "E6", "E4"), c(2, 2, 2))
border_df = data.frame(c("S1", "S2", "S3"), c("E5", "E6", "E4"), c(1, 1, 1))
lty_df
lwd_df
border_df

chordDiagram(mat, grid.col = grid.col, link.lty = lty_df, link.lwd = lwd_df,
             link.border = border_df)
circos.clear()
```

![文章图片 20](assets/031_基本功修炼：Chord%20diagram%20和弦图的基础函数/020.png)

开心，今天学习到这里。

下期就来画这里面好看的图：[cellchat细胞通讯绘制弦图函数的参数这么难搞定吗？](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247542658&idx=1&sn=adabcd404adc4cd33d3991909888ec76#wechat_redirect)

#### 文末友情宣传

强烈建议你推荐给身边的**博士后以及年轻生物学PI**，多一点数据认知，让他们的科研上一个台阶：

- [生信入门&数据挖掘线上直播课8月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247544311&idx=1&sn=d41b5838e799f52280e78703135bb603#wechat_redirect)，你的生物信息学入门课

- [时隔5年，我们的生信技能树VIP学徒继续招生啦](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247525079&idx=1&sn=0b997af16a58195b4192691373048fd5#wechat_redirect)

- [满足你生信分析计算需求的低价解决方案](https://mp.weixin.qq.com/s?__biz=MzUzMTEwODk0Ng%3D%3D&mid=2247530048&idx=1&sn=28aa7bbd5e00521f79e074496a5f5d66#wechat_redirect)

- [生信故事会](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=1679199708449144836#wechat_redirect)，来看看他们的生信入门故事

- [生信马拉松答疑专辑](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=3690970204957147140#wechat_redirect)，获取你的生信专属答疑

<!-- wechat-article-fetcher: complete -->
