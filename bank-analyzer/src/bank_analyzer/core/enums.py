import enum


class Category(enum.Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    SALARY = "salary"
    HOUSING = "housing"
    INVESTMENTS = "investments"
    EDUCATION = "education"
    HEALTH = "health"
    LEISURE = "leisure"
    OTHER = "other"


class TransactionType(enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class Status(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
