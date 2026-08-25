# 技术报告一键编译（XeLaTeX + BibTeX）
# 用法: make        -> 编译 main.pdf
#       make clean  -> 清理中间文件
#       make distclean -> 清理含 pdf
MAIN = main
LATEXMK = latexmk -xelatex -interaction=nonstopmode

.PHONY: all clean distclean check

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex refs.bib
	$(LATEXMK) $(MAIN).tex

clean:
	latexmk -c
	rm -f *.synctex.gz *.fls *.fdb_latexmk

distclean: clean
	rm -f $(MAIN).pdf $(MAIN).bbl

check:
	@echo "== 未定义引用/标签 =="; grep -E "undefined|multiply defined" $(MAIN).log || echo "ok"
	@echo "== 匿名检查 =="; ! grep -inE "大学|学院|学校|导师|指导教师|校徽|学号" $(MAIN).tex || echo "WARN: 命中匿名违禁词，请检查"
