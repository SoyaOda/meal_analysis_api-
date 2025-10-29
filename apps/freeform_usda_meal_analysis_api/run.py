#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cloud Run entry point for Freeform USDA Meal Analysis API

This file serves as the entry point for Cloud Run deployment,
resolving relative import issues in main.py
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))

    # Import app from main module
    from main import app

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
