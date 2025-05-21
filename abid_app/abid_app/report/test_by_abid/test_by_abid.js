frappe.query_reports["Test By Abid"] = {
    onload: function(report) {
        report.page.add_inner_button(__('Create Journal Entry'), function() {
            // Get filtered report data excluding headers
            let sales_entries = report.data.filter(
                row => row.title && !row.title.startsWith("<b>") && row.vat_amount_sar
            );
            
            console.log("Filtered entries:", sales_entries);

            // Create new Journal Entry
            frappe.new_doc('Journal Entry').then(function(frm) {
                // Set main fields
                frm.set_value("company", frappe.query_report.get_filter_value("company"));
                frm.set_value("posting_date", frappe.datetime.get_today());
                frm.set_value("user_remark", "Being VAT Balance Transfer to VAT Payable Account");

                // Add accounts entries
                sales_entries.forEach(function(entry) {
                    let child = frm.add_child("accounts");
                    child.account = entry.title;
                    child.debit_in_account_currency = entry.vat_amount_sar;
                    child.credit_in_account_currency = 0;
                });

                // Refresh the accounts table
                frm.refresh_field("accounts");
            });
        }, __("Create"));
    }
};