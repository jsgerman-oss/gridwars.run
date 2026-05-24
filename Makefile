.PHONY: help install migrate run stop test

GAMEDIR := gridwars

help: ## Print this target list
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*##"}; {printf "  %-10s %s\n", $$1, $$2}'

install: ## Create .venv (python3.12) if missing, then pip-install vendored Evennia
	@if [ ! -d .venv ]; then \
		python3.12 -m venv .venv; \
	fi
	.venv/bin/pip install --upgrade pip setuptools wheel
	.venv/bin/pip install -e ./vendor/evennia

migrate: ## Run Evennia DB migrations (non-interactive; use make createsuperuser afterwards)
	cd $(GAMEDIR) && DJANGO_SETTINGS_MODULE=server.conf.settings \
		$(CURDIR)/.venv/bin/python -m django migrate
	@echo ""
	@echo "Migrations applied. If this is your first run, create a superuser with:"
	@echo "  make createsuperuser"

createsuperuser: ## Create the #1 superuser account interactively
	cd $(GAMEDIR) && PATH="$(CURDIR)/.venv/bin:$$PATH" evennia createsuperuser

run: ## Start the Evennia server
	cd $(GAMEDIR) && PATH="$(CURDIR)/.venv/bin:$$PATH" evennia start

stop: ## Stop the Evennia server
	cd $(GAMEDIR) && PATH="$(CURDIR)/.venv/bin:$$PATH" evennia stop

test: ## Run the Evennia test harness against gridwars/
	cd $(GAMEDIR) && PATH="$(CURDIR)/.venv/bin:$$PATH" evennia test .
