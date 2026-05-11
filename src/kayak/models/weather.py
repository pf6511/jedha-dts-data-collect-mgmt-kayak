
from sqlalchemy import Column, Integer, String, DateTime, Numeric

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import ForeignKey,UniqueConstraint

from kayak.models.base import Base

class DestinationWeatherForecast(Base):
    __tablename__ = "destination_weather_forecast"

    #id = Column(Integer, Sequence('seq_destination_weatherforecast_id', start=1, increment=1),primary_key=True)
    destination_id = Column(Integer, ForeignKey("destination.destination_id"),primary_key=True)
    dt = Column(DateTime(timezone=True), primary_key=True)
    temp = Column(Numeric(5,2))
    temp_min = Column(Numeric(5,2))
    temp_max = Column(Numeric(5,2))
    pressure = Column(Integer)
    humidity = Column(Integer)
    weather_main = Column(String)
    weather_descr = Column(String)
    clouds_info_dict = Column(JSONB, nullable=True)
    pop = Column(Numeric(5,3))

    '''
    __table_args__ = (
        UniqueConstraint('destination_id', 'dt', name='uq_destination_dt'),
    )
    '''

    def __repr__(self):
        return (
            f"<DestinationWeatherForecast(destination_id={self.destination_id}, "
            f"dt='{self.dt}')>"
        )
    

class DestinationWeatherScorePeriod(Base):
     __tablename__ = "destination_weather_score_period"

     #id = Column(Integer, Sequence('seq_destination_weatherscoreperiod_id', start=1, increment=1),primary_key=True)
     #id = Column(Integer,primary_key=True)
     destination_id = Column(Integer, ForeignKey("destination.destination_id"),primary_key=True)
     weather_median_score = Column(Numeric(5,3))
     avg_temp = Column(Numeric(5,2))
     weather_rank = Column(Integer)
     start_date = Column(DateTime(timezone=True), primary_key=True)
     end_date = Column(DateTime(timezone=True), primary_key=True)


     def __repr__(self):
        return (
            f"<DestinationWeatherScorePeriod(destination_id={self.destination_id}, "
            f"start_date={self.start_date}, "
            f"end_date={self.end_date})>"
        )

"""      __table_args__ = (
        UniqueConstraint(
            'destination_id',
            'start_date',
            'end_date',
            name='uq_destination_period'
        ),
    ) """
    