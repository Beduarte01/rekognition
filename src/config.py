import os

def _get_float(name, default):
    try:
        return float(os.getenv(name, default))
    except:
        return default

def _get_int(name, default):
    try:
        return int(os.getenv(name, default))
    except:
        return default

CFG = {
    "aws_region": os.getenv("AWS_REGION", "us-east-1"),
    "min_confidence": _get_float("MIN_CONFIDENCE", 75.0),
    "max_labels": _get_int("MAX_LABELS", 10),
    "images_prefix": os.getenv("IMAGES_PREFIX", "images/"),
    "reference_prefix": os.getenv("REFERENCE_PREFIX", "reference/"),
    "results_prefix": os.getenv("RESULTS_PREFIX", "results/"),
}