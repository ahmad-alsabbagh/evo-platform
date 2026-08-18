import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_create_catalog_entries"
down_revision = "0001_create_evaluation_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_entries",
        sa.Column("id", sa.String(length=256), primary_key=True),
        sa.Column("capability_id", sa.String(length=256), nullable=False),
        sa.Column("capability_version", sa.String(length=64), nullable=False),
        sa.Column("lifecycle", sa.String(length=32), nullable=False),
        sa.Column("risk_level", sa.String(length=16), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "capability_id",
            "capability_version",
            name="uq_catalog_capability_version",
        ),
    )
    op.create_index("ix_catalog_entries_lifecycle", "catalog_entries", ["lifecycle"])
    op.create_index("ix_catalog_entries_risk_level", "catalog_entries", ["risk_level"])
    op.create_table(
        "promotion_decisions",
        sa.Column("id", sa.String(length=256), primary_key=True),
        sa.Column("catalog_entry_id", sa.String(length=256), nullable=False),
        sa.Column("evaluation_run_id", sa.String(length=256), nullable=False),
        sa.Column("allowed", sa.Boolean(), nullable=False),
        sa.Column("target_lifecycle", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("policy_snapshot_hash", sa.String(length=71)),
        sa.Column("reasons", postgresql.JSONB(), nullable=False),
        sa.Column("actor", sa.String(length=256)),
        sa.Column("artifact_digest", sa.String(length=71)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["catalog_entry_id"], ["catalog_entries.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["evaluation_run_id"], ["evaluation_runs.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_promotion_decisions_catalog_id",
        "promotion_decisions",
        ["catalog_entry_id"],
    )
    op.create_index("ix_promotion_decisions_created_at", "promotion_decisions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_promotion_decisions_created_at", table_name="promotion_decisions")
    op.drop_index("ix_promotion_decisions_catalog_id", table_name="promotion_decisions")
    op.drop_table("promotion_decisions")
    op.drop_index("ix_catalog_entries_risk_level", table_name="catalog_entries")
    op.drop_index("ix_catalog_entries_lifecycle", table_name="catalog_entries")
    op.drop_table("catalog_entries")
