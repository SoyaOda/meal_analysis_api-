"""
Admin Panel Router for Configuration Management
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .config_manager import (
    ConfigManager,
    get_config_manager,
    APIConfig,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

# Templates setup
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


# ========== Request/Response Models ==========

class ConfigUpdateRequest(BaseModel):
    """Configuration update request"""
    updates: Dict[str, Any] = Field(
        ...,
        description="Updates to apply (supports dot notation like 'vlm.temperature')",
        example={"vlm.temperature": 0.7, "search.rrf_weight": 0.6}
    )


class ConfigResponse(BaseModel):
    """Configuration response"""
    success: bool
    config: APIConfig
    message: Optional[str] = None


class PromptInfo(BaseModel):
    """Prompt file information"""
    filename: str
    size_bytes: int
    preview: str


# ========== Admin UI Routes ==========

@router.get("", response_class=HTMLResponse, include_in_schema=False)
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def admin_dashboard(request: Request):
    """Admin dashboard page"""
    config_manager = get_config_manager()
    config = config_manager.get_config()

    # Get available prompts
    prompts = await get_available_prompts()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "config": config.model_dump(),
            "prompts": prompts,
            "use_firestore": config_manager.use_firestore,
        }
    )


# ========== Admin API Routes ==========

@router.get("/api/config", response_model=ConfigResponse)
async def get_config(
    refresh: bool = Query(False, description="Force refresh from Firestore"),
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    Get current API configuration

    Returns the current configuration settings including VLM, Search, and Reranker parameters.
    """
    try:
        config = config_manager.get_config(force_refresh=refresh)
        return ConfigResponse(
            success=True,
            config=config,
            message="Configuration loaded successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/config", response_model=ConfigResponse)
async def update_config(
    request: ConfigUpdateRequest,
    updated_by: str = Query("admin", description="Who is making the update"),
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    Update API configuration

    Supports dot notation for nested updates:
    - `vlm.temperature`: 0.7
    - `search.rrf_weight`: 0.6
    - `reranker.top_n`: 10
    """
    try:
        config = config_manager.update_config(
            updates=request.updates,
            updated_by=updated_by
        )
        return ConfigResponse(
            success=True,
            config=config,
            message=f"Configuration updated: {list(request.updates.keys())}"
        )
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/reset", response_model=ConfigResponse)
async def reset_config(
    updated_by: str = Query("admin", description="Who is resetting"),
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    Reset configuration to defaults

    Resets all settings to their default values defined in settings.py
    """
    try:
        config = config_manager.reset_to_defaults(updated_by=updated_by)
        return ConfigResponse(
            success=True,
            config=config,
            message="Configuration reset to defaults"
        )
    except Exception as e:
        logger.error(f"Failed to reset config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/invalidate-cache")
async def invalidate_cache(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    Invalidate configuration cache

    Forces the next config read to fetch from Firestore
    """
    try:
        config_manager.invalidate_cache()
        return {"success": True, "message": "Cache invalidated"}
    except Exception as e:
        logger.error(f"Failed to invalidate cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/prompts", response_model=List[PromptInfo])
async def get_available_prompts():
    """
    List available prompt files

    Returns a list of prompt files in the prompts/ directory
    """
    try:
        from ..config.settings import get_settings
        settings = get_settings()
        prompts_dir = settings.PROMPTS_DIR

        prompts = []
        for prompt_file in sorted(prompts_dir.glob("*.txt")):
            # Skip research/test files
            if "test_" in prompt_file.name or prompt_file.name.startswith("."):
                continue

            try:
                content = prompt_file.read_text()
                preview = content[:200] + "..." if len(content) > 200 else content
                prompts.append(PromptInfo(
                    filename=prompt_file.name,
                    size_bytes=prompt_file.stat().st_size,
                    preview=preview.replace("\n", " ")
                ))
            except Exception:
                continue

        return prompts

    except Exception as e:
        logger.error(f"Failed to list prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/prompt/{filename}")
async def get_prompt_content(filename: str):
    """
    Get prompt file content

    Returns the full content of a specific prompt file
    """
    try:
        from ..config.settings import get_settings
        settings = get_settings()
        prompt_path = settings.PROMPTS_DIR / filename

        if not prompt_path.exists():
            raise HTTPException(status_code=404, detail=f"Prompt file not found: {filename}")

        if not prompt_path.suffix == ".txt":
            raise HTTPException(status_code=400, detail="Only .txt files allowed")

        content = prompt_path.read_text()
        return {
            "filename": filename,
            "content": content,
            "size_bytes": len(content.encode())
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to read prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/status")
async def get_status(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    Get admin panel status

    Returns information about the configuration backend and cache status
    """
    return {
        "backend": "firestore" if config_manager.use_firestore else "in-memory",
        "cache_ttl_seconds": config_manager.cache_ttl_seconds,
        "cache_valid": config_manager._is_cache_valid(),
        "google_cloud_project": os.getenv("GOOGLE_CLOUD_PROJECT"),
    }
