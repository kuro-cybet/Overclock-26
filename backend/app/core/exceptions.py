from fastapi import HTTPException, status

class CampusOpsException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)

class EntityNotFoundError(CampusOpsException):
    def __init__(self, entity_name: str, entity_id: any):
        super().__init__(
            detail=f"{entity_name} with identifier '{entity_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

class PermissionDeniedError(CampusOpsException):
    def __init__(self, action: str, reason: str = "Insufficient permissions"):
        super().__init__(
            detail=f"Access denied for action '{action}': {reason}",
            status_code=status.HTTP_403_FORBIDDEN,
        )

class InvalidStateTransitionError(CampusOpsException):
    def __init__(self, current_state: str, attempted_state: str, allowed_states: list):
        super().__init__(
            detail=f"Cannot transition from '{current_state}' to '{attempted_state}'. Valid transitions are: {allowed_states}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

class StockUnavailableError(CampusOpsException):
    def __init__(self, item_name: str, requested: int, available: int):
        super().__init__(
            detail=f"Cannot reserve {requested} units of '{item_name}'. Only {available} available.",
            status_code=status.HTTP_409_CONFLICT,
        )

class BookingConflictError(CampusOpsException):
    def __init__(self, room_name: str, conflict_details: str):
        super().__init__(
            detail=f"Booking conflict in room '{room_name}': {conflict_details}",
            status_code=status.HTTP_409_CONFLICT,
        )

class SeparationOfDutiesError(CampusOpsException):
    def __init__(self, message: str = "Separation of duties policy violated. Requester cannot approve their own submission."):
        super().__init__(
            detail=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )
