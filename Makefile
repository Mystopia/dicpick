# lint:
# 	pipx run black dicpick main

requirements.txt:
	pip-compile --allow-unsafe --generate-hashes
