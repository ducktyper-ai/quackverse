# Terminal colors
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)
BLUE   := $(shell tput -Txterm setaf 4)

# Project settings
PYTHON_VERSION := 3.13
VENV_NAME := .venv
PROJECT_NAME := quackcore
REPO_ROOT := $(shell pwd)
PYTHON := $(REPO_ROOT)/$(VENV_NAME)/bin/python

# Test settings
TEST_PATH := tests/
PYTEST_ARGS ?= -v
COVERAGE_THRESHOLD := 90

RUN_ARGS ?= --help

help: ## Show this help message
	@echo ''
	@echo '${YELLOW}Development Guide${RESET}'
	@echo ''
	@echo '${YELLOW}Installation Options:${RESET}'
	@echo '  Tutorial:    ${GREEN}make install-tutorial${RESET}   - Install quackcore'
	@echo '  All:        ${GREEN}make install-all${RESET}        - Install both packages'
	@echo '  Development:${GREEN}make install-dev${RESET}        - Development tools'
	@echo ''
	@echo '${YELLOW}Development Workflow:${RESET}'
	@echo '  1. Setup:     ${GREEN}make setup${RESET}         - Full development environment'
	@echo '  2. Source:    ${GREEN}source setup.sh${RESET}    - Activate environment'
	@echo '  3. Install:   ${GREEN}make install-all${RESET}   - Install packages'
	@echo ''
	@echo '${YELLOW}Available Targets:${RESET}'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  ${YELLOW}%-15s${GREEN}%s${RESET}\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ''

# Development environment targets
.PHONY: env
env: ## Create virtual environment using uv
	@echo "${BLUE}Creating virtual environment...${RESET}"
	uv venv --python $(PYTHON_VERSION)
	@echo "${GREEN}Virtual environment created. Activate it with:${RESET}"
	@echo "source $(VENV_NAME)/bin/activate"

.PHONY: install-quackcore
install-quackcore: ## Install quackcore package
	@echo "${BLUE}Installing quackcore package...${RESET}"
	cd quackcore && uv pip install -e .
	@echo "${GREEN}quackcore installed successfully${RESET}"
	@# Verify installation
	@$(PYTHON) -c "import quackcore; print(f'quackcore installed at: {quackcore.__file__}')"

.PHONY: install-ducktyper
install-ducktyper: install-quackcore ## Install ducktyper package
	@echo "${BLUE}Installing ducktyper package...${RESET}"
	cd ducktyper && uv pip install -e .
	@echo "${GREEN}ducktyper installed successfully${RESET}"
	@# Verify installation
	@$(PYTHON) -c "import ducktyper; print(f'ducktyper installed at: {ducktyper.__file__}')"

.PHONY: install-quackster
install-quackster: install-quackcore ## Install quackster package
	@echo "${BLUE}Installing quackster package...${RESET}"
	cd quackster && uv pip install -e .
	@echo "${GREEN}quackster installed successfully${RESET}"
	@# Verify installation
	@$(PYTHON) -c "import quackster; print(f'quackster installed at: {quackster.__file__}')"

.PHONY: install-all
install-all: install-quackcore install-ducktyper install-quackster ## Install all packages with their optional dependencies
	@echo "${BLUE}Installing optional dependencies for all packages...${RESET}"
	cd quackcore && uv pip install -e ".[gmail,notion,google,drive,pandoc,llms,ducktyper, github]"
	cd ducktyper && uv pip install -e ".[all]"
	cd quackster && uv pip install -e ".[all]"
	@echo "${GREEN}All packages and dependencies installed successfully${RESET}"

.PHONY: install-dev
install-dev: ## Install development dependencies for all packages
	@echo "${BLUE}Installing development tools...${RESET}"
	cd quackcore && uv pip install -e ".[dev]"
	cd ducktyper && uv pip install -e ".[dev]"
	cd quackster && uv pip install -e ".[dev]"
	uv pip install -e ".[dev]"
	@echo "${GREEN}Development dependencies installed successfully${RESET}"

.PHONY: setup
setup: ## Create environment and install full development dependencies
	@echo "${BLUE}Creating complete development environment...${RESET}"
	@echo '#!/bin/bash' > setup.sh
	@echo 'uv venv --python $(PYTHON_VERSION)' >> setup.sh
	@echo 'source $(VENV_NAME)/bin/activate' >> setup.sh
	@echo 'make install-all' >> setup.sh
	@echo 'make install-dev' >> setup.sh
	@echo 'echo "${GREEN}Setup complete! Development environment ready.${RESET}"' >> setup.sh
	@echo 'rm "$$0"' >> setup.sh
	@chmod +x setup.sh
	@echo "${GREEN}Environment setup script created. To complete setup, run:${RESET}"
	@echo "${YELLOW}source setup.sh${RESET}"

.PHONY: test
test: ## Run tests with coverage
	@echo "${BLUE}Running tests with coverage...${RESET}"
	cd quackcore && \
	PYTHONPATH="$(REPO_ROOT)/quackcore:$(REPO_ROOT)/quackcore/tests:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests -v --cov=src --cov-report=term-missing && \
	cd ../ducktyper && \
	PYTHONPATH="$(REPO_ROOT)/ducktyper:$(REPO_ROOT)/ducktyper/tests:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests -v --cov=src --cov-report=term-missing && \
	cd ../quackster && \
	PYTHONPATH="$(REPO_ROOT)/quackster:$(REPO_ROOT)/quackster/tests:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests -v --cov=src --cov-report=term-missing

.PHONY: test-quackcore
test-quackcore: ## Run only quackcore tests
	@echo "${BLUE}Running quackcore tests...${RESET}"
	cd quackcore && \
	PYTHONPATH="$(REPO_ROOT)/quackcore:$(REPO_ROOT)/quackcore/tests:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests -v --cov=src --cov-report=term-missing

.PHONY: test-ducktyper
test-ducktyper: ## Run only ducktyper tests
	@echo "${BLUE}Running ducktyper tests...${RESET}"
	cd ducktyper && \
	PYTHONPATH="$(REPO_ROOT)/ducktyper:$(REPO_ROOT)/ducktyper/tests:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests -v --cov=src --cov-report=term-missing

.PHONY: test-quackster
test-quackster: ## Run only quackster tests
	@echo "${BLUE}Running quackster tests...${RESET}"
	cd quackster && \
	PYTHONPATH="$(REPO_ROOT)/quackster:$(REPO_ROOT)/quackster/tests:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests -v --cov=src --cov-report=term-missing

.PHONY: test-integration
test-integration: ## Run only integration tests
	@echo "${BLUE}Running integration tests...${RESET}"
	PYTHONPATH="$(REPO_ROOT)/quackcore:$(REPO_ROOT)/ducktyper:$(REPO_ROOT)/quackster:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests/integration $(PYTEST_ARGS) \
		--cov=quackcore/src --cov=ducktyper/src --cov=quackster/src --cov-report=term-missing

.PHONY: test-module
test-module: ## Run only integration tests with coverage
	@echo "${BLUE}Running specific integration tests...${RESET}"
	$(PYTHON) -m pytest tests/test_integrations/pandoc $(PYTEST_ARGS) --cov=quackcore/src --cov-report=term-missing

.PHONY: format
format: ## Format code with Ruff and isort
	@echo "${BLUE}Formatting code...${RESET}"
	$(PYTHON) -m ruff check quackcore/src/ quackcore/tests/ ducktyper/src/ ducktyper/tests/ quackster/src/ quackster/tests/ examples/ --fix
	$(PYTHON) -m ruff format .
	$(PYTHON) -m isort .

.PHONY: lint
lint: ## Run linters
	@echo "${BLUE}Running linters...${RESET}"
	$(PYTHON) -m ruff check quackcore/src/ quackcore/tests/ ducktyper/src/ ducktyper/tests/ quackster/src/ quackster/tests/ examples/
	$(PYTHON) -m ruff format --check quackcore/src/ quackcore/tests/ ducktyper/src/ ducktyper/tests/ quackster/src/ quackster/tests/ examples/
	$(PYTHON) -m mypy quackcore/src/ quackcore/tests/ ducktyper/src/ ducktyper/tests/ quackster/src/ quackster/tests/ examples/

.PHONY: clean
clean: ## Clean build artifacts and cache
	@echo "${BLUE}Cleaning build artifacts and cache...${RESET}"
	rm -rf build/ dist/ *.egg-info .coverage .mypy_cache .pytest_cache .ruff_cache $(VENV_NAME)
	rm -rf setup.sh
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	# Clean subpackages
	cd quackcore && rm -rf build/ dist/ *.egg-info
	cd ducktyper && rm -rf build/ dist/ *.egg-info
	cd quackster && rm -rf build/ dist/ *.egg-info
	@echo "${GREEN}Cleaned all build artifacts and cache.${RESET}"

.PHONY: build
build: clean format lint test ## Build all packages for distribution
	@echo "${BLUE}Building packages for distribution...${RESET}"
	cd quackcore && uv pip build
	cd ducktyper && uv pip build
	cd quackster && uv pip build
	@echo "${GREEN}Packages built successfully. Distribution files in respective dist/ directories.${RESET}"

.PHONY: publish
publish: build ## Publish packages to PyPI
	@echo "${BLUE}Publishing packages to PyPI...${RESET}"
	@echo "${YELLOW}This will publish the following packages:${RESET}"
	@echo "  - quackcore"
	@echo "  - ducktyper"
	@echo "  - quackster"
	@echo "${YELLOW}Are you sure you want to continue? (y/n)${RESET}"
	@read -p " " yn; \
	if [ "$$yn" = "y" ]; then \
		cd quackcore && uv pip publish --repository pypi; \
		cd ../ducktyper && uv pip publish --repository pypi; \
		cd ../quackster && uv pip publish --repository pypi; \
		echo "${GREEN}All packages published successfully!${RESET}"; \
	else \
		echo "${YELLOW}Publishing cancelled.${RESET}"; \
	fi

.PHONY: pre-commit
pre-commit: format lint test ## Run all checks before committing
	@echo "${GREEN}✓ All checks passed${RESET}"

.PHONY: structure
structure: ## Show project structure
	@echo "${YELLOW}Current Project Structure:${RESET}"
	@echo "${BLUE}"
	@if command -v tree > /dev/null; then \
		tree -a -I '.git|.venv|__pycache__|*.pyc|*.pyo|*.pyd|.pytest_cache|.ruff_cache|.coverage|htmlcov'; \
	else \
		find . -not -path '*/\.*' -not -path '*.pyc' -not -path '*/__pycache__/*' \
			-not -path './.venv/*' -not -path './build/*' -not -path './dist/*' \
			-not -path './*.egg-info/*' \
			| sort | \
			sed -e "s/[^-][^\/]*\// │   /g" -e "s/├── /│── /" -e "s/└── /└── /"; \
	fi
	@echo "${RESET}"

# Additional targets remain unchanged
.PHONY: prune-branches
prune-branches: ## Remove local branches that are no longer tracked on the remote
	@echo "${BLUE}Pruning local branches that are no longer tracked on the remote...${RESET}"
	@git fetch -p && \
	  for branch in $$(git branch -vv | grep ': gone]' | awk '{print $$1}'); do \
	    git branch -D $$branch; \
	  done
	@echo "${GREEN}Stale branches have been removed.${RESET}"

.PHONY: add-paths
add-paths: ## Add file paths as first-line comments to all Python files
	@echo "${BLUE}Adding file paths as comments to Python files...${RESET}"
	@echo '#!/usr/bin/env python' > add_paths.py
	@echo '# add_paths.py' >> add_paths.py
	@echo '"""' >> add_paths.py
	@echo 'Script to add file paths as first-line comments to Python files.' >> add_paths.py
	@echo '"""' >> add_paths.py
	@echo 'import os' >> add_paths.py
	@echo 'import sys' >> add_paths.py
	@echo 'import traceback' >> add_paths.py
	@echo '' >> add_paths.py
	@echo 'def update_file(filepath):' >> add_paths.py
	@echo '    try:' >> add_paths.py
	@echo '        relpath = os.path.relpath(filepath)' >> add_paths.py
	@echo '        print(f"Processing {relpath}...")' >> add_paths.py
	@echo '' >> add_paths.py
	@echo '        with open(filepath, "r") as f:' >> add_paths.py
	@echo '            content = f.read()' >> add_paths.py
	@echo '' >> add_paths.py
	@echo '        lines = content.split("\\n")' >> add_paths.py
	@echo '        if not lines:' >> add_paths.py
	@echo '            print(f"  Skipping {relpath}: empty file")' >> add_paths.py
	@echo '            return' >> add_paths.py
	@echo '' >> add_paths.py
	@echo '        has_path_comment = False' >> add_paths.py
	@echo '        if lines[0].strip().startswith("#"):' >> add_paths.py
	@echo '            has_path_comment = True' >> add_paths.py
	@echo '            old_line = lines[0]' >> add_paths.py
	@echo '            lines[0] = f"# {relpath}"' >> add_paths.py
	@echo '            print(f"  Replacing comment: {old_line} -> # {relpath}")' >> add_paths.py
	@echo '        else:' >> add_paths.py
	@echo '            lines.insert(0, f"# {relpath}")' >> add_paths.py
	@echo '            print(f"  Adding new comment: # {relpath}")' >> add_paths.py
	@echo '' >> add_paths.py
	@echo '        with open(filepath, "w") as f:' >> add_paths.py
	@echo '            f.write("\\n".join(lines))' >> add_paths.py
	@echo '' >> add_paths.py
	@echo '        print(f"  Updated {relpath}")' >> add_paths.py
	@echo '    except Exception as e:' >> add_paths.py
	@echo '        print(f"  Error processing {filepath}: {str(e)}")' >> add_paths.py
	@echo '        traceback.print_exc()' >> add_paths.py
	@echo '' >> add_paths.py
	@echo 'def main():' >> add_paths.py
	@echo '    try:' >> add_paths.py
	@echo '        count = 0' >> add_paths.py
	@echo '        print("Starting file scan...")' >> add_paths.py
	@echo '        for root, dirs, files in os.walk("."):' >> add_paths.py
	@echo '            # Skip hidden and build directories' >> add_paths.py
	@echo '            if any(x in root for x in [".git", ".venv", "__pycache__", ".mypy_cache",' >> add_paths.py
	@echo '                                      ".pytest_cache", ".ruff_cache", "build", "dist", ".egg-info"]):' >> add_paths.py
	@echo '                continue' >> add_paths.py
	@echo '' >> add_paths.py
	@echo '            for file in files:' >> add_paths.py
	@echo '                if file.endswith(".py"):' >> add_paths.py
	@echo '                    filepath = os.path.join(root, file)' >> add_paths.py
	@echo '                    update_file(filepath)' >> add_paths.py
	@echo '                    count += 1' >> add_paths.py
	@echo '' >> add_paths.py
	@echo '        print(f"Processed {count} Python files")' >> add_paths.py
	@echo '    except Exception as e:' >> add_paths.py
	@echo '        print(f"Fatal error: {str(e)}")' >> add_paths.py
	@echo '        traceback.print_exc()' >> add_paths.py
	@echo '        sys.exit(1)' >> add_paths.py
	@echo '' >> add_paths.py
	@echo 'if __name__ == "__main__":' >> add_paths.py
	@echo '    main()' >> add_paths.py
	@chmod +x add_paths.py
	@$(PYTHON) add_paths.py
	@rm add_paths.py
	@echo "${GREEN}✓ File paths added to all Python files${RESET}"

.DEFAULT_GOAL := help