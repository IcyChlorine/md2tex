字体族：类似字体。之所以叫“族”，是因为英文中很多字体除了标准体之外还有配套的粗体、斜体、不同大小的字体。共同配套，就形成了一个“字体族”。

latex中三个基础的字体族分别是：

`\rmfamily` Roman Family, 罗马字体。可以用`\setroman

`\ttfamily` (Tele)Typewriter Family, 打字机字体。为了适应打字机，因此打字机字体是等宽的。这使得这种字体也更适合编程。作为等宽字体，因此又被叫做monospace。

`\sffamily` Sans serif Family, 无衬线字体。这看上去有些难以理解。衬线是指字体笔画末尾处的那种小横笔。无衬线字体，顾名思义就是无衬线的字体。那为什么叫sans serif呢？在英文中，serif就是衬线的意思。sans则源自法语，是without的意思。所以sans serif其实不是某个冠名字体，而是“无衬线”的字面意思。



在latex中通过引入`fontspec`宏包

`\usepackage{fontspec}`

可以修改三个字体族的实际字体。

修改Roman family，命令是`\setmainfont{Times New Roman}`.从“main”可以看出，罗马体在英文排版中的中心地位。

修改Typewriter family，命令是`\setmonofont`。这将默认的字机字体为某个具体的等宽字体。例如：`\setmonofont{Consolas}`将`\ttyfamily`代表的等宽字体族更改为著名的Consolas字体。注意，命令中是“mono”，而不是“tt”，这是表示等宽(monospace)的意思。

修改Sans serif family, 命令是`\setsansfamily`.



如果在ctex中用中文排版，三个命令分别为：

`\setCJKmainfont`,`\setCJKmonofont`,`\setCJKsansfont`.



参考：

1. Wikipedia: Sans-serif, serif, typeface, typography, etc.
2. latex字体设置，https://www.jianshu.com/p/68da21a1501a
3. LaTex学习笔记1 字体属性，https://blog.csdn.net/qq_41647438/article/details/107233310

