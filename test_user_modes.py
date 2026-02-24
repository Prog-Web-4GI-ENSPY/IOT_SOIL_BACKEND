from app.database import get_db
from app.models.user import User

db_gen = get_db()
db = next(db_gen)
user = db.query(User).first()

if user:
    print("User Email:", user.email)
    print("User Telephone:", user.telephone)
    print("Notification modes:", user.notification_modes)
else:
    print("No user found")
