from msgspec import Struct


class WorkLocation(Struct):
    id: str
    label: str


class Department(Struct):
    id: str
    label: str


class JobOutline(Struct):
    uuid: str
    name: str
    department: Department
    url: str
    workLocation: WorkLocation
