.DEFAULT_GOAL := usage

usage:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

up: ## コンテナ立ち上げ
	docker-compose up

run: ## app.py走らせる
	docker-compose run --rm app python3 app.py

build: ## Build or rebuild services.
	docker-compose build

stop: ## Stop running containers without removing them.
	docker-compose stop
