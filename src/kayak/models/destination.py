from sqlalchemy import Column, Integer, String, Float
from kayak.models.base import Base


class Destination(Base):
    __tablename__ = "destination"

    destination_id = Column(Integer, primary_key=True)
    destination_key = Column(String)
    destination = Column(String)
    gps_long = Column(Float, nullable=False)
    gps_lat = Column(Float, nullable=False)

    def __repr__(self):
        return (
            f"<Destination(destination_id={self.destination_id}, "
            f"destination='{self.destination}', "
            f"gps=({self.gps_lat}, {self.gps_long}))>"
        )