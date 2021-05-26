from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import LabOrder

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.laborders import delete_laborder, get_laborder, get_laborders
from ukrdc_fastapi.schemas.laborder import LabOrderSchema, LabOrderShortSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter(tags=["Lab Orders"])


@router.get(
    "/",
    response_model=Page[LabOrderShortSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def laborders(
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a list of all lab orders"""
    return paginate(get_laborders(ukrdc3, user))


@router.get(
    "/{order_id}/",
    response_model=LabOrderSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def laborder_get(
    order_id: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
) -> LabOrder:
    """Retreive a particular lab order"""
    return get_laborder(ukrdc3, order_id, user)


@router.delete(
    "/{order_id}/",
    status_code=204,
    dependencies=[Security(auth.permission(Permissions.WRITE_RECORDS))],
)
def laborder_delete(
    order_id: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
) -> None:
    """Mark a particular lab order for deletion"""
    delete_laborder(ukrdc3, order_id, user)
