"""empty message

Revision ID: 9124a3977e09
Revises: 068dbcd14588
Create Date: 2021-02-20 17:05:27.651623

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9124a3977e09'
down_revision = '068dbcd14588'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('serving_size', table_name='food')
    op.drop_index('serving_unit', table_name='food')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('serving_unit', 'food', ['serving_unit'], unique=True)
    op.create_index('serving_size', 'food', ['serving_size'], unique=True)
    # ### end Alembic commands ###
