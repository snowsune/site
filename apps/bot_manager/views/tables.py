from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from ..utils import has_fops_admin_access, get_fops_connection


@login_required
def table_data(request, table_name):
    """Display data from a specific table"""
    admin_access = has_fops_admin_access(request.user)
    if admin_access == "DECRYPTION_FAILED":
        messages.error(
            request, "Your Discord authentication has expired. Please log in again."
        )
        return redirect("bot_manager_dashboard")
    elif not request.user.discord_access_token or not admin_access:
        return redirect("bot_manager_dashboard")

    try:
        # Get table data from Fops database
        with get_fops_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM {table_name} LIMIT 100")
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()

        context = {
            "table_name": table_name,
            "columns": columns,
            "rows": rows,
        }
        response = render(request, "bot_manager/table_data.html", context)
        response["Vary"] = "Cookie"
        return response
    except Exception as e:
        messages.error(request, f"Error loading table data: {str(e)}")
        return redirect("bot_manager_dashboard")
