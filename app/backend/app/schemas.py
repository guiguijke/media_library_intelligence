from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


# Plex Library
class PlexLibraryBase(BaseModel):
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    category: str
    genre_ids: Optional[List[int]] = None
    tmdb_id: Optional[int] = None
    tvdb_id: Optional[int] = None
    anilist_id: Optional[int] = None
    poster_url: Optional[str] = None
    added_date: Optional[datetime] = None


class PlexLibraryCreate(PlexLibraryBase):
    pass


class PlexLibraryOut(PlexLibraryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    imdb_id: Optional[str] = None
    collection_id: Optional[int] = None
    collection_name: Optional[str] = None
    collections: Optional[List[str]] = None
    rating_key: Optional[str] = None


class PlexMappingCreate(BaseModel):
    library_key: str
    library_name: str
    category: str


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
    tvdb_id: Optional[int] = None
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


# Queue (Sonarr / Radarr live)
class QueueItemOut(BaseModel):
    id: str
    title: str
    year: Optional[int] = None
    poster_url: Optional[str] = None
    status: str
    progress: float = 0.0
    size: Optional[int] = None
    sizeleft: Optional[int] = None
    timeleft: Optional[str] = None
    quality: Optional[str] = None
    protocol: Optional[str] = None
    added_at: Optional[datetime] = None


# Wishlist
class WishlistBase(BaseModel):
    external_id: str
    category: str
    title: str
    poster_url: Optional[str] = None
    tmdb_id: Optional[int] = None
    tvdb_id: Optional[int] = None
    anilist_id: Optional[int] = None
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
    offset: int = 0
    limit: int = 50


class RecommendationFilter(BaseModel):
    categories: Optional[List[str]] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    rating_min: Optional[float] = None
    genres: Optional[List[int]] = None
    hide_in_plex: bool = True
    hide_monitored: bool = False
    user_id: Optional[str] = None
    limit: int = 50
    offset: int = 0


# Search
class SearchResultItem(BaseModel):
    id: str
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    category: str
    tmdb_id: Optional[int] = None
    anilist_id: Optional[int] = None
    poster_url: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    is_owned: bool = False


class SearchResponse(BaseModel):
    items: List[SearchResultItem]
    total: int
    limit: int
    offset: int


# Media detail
class MediaDetailOut(BaseModel):
    id: str
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    category: str
    tmdb_id: Optional[int] = None
    tvdb_id: Optional[int] = None
    anilist_id: Optional[int] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    overview: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    popularity: Optional[float] = None
    genres: Optional[List[str]] = []
    runtime: Optional[int] = None
    number_of_seasons: Optional[int] = None
    number_of_episodes: Optional[int] = None
    cast: Optional[List[Dict[str, Any]]] = []
    crew: Optional[List[Dict[str, Any]]] = []
    videos: Optional[List[Dict[str, Any]]] = []
    similar: Optional[List[Dict[str, Any]]] = []
    watch_providers: Optional[List[str]] = []
    images: Optional[List[str]] = []


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
    collection_id: Optional[int] = None
    missing_count: Optional[int] = None


class TrendItem(BaseModel):
    genre: str
    count: int


class DashboardStats(BaseModel):
    movies: int
    series: int
    anime: int
    cartoons: int
    incomplete_collections: List[IncompleteCollection] = []
    trends: List[TrendItem] = []


# Sync
class SyncTriggerResponse(BaseModel):
    task_id: Optional[str] = None
    status: str
    message: str
