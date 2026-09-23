.PHONY: all clean fclean re tests_run

all: my_pgp

my_pgp: $(wildcard src/*.py) Makefile
	printf '%s\n' '#!/bin/sh' 'exec python3 "$$(dirname "$$0")/src/my_pgp.py" "$$@"' > $@
	chmod +x $@

clean:
	rm -rf src/__pycache__ tests/__pycache__

fclean: clean
	rm -f my_pgp

re: fclean
	$(MAKE) all

tests_run: all
	python3 -m unittest discover -s tests -v
