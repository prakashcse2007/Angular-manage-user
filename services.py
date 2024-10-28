from db import get_db_connection
from schemas import ClaimRequest, ClaimResponse, ClaimLineItemResponse
from exceptions import ClaimProcessingException

def get_rate_sheets(conn, line_items):
    """
    Fetch rate sheet details for all line items in a single query.
    """
    placeholders = ', '.join(['%s'] * len(line_items))
    query = f"""
        SELECT rendering_npi, service_code, billing_provider_tin, postal_code,
               rate_sheet_id, rbrvs_percentage, flat_rate, rbrvs_amount
        FROM rate_sheets
        WHERE (rendering_npi, service_code, billing_provider_tin, postal_code) 
              IN ({placeholders})
    """

    params = [(item.rendering_npi, item.service_code, item.tin, item.postal_code)
              for item in line_items]
    
    with conn.cursor() as cur:
        cur.execute(query, [val for tup in params for val in tup])
        rows = cur.fetchall()
        
    if not rows:
        raise ClaimProcessingException("No rate sheets found for the provided line items.")

    # Create a lookup dictionary for quick access by keys (NPI, service code, etc.)
    return {(row['rendering_npi'], row['service_code'], 
             row['billing_provider_tin'], row['postal_code']): row for row in rows}

def process_claim(claim_data: ClaimRequest) -> ClaimResponse:
    conn = get_db_connection()
    try:
        # Fetch all rate sheets in a single query
        rate_sheets = get_rate_sheets(conn, claim_data.line_items)

        total_billed = total_diff = total_commission = 0.0
        processed_line_items = []

        for line in claim_data.line_items:
            rate_data = rate_sheets.get(
                (line.rendering_npi, line.service_code, line.tin, line.postal_code)
            )

            if not rate_data:
                raise ClaimProcessingException(
                    f"Rate sheet not found for item {line.item_id}."
                )

            billed_amount = (
                rate_data['flat_rate'] if rate_data['flat_rate'] 
                else (rate_data['rbrvs_percentage'] / 100) * rate_data['rbrvs_amount']
            )
            differential_amount = billed_amount - line.provider_allowed_amount

            # Calculate commission and process codes
            commission, code = calculate_commission_and_code(
                differential_amount=differential_amount,
                billable_amount=billed_amount,
                flat_rate=rate_data['flat_rate']
            )

            total_billed += billed_amount
            total_diff += differential_amount
            total_commission += commission

            processed_line_items.append({
                **line.dict(),
                "rate_sheet_id": rate_data['rate_sheet_id'],
                "billed_amount": billed_amount,
                "differential_amount": differential_amount,
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