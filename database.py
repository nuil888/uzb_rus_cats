import logging
import time
from typing import Any, Optional, Sequence
from sqlalchemy import BigInteger, String, Integer, select, func, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import DB_URL

logging.basicConfig(level=logging.INFO)

engine = create_async_engine(
    DB_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True
)

async_session = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

# Простой TTL кэш в памяти для каталогов по городам
_CAT_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_FLAT_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
CACHE_TTL = 60.0  # секунды

def clear_catalog_cache():
    _CAT_CACHE.clear()
    _FLAT_CACHE.clear()

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    lang: Mapped[str] = mapped_column(String, default="ru")
    balance: Mapped[int] = mapped_column(Integer, default=0)

class Cat(Base):
    __tablename__ = "cats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    msg_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    photo: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[str] = mapped_column(String, nullable=False)
    nationality: Mapped[str] = mapped_column(String, default="Не указано")
    city: Mapped[str] = mapped_column(String, nullable=False, index=True)
    price_walk: Mapped[int] = mapped_column(Integer, default=0)
    price_hour: Mapped[int] = mapped_column(Integer, default=0)
    price_night: Mapped[int] = mapped_column(Integer, default=0)

class Flat(Base):
    __tablename__ = "flats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    msg_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    photos: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False, index=True)
    price_day: Mapped[int] = mapped_column(Integer, default=0)

class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)

async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def _user_to_dict(user: Optional[User]) -> Optional[dict[str, Any]]:
    if not user:
        return None
    return {
        "user_id": user.user_id,
        "name": user.name or "Не указано",
        "phone": user.phone or "",
        "city": user.city or "",
        "lang": user.lang or "ru",
        "balance": user.balance or 0,
    }

def _cat_to_dict(cat: Optional[Cat]) -> Optional[dict[str, Any]]:
    if not cat:
        return None
    return {
        "id": cat.id,
        "msg_id": cat.msg_id or cat.id,
        "photo": cat.photo,
        "name": cat.name,
        "age": cat.age,
        "nationality": cat.nationality or "Не указано",
        "city": cat.city,
        "price_walk": cat.price_walk or 0,
        "price_hour": cat.price_hour or 0,
        "price_night": cat.price_night or 0,
    }

def _flat_to_dict(flat: Optional[Flat]) -> Optional[dict[str, Any]]:
    if not flat:
        return None
    photos_list = [p.strip() for p in flat.photos.split(",") if p.strip()] if flat.photos else []
    return {
        "id": flat.id,
        "msg_id": flat.msg_id or flat.id,
        "photos": photos_list,
        "title": flat.title,
        "location": flat.location,
        "city": flat.city,
        "price_day": flat.price_day or 0,
    }

async def db_get_user(user_id: int) -> Optional[dict[str, Any]]:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        return _user_to_dict(result.scalar_one_or_none())

async def db_add_user(user_id: int, name: str, phone: str, city: str, lang: str = "ru") -> Optional[dict[str, Any]]:
    async with async_session() as session:
        user = User(user_id=user_id, name=name, phone=phone, city=city, lang=lang, balance=0)
        session.add(user)
        await session.commit()
        return _user_to_dict(user)

async def db_update_user_lang(user_id: int, lang: str) -> None:
    async with async_session() as session:
        await session.execute(
            update(User).where(User.user_id == user_id).values(lang=lang)
        )
        await session.commit()

async def db_update_user_field(user_id: int, field: str, value: Any) -> None:
    async with async_session() as session:
        if hasattr(User, field):
            await session.execute(
                update(User).where(User.user_id == user_id).values({field: value})
            )
            await session.commit()

async def db_change_user_balance(user_id: int, delta: int) -> bool:
    """Safely increments or decrements balance atomically."""
    async with async_session() as session:
        user = (await session.execute(select(User).where(User.user_id == user_id))).scalar_one_or_none()
        if not user:
            return False
        if delta < 0 and user.balance + delta < 0:
            return False
        user.balance += delta
        await session.commit()
        return True

async def db_get_all_users() -> Sequence[User]:
    async with async_session() as session:
        result = await session.scalars(select(User))
        return result.all()

async def db_add_cat(msg_id: int, photo: str, name: str, age: str, nationality: str, city: str, price_walk: int, price_hour: int, price_night: int) -> None:
    async with async_session() as session:
        cat = Cat(
            msg_id=msg_id, 
            photo=photo, 
            name=name, 
            age=age, 
            nationality=nationality, 
            city=city, 
            price_walk=price_walk, 
            price_hour=price_hour, 
            price_night=price_night
        )
        session.add(cat)
        await session.commit()
        clear_catalog_cache()

async def db_get_cats_by_city(city: str) -> list[dict[str, Any]]:
    now = time.time()
    if city in _CAT_CACHE:
        ts, data = _CAT_CACHE[city]
        if now - ts < CACHE_TTL:
            return data

    async with async_session() as session:
        result = await session.scalars(select(Cat).where(Cat.city == city))
        res = [_cat_to_dict(c) for c in result.all() if c]
        _CAT_CACHE[city] = (now, res)
        return res

async def db_get_cat_by_id(cat_id: int) -> Optional[dict[str, Any]]:
    async with async_session() as session:
        result = await session.scalars(select(Cat).where((Cat.msg_id == cat_id) | (Cat.id == cat_id)))
        return _cat_to_dict(result.first())

async def db_update_cat_field(cat_id: int, field: str, value: Any) -> None:
    async with async_session() as session:
        if hasattr(Cat, field):
            await session.execute(
                update(Cat).where((Cat.msg_id == cat_id) | (Cat.id == cat_id)).values({field: value})
            )
            await session.commit()
            clear_catalog_cache()

async def db_delete_cat(msg_id: int) -> None:
    async with async_session() as session:
        result = await session.scalars(select(Cat).where((Cat.msg_id == msg_id) | (Cat.id == msg_id)))
        cat = result.first()
        if cat:
            await session.delete(cat)
            await session.commit()
            clear_catalog_cache()

async def db_get_all_cats() -> Sequence[Cat]:
    async with async_session() as session:
        result = await session.scalars(select(Cat))
        return result.all()

async def db_add_flat(msg_id: int, photos: list[str], title: str, location: str, city: str, price_day: int) -> None:
    async with async_session() as session:
        photos_str = ",".join(photos)
        flat = Flat(
            msg_id=msg_id,
            photos=photos_str,
            title=title,
            location=location,
            city=city,
            price_day=price_day
        )
        session.add(flat)
        await session.commit()
        clear_catalog_cache()

async def db_get_flats_by_city(city: str) -> list[dict[str, Any]]:
    now = time.time()
    if city in _FLAT_CACHE:
        ts, data = _FLAT_CACHE[city]
        if now - ts < CACHE_TTL:
            return data

    async with async_session() as session:
        result = await session.scalars(select(Flat).where(Flat.city == city))
        res = [_flat_to_dict(f) for f in result.all() if f]
        _FLAT_CACHE[city] = (now, res)
        return res

async def db_get_flat_by_id(flat_id: int) -> Optional[dict[str, Any]]:
    async with async_session() as session:
        result = await session.scalars(select(Flat).where((Flat.msg_id == flat_id) | (Flat.id == flat_id)))
        return _flat_to_dict(result.first())

async def db_update_flat_field(flat_id: int, field: str, value: Any) -> None:
    async with async_session() as session:
        if field == "photos" and isinstance(value, list):
            value = ",".join(value)
        if hasattr(Flat, field):
            await session.execute(
                update(Flat).where((Flat.msg_id == flat_id) | (Flat.id == flat_id)).values({field: value})
            )
            await session.commit()
            clear_catalog_cache()

async def db_delete_flat(msg_id: int) -> None:
    async with async_session() as session:
        result = await session.scalars(select(Flat).where((Flat.msg_id == msg_id) | (Flat.id == msg_id)))
        flat = result.first()
        if flat:
            await session.delete(flat)
            await session.commit()
            clear_catalog_cache()

async def db_get_all_flats() -> Sequence[Flat]:
    async with async_session() as session:
        result = await session.scalars(select(Flat))
        return result.all()

async def db_get_stats() -> tuple[int, int, int]:
    async with async_session() as session:
        u_count = await session.scalar(select(func.count(User.user_id)))
        c_count = await session.scalar(select(func.count(Cat.id)))
        f_count = await session.scalar(select(func.count(Flat.id)))
        return u_count or 0, c_count or 0, f_count or 0

async def db_get_setting(key: str, default: str = "") -> str:
    async with async_session() as session:
        result = await session.scalars(select(Setting).where(Setting.key == key))
        setting = result.first()
        return setting.value if setting else default

async def db_set_setting(key: str, value: str) -> None:
    async with async_session() as session:
        result = await session.scalars(select(Setting).where(Setting.key == key))
        setting = result.first()
        if setting:
            setting.value = value
        else:
            session.add(Setting(key=key, value=value))
        await session.commit()
