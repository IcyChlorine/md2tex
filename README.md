# md2tex

![](md2tex.png)

**md2tex** is a python tool that converts markdown source into latex source codes, while preserving most of the important formats such as titles, sections and formulas.

### Initiative

**Latex** is the standard and most powerful typesetting software within the domain of science and technology, but it is relatively difficult to write latex codes. On the other hand, **markdown** is a lightweight mark language that is easier to edit. Thanks to `typora`, markdown can be rendered in real-time and make its editing much easier. Lightweight as it is though, markdown still supports most elements for writing an elegant article or technical note, such as subtitle, formula and code environment, enumerate environment and etc. 

Realizing that latex and markdown share a lot of features and functions, I started to ponder whether I can write a markdown to latex convertor, so that I can enjoy the merits of both latex and markdown. So I started working on this project. Now md2tex can convert most of the markdown features that I use into latex, which is quite helpful.

### How to use

Python environment is required. It is quite simple to use: 

```
py md2tex.py <input_filename> [-o <output_filename>]
```

The program reads in a markdown source file (`*.md`) and outputs a latex source file(`*.tex`). Note that the output file is still a latex source file and further compilation is needed to get a pdf file. 

### Some Notes

I personally use vscode to further edit and compile latex source into final files. My vscode settings for latex is in `./vscode_sample_for_latex/` directory as reference.

There're some demo cases that you can refer to in `./demo/`. You can also try to convert this `README.md` file into latex to see what will happen.

Note that `md2tex` doesn't guarantee that the generated latex code is compliable. It only converts the key elements and there maybe subtle bugs(usually rare) that have to be handled manually.

`md2tex` is built to **customizable**.  You can easily customize the generated latex source by modifying `sym2tex_template.json`. For example, you can change the preamble to be generated by doing this.

***

### What it can do

Listed below are formats that `md2tex` can convert now:

+ Title
+ Section
+ *Italic* and **Bold** texts
+ Formula
+ Code (multi-line only)
+ Figure
+ "\newcommand" control sequence in formula
+ Delim lines
+ Enumerations(such as the one here)
+ Quotation(recognizable but can't transform)

See `./demo/` to get see some of the formats above converted into latex sources.

### What it can not do

There're also some known formats that `md2tex` can't convert/can't handle properly for the time being:

+ Nested Enumerations
+ Inline code sectors(they will be left unchanged, and there's plan to support it in future versions)
+ lines begin with "### " in code environment will be falsefully recognized as section
+ Special math environment , such as `\beign{align}` in multiline formulas
+ italic and bold environments that interleaves with each other(even in typora this cannot be correctly recognized, actually)

### Some additional notes

**Q**: How it works?
**A**: `md2tex` first parse markdown source files into an intermediate representation, that convert the intermediate representation to latex source files. Modify `DEBUG_PRINT` as `True` in `constants.py` to see the intermediate representations.

**Q**: What's its difference from pandoc?
**A**: It's widely known that typora has a built-in link for markdown-to-latex convertor, which leads to a tool called `pandoc`. `pandoc` can convert markdown source into latex as well, but there's a few differences between this project and`pandoc`.

`pandoc` try to convert all details and formats from markdown to latex, but this will make the generated latex obscure and sometimes hard to compile. On the other hand, `md2tex` only try to convert the most elementary elements into latex, so the code generated will be clearer, simpler and easier to read or compile. 

Moreover, `md2tex` is built to be customizable. You can easily customize the generated latex source by changing `md2sym_template.json` and `sym2tex_template.json`.

