from sqlalchemy.future import select
from sqlalchemy import update
from db.models import Credential, Order, Conversation
from datetime import datetime

async def get_unassigned_credential(db_session, package_name):
    """
    Fetches one unassigned credential for a specific package.
    """
    result = await db_session.execute(
        select(Credential).where(
            Credential.package_name == package_name,
            Credential.assigned_to == None
        ).limit(1)
    )
    return result.scalars().first()

async def assign_credential(db_session, credential_id, phone):
    """
    Marks a credential as assigned to a phone number.
    """
    await db_session.execute(
        update(Credential)
        .where(Credential.id == credential_id)
        .values(assigned_to=phone, assigned_at=datetime.utcnow())
    )
    await db_session.commit()

async def update_order_status(db_session, phone, status):
    """
    Updates the latest order status for a customer.
    """
    await db_session.execute(
        update(Order)
        .where(Order.phone == phone)
        .values(status=status)
    )
    await db_session.commit()

async def update_conversation_stage(db_session, phone, stage):
    """
    Updates the sales stage for a customer.
    """
    await db_session.execute(
        update(Conversation)
        .where(Conversation.phone == phone)
        .values(stage=stage, updated_at=datetime.utcnow())
    )
    await db_session.commit()
