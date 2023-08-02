"""init db

Revision ID: 57ff5da24acb
Revises: 
Create Date: 2023-08-02 14:14:46.087796

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '57ff5da24acb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('nonebot_plugin_bind_user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('nonebot_plugin_bind_platformuser',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('platform', sa.String(), nullable=False),
    sa.Column('account', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['nonebot_plugin_bind_user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('platform', 'account', name='uc_platform_account')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('nonebot_plugin_bind_platformuser')
    op.drop_table('nonebot_plugin_bind_user')
    # ### end Alembic commands ###
