.PHONY: help update postprocess plot clean test install lint format check-csv

# Default target
help:
	@echo "Available commands:"
	@echo "  make update      - Complete data update workflow (recommended for annual updates)"
	@echo "  make install     - Install dependencies using Poetry"
	@echo "  make download-only - Download latest data without processing"
	@echo "  make postprocess - Post-process and sort data files"
	@echo "  make fix-riders-history - Fix riders history from all rankings data"
	@echo "  make plot        - Generate plots from existing data"
	@echo "  make all         - Legacy command (use 'update' instead)"
	@echo "  make clean       - Clean temporary files and caches"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linting checks"
	@echo "  make format      - Format code"
	@echo "  make check-csv   - Check CSV file integrity"

# Install dependencies
install:
	@echo "Installing dependencies with Poetry..."
	poetry install
	@echo "✅ Dependencies installed successfully"

# Complete data update workflow (download, postprocess, fix, verify)
update:
	@echo "🔄 Starting complete data update workflow..."
	@echo "📥 Step 1: Downloading latest Tour de France data..."
	poetry run python scripts/download_data.py
	@echo "🔧 Step 2: Post-processing data files..."
	poetry run python scripts/postprocess_data.py
	@echo "🩹 Step 3: Fixing riders history if needed..."
	poetry run python scripts/fix_riders_history.py || echo "⚠️  Fix script completed with warnings (may be expected)"
	@echo "🛡️ Step 4: Verifying CSV integrity..."
	poetry run python .github/scripts/check_csv_integrity.py
	@echo "📊 Step 5: Generating plots..."
	poetry run python scripts/generate_plots.py
	@echo "✅ Complete data update workflow finished successfully!"
	@echo "📋 Next steps: Review changes and commit/push if everything looks good"

# Quick data download only (no postprocessing or plots)
download-only:
	@echo "📥 Downloading latest Tour de France data only..."
	poetry run python scripts/download_data.py
	@echo "✅ Data download completed"

# Post-process data files (sort and organize)
postprocess:
	@echo "🔧 Post-processing data files..."
	poetry run python scripts/postprocess_data.py
	@echo "✅ Post-processing completed"

# Fix riders history (extract GC from all rankings if missing)
fix-riders-history:
	@echo "🔧 Fixing riders history files..."
	poetry run python scripts/fix_riders_history.py
	@echo "✅ Riders history fixed"

# Generate plots from existing data
plot:
	@echo "📊 Generating plots..."
	poetry run python scripts/generate_plots.py
	@echo "✅ Plots generated successfully"

# Legacy: Run both update and plot (deprecated - use 'update' instead)
all: update
	@echo "ℹ️  Note: 'make all' is deprecated. Use 'make update' for the complete workflow."
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
	poetry run python tests/test_recent_links.py
	poetry run python tests/test_recent_download.py
	poetry run python tests/debug_latest_data.py
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
