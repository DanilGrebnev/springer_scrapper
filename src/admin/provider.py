from fastapi_admin.providers.login import UsernamePasswordProvider

from src.admin.models import Admin

login_provider = UsernamePasswordProvider(
    admin_model=Admin,
)
