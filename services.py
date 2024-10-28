from db import get_db_connection
from schemas import ClaimRequest, ClaimResponse, ClaimLineItemResponse

def calculate_commission_and_code(
    differential_amount: float, 
    billable_amount: float, 
    flat_rate: float = None, 
    threshold: float = 150.0
) -> tuple[float, str]:
    """
    Calculate the payment amount with flat rate and determine process codes.
    """
    ten_percent_billable = 0.10 * billable_amount

    # Calculate payment amount considering flat rate
    if flat_rate is not None and flat_rate < threshold:
        payment_amount = min(flat_rate, ten_percent_billable)
    else:
        payment_amount = min(threshold, ten_percent_billable)

    # Determine process codes
    process_codes = []
    if differential_amount < threshold:
        process_codes.append("TFDA")
    if ten_percent_billable < 150:
        process_codes.append("TPBA")

    process_code = ",".join(process_codes)
    return payment_amount, process_code

def process_claim(claim_data: ClaimRequest) -> ClaimResponse:
    conn = get_db_connection()
    try:
        total_billed = total_diff = total_commission = 0.0
        processed_line_items = []

        for line in claim_data.line_items:
            result = process_claim_line_item(conn, line)

            commission, code = calculate_commission_and_code(
                differential_amount=result.differential_amount,
                billable_amount=result.billed_amount,
                flat_rate=result.flat_rate
            )

            total_billed += result.billed_amount
            total_diff += result.differential_amount
            total_commission += commission

            processed_line_items.append({
                **result.dict(),
                "commission_amount": commission,
                "process_code": code
            })

        return ClaimResponse(
            claim_id=claim_data.claim_id,
            total_billed_amount=total_billed,
            total_differential_amount=total_diff,
            total_commission_amount=total_commission,
            line_items=processed_line_items
        )
    finally:
        conn.close()

def process_claim_line_item(conn, line_item):
    # Simulate a database call to fetch rate sheet data
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT rate_sheet_id, rbrvs_percentage, flat_rate, rbrvs_amount
            FROM rate_sheets
            WHERE rendering_npi = %s AND service_code = %s 
              AND billing_provider_tin = %s AND postal_code = %s
            """,
            (line_item.rendering_npi, line_item.service_code, 
             line_item.tin, line_item.postal_code)
        )
        row = cur.fetchone()

    if row:
        rate_sheet_id, percentage, flat_rate, rbrvs_amount = row
        billed_amount = flat_rate if flat_rate else (percentage / 100) * rbrvs_amount
        differential_amount = billed_amount - line_item.provider_allowed_amount

        return ClaimLineItemResponse(
            item_id=line_item.item_id,
            rendering_npi=line_item.rendering_npi,
            service_code=line_item.service_code,
            tin=line_item.tin,
            postal_code=line_item.postal_code,
            provider_allowed_amount=line_item.provider_allowed_amount,
            rate_sheet_id=rate_sheet_id,
            billed_amount=billed_amount,
            differential_amount=differential_amount,
            flat_rate=flat_rate
        )
    else:
        raise ValueError("Rate sheet not found for the given parameters.")