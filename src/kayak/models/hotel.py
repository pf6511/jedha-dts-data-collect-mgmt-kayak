from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import Column, Integer, String, SmallInteger, Date, Float

from sqlalchemy import ForeignKey

from kayak.models.base import Base

class HotelSearchParam(Base):
    __tablename__ = "hotel_search_param"

    #id = Column(Integer, Sequence('seq_hotel_search_param_id', start=1, increment=1),primary_key=True)
    search_id = Column(UUID(as_uuid=True), primary_key=True,default=uuid.uuid4)
    checkin_date = Column(Date, nullable=False)
    checkout_date = Column(Date, nullable=False)
    destination_country = Column(String(50), nullable=False)
    destination_type = Column(String(50), nullable=False)
    group_adults = Column(SmallInteger)
    group_children = Column(SmallInteger)


    def __repr__(self):
        return (
            f"<HotelSearchParam(id={self.id}, "
            f"search_id='{self.search_id}')>"
        )
    

class HotelSearchResult(Base):
    __tablename__ = "hotel_search_result"

    id = Column(Integer,primary_key=True, autoincrement=True)
    search_id = Column(
        UUID(as_uuid=True),
        ForeignKey("hotel_search_param.search_id", ondelete="CASCADE"),
        nullable=False
    )
    destination_id = Column(Integer, nullable=False)
    hotel_name = Column(String)
    url = Column(String)
    gps_lat = Column(Float)
    gps_long = Column(Float)
    score = Column(Float)
    description = Column(String)
    address = Column(String)

    def __repr__(self):
        return (
            f"<HotelSearchResult(id={self.id}, "
            f"search_id='{self.search_id}', "
            f"destination_id={self.destination_id}, "
            f"hotel_name='{self.hotel_name}' )>"
        )