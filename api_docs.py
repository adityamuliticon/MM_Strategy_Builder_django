"""Serves the OpenAPI spec and ReDoc documentation UI."""

import json
import os
import yaml
from django.http import HttpResponse, JsonResponse
from django.conf import settings


def openapi_spec(request):
    """Serve the OpenAPI spec as JSON at /openapi.json."""
    spec_path = os.path.join(settings.BASE_DIR, 'docs', 'openapi.yaml')
    with open(spec_path, 'r') as f:
        spec = yaml.safe_load(f)
    return JsonResponse(spec)


def redoc_view(request):
    """Serve the ReDoc documentation UI at /docs/."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Market Maya Strategy Builder — API Docs</title>
  <style>
    body { margin: 0; padding: 0; }
  </style>
</head>
<body>
  <redoc spec-url="/openapi.json"></redoc>
  <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
</body>
</html>"""
    return HttpResponse(html, content_type='text/html')
