frappe.listview_settings['Interview'] = {
    hide_name_column: true,
    add_fields: ["Status"],
    

    button: {
        show(doc) {
            return true;
        },
        get_label(doc) {
            return __("✉ Mail");
        },
        get_description(doc) {
            return __('Mail');
        },
        action(doc) {
            frappe.call({
                method: 'abid_app.hrms.interview.notifications.send_interview_notifications',
                args: {
                    interviews: doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(`
                            <b>Mail sent successfully</b><br><br>
                            <b>Applicant Email:</b> ${r.message.applicant_email || 'N/A'}<br>
                            <b>Interviewers:</b> ${(r.message.interviewer_emails || []).join(", ")}
                        `);
                    } else {
                        frappe.msgprint(__('Error sending notification for: {0}', [doc.name]));
                    }
                }

            });
        }
    }
};
