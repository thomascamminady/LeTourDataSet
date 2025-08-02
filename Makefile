.PHONY: help update plot clean test install lint format check-csv

# Default target
help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies using Poetry"
	@echo "  make update     - Download latest Tour de France data"
	@echo "  make plot       - Generate plots from existing data"
	@echo "  make all        - Run update and plot"
	@echo "  make clean      - Clean temporary files and caches"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linting checks"
	@echo "  make format     - Format code"
	@echo "  make check-csv  - Check CSV file integrity"

# Install dependencies
install:
	@echo "Installing dependencies with Poetry..."
	poetry install
	@echo "✅ Dependencies installed successfully"

# Update data (download only, no plots)
update:
	@echo "🔄 Downloading latest Tour de France data..."
	cd scripts && poetry run python download_data.py
	@echo "✅ Data update completed"

# Generate plots from existing data
plot:
	@echo "📊 Generating plots..."
	cd scripts && poetry run python generate_plots.py
	@echo "✅ Plots generated successfully"

# Run both update and plot
all: update plot
	@echo "✅ All tasks completed"

# Clean temporary files
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✅ Cleanup completed"

# Run tests
test:
	@echo "🧪 Running tests..."
	cd tests && poetry run python test_recent_links.py
	cd tests && poetry run python test_recent_download.py
	cd tests && poetry run python debug_latest_data.py
	@echo "✅ Tests completed"

# Run linting
lint:
	@echo "🔍 Running linting checks..."
	poetry run flake8 src/ scripts/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	@echo "✅ Linting completed"

# Format code
format:
	@echo "🎨 Formatting code..."
	poetry run black src/ scripts/ tests/
	poetry run isort src/ scripts/ tests/
	@echo "✅ Code formatting completed"

# Check CSV integrity
check-csv:
	@echo "🛡️ Checking CSV file integrity..."
	poetry run python .github/scripts/check_csv_integrity.py
	@echo "✅ CSV integrity check completed"

# Development workflow
dev: install lint test
	@echo "✅ Development setup completed"

# CI workflow
ci: install lint test check-csv
	@echo "✅ CI pipeline completed"

# Move existing CSV files to new structure (one-time migration)
migrate-data:
	@echo "📁 Migrating data to new folder structure..."
	@if [ -f "data/TDF_Riders_History.csv" ]; then \
		mkdir -p data/men data/women data/plots; \
		mv data/TDF_*.csv data/men/ 2>/dev/null || true; \
		mv data/TDFF_*.csv data/women/ 2>/dev/null || true; \
		mv data/*.png data/plots/ 2>/dev/null || true; \
		echo "✅ Data migration completed"; \
	else \
		echo "ℹ️  No legacy data files found to migrate"; \
	fi
