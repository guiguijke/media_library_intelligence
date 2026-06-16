import enum
from typing import List, Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, Enum, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class CategoryEnum(str, enum.Enum):
    movie = "movie"
    series = "series"
    anime = "anime"
    cartoon = "cartoon"
    ignore = "ignore"


class PlexLibrary(Base):
    __tablename__ = "plex_library"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    original_title = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    category = Column(Enum(CategoryEnum), nullable=False, index=True)
    genre_ids = Column(JSON, nullable=True)
    collections = Column(JSON, nullable=True)
    tmdb_id = Column(Integer, nullable=True, index=True)
    tvdb_id = Column(Integer, nullable=True, index=True)
    anilist_id = Column(Integer, nullable=True, index=True)
    imdb_id = Column(String, nullable=True, index=True)
    collection_id = Column(Integer, nullable=True, index=True)
    collection_name = Column(String, nullable=True)
    poster_url = Column(String, nullable=True)
    rating_key = Column(String, nullable=True, index=True)
    added_date = Column(DateTime(timezone=True), default=func.now())
    sync_hash = Column(String, nullable=True, index=True)


class TautulliStats(Base):
    __tablename__ = "tautulli_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    media_id = Column(String, nullable=False, index=True)
    watch_count = Column(Integer, default=0)
    percent_complete = Column(Float, default=0.0)
    last_watched = Column(DateTime(timezone=True), nullable=True)


class ExternalClassics(Base):
    __tablename__ = "external_classics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    original_title = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    category = Column(Enum(CategoryEnum), nullable=False, index=True)
    genre_ids = Column(JSON, nullable=True)
    tmdb_id = Column(Integer, nullable=True, index=True)
    tvdb_id = Column(Integer, nullable=True, index=True)
    anilist_id = Column(Integer, nullable=True, index=True)
    source_api = Column(String, nullable=False, index=True)
    source_list = Column(String, nullable=True)
    score_external = Column(Float, nullable=True)
    popularity = Column(Float, nullable=True)
    poster_url = Column(String, nullable=True)
    last_synced = Column(DateTime(timezone=True), default=func.now())
    is_recommended = Column(Boolean, default=False)


class SonarrQueue(Base):
    __tablename__ = "sonarr_queue"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    added_at = Column(DateTime(timezone=True), default=func.now())


class RadarrQueue(Base):
    __tablename__ = "radarr_queue"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    added_at = Column(DateTime(timezone=True), default=func.now())


class Wishlist(Base):
    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, nullable=False, index=True)
    category = Column(Enum(CategoryEnum), nullable=False)
    title = Column(String, nullable=False)
    poster_url = Column(String, nullable=True)
    tmdb_id = Column(Integer, nullable=True, index=True)
    tvdb_id = Column(Integer, nullable=True, index=True)
    anilist_id = Column(Integer, nullable=True, index=True)
    added_at = Column(DateTime(timezone=True), default=func.now())
    notes = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("external_id", "category", name="uq_wishlist_external_id_category"),
    )


class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True)
    key = Column(String, nullable=False, unique=True, index=True)
    value = Column(Text, nullable=True)
    is_secret = Column(Boolean, default=False)
    description = Column(String, nullable=True)


class TaskStatus(Base):
    __tablename__ = "task_status"
    id = Column(Integer, primary_key=True)
    task_id = Column(String, nullable=False, unique=True, index=True)
    task_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    progress = Column(Integer, default=0)
    message = Column(String, nullable=True)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class PlexLibraryMapping(Base):
    __tablename__ = "plex_library_mappings"
    id = Column(Integer, primary_key=True)
    library_key = Column(String, nullable=False, unique=True)
    library_name = Column(String, nullable=False)
    category = Column(Enum(CategoryEnum), nullable=False)


class TMDBCollection(Base):
    __tablename__ = "tmdb_collections"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    total = Column(Integer, nullable=False, default=0)
    poster_url = Column(String, nullable=True)
    backdrop_url = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
