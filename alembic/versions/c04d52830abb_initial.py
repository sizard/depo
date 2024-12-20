"""initial

Revision ID: c04d52830abb
Revises: 
Create Date: 2024-11-27 23:28:24.226599

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c04d52830abb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('full_name', sa.String(), nullable=False),
    sa.Column('position', sa.String(), nullable=False),
    sa.Column('railway', sa.Enum('YUGO_VOSTOCHNAYA', 'MOSKOVSKAYA', 'PRIVOLZHSKAYA', 'SEVERO_KAVKAZSKAYA', 'KALININGRADSKAYA', 'GORKOVSKAYA', 'DALNEVOSTOCHNAYA', 'ZABAIKALSKAYA', 'ZAPADNOSIBIRSKAYA', 'KRASNOYARSKAYA', 'KUYBYSHEVSKAYA', 'OKTYABRSKAYA', 'SVERDLOVSKAYA', 'SEVERO_ZAPADNAYA', 'SEVERNAYA', 'YUGO_ZAPADNAYA', name='railway'), nullable=False),
    sa.Column('branch', sa.String(), nullable=False),
    sa.Column('phone', sa.String(), nullable=False),
    sa.Column('role', sa.Enum('USER', 'ADMIN', name='userrole'), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_blocked', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('train_receptions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('train_number', sa.String(), nullable=False),
    sa.Column('train_type', sa.Enum('ELEKTRICHKA', 'RAIL_BUS', name='traintype'), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('is_completed', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('blocks_in_train',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('reception_id', sa.Integer(), nullable=False),
    sa.Column('block_number', sa.String(), nullable=False),
    sa.Column('is_checked', sa.Boolean(), nullable=True),
    sa.Column('notes', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['reception_id'], ['train_receptions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('blocks_in_train')
    op.drop_table('train_receptions')
    op.drop_table('users')
    # ### end Alembic commands ###
