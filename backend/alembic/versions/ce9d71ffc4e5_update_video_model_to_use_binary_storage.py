"""Update video model to use binary storage

Revision ID: ce9d71ffc4e5
Revises: 
Create Date: 2025-04-03 14:12:06.192486

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce9d71ffc4e5'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('videos', sa.Column('video_data', sa.LargeBinary(), nullable=True))
    op.drop_column('videos', 'filepath')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('videos', sa.Column('filepath', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('videos', 'video_data')
    # ### end Alembic commands ###
