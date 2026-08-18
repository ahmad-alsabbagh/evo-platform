import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_create_evaluation_runs"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.String(length=256), primary_key=True),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("capability_id", sa.String(length=256), nullable=False),
        sa.Column("capability_version", sa.String(length=64), nullable=False),
        sa.Column("dataset_id", sa.String(length=256), nullable=False),
        sa.Column("dataset_version", sa.String(length=64), nullable=False),
        sa.Column("dataset_hash", sa.String(length=71), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("promotion", sa.String(length=32), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.String(length=256)),
    )
    op.create_index(
        "ix_evaluation_runs_capability",
        "evaluation_runs",
        ["capability_id", "capability_version"],
    )
    op.create_index("ix_evaluation_runs_created_at", "evaluation_runs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_evaluation_runs_created_at", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_capability", table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
