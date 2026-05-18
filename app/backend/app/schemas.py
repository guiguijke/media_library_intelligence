from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


# Plex Library
class PlexLibraryBase(BaseModel):
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    category: str
    genre_ids: Optional[List[int]] = None
    tmdb_id: Optional[int] = None
    anilist_id: Optional[int] = None
    poster_url: Optional[str] = None
    added_date: Optional[datetime] = None


class PlexLibraryCreate(PlexLibraryBase):
    pass


class PlexLibraryOut(PlexLibraryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# Tautulli Stats
class TautulliStatBase(BaseModel):
    user_id: str
    media_id: str
    watch_count: int = 0
    percent_complete: float = 0.0
    last_watched: Optional[datetime] = None


class TautulliStatOut(TautulliStatBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# External Classics
class ExternalClassicBase(BaseModel):
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    category: str
    tmdb_id: Optional[int] = None
    anilist_id: Optional[int] = None
    source_api: str
    source_list: Optional[str] = None
    score_external: Optional[float] = None
    popularity: Optional[float] = None
    poster_url: Optional[str] = None
    last_synced: Optional[datetime] = None
    is_recommended: bool = False


class ExternalClassicOut(ExternalClassicBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# Sonarr Queue
class SonarrQueueBase(BaseModel):
    external_id: str
    title: str
    status: str
    added_at: Optional[datetime] = None


class SonarrQueueOut(SonarrQueueBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# Radarr Queue
class RadarrQueueBase(BaseModel):
    external_id: str
    title: str
    status: str
    added_at: Optional[datetime] = None


class RadarrQueueOut(RadarrQueueBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# Wishlist
class WishlistBase(BaseModel):
    external_id: str
    category: str
    title: str
    poster_url: Optional[str] = None
    notes: Optional[str] = None


class WishlistCreate(WishlistBase):
    pass


class WishlistOut(WishlistBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    added_at: Optional[datetime] = None


# Recommendations
class RecommendationItem(BaseModel):
    id: str
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    category: str
    tmdb_id: Optional[int] = None
    anilist_id: Optional[int] = None
    poster_url: Optional[str] = None
    score: float
    reason: str
    score_reason: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    genres: Optional[List[str]] = None


class RecommendationResponse(BaseModel):
    items: List[RecommendationItem]
    total: int


class RecommendationFilter(BaseModel):
    categories: Optional[List[str]] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    genres: Optional[List[int]] = None
    limit: int = 50


# Batch
class BatchRadarrRequest(BaseModel):
    ids: List[int]
    quality_profile: Optional[int] = None


class BatchSonarrRequest(BaseModel):
    ids: List[int]
    quality_profile: Optional[int] = None


class BatchWishlistRequest(BaseModel):
    items: List[WishlistCreate]


# Dashboard
class IncompleteCollection(BaseModel):
    id: int
    name: str
    owned: int
    total: int


class TrendItem(BaseModel):
    genre: str
    count: int


class DashboardStats(BaseModel):
    movies: int
    series: int
    anime: int
    cartoons: int
    disk_usage: float = 0.0
    incomplete_collections: List[IncompleteCollection] = []
    trends: List[TrendItem] = []


# Sync
class SyncTriggerResponse(BaseModel):
    task_id: Optional[str] = None
    status: str
    message: str
