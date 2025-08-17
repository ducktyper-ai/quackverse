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

# Aggregate settings - use first argument or current directory
AGGREGATE_TARGET = $(if $(filter-out aggregate,$(MAKECMDGOALS)),$(filter-out aggregate,$(MAKECMDGOALS)),.)

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
	@echo '${YELLOW}File Operations:${RESET}'
	@echo '  Aggregate:   ${GREEN}make aggregate <directory>${RESET}  - Aggregate files from directory'
	@echo '               ${GREEN}make aggregate${RESET}             - Aggregate files from current directory'
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
	cd quackcore && uv pip install -e ".[gmail,notion,google,drive,pandoc,llms,ducktyper, github, http]"
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

.PHONY: update
update: ## Update all dependencies
	@echo "${BLUE}Updating dependencies...${RESET}"
	make install-dev

.PHONY: aggregate
aggregate: ## Aggregate text files from a directory (usage: make aggregate <directory>)
	@echo "${BLUE}Aggregating files from: ${AGGREGATE_TARGET}${RESET}"
	@# Create the aggregate script in memory and execute it
	@echo '#!/bin/bash' > .temp_aggregate.sh
	@echo '# Temporary aggregation script generated by Makefile' >> .temp_aggregate.sh
	@echo 'set -euo pipefail' >> .temp_aggregate.sh
	@echo '' >> .temp_aggregate.sh
	@echo '# Ensure Homebrew coreutils gnubin is on PATH (for grealpath/realpath on macOS)' >> .temp_aggregate.sh
	@echo 'if [ -d "/opt/homebrew/opt/coreutils/libexec/gnubin" ]; then' >> .temp_aggregate.sh
	@echo '  export PATH="/opt/homebrew/opt/coreutils/libexec/gnubin:$$PATH"' >> .temp_aggregate.sh
	@echo 'fi' >> .temp_aggregate.sh
	@echo '' >> .temp_aggregate.sh
	@echo 'portable_realpath() {' >> .temp_aggregate.sh
	@echo '  if command -v realpath >/dev/null 2>&1; then' >> .temp_aggregate.sh
	@echo '    realpath "$$1"' >> .temp_aggregate.sh
	@echo '  elif command -v grealpath >/dev/null 2>&1; then' >> .temp_aggregate.sh
	@echo '    grealpath "$$1"' >> .temp_aggregate.sh
	@echo '  elif command -v python3 >/dev/null 2>&1; then' >> .temp_aggregate.sh
	@echo '    python3 -c "import os,sys; print(os.path.abspath(os.path.expanduser(sys.argv[1])))" "$$1"' >> .temp_aggregate.sh
	@echo '  else' >> .temp_aggregate.sh
	@echo '    if [ -d "$$1" ]; then (cd "$$1" && pwd -P); else (cd "$$(dirname "$$1")" && printf "%s/%s\n" "$$PWD" "$$(basename "$$1")"); fi' >> .temp_aggregate.sh
	@echo '  fi' >> .temp_aggregate.sh
	@echo '}' >> .temp_aggregate.sh
	@echo '' >> .temp_aggregate.sh
	@echo 'INPUT_ARG="$$1"' >> .temp_aggregate.sh
	@echo 'INPUT_PATH="$$(portable_realpath "$$INPUT_ARG")"' >> .temp_aggregate.sh
	@echo 'if [ ! -d "$$INPUT_PATH" ]; then' >> .temp_aggregate.sh
	@echo '  echo "incorrect path"' >> .temp_aggregate.sh
	@echo '  echo "  pwd       : $$PWD"' >> .temp_aggregate.sh
	@echo '  echo "  input arg : $$INPUT_ARG"' >> .temp_aggregate.sh
	@echo '  echo "  resolved  : $$INPUT_PATH"' >> .temp_aggregate.sh
	@echo '  echo "hint: run from repo root, e.g. make aggregate ./quackcore/src/quackcore/config"' >> .temp_aggregate.sh
	@echo '  exit 1' >> .temp_aggregate.sh
	@echo 'fi' >> .temp_aggregate.sh
	@echo '' >> .temp_aggregate.sh
	@echo 'TRANSIENT_DIR="$$INPUT_PATH/_transient-files"' >> .temp_aggregate.sh
	@echo 'TIMESTAMP="$$(date +%Y-%m-%d)"' >> .temp_aggregate.sh
	@echo 'DIRECTORY_NAME="$$(basename "$$INPUT_PATH")"' >> .temp_aggregate.sh
	@echo 'OUTPUT_FILE="$$TRANSIENT_DIR/$$TIMESTAMP-$$DIRECTORY_NAME.txt"' >> .temp_aggregate.sh
	@echo 'USE_GITIGNORE=false' >> .temp_aggregate.sh
	@echo 'if [ -f "$$INPUT_PATH/.gitignore" ] && command -v git >/dev/null 2>&1; then' >> .temp_aggregate.sh
	@echo '  USE_GITIGNORE=true' >> .temp_aggregate.sh
	@echo 'fi' >> .temp_aggregate.sh
	@echo 'mkdir -p "$$TRANSIENT_DIR"' >> .temp_aggregate.sh
	@echo 'if [ ! -f "$$OUTPUT_FILE" ]; then' >> .temp_aggregate.sh
	@echo '  : > "$$OUTPUT_FILE"' >> .temp_aggregate.sh
	@echo '  echo "Created output file: $$OUTPUT_FILE"' >> .temp_aggregate.sh
	@echo 'else' >> .temp_aggregate.sh
	@echo '  echo "Output file already exists: $$OUTPUT_FILE"' >> .temp_aggregate.sh
	@echo 'fi' >> .temp_aggregate.sh
	@echo '' >> .temp_aggregate.sh
	@echo 'file_already_added() {' >> .temp_aggregate.sh
	@echo '  local file="$$1"' >> .temp_aggregate.sh
	@echo '  grep -q "here is $$file:" "$$OUTPUT_FILE" || return 1' >> .temp_aggregate.sh
	@echo '}' >> .temp_aggregate.sh
	@echo '' >> .temp_aggregate.sh
	@echo 'is_ignored_by_gitignore() {' >> .temp_aggregate.sh
	@echo '  local path="$$1"' >> .temp_aggregate.sh
	@echo '  if $$USE_GITIGNORE; then git -C "$$INPUT_PATH" check-ignore "$$path" >/dev/null 2>&1; return $$?; fi' >> .temp_aggregate.sh
	@echo '  return 1' >> .temp_aggregate.sh
	@echo '}' >> .temp_aggregate.sh
	@echo '' >> .temp_aggregate.sh
	@echo 'FILE_EXTENSIONS=("*.txt" "*.md" "*.py" "*.yaml" "*.template" "*.toml" "Makefile" "*.ts" "*.tsx" "*.mdx" "*.js" "*.jsx")' >> .temp_aggregate.sh
	@echo 'FILES_ADDED=0' >> .temp_aggregate.sh
	@echo 'FILES_PROCESSED=0' >> .temp_aggregate.sh
	@echo 'for EXT in "$${FILE_EXTENSIONS[@]}"; do' >> .temp_aggregate.sh
	@echo '  while IFS= read -r FILE; do' >> .temp_aggregate.sh
	@echo '    FILEPATH="$$(portable_realpath "$$FILE")"' >> .temp_aggregate.sh
	@echo '    if [[ "$$FILEPATH" == "$$TRANSIENT_DIR"* ]] || is_ignored_by_gitignore "$$FILEPATH"; then' >> .temp_aggregate.sh
	@echo '      continue' >> .temp_aggregate.sh
	@echo '    fi' >> .temp_aggregate.sh
	@echo '    FILENAME="$$(basename "$$FILE")"' >> .temp_aggregate.sh
	@echo '    if [[ "$$FILENAME" == deprecated_* ]]; then' >> .temp_aggregate.sh
	@echo '      echo "Skipping deprecated file: $$FILEPATH"' >> .temp_aggregate.sh
	@echo '      continue' >> .temp_aggregate.sh
	@echo '    fi' >> .temp_aggregate.sh
	@echo '    ((FILES_PROCESSED++))' >> .temp_aggregate.sh
	@echo '    if file_already_added "$$FILEPATH"; then' >> .temp_aggregate.sh
	@echo '      echo "Skipping already added file: $$FILEPATH"' >> .temp_aggregate.sh
	@echo '      continue' >> .temp_aggregate.sh
	@echo '    fi' >> .temp_aggregate.sh
	@echo '    echo "Processing: $$FILEPATH"' >> .temp_aggregate.sh
	@echo '    echo "here is $$FILEPATH:" >> "$$OUTPUT_FILE"' >> .temp_aggregate.sh
	@echo '    echo "<$$FILENAME>" >> "$$OUTPUT_FILE"' >> .temp_aggregate.sh
	@echo '    cat "$$FILE" >> "$$OUTPUT_FILE"' >> .temp_aggregate.sh
	@echo '    echo "</$$FILENAME>" >> "$$OUTPUT_FILE"' >> .temp_aggregate.sh
	@echo '    echo "" >> "$$OUTPUT_FILE"' >> .temp_aggregate.sh
	@echo '    ((FILES_ADDED++))' >> .temp_aggregate.sh
	@echo '  done < <(find "$$INPUT_PATH" -type f -name "$$EXT" ! -path "$$TRANSIENT_DIR/*" ! -name ".*")' >> .temp_aggregate.sh
	@echo 'done' >> .temp_aggregate.sh
	@echo '' >> .temp_aggregate.sh
	@echo 'if [ $$FILES_PROCESSED -eq 0 ]; then' >> .temp_aggregate.sh
	@echo '  echo "No files found matching the specified criteria. Exiting."' >> .temp_aggregate.sh
	@echo '  exit 0' >> .temp_aggregate.sh
	@echo 'fi' >> .temp_aggregate.sh
	@echo 'if [ $$FILES_ADDED -eq 0 ]; then' >> .temp_aggregate.sh
	@echo '  echo "No new files to add. Exiting."' >> .temp_aggregate.sh
	@echo '  exit 0' >> .temp_aggregate.sh
	@echo 'else' >> .temp_aggregate.sh
	@echo '  echo "All files aggregated into: $$OUTPUT_FILE"' >> .temp_aggregate.sh
	@echo '  exit 0' >> .temp_aggregate.sh
	@echo 'fi' >> .temp_aggregate.sh
	@chmod +x .temp_aggregate.sh
	@./.temp_aggregate.sh "$(AGGREGATE_TARGET)"
	@rm -f .temp_aggregate.sh
	@echo "${GREEN}✓ File aggregation completed${RESET}"

# Dummy target for directory arguments to aggregate
%:
	@:

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
	rm -rf setup.sh .temp_aggregate.sh
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

.PHONY: api-run
api-run: ## Run HTTP adapter server
	@echo "${BLUE}Starting QuackCore HTTP adapter...${RESET}"
	cd quackcore && \
	PYTHONPATH="$(REPO_ROOT)/quackcore:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/uvicorn quackcore.adapters.http.app:create_app --factory --host 0.0.0.0 --port 8080

.PHONY: api-run-reload
api-run-reload: ## Run HTTP adapter server with auto-reload
	@echo "${BLUE}Starting QuackCore HTTP adapter with reload...${RESET}"
	cd quackcore && \
	PYTHONPATH="$(REPO_ROOT)/quackcore:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/uvicorn quackcore.adapters.http.app:create_app --factory --reload --host 0.0.0.0 --port 8080

.PHONY: api-test
api-test: ## Run HTTP adapter tests
	@echo "${BLUE}Running HTTP adapter tests...${RESET}"
	cd quackcore && \
	PYTHONPATH="$(REPO_ROOT)/quackcore:$(REPO_ROOT)/quackcore/tests/test_http:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests/test_http -v --cov=src/quackcore/adapters/http --cov-report=term-missing

.PHONY: api-test-verbose
api-test-verbose: ## Run HTTP adapter tests with verbose output
	@echo "${BLUE}Running HTTP adapter tests (verbose)...${RESET}"
	cd quackcore && \
	PYTHONPATH="$(REPO_ROOT)/quackcore:$(REPO_ROOT)/quackcore/tests/test_http:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests/test_http -v --cov=src/quackcore/adapters/http --cov-report=term-missing

.PHONY: api-cov
api-cov: ## Run HTTP adapter tests with coverage
	@echo "${BLUE}Running HTTP adapter tests with coverage...${RESET}"
	cd quackcore && \
	PYTHONPATH="$(REPO_ROOT)/quackcore:$(REPO_ROOT)/quackcore/tests/test_http:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests/test_http -v --cov=src/quackcore/adapters/http --cov-report=html --cov-report=term-missing

.DEFAULT_GOAL := help