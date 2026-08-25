MAIN = main
LATEXMK = latexmk -xelatex -interaction=nonstopmode
.PHONY: all clean distclean
all: $(MAIN).pdf
$(MAIN).pdf: $(MAIN).tex
	$(LATEXMK) $(MAIN).tex
clean:
	latexmk -c; rm -f *.synctex.gz *.fls *.fdb_latexmk
distclean: clean
	rm -f $(MAIN).pdf
