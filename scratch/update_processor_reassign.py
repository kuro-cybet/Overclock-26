with open('backend/app/services/whatsapp_message_processor.py', 'r', encoding='utf-8') as f:
    content = f.read()

import_target = 'from app.database.models.incident import Incident\n'
new_imports = 'from app.database.models.incident import Incident\nfrom app.database.models.report import Report\nfrom app.database.models.notification import Notification\n'
assert import_target in content, "import_target not found"
content = content.replace(import_target, new_imports)

old_block = '''                    db.query(WhatsAppConversation).filter(WhatsAppConversation.user_id == tu.id).update({"user_id": matched_user.id})
                    db.query(Incident).filter(Incident.reporter_id == tu.id).update({"reporter_id": matched_user.id})
                    db.delete(tu)'''

new_block = '''                    db.query(WhatsAppConversation).filter(WhatsAppConversation.user_id == tu.id).update({"user_id": matched_user.id})
                    db.query(Incident).filter(Incident.reporter_id == tu.id).update({"reporter_id": matched_user.id})
                    db.query(Report).filter(Report.reporter_id == tu.id).update({"reporter_id": matched_user.id})
                    db.query(Notification).filter(Notification.recipient_id == tu.id).update({"recipient_id": matched_user.id})
                    db.delete(tu)'''

assert old_block in content, "old_block not found"
content = content.replace(old_block, new_block)

with open('backend/app/services/whatsapp_message_processor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated whatsapp_message_processor.py successfully")

