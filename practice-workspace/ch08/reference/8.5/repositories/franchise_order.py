"""가맹점 발주 저장.

검증과 판단을 마친 BranchOrderPlan을 발주 마스터·상세·감사 기록으로 한 트랜잭션에 저장한다.
"""

from sqlalchemy.orm import Session

from models import AuditLog, PurchaseOrder, PurchaseOrderDetail
from services.franchise_order import BranchOrderPlan


def persist_franchise_order(plan: BranchOrderPlan, db: Session) -> int:
    """발주 계획을 마스터·상세·감사로 한 트랜잭션에 저장하고 발주번호를 돌려준다.

    저장 순서는 마스터 flush(DB가 발주번호 생성) → 모든 상세 flush → 감사 flush다.
    상세와 감사에는 마스터가 만든 발주번호를 연결한다. 상세에는 계획의 서버 단가·공급가액·
    VAT·합계를, 감사에는 action "INSERT"와 상세 건수·총액을 남긴다. 발주 마스터·상세·감사
    외의 테이블은 읽지도 쓰지도 않는다.

    세션 조건:
        이 함수가 `db.begin()`으로 트랜잭션을 직접 시작하므로, 받는 Session은 트랜잭션이
        시작되지 않은 상태여야 한다. Session은 조회·add 등의 작업으로 트랜잭션을 자동 시작(autobegin)할 수 있다.
        조회 등으로 트랜잭션을 시작하고 커밋·롤백하지 않은 세션을
        넘기면 `InvalidRequestError`가 발생한다. 호출자가 연 트랜잭션에 참여하는 함수가
        아니다. 필요한 flush는 이 함수가 명시적으로 호출하므로 autoflush에 의존하지 않는다.

    트랜잭션 결과:
        블록이 정상 종료될 때만 커밋한다. 마스터·상세·감사 중 어느 저장에서든 예외가 나면
        전체를 롤백하고 예외를 그대로 다시 던진다. 예외 변환은 호출자의 몫이다.

    8.5 확인 사항:
        API 연결에서 상품 조회와 이 저장 함수를 어떤 세션 상태로 이어 호출할지는 8.5의 규약과
        실제 코드로 확인할 사항이다. 이 단계에서는 확정하거나 구현하지 않았다.

    Args:
        plan: 서버가 계산한 불변 발주 계획. 상세가 1건 이상이어야 한다.
        db: 트랜잭션이 시작되지 않은 SQLAlchemy Session.

    Returns:
        DB가 만든 발주번호.
    """
    with db.begin():
        order = PurchaseOrder(
            corp_id=plan.corp_id,
            partner_id=plan.partner_id,
            dept_code=plan.dept_code,
            emp_code=plan.emp_code,
            delivery_code=plan.delivery_code,
            is_vat=plan.is_vat,
            order_status=plan.order_status,
            total_amount=plan.total_amount,
        )
        db.add(order)
        db.flush()
        order_no = order.purchase_order_no

        db.add_all(
            PurchaseOrderDetail(
                purchase_order_no=order_no,
                prod_code=line.prod_code,
                qty=line.qty,
                unit_price=line.unit_price,
                net_price=line.net_price,
                vat=line.vat,
                total_amount=line.total_amount,
            )
            for line in plan.details
        )
        db.flush()

        db.add(
            AuditLog(
                purchase_order_no=order_no,
                action="INSERT",
                detail_count=len(plan.details),
                total_amount=plan.total_amount,
            )
        )
        db.flush()

    return order_no
