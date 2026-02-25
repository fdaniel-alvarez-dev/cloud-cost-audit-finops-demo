.PHONY: bootstrap demo report dashboard verify clean

PYTHON := .venv/bin/python
PIP := .venv/bin/pip

bootstrap:
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

demo:
	$(PYTHON) -m cloud_cost_audit.cli demo --config config/demo.yaml

report:
	$(PYTHON) -m cloud_cost_audit.cli report --config config/demo.yaml

dashboard:
	$(PYTHON) -m cloud_cost_audit.cli dashboard --config config/demo.yaml

verify:
	$(PYTHON) -m ruff format --check .
	$(PYTHON) -m ruff check .
	$(PYTHON) -m mypy cloud_cost_audit tests
	$(PYTHON) -m pytest --cov=cloud_cost_audit

clean:
	rm -rf .venv out data/generated
