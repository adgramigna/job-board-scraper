from msgspec import Struct
from typing import Optional
from datetime import datetime


class PostalAddress(Struct):
    addressCountry: Optional[str] = None
    addressLocality: Optional[str] = None
    addressRegion: Optional[str] = None


class Address(Struct):
    postalAddress: PostalAddress


class SecondaryLocation(Struct):
    location: Optional[str] = None
    address: Optional[Address] = None


class JobOutline(Struct):
    id: str
    title: str
    department: str
    team: str
    employmentType: str
    location: str
    publishedAt: datetime
    jobUrl: str
    descriptionPlain: str
    secondaryLocations: list[SecondaryLocation]
    isRemote: Optional[bool]
    isListed: Optional[bool]
    address: Optional[Address] = None
    shouldDisplayCompensationOnJobPostings: Optional[bool] = None
