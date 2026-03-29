VENV_BIN := ./venv/bin
ALEMBIC := $(VENV_BIN)/alembic
MSG ?= auto

.PHONY: makemigrations migrate downgrade current history

makemigrations:
	$(ALEMBIC) revision --autogenerate -m "$(MSG)"

migrate:
	$(ALEMBIC) upgrade head

downgrade:
	$(ALEMBIC) downgrade -1

current:
	$(ALEMBIC) current

history:
	$(ALEMBIC) history
