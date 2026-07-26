import json
import os

_CONFIG_DIR = os.path.dirname(__file__)


def load(name):
	"""Load a recipe file from this directory, e.g. load('chart_of_accounts')."""
	path = os.path.join(_CONFIG_DIR, f"{name}.json")
	with open(path, encoding="utf-8") as f:
		return json.load(f)


def chart_of_accounts():
	return load("chart_of_accounts")


def tax_templates():
	return load("tax_templates")


def withholding_tax_types():
	return load("withholding_tax_types")
