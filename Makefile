.PHONY: all clean fclean re tests_run

all: my_pgp

my_pgp: src/my_pgp.py
	cp $< $@
	chmod +x $@

clean:
	rm -rf src/__pycache__ tests/__pycache__

fclean: clean
	rm -f my_pgp

re: fclean
	$(MAKE) all

tests_run: all
	python3 -m unittest discover -s tests -v
