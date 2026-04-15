"""phase 1 schema

Revision ID: 202604110001
Revises:
Create Date: 2026-04-11 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202604110001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "drivers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("driver_id", sa.String(length=40), nullable=False),
        sa.Column("primary_email", sa.String(length=320), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("driver_id", name="uq_drivers_driver_id"),
    )
    op.create_index("ix_drivers_primary_email", "drivers", ["primary_email"])

    op.create_table(
        "driver_identities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("driver_fk", sa.String(length=36), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_subject_id", sa.String(length=256), nullable=False),
        sa.Column("provider_email", sa.String(length=320), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("provider", "provider_subject_id", name="uq_driver_identity_provider"),
    )
    op.create_index("ix_driver_identities_driver_fk", "driver_identities", ["driver_fk"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("driver_fk", sa.String(length=36), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("jti_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("jti_hash", name="uq_refresh_tokens_jti_hash"),
    )
    op.create_index("ix_refresh_tokens_driver_fk", "refresh_tokens", ["driver_fk"])

    op.create_table(
        "trips",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("trip_id", sa.String(length=48), nullable=False),
        sa.Column("driver_fk", sa.String(length=36), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("client_trip_id", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("start_lat", sa.Float(), nullable=True),
        sa.Column("start_lng", sa.Float(), nullable=True),
        sa.Column("end_lat", sa.Float(), nullable=True),
        sa.Column("end_lng", sa.Float(), nullable=True),
        sa.Column("device_platform", sa.String(length=32), nullable=True),
        sa.Column("app_version", sa.String(length=32), nullable=True),
        sa.Column("os_version", sa.String(length=32), nullable=True),
        sa.Column("device_distance_meters", sa.Float(), nullable=True),
        sa.Column("total_distance_meters", sa.Float(), nullable=True),
        sa.Column("point_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("trip_id", name="uq_trips_trip_id"),
        sa.UniqueConstraint("driver_fk", "client_trip_id", name="uq_trips_driver_client_trip"),
    )
    op.create_index("ix_trips_driver_started", "trips", ["driver_fk", "started_at"])
    op.create_index("ix_trips_status", "trips", ["status"])

    op.create_table(
        "trip_point_batches",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("trip_fk", sa.String(length=36), sa.ForeignKey("trips.id"), nullable=False),
        sa.Column("batch_id", sa.String(length=120), nullable=False),
        sa.Column("accepted_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("trip_fk", "batch_id", name="uq_trip_point_batches_trip_batch"),
    )

    op.create_table(
        "trip_points",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("trip_fk", sa.String(length=36), sa.ForeignKey("trips.id"), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("horizontal_accuracy", sa.Float(), nullable=False),
        sa.Column("vertical_accuracy", sa.Float(), nullable=True),
        sa.Column("speed_mps", sa.Float(), nullable=True),
        sa.Column("course_degrees", sa.Float(), nullable=True),
        sa.Column("altitude_meters", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="ios_corelocation"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "trip_fk",
            "recorded_at",
            "latitude",
            "longitude",
            name="uq_trip_points_trip_time_location",
        ),
    )
    op.create_index("ix_trip_points_trip_recorded", "trip_points", ["trip_fk", "recorded_at"])

    op.create_table(
        "media_objects",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("media_id", sa.String(length=48), nullable=False),
        sa.Column("driver_fk", sa.String(length=36), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("bucket_name", sa.String(length=120), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("original_file_name", sa.String(length=255), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("processing_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("media_id", name="uq_media_objects_media_id"),
        sa.UniqueConstraint("storage_key", name="uq_media_objects_storage_key"),
    )
    op.create_index("ix_media_objects_driver_fk", "media_objects", ["driver_fk"])

    op.create_table(
        "sticker_submissions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("submission_id", sa.String(length=48), nullable=False),
        sa.Column("driver_fk", sa.String(length=36), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("media_object_fk", sa.String(length=36), sa.ForeignKey("media_objects.id"), nullable=False),
        sa.Column("trip_fk", sa.String(length=36), sa.ForeignKey("trips.id"), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("gps_lat", sa.Float(), nullable=True),
        sa.Column("gps_lng", sa.Float(), nullable=True),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("submission_id", name="uq_sticker_submissions_submission_id"),
    )
    op.create_index("ix_sticker_submissions_driver_submitted", "sticker_submissions", ["driver_fk", "submitted_at"])

    op.create_table(
        "odometer_submissions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("submission_id", sa.String(length=48), nullable=False),
        sa.Column("driver_fk", sa.String(length=36), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("media_object_fk", sa.String(length=36), sa.ForeignKey("media_objects.id"), nullable=False),
        sa.Column("trip_fk", sa.String(length=36), sa.ForeignKey("trips.id"), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("gps_lat", sa.Float(), nullable=True),
        sa.Column("gps_lng", sa.Float(), nullable=True),
        sa.Column("ocr_value", sa.Integer(), nullable=True),
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("submission_id", name="uq_odometer_submissions_submission_id"),
    )
    op.create_index("ix_odometer_submissions_driver_submitted", "odometer_submissions", ["driver_fk", "submitted_at"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("driver_id", sa.String(length=40), nullable=True),
        sa.Column("trip_id", sa.String(length=48), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_events_created", "audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_index("ix_odometer_submissions_driver_submitted", table_name="odometer_submissions")
    op.drop_table("odometer_submissions")
    op.drop_index("ix_sticker_submissions_driver_submitted", table_name="sticker_submissions")
    op.drop_table("sticker_submissions")
    op.drop_index("ix_media_objects_driver_fk", table_name="media_objects")
    op.drop_table("media_objects")
    op.drop_index("ix_trip_points_trip_recorded", table_name="trip_points")
    op.drop_table("trip_points")
    op.drop_table("trip_point_batches")
    op.drop_index("ix_trips_status", table_name="trips")
    op.drop_index("ix_trips_driver_started", table_name="trips")
    op.drop_table("trips")
    op.drop_index("ix_refresh_tokens_driver_fk", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_driver_identities_driver_fk", table_name="driver_identities")
    op.drop_table("driver_identities")
    op.drop_index("ix_drivers_primary_email", table_name="drivers")
    op.drop_table("drivers")
