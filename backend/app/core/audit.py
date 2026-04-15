import json
from functools import wraps
from sqlalchemy.orm import Session
from app.models.models import ActivityLog
import asyncio

# 1. HÀM LÕI THỰC THI GHI VÀO DATABASE
def log_action(db: Session, user_id: int, module: str, action: str, entity: str, entity_id: int, old_data: dict, new_data: dict, event_name: str, ip: str = "127.0.0.1"):
    try:
        print(f"[DEBUG-LOG] Đang chuẩn bị ghi log cho {module}...")
        
        # Lọc bỏ thuộc tính hệ thống của SQLAlchemy
        if new_data and '_sa_instance_state' in new_data:
            new_data.pop('_sa_instance_state', None)
        if old_data and '_sa_instance_state' in old_data:
            old_data.pop('_sa_instance_state', None)

        # CHÚ Ý: Đã thêm default=str để fix lỗi không lưu được Ngày tháng
        log = ActivityLog(
            user_id=user_id,
            module_name=module,
            action_type=action,
            entity_type=entity,
            entity_id=entity_id,
            old_data_json=json.dumps(old_data, ensure_ascii=False, default=str) if old_data else None,
            new_data_json=json.dumps(new_data, ensure_ascii=False, default=str) if new_data else None,
            event_name=event_name,
            ip_address=ip
        )
        db.add(log)
        db.commit()
        print(f"[DEBUG-LOG] => GHI LOG THÀNH CÔNG VÀO DATABASE!")
    except Exception as e:
        print(f"[AUDIT LOG ERROR] LỖI RỒI: {e}")
        db.rollback()

# 2. DECORATOR DÙNG ĐỂ GẮN LÊN CÁC API
def audit_log(module: str, action: str, event_name: str):
    def decorator(func):
        # Hàm xử lý log dùng chung
        def _process_audit(kwargs_dict, result):
            db = kwargs_dict.get('db')
            current_user = kwargs_dict.get('current_admin') or kwargs_dict.get('current_user')
            
            if not db:
                print(f"[DEBUG-LOG] CẢNH BÁO: Không tìm thấy biến 'db' ở API {func.__name__}")
            if not current_user:
                print(f"[DEBUG-LOG] CẢNH BÁO: Không tìm thấy 'current_admin' ở API {func.__name__}")

            if db and current_user:
                if isinstance(result, dict):
                    entity_id = result.get('id') or result.get('tournament_id') # Lấy ID từ dict
                else:
                    entity_id = getattr(result, 'id', None) # Lấy ID từ Object
                new_data = {}
                # Lấy dữ liệu trả về từ API
                if hasattr(result, '__dict__'):
                    new_data = result.__dict__.copy()
                elif isinstance(result, dict):
                    new_data = result.copy()

                log_action(db, current_user.id, module, action, module.capitalize(), entity_id, None, new_data, event_name)

        # Hỗ trợ API dùng Async
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                _process_audit(kwargs, result)
                return result
            return async_wrapper
        
        # Hỗ trợ API dùng def bình thường
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                _process_audit(kwargs, result)
                return result
            return sync_wrapper

    return decorator