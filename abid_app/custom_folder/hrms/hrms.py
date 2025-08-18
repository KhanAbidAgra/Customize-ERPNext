import calendar
from frappe.utils import getdate
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip

class CustomSalarySlip(SalarySlip):
    def get_working_days_details(self, lwp=None, for_preview=0):
        # Call original method first to calculate leave, absent, etc.
        super().get_working_days_details(lwp, for_preview)

        if not self.end_date:
            return

        # Force total working days to days in month
        end_date = getdate(self.end_date)
        days_in_month = calendar.monthrange(end_date.year, end_date.month)[1]
        self.total_working_days = days_in_month

        # Recalculate payment days based on forced total
        leave = self.leave_without_pay or 0
        absent = self.absent_days or 0
        self.payment_days = days_in_month - leave - absent
