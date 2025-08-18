import frappe
from frappe.model.document import Document
from erpnext.manufacturing.doctype.bom.bom import get_bom_items_as_dict

def get_default_warehouse(item_code, company, fallback=None):
    """Fetch default warehouse for an item or return fallback."""
    return frappe.db.get_value("Item Default", {
        "parent": item_code,
        "company": company
    }, "default_warehouse") or fallback

def after_submit(doc, method):
    if not doc.is_return or not doc.update_stock:
        return

    for si_item in doc.items:
        if not frappe.db.get_value("Item", si_item.item_code, "is_stock_item"):
            continue

        # Get default BOM
        bom = frappe.db.get_value("BOM", {
            "item": si_item.item_code,
            "is_default": 1,
            "is_active": 1
        })
        if not bom:
            frappe.msgprint(f"No BOM found for item {si_item.item_code}")
            continue

        # Get BOM quantity (important for ratio calculations)
        bom_qty = frappe.db.get_value("BOM", bom, "quantity") or 1
        if bom_qty == 0:
            frappe.throw(f"BOM quantity is 0 for BOM {bom}. Cannot create Stock Entry.")

        # Create Stock Entry (Repack)
        se = frappe.new_doc("Stock Entry")
        se.update({
            "purpose": "Disassemble",
            "stock_entry_type": "Disassemble",
            "company": doc.company,
            "set_posting_time": 1,
            "posting_date": doc.posting_date,
            "posting_time": doc.posting_time,
            "from_bom": 1,
            "bom_no": bom,
            "use_multi_level_bom": 1,
            "fg_completed_qty": abs(si_item.qty),
            "remark": f"De-assembled from Sales Invoice Return {doc.name}"
        })

        # Add FG item (returned item)
        se.append("items", {
            "item_code": si_item.item_code,
            "qty": abs(si_item.qty),
            "s_warehouse": si_item.warehouse,
            "is_finished_item": 1,
            "expense_account": "Return Wastage - FH"
        })

        # Add Scrap Items if any
        scrap_items = frappe.get_all("BOM Scrap Item", filters={"parent": bom}, fields=["item_code", "stock_qty"])
        for scrap in scrap_items:
            if not scrap.stock_qty:
                continue

            valuation_rate = frappe.db.get_value("Item", scrap.item_code, "valuation_rate") or 0
            se.append("items", {
                "item_code": scrap.item_code,
                "qty": (scrap.stock_qty / bom_qty) * abs(si_item.qty),
                "s_warehouse": get_default_warehouse(scrap.item_code, doc.company, fallback=si_item.warehouse),
                "valuation_rate": valuation_rate,
                "is_scrap_item": 1,
                "expense_account": "Return Wastage - FH"
            })

        # Add BOM raw materials
        bom_items = get_bom_items_as_dict(
            bom, company=doc.company, qty=abs(si_item.qty), fetch_exploded=1
        )

        for item_code, bom_item in bom_items.items():
            # Skip if Item Group is Consumables
            item_group = frappe.db.get_value("Item", item_code, "item_group")
            if item_group == "Consumables":
                continue

            se.append("items", {
                "item_code": item_code,
                "qty": bom_item["qty"],
                "t_warehouse": get_default_warehouse(item_code, doc.company, fallback=si_item.warehouse),
                "is_finished_item": 0,
                "expense_account": "Return Wastage - FH"
            })

        se.insert(ignore_permissions=True)
        se.custom_sales_invoice_reference = doc.name
        se.submit()
        frappe.msgprint(f"Repack Stock Entry {se.name} Created for {si_item.item_code}")

