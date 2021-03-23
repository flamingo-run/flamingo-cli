setup:
	@pip install -U pip poetry
	@poetry config pypi-token.pypi $(PYPI_API_TOKEN)

dependencies:
	@make setup
	@poetry install --no-root --extras "tasks build storage bigquery speech sheets pubsub datastore dns monitoring"

update:
	@poetry update

check:
	@poetry check

lint:
	@echo "Checking code style ..."
	@poetry run pylint --rcfile=./.pylintrc flamingo

clean:
	@rm -rf .coverage coverage.xml dist/ build/ *.egg-info/

publish:
	@make clean
	@printf "\nPublishing lib"
	@make setup
	@poetry publish --build
	@make clean


.PHONY: setup dependencies update test check lint clean publish
