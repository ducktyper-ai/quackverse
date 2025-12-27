# Terminal colors
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)
BLUE   := $(shell tput -Txterm setaf 4)

# Project settings
PYTHON_VERSION := 3.13
VENV_NAME := .venv
PROJECT_NAME := quack-core
REPO_ROOT := $(shell pwd)
PYTHON := $(REPO_ROOT)/$(VENV_NAME)/bin/python
# Prefer venv python if present, otherwise fall back to system python3/python, otherwise blank
PYTHON_BIN := $(shell \
  if [ -x "$(PYTHON)" ]; then echo "$(PYTHON)"; \
  elif command -v python3 >/dev/null 2>&1; then echo python3; \
  elif command -v python >/dev/null 2>&1; then echo python; \
  else echo ""; fi)


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
	@echo '  Quackcore:    ${GREEN}make install-quackcore${RESET}   - Install quack-core'
	@echo '  All:        ${GREEN}make install-all${RESET}        - Install both packages'
	@echo '  Development:${GREEN}make install-dev${RESET}        - Development tools'
	@echo ''
	@echo '${YELLOW}Development Workflow:${RESET}'
	@echo '  1. Setup:     ${GREEN}make setup${RESET}              - Full development environment'
	@echo '  2. Activate:  ${GREEN}source .venv/bin/activate${RESET} - Activate environment'
	@echo '  3. Check:     ${GREEN}make check-env${RESET}          - Verify installation'
	@echo ''
	@echo '${YELLOW}Quick Setup:${RESET}'
	@echo '  All-in-one:  ${GREEN}make quick-setup${RESET}         - Fast complete setup'
	@echo ''
	@echo '${YELLOW}File Operations:${RESET}'
	@echo '  Aggregate:   ${GREEN}make aggregate <directory>${RESET}  - Aggregate files from directory'
	@echo '               ${GREEN}make aggregate${RESET}             - Aggregate files from current directory'
	@echo ''
	@echo '${YELLOW}Available Targets:${RESET}'
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_.-]+:.*## / {printf "  ${YELLOW}%-15s${GREEN}%s${RESET}\n", $$1, $$2}' $(MAKEFILE_LIST)
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
	@echo "${BLUE}Installing quack-core package...${RESET}"
	@# Ensure we're using the virtual environment
	@if [ ! -f "$(PYTHON)" ]; then \
		echo "${YELLOW}Virtual environment not found. Creating it first...${RESET}"; \
		make env; \
	fi
	@# Install the package in editable mode using global uv but targeting the venv
	cd quack-core && uv pip install -e . --python $(REPO_ROOT)/$(VENV_NAME)/bin/python
	@echo "${GREEN}quack-core installed successfully${RESET}"
	@# Verify installation with proper PYTHONPATH
	@echo "${BLUE}Verifying installation...${RESET}"
	@PYTHONPATH="$(REPO_ROOT)/quack-core/src:$(PYTHONPATH)" $(PYTHON) -c "import quack_core; print(f'✓ quack-core installed at: {quack_core.__file__}')" || \
	(echo "${YELLOW}Warning: Import verification failed. This might be expected if package structure needs adjustment.${RESET}" && \
	 echo "${BLUE}Checking package installation status...${RESET}" && \
	 $(PYTHON) -m pip list | grep quack-core)

.PHONY: install-all
install-all: install-quackcore ## Install all packages with their optional dependencies
	@echo "${BLUE}Installing optional dependencies for all packages...${RESET}"
	cd quack-core && uv pip install -e ".[gmail,notion,google,drive,pandoc,llms,github,http]" --python $(REPO_ROOT)/$(VENV_NAME)/bin/python
	@echo "${GREEN}All packages and dependencies installed successfully${RESET}"

.PHONY: install-dev
install-dev: ## Install development dependencies for all packages
	@echo "${BLUE}Installing development tools...${RESET}"
	@# Ensure we have the virtual environment
	@if [ ! -f "$(PYTHON)" ]; then \
		echo "${YELLOW}Virtual environment not found. Creating it first...${RESET}"; \
		make env; \
	fi
	cd quack-core && uv pip install -e ".[dev]" --python $(REPO_ROOT)/$(VENV_NAME)/bin/python
	@# Install root development dependencies
	uv pip install -e ".[dev]" --python $(REPO_ROOT)/$(VENV_NAME)/bin/python
	@echo "${GREEN}Development dependencies installed successfully${RESET}"

.PHONY: setup
setup: ## Create environment and install full development dependencies
	@echo "${BLUE}Creating complete development environment...${RESET}"
	@echo "${YELLOW}Note: This will create a virtual environment but won't activate it automatically.${RESET}"
	@echo "${YELLOW}After completion, run: source .venv/bin/activate${RESET}"
	@echo ""
	make env
	@echo "${BLUE}Installing all packages and dependencies...${RESET}"
	make install-all
	make install-dev
	@echo ""
	@echo "${GREEN}Setup complete! Development environment ready.${RESET}"
	@echo "${YELLOW}To activate the environment, run:${RESET}"
	@echo "  ${GREEN}source .venv/bin/activate${RESET}"

.PHONY: setup-and-activate
setup-and-activate: ## Create environment, install dependencies, and generate activation helper
	@echo "${BLUE}Creating complete development environment...${RESET}"
	make env
	make install-all
	make install-dev
	@echo '#!/bin/bash' > activate_env.sh
	@echo 'source .venv/bin/activate' >> activate_env.sh
	@echo 'echo "QuackVerse development environment activated!"' >> activate_env.sh
	@echo 'echo "Python: $(which python)"' >> activate_env.sh
	@chmod +x activate_env.sh
	@echo ""
	@echo "${GREEN}Setup complete! Development environment ready.${RESET}"
	@echo "${YELLOW}To activate the environment, run:${RESET}"
	@echo "  ${GREEN}source activate_env.sh${RESET}"
	@echo ""
	@echo "${YELLOW}Or manually activate with:${RESET}"
	@echo "  ${GREEN}source .venv/bin/activate${RESET}"

.PHONY: check-env
check-env: ## Check if virtual environment is active and working
	@echo "${BLUE}Checking environment...${RESET}"
	@if [ ! -f "$(PYTHON)" ]; then \
		echo "${YELLOW}Virtual environment not found at $(PYTHON)${RESET}"; \
		echo "Run 'make env' first"; \
		exit 1; \
	fi
	@echo "Python: $(PYTHON)"
	@$(PYTHON) --version
	@$(PYTHON) -c "import sys; print(f'Python executable: {sys.executable}')"
	@$(PYTHON) -m pip list | head -5
	@echo "${GREEN}Environment check complete${RESET}"

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
	@echo '  echo "hint: run from repo root, e.g. make aggregate ./quack-core/src/quack_core/config"' >> .temp_aggregate.sh
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
	cd quack-core && \
	PYTHONPATH="$(REPO_ROOT)/quack-core/src:$(REPO_ROOT)/quack-core/tests:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests -v --cov=src --cov-report=term-missing && \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests -v --cov=src --cov-report=term-missing

.PHONY: test-quackcore
test-quackcore: ## Run only quackcore tests
	@echo "${BLUE}Running quack-core tests...${RESET}"
	cd quack-core && \
	PYTHONPATH="$(REPO_ROOT)/quack-core/src:$(REPO_ROOT)/quack-core/tests:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests -v --cov=src --cov-report=term-missing

.PHONY: test-integration
test-integration: ## Run only integration tests
	@echo "${BLUE}Running integration tests...${RESET}"
	PYTHONPATH="$(REPO_ROOT)/quack-core/src:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests/integration $(PYTEST_ARGS) \
		--cov=quack-core/src --cov-report=term-missing

.PHONY: test-module
test-module: ## Run only integration tests with coverage
	@echo "${BLUE}Running specific integration tests...${RESET}"
	$(PYTHON) -m pytest tests/test_integrations/pandoc $(PYTEST_ARGS) --cov=quack-core/src --cov-report=term-missing

.PHONY: format
format: ## Format code with Ruff and isort
	@echo "${BLUE}Formatting code...${RESET}"
	$(PYTHON) -m ruff check quack-core/src/ quack-core/tests/ examples/ --fix
	$(PYTHON) -m ruff format .
	$(PYTHON) -m isort .

.PHONY: lint
lint: ## Run linters
	@echo "${BLUE}Running linters...${RESET}"
	$(PYTHON) -m ruff check quack-core/src/ quack-core/tests/ examples/
	$(PYTHON) -m ruff format --check quack-core/src/ quack-core/tests/ examples/
	$(PYTHON) -m mypy quack-core/src/ quack-core/tests/ examples/

.PHONY: clean
clean: ## Clean build artifacts and cache
	@echo "${BLUE}Cleaning build artifacts and cache...${RESET}"
	rm -rf build/ dist/ *.egg-info .coverage .mypy_cache .pytest_cache .ruff_cache $(VENV_NAME)
	rm -rf setup.sh .temp_aggregate.sh
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	# Clean subpackages
	cd quack-core && rm -rf build/ dist/ *.egg-info
	@echo "${GREEN}Cleaned all build artifacts and cache.${RESET}"

.PHONY: build
build: clean format lint test ## Build all packages for distribution
	@echo "${BLUE}Building packages for distribution...${RESET}"
	cd quack-core && uv build
	@echo "${GREEN}Packages built successfully. Distribution files in respective dist/ directories.${RESET}"

.PHONY: publish
publish: build ## Publish packages to PyPI
	@echo "${BLUE}Publishing packages to PyPI...${RESET}"
	@echo "${YELLOW}This will publish the following packages:${RESET}"
	@echo "  - quack_core"
	@echo "${YELLOW}Are you sure you want to continue? (y/n)${RESET}"
	@read -p " " yn; \
	if [ "$$yn" = "y" ]; then \
		cd quack-core && uv publish --repository pypi; \
		echo "${GREEN}All packages published successfully!${RESET}"; \
	else \
		echo "${YELLOW}Publishing cancelled.${RESET}"; \
	fi

.PHONY: pre-commit
pre-commit: format lint test ## Run all checks before committing
	@echo "${GREEN}✓ All checks passed${RESET}"

.PHONY: structure
structure: ## Show project structure (filtered + summary)
	@echo "${YELLOW}Project Summary:${RESET}"
	@echo "  Python: $$( [ -n "$(PYTHON_BIN)" ] && $(PYTHON_BIN) -V 2>/dev/null || echo 'n/a')"
	@echo "  Git branch: $$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'n/a')"
	@echo "  Files: $$(find . -type f -not -path './.git/*' -not -path './.venv/*' -not -path './_transient-files/*' -not -path './.idea/*' -not -path './.hypothesis/*' | wc -l | tr -d ' ')"
	@echo "  Dirs:  $$(find . -type d -not -path './.git/*' -not -path './.venv/*' -not -path './_transient-files/*' -not -path './.idea/*' -not -path './.hypothesis/*' | wc -l | tr -d ' ')"
	@echo ""
	@$(MAKE) --no-print-directory structure-insights
	@echo ""
	@$(MAKE) --no-print-directory structure-tree

.PHONY: structure-tree
structure-tree:
	@echo "${YELLOW}Current Project Structure:${RESET}"
	@echo "${BLUE}"
	@IGNORE='\.git|\.venv|__pycache__|\.DS_Store|_transient-files|\.idea|\.hypothesis|\.pytest_cache|\.ruff_cache|\.mypy_cache|\.coverage|htmlcov|build|dist|.*\.egg-info'; \
	if command -v tree > /dev/null; then \
		tree -a -I "$$IGNORE"; \
	else \
		find . \
			-not -path './.git/*' \
			-not -path './.venv/*' \
			-not -path './__pycache__/*' \
			-not -path './_transient-files/*' \
			-not -path './.idea/*' \
			-not -path './.hypothesis/*' \
			-not -name '.DS_Store' \
			-not -path './.pytest_cache/*' \
			-not -path './.ruff_cache/*' \
			-not -path './.mypy_cache/*' \
			-not -path './htmlcov/*' \
			-not -path './build/*' \
			-not -path './dist/*' \
			-not -path './*.egg-info/*' \
			| sort; \
	fi
	@echo "${RESET}"

.PHONY: structure-brief
structure-brief: ## High-signal structure view (2 levels)
	@echo "${YELLOW}High-signal Structure (2 levels):${RESET}"
	@echo "${BLUE}"
	@IGNORE='\.git|\.venv|__pycache__|\.DS_Store|_transient-files|\.idea|\.hypothesis|\.pytest_cache|\.ruff_cache|\.mypy_cache|\.coverage|htmlcov|build|dist|.*\.egg-info'; \
	tree -a -L 3 -I "$$IGNORE" .
	@echo "${RESET}"

.PHONY: structure-insights
structure-insights: ## Repo hotspots (largest dirs / file counts)
	@echo "${YELLOW}Hotspots (by file count):${RESET}"
	@find . -type f \
		-not -path './.git/*' -not -path './.venv/*' \
		-not -path './_transient-files/*' -not -path './.idea/*' -not -path './.hypothesis/*' \
		| sed 's|^\./||' \
		| awk -F/ '{print $$1}' \
		| sort | uniq -c | sort -nr | head -n 12 \
		| awk '{printf "  %-6s %s\n", $$1, $$2}'
	@echo ""
	@echo "${YELLOW}Largest subtrees (depth 2):${RESET}"
	@find . -type f \
		-not -path './.git/*' -not -path './.venv/*' \
		-not -path './_transient-files/*' -not -path './.idea/*' -not -path './.hypothesis/*' \
		| sed 's|^\./||' \
		| awk -F/ 'NF>=2 {print $$1"/"$$2}' \
		| sort | uniq -c | sort -nr | head -n 12 \
		| awk '{printf "  %-6s %s\n", $$1, $$2}'


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
	@echo 'EXTENSIONS = (".py", ".yaml", ".yml", ".toml", ".env", ".example")' >> add_paths.py
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
	@echo '                if file.endswith(EXTENSIONS):' >> add_paths.py
	@echo '                    filepath = os.path.join(root, file)' >> add_paths.py
	@echo '                    update_file(filepath)' >> add_paths.py
	@echo '                    count += 1' >> add_paths.py
	@echo '' >> add_paths.py
	@echo '        print(f"Processed {count} files (extensions: {EXTENSIONS})")' >> add_paths.py
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
	@echo "${GREEN}✓ File paths added to all files${RESET}"

# --- Flatten defaults (override on CLI) ---
FLATTEN_OUT ?= _transient-files/flatten
FLATTEN_EXT ?= .py,.yaml,.yml,.toml,.env,.example,.md
FLATTEN_SKIP ?= .git,.venv,__pycache__,.mypy_cache,.pytest_cache,.ruff_cache,build,dist,.egg-info,node_modules

# Default to repo root; override with: make flatten SCOPE=quack-core/src/quack_core/lib/fs
FLATTEN_SCOPE ?= .

# Cap output to keep it shareable; override with: make flatten MAX_BYTES=8000000
MAX_BYTES ?= 4000000
MAX_FILES ?=

.PHONY: flatten-scope
flatten-scope: ## Flatten a specific directory: make flatten-scope SCOPE=quack-core/src/quack_core/lib/fs
	@test -n "$(SCOPE)" || (echo "Usage: make flatten-scope SCOPE=path/to/dir" && exit 1)
	@$(PYTHON) scripts/flatten.py \
		--mode scope \
		--scope "$(SCOPE)" \
		--out-dir "$(FLATTEN_OUT)" \
		--extensions "$(FLATTEN_EXT)" \
		--skip-dirs "$(FLATTEN_SKIP)" \
		--exclude "flat.txt" \
		--exclude "_transient-files/**" \
		--max-bytes 4000000

.PHONY: flatten-tree
flatten-tree: ## Flatten one file per subdir: make flatten-tree SCOPE=quack-core/src/quack_core/lib/fs
	@test -n "$(SCOPE)" || (echo "Usage: make flatten-tree SCOPE=path/to/dir" && exit 1)
	@$(PYTHON) scripts/flatten.py \
		--mode tree \
		--scope "$(SCOPE)" \
		--out-dir "$(FLATTEN_OUT)" \
		--extensions "$(FLATTEN_EXT)" \
		--skip-dirs "$(FLATTEN_SKIP)" \
		--exclude "flat.txt" \
		--exclude "_transient-files/**" \
		--max-bytes 2500000

.PHONY: flatten-clean
flatten-clean: ## Remove transient flatten outputs
	@rm -rf "$(FLATTEN_OUT)"

.PHONY: flatten
flatten: ## Flatten files using scripts/flatten.py (defaults to repo root). Override: make flatten SCOPE=path
	@echo "${BLUE}Flattening '$(FLATTEN_SCOPE)' into $(FLATTEN_OUT) (max $(MAX_BYTES) bytes)...${RESET}"
	@mkdir -p "$(FLATTEN_OUT)"
	@$(PYTHON) scripts/flatten.py \
		--mode scope \
		--scope "$(FLATTEN_SCOPE)" \
		--out-dir "$(FLATTEN_OUT)" \
		--extensions "$(FLATTEN_EXT)" \
		--skip-dirs "$(FLATTEN_SKIP)" \
		--exclude "flat.txt" \
		--exclude "_transient-files/**" \
		$(if $(MAX_FILES),--max-files $(MAX_FILES),) \
		$(if $(MAX_BYTES),--max-bytes $(MAX_BYTES),)
	@echo "${GREEN}✓ Done. See: $(FLATTEN_OUT)/manifest.md${RESET}"


.PHONY: api-run
api-run: ## Run HTTP adapter server
	@echo "${BLUE}Starting QuackCore HTTP adapter...${RESET}"
	cd quack-core && \
	PYTHONPATH="$(REPO_ROOT)/quack-core/src:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/uvicorn quack_core.adapters.http.app:create_app --factory --host 0.0.0.0 --port 8080

.PHONY: api-run-reload
api-run-reload: ## Run HTTP adapter server with auto-reload
	@echo "${BLUE}Starting QuackCore HTTP adapter with reload...${RESET}"
	cd quack-core && \
	PYTHONPATH="$(REPO_ROOT)/quack-core/src:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/uvicorn quack_core.adapters.http.app:create_app --factory --reload --host 0.0.0.0 --port 8080

.PHONY: api-test
api-test: ## Run HTTP adapter tests
	@echo "${BLUE}Running HTTP adapter tests...${RESET}"
	cd quack-core && \
	PYTHONPATH="$(REPO_ROOT)/quack-core/src:$(REPO_ROOT)/quack-core/tests/test_http:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests/test_http -v --cov=src/quack-core/adapters/http --cov-report=term-missing

.PHONY: api-test-verbose
api-test-verbose: ## Run HTTP adapter tests with verbose output
	@echo "${BLUE}Running HTTP adapter tests (verbose)...${RESET}"
	cd quack-core && \
	PYTHONPATH="$(REPO_ROOT)/quack-core/src:$(REPO_ROOT)/quack-core/tests/test_http:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests/test_http -v --cov=src/quack-core/adapters/http --cov-report=term-missing

.PHONY: api-cov
api-cov: ## Run HTTP adapter tests with coverage
	@echo "${BLUE}Running HTTP adapter tests with coverage...${RESET}"
	cd quack-core && \
	PYTHONPATH="$(REPO_ROOT)/quack-core/src:$(REPO_ROOT)/quack-core/tests/test_http:$(PYTHONPATH)" \
	$(REPO_ROOT)/$(VENV_NAME)/bin/python -m pytest tests/test_http -v --cov=src/quack-core/adapters/http --cov-report=html --cov-report=term-missing

.DEFAULT_GOAL := help