from sqlalchemy.future import select
from sqlalchemy.sql import func

async def paginate_query(session, query, page, size):
    # Count total items (without loading them all)
    total_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(total_query)).scalar()

    # Apply Pagination Efficiently at the DB Level
    paginated_query = query.offset((page - 1) * size).limit(size)

    # Fetch only the required data
    results = await session.execute(paginated_query)
    result = results.scalars().all()

    response_data = {
        "items": result,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total // size) + (1 if total % size else 0),
    }

    return response_data