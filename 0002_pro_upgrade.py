"""pro upgrade - add kyc, premium, spin, encryption, xp, rating, complaints

Revision ID: 0002
Revises: 
Create Date: 2026-09-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_pro_upgrade"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # users additions
    for col, typ in [
        ("language", sa.String(5)),
        ("captcha_verified", sa.Boolean()),
        ("premium_until", sa.DateTime(timezone=True)),
        ("kyc_status", sa.String(16)),
        ("kyc_data", sa.String(512)),
        ("total_referral_volume", sa.Integer()),
        ("last_spin", sa.DateTime(timezone=True)),
        ("referrals_today", sa.Integer()),
        ("referrals_today_date", sa.DateTime(timezone=True)),
        ("xp", sa.Integer()),
        ("achievements", sa.Text()),
    ]:
        try:
            op.add_column("users", sa.Column(col, typ, nullable=True))
        except Exception:
            pass
    # withdrawals
    for col, typ in [("proof_url", sa.String(512)), ("tx_hash", sa.String(128))]:
        try:
            op.add_column("withdrawals", sa.Column(col, typ, nullable=True))
        except:
            pass
    # campaign_ratings
    try:
        op.create_table("campaign_ratings",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("campaign_id", sa.Integer, sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
            sa.Column("rating", sa.Integer, nullable=False),
            sa.Column("comment", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", "campaign_id", name="uq_user_campaign_rating")
        )
    except:
        pass
    # complaints
    try:
        op.create_table("complaints",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("campaign_id", sa.Integer, sa.ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True),
            sa.Column("reason", sa.String(256), nullable=False),
            sa.Column("status", sa.String(16), server_default="open"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    except:
        pass

def downgrade():
    for tbl in ["complaints", "campaign_ratings"]:
        try:
            op.drop_table(tbl)
        except:
            pass
