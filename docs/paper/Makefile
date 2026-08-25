# 技术报告一键编译（XeLaTeX + BibTeX）
# 用法: make          -> 编译 main.pdf
#       make doctor   -> 检查本地 LaTeX 工具链和 GB/T 7714 样式
#       make clean    -> 清理中间文件
#       make distclean -> 清理含 pdf
MAIN = main
LATEXMK = latexmk -xelatex -interaction=nonstopmode -file-line-error

.PHONY: all build clean distclean check doctor

all: build

# 每次显式交给 latexmk 判断 LaTeX/BibTeX/目录/交叉引用依赖，
# 不让 make 仅凭 main.pdf 的时间戳跳过完整编译链。
build:
	$(LATEXMK) $(MAIN).tex

clean:
	latexmk -c
	rm -f *.synctex.gz *.fls *.fdb_latexmk

distclean: clean
	rm -f $(MAIN).pdf $(MAIN).bbl

doctor:
	@echo "== executables =="
	@command -v xelatex >/dev/null && xelatex --version | head -1 || (echo "ERROR: xelatex not found"; exit 1)
	@command -v latexmk >/dev/null && latexmk -v | head -2 || (echo "ERROR: latexmk not found"; exit 1)
	@command -v bibtex >/dev/null && bibtex --version | head -1 || (echo "ERROR: bibtex not found"; exit 1)
	@echo "== bibliography style =="
	@BST="$$(kpsewhich gbt7714-numerical.bst)"; \
	 if [ -n "$$BST" ]; then echo "OK: $$BST"; \
	 else echo "ERROR: gbt7714-numerical.bst not found"; \
	      echo "Linux Mint/Ubuntu: sudo apt install texlive-bibtex-extra"; exit 1; fi
	@echo "== Chinese class =="
	@CTEX="$$(kpsewhich ctexart.cls)"; \
	 if [ -n "$$CTEX" ]; then echo "OK: $$CTEX"; \
	 else echo "ERROR: ctexart.cls not found"; \
	      echo "Linux Mint/Ubuntu: sudo apt install texlive-lang-chinese texlive-xetex"; exit 1; fi

check:
	@echo "== 未定义引用/标签 =="; grep -E "undefined|multiply defined" $(MAIN).log || echo "ok"
	@echo "== 匿名检查 =="; ! grep -inE "大学|学院|学校|导师|指导教师|校徽|学号" $(MAIN).tex || echo "WARN: 命中匿名违禁词，请检查"
