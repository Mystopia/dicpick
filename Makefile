# lint:
# 	pipx run black dicpick main

.PHONY: requirements.txt
requirements.txt:
	pip-compile --allow-unsafe --generate-hashes requirements.in
	pip-compile --allow-unsafe --generate-hashes requirements-dev.in
