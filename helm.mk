# Helm Chart Management
# =============================================================================
# Package, lint, and push the Vagrantfile Generator Helm chart to OCI registry.
#
# Prerequisites:
#   - helm >= 4.0
#   - Registry login: make helm-login (or run helm registry login manually)
#
# Usage:
#   make -f helm.mk helm-package       # Package chart into .tgz
#   make -f helm.mk helm-push          # Push .tgz to OCI registry
#   make -f helm.mk helm-release       # Lint + package + push in one step
#   make -f helm.mk helm-login         # Interactive registry login
#   make -f helm.mk helm-lint          # Lint the chart
#   make -f helm.mk helm-dry-run       # Render templates locally
#   make -f helm.mk clean-helm         # Remove packaged .tgz files

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CHART_DIR    ?= helm/vagrantfile-generator
CHART_NAME   ?= vagrantfile-generator
OCI_REGISTRY ?= registry.gm5.lan:8443
OCI_PATH     ?= oci://$(OCI_REGISTRY)/vgf

# Extra flags for self-signed / internal registries
HELM_INSECURE ?= --insecure

.PHONY: helm-lint helm-package helm-push helm-release helm-login helm-dry-run clean-helm

# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------

## Lint the chart
helm-lint:
	@echo "Linting chart $(CHART_DIR)..."
	helm lint $(CHART_DIR)

## Package chart into a .tgz archive
helm-package: helm-lint
	@echo "Packaging chart $(CHART_DIR)..."
	helm package $(CHART_DIR) --destination .

## Push packaged chart to OCI registry
helm-push:
	@PACKAGE=$$(ls -1t $(CHART_NAME)-*.tgz 2>/dev/null | head -1); \
	if [ -z "$$PACKAGE" ]; then \
		echo "ERROR: No .tgz found. Run 'make -f helm.mk helm-package' first."; \
		exit 1; \
	fi; \
	echo "Pushing $$PACKAGE to $(OCI_PATH)..."; \
	helm push "$$PACKAGE" $(OCI_PATH)

## Lint, package, and push in one step
helm-release: helm-lint helm-package helm-push
	@echo ""
	@echo "===================================================================="
	@echo " Release complete!"
	@echo " Chart pushed to: $(OCI_PATH)/$(CHART_NAME)"
	@echo "===================================================================="

## Interactive registry login
helm-login:
	@echo "Logging into $(OCI_REGISTRY)..."
	helm registry login $(OCI_REGISTRY) $(HELM_INSECURE)

## Render templates locally without deploying (dry-run)
helm-dry-run:
	@echo "Rendering templates from $(CHART_DIR)..."
	helm template test-release $(CHART_DIR)

## Remove packaged .tgz artifacts
clean-helm:
	@echo "Removing packaged charts..."
	rm -f $(CHART_NAME)-*.tgz
