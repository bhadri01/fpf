from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database.base_model import Base

class Country(Base):
    __tablename__ = "countries"

    name: Mapped[str] = mapped_column(String, unique=True, index=True)

    # Relationships
    states: Mapped[list["State"]] = relationship("State", back_populates="country")
    __allowed__ = True  


class State(Base):
    __tablename__ = "states"

    name: Mapped[str] = mapped_column(String, index=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"))

    # Relationships
    country: Mapped["Country"] = relationship("Country", back_populates="states")
    districts: Mapped[list["District"]] = relationship("District", back_populates="state")
    __allowed__ = True  


class District(Base):
    __tablename__ = "districts"

    name: Mapped[str] = mapped_column(String, index=True)
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"))

    # Relationships
    state: Mapped["State"] = relationship("State", back_populates="districts")
    __allowed__ = True  
