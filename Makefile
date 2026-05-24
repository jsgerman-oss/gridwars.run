.PHONY: help install migrate run stop test

help: ## Print this target list
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*##"}; {printf "  %-10s %s\n", $$1, $$2}'

install: ## Create .venv (python3.12) if missing, then pip-install vendored Evennia
	@if [ ! -d .venv ]; then \
		python3.12 -m venv .venv; \
	fi
	.venv/bin/pip install --upgrade pip setuptools wheel
	.venv/bin/pip install -e ./vendor/evennia

migrate: ## Run Evennia DB migrations
	.venv/bin/evennia migrate

run: ## Start the Evennia server (foreground)
	.venv/bin/evennia start

stop: ## Stop the Evennia server
	.venv/bin/evennia stop

test: ## Run the Evennia test harness against gridwars/
	.venv/bin/evennia test gridwars
