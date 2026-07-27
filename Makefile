.PHONY: help update download-only postprocess fix-riders-history docs check-docs plot clean test diagnose install lint format check-csv dev ci

# Default target
help:
	@echo "Available commands:"
	@echo "  make update      - Complete data update workflow (recommended for annual updates)"
	@echo "  make install     - Install dependencies using uv"
	@echo "  make download-only - Download latest data without processing"
	@echo "  make postprocess - Post-process and sort data files"
	@echo "  make fix-riders-history - Reconstruct a missing GC from all rankings data"
	@echo "  make docs        - Sync documented year ranges to the data"
	@echo "  make check-docs  - Fail if the docs drifted from the data"
	@echo "  make plot        - Generate plots from existing data"
	@echo "  make clean       - Clean temporary files and caches"
	@echo "  make test        - Run the test suite (pytest, offline)"
	@echo "  make diagnose    - Manual checks against the live letour.fr pages"
	@echo "  make lint        - Run linting checks (ruff + ty)"
	@echo "  make format      - Format code (ruff)"
	@echo "  make check-csv   - Check CSV file integrity"

# Install dependencies
install:
	@echo "Installing dependencies with uv..."
	uv sync
	@echo "✅ Dependencies installed successfully"

# Complete data update workflow (download, postprocess, fix, verify)
update:
	@echo "🔄 Starting complete data update workflow..."
	@echo "📥 Step 1: Downloading latest Tour de France data..."
	uv run python scripts/download_data.py
	@echo "🔧 Step 2: Post-processing data files..."
	uv run python scripts/postprocess_data.py
	@echo "🩹 Step 3: Fixing riders history if needed..."
	uv run python scripts/fix_riders_history.py
	@echo "🛡️ Step 4: Verifying CSV integrity (informational for local runs)..."
	-uv run python .github/scripts/check_csv_integrity.py
	@echo "📝 Step 5: Syncing the documented year ranges to the data..."
	uv run python scripts/update_docs.py
	@echo "📊 Step 6: Generating plots..."
	uv run python scripts/generate_plots.py
	@echo "✅ Complete data update workflow finished successfully!"
	@echo "📋 Next steps: Review changes and commit/push if everything looks good"

# Quick data download only (no postprocessing or plots)
download-only:
	@echo "📥 Downloading latest Tour de France data only..."
	uv run python scripts/download_data.py
	@echo "✅ Data download completed"

# Post-process data files (sort and organize)
postprocess:
	@echo "🔧 Post-processing data files..."
	uv run python scripts/postprocess_data.py
	@echo "✅ Post-processing completed"

# Fix riders history (extract GC from all rankings if missing)
fix-riders-history:
	@echo "🔧 Fixing riders history files..."
	uv run python scripts/fix_riders_history.py
	@echo "✅ Riders history fixed"

# Sync the year ranges in README.md and docs/index.html to the data
docs:
	@echo "📝 Syncing documented year ranges to the data..."
	uv run python scripts/update_docs.py
	@echo "✅ Docs synced"

# Verify the docs match the data (used by CI)
check-docs:
	@echo "🔍 Checking that the docs match the data..."
	uv run python scripts/update_docs.py --check
	@echo "✅ Docs are up to date"

# Generate plots from existing data
plot:
	@echo "📊 Generating plots..."
	uv run python scripts/generate_plots.py
	@echo "✅ Plots generated successfully"

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
	uv run pytest
	@echo "✅ Tests completed"

# Manual diagnostics against the live letour.fr / letourfemmes.fr sites
diagnose:
	@echo "🌐 Running live-site diagnostics (requires network)..."
	uv run python scripts/diagnostics/test_recent_links.py
	uv run python scripts/diagnostics/test_recent_download.py
	@echo "✅ Diagnostics completed"

# Run linting
lint:
	@echo "🔍 Running linting checks..."
	uv run ruff check src/ scripts/ tests/ .github/scripts/
	uv run ty check src/
	@echo "✅ Linting completed"

# Format code
format:
	@echo "🎨 Formatting code..."
	uv run ruff format src/ scripts/ tests/ .github/scripts/
	@echo "✅ Code formatting completed"

# Check CSV integrity
check-csv:
	@echo "🛡️ Checking CSV file integrity..."
	uv run python .github/scripts/check_csv_integrity.py
	@echo "✅ CSV integrity check completed"

# Development workflow
dev: install lint test
	@echo "✅ Development setup completed"

# CI workflow
ci: install lint test check-docs check-csv
	@echo "✅ CI pipeline completed"
