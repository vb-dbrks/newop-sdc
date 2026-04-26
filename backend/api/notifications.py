from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(unread: bool = False):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{notification_id}:read")
async def mark_read(notification_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post(":read-all")
async def mark_all_read():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
