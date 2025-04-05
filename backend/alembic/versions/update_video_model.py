"""update video model

Revision ID: update_video_model
Revises: 
Create Date: 2024-04-05 12:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_video_model'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Drop the old video_data column if it exists
    op.drop_column('videos', 'video_data')
    
    # Add the new filepath column
    op.add_column('videos', sa.Column('filepath', sa.String(), nullable=True))
    
    # Add the processed_filepath column if it doesn't exist
    op.add_column('videos', sa.Column('processed_filepath', sa.String(), nullable=True))


def downgrade():
    # Remove the new columns
    op.drop_column('videos', 'filepath')
    op.drop_column('videos', 'processed_filepath')
    
    # Add back the video_data column
    op.add_column('videos', sa.Column('video_data', sa.LargeBinary(), nullable=True)) 