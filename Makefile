venv:
	rm -rf .venv
	python3 -m venv .venv
	@echo "Run 'source .venv/bin/activate' to activate the virtual environment"

list:
	pip list -v

install:
	pip install jupyter
	pip install -r requirements.txt 

run:
	jupyter notebook