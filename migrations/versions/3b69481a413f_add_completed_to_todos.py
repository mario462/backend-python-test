"""add completed to todos

Revision ID: 3b69481a413f
Revises: d6ca03c8bcb2
Create Date: 2019-07-11 12:32:21.602705

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3b69481a413f'
down_revision = 'd6ca03c8bcb2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('todo', sa.Column('completed', sa.Boolean(), server_default='0', nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('todo', 'completed')
    # ### end Alembic commands ###