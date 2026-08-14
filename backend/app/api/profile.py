from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from app.db import get_database
from app.repositories import ProfileRepository
from app.schemas.profile import ProfileCreateSchema, ProfileUpdateSchema, ProfileResponseSchema

router = APIRouter(prefix="/profile", tags=["profile"])


def get_profile_repo(db=Depends(get_database)) -> ProfileRepository:
    return ProfileRepository(db)


@router.get("", response_model=ProfileResponseSchema)
async def get_profile(repo: Annotated[ProfileRepository, Depends(get_profile_repo)]) -> ProfileResponseSchema:
    """Get the single user profile."""
    profile = await repo.get_profile()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": "Profile not set"}
        )
    return ProfileResponseSchema.model_validate(profile)


@router.put("", response_model=ProfileResponseSchema)
async def upsert_profile(
    profile_data: ProfileCreateSchema,
    repo: Annotated[ProfileRepository, Depends(get_profile_repo)]
) -> ProfileResponseSchema:
    """Create or update the single user profile."""
    # Convert schema to model for repository
    from app.models import ProfileCreate, ProfileUpdate
    
    # Check if profile exists to determine create vs update
    existing = await repo.get_profile()
    if existing:
        model_data = ProfileUpdate(**profile_data.model_dump(exclude_unset=True))
    else:
        model_data = ProfileCreate(**profile_data.model_dump())
    
    profile = await repo.upsert_profile(model_data)
    return ProfileResponseSchema.model_validate(profile)