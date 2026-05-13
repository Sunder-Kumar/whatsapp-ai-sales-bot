from sqlalchemy.future import select
from sqlalchemy import func, desc
from db.models import Order, Conversation, Message, Customer
from datetime import datetime, timedelta

async def get_dashboard_stats(db_session):
    """
    Calculates summary statistics for the dashboard.
    """
    # Total Revenue
    revenue_result = await db_session.execute(
        select(func.sum(Order.amount_paid)).where(Order.status == 'delivered')
    )
    total_revenue = revenue_result.scalar() or 0

    # Total Sales
    sales_result = await db_session.execute(
        select(func.count(Order.id)).where(Order.status == 'delivered')
    )
    total_sales = sales_result.scalar() or 0

    # Active Chats (updated in last 24h)
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    active_chats_result = await db_session.execute(
        select(func.count(Conversation.id)).where(Conversation.updated_at >= one_day_ago)
    )
    active_chats = active_chats_result.scalar() or 0

    return {
        "total_revenue": total_revenue,
        "total_sales": total_sales,
        "active_chats": active_chats
    }

async def get_sales_by_package(db_session):
    """
    Returns sales count grouped by package name.
    """
    result = await db_session.execute(
        select(Order.package_name, func.count(Order.id))
        .where(Order.status == 'delivered')
        .group_by(Order.package_name)
    )
    return dict(result.all())

async def get_daily_sales_trend(db_session, days=7):
    """
    Returns sales count for each of the last X days.
    """
    since = datetime.utcnow() - timedelta(days=days)
    result = await db_session.execute(
        select(func.date(Order.created_at), func.count(Order.id))
        .where(Order.status == 'delivered', Order.created_at >= since)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
    )
    return dict(result.all())
