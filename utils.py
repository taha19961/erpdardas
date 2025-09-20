import os
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import url_for

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, upload_dir, prefix=""):
    if file and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'pdf'}):
        filename = secure_filename(file.filename)
        unique_filename = f"{prefix}_{int(datetime.now().timestamp())}_{filename}"
        filepath = os.path.join(upload_dir, unique_filename)
        os.makedirs(upload_dir, exist_ok=True)
        file.save(filepath)
        return unique_filename, filepath
    return None, None

def log_activity(user, action, entity_type, entity_id=None, details=""):
    from models import AuditLog, db
    log = AuditLog(
        user_id=user.id if user else None,
        username=user.username if user else "system",
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details
    )
    db.session.add(log)
    db.session.commit()